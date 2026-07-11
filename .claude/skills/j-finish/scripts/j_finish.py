#!/usr/bin/env python3
"""j-finish — output adapter that finishes a completed branch into the
pre-approval resting state, then hands off to the human approval gate.

It performs the FULL pre-approval finish, in a fixed order so the PR URL is
captured before it is referenced downstream:

  1. push the branch
  2. open the PR (body authored in Japanese by the caller; --pr-body-file)
  3. move the Joifup Task -> "In review" (SURGICAL: only the status line;
     every other frontmatter key/relation/body byte is preserved)
  4. file a user-action Task ("承認待ち") as a child of the task, so the
     approval surfaces in the human's Joifup task list
  5. notify Discord (Japanese, scoped mention, PR link)

It never marks the task Done and never merges — the human's approval session
owns status->Done + `chore(joifup): approve TASK-xxx` + merge.

Network/side-effect steps (git/gh/curl) are gated by --dry-run, which prints
the exact commands instead of running them. The local file mechanics (status
edit, user-action task) run in both modes so they can be verified.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:
    sys.exit("j-finish: PyYAML is required (pip install pyyaml)")


def die(msg):
    sys.exit(f"j-finish: {msg}")


def find_schema(db, start_dir):
    d = os.path.abspath(start_dir)
    while True:
        cand = os.path.join(d, ".joifup", "databases", db, "schema.yaml")
        if os.path.isfile(cand):
            return cand
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    home = os.path.join(os.path.expanduser("~"), ".joifup", "databases", db,
                        "schema.yaml")
    if os.path.isfile(home):
        return home
    die(f"could not locate {db} schema.yaml (repo .joifup/ or ~/.joifup/)")


def valid_status_values(tasks_dir):
    schema = yaml.safe_load(open(find_schema("tasks", tasks_dir), encoding="utf-8"))
    groups = schema.get("properties", {}).get("status", {}).get("groups", {})
    vals = set()
    for opts in groups.values():
        for o in opts:
            vals.add(o["value"])
    return vals


def run(cmd, dry_run):
    printable = " ".join(cmd)
    if dry_run:
        print(f"[dry-run] {printable}")
        return ""
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        die(f"command failed: {printable}\n{res.stderr.strip()}")
    return res.stdout.strip()


def surgical_status(task_file, new_status):
    """Replace ONLY the status value inside the frontmatter block."""
    text = open(task_file, encoding="utf-8").read()
    if not text.startswith("---\n"):
        die(f"task file has no frontmatter: {task_file}")
    end = text.find("\n---\n", 4)
    if end == -1:
        die(f"unterminated frontmatter: {task_file}")
    head, body = text[:end + 1], text[end + 1:]
    new_head, n = re.subn(r"(?m)^status:[ \t]*.*$", f"status: {new_status}", head)
    if n == 0:
        die("no `status:` line found in task frontmatter")
    open(task_file, "w", encoding="utf-8").write(new_head + body)


def read_title(task_file):
    for line in open(task_file, encoding="utf-8"):
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip()
    return os.path.splitext(os.path.basename(task_file))[0]


def next_number(d):
    if not os.path.isdir(d):
        return "001"
    nums = [int(m.group(1)) for name in os.listdir(d)
            if (m := re.match(r"^(\d+)-", name))]
    return str((max(nums) + 1) if nums else 1).zfill(3)


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


_QUOTE_START = "-?:#&*!|>'\"%@`,[]{} "


def fmt_scalar(v):
    if not isinstance(v, str):
        return str(v)
    if v == "" or v[0] in _QUOTE_START or v[-1] == " " or ":" in v or "#" in v:
        return "'" + v.replace("'", "''") + "'"
    return v


def emit_frontmatter(items):
    lines = []
    for k, v in items:
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(fmt_scalar(x) for x in v)}]")
        else:
            lines.append(f"{k}: {fmt_scalar(v)}")
    return "\n".join(lines)


def file_user_action(tasks_dir, parent_id, parent_title, project, pr_url):
    """Create a '承認待ち' Task as a child of the finished task."""
    num = next_number(tasks_dir)
    slug = slugify(f"approve {parent_title}") or "approve"
    dest = os.path.join(tasks_dir, f"{num}-{slug}.md")
    today = datetime.date.today().isoformat()
    items = [("title", f"承認待ち: {parent_title}"),
             ("status", "Not started"),
             ("parent", parent_id)]
    if project:
        items.append(("Project", project))  # single value -> scalar
    items += [("created_at", today), ("updated_at", today)]
    fm_yaml = emit_frontmatter(items)
    body = (f"# 承認待ち: {parent_title}\n\n"
            f"レビュー承認をお願いします。承認後、このセッションで親Taskを "
            f"`In review` → `Done` に更新し main へマージしてください。\n\n"
            f"- PR: {pr_url}\n- 親Task: {parent_id}\n")
    open(dest, "w", encoding="utf-8").write(f"---\n{fm_yaml}\n---\n\n{body}")
    return dest


def main():
    ap = argparse.ArgumentParser(prog="j-finish")
    ap.add_argument("--task-file", required=True, help="Joifup Task md to finish")
    ap.add_argument("--pr-title", required=True)
    ap.add_argument("--pr-body-file", required=True, help="Japanese PR body (file)")
    ap.add_argument("--base", default="main")
    ap.add_argument("--head", help="branch (default: current)")
    ap.add_argument("--status", default="In review", help="pre-approval status")
    ap.add_argument("--project", help="Project id to inherit onto the action task")
    ap.add_argument("--no-pr", action="store_true")
    ap.add_argument("--no-user-action", action="store_true")
    ap.add_argument("--no-discord", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.task_file):
        die(f"task file not found: {args.task_file}")
    if not os.path.isfile(args.pr_body_file):
        die(f"pr body file not found: {args.pr_body_file}")

    tasks_dir = os.path.dirname(os.path.abspath(args.task_file))
    valid = valid_status_values(tasks_dir)
    if args.status not in valid:
        die(f"--status '{args.status}' not in schema: {sorted(valid)}")
    if args.status in ("Done", "Cancelled"):
        die("j-finish never sets a complete-group status; the human owns Done")

    parent_id = os.path.splitext(os.path.basename(args.task_file))[0]
    parent_title = read_title(args.task_file)

    head = args.head or run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                            dry_run=False) or "HEAD"

    # 1. push
    run(["git", "push", "-u", "origin", head], args.dry_run)

    # 2. PR
    pr_url = "<PR_URL>"
    if not args.no_pr:
        out = run(["gh", "pr", "create", "--base", args.base, "--head", head,
                   "--title", args.pr_title, "--body-file", args.pr_body_file],
                  args.dry_run)
        if not args.dry_run and out:
            pr_url = out.splitlines()[-1].strip()

    # 3. surgical status edit (runs in dry-run too, so it is verifiable)
    surgical_status(args.task_file, args.status)
    print(f"status -> {args.status}: {args.task_file}")

    # 4. user-action task
    if not args.no_user_action:
        dest = file_user_action(tasks_dir, parent_id, parent_title,
                                args.project, pr_url)
        print(f"user-action task: {dest}")

    # 5. Discord — rich embed (matches auto-workflow/scripts/discord-notify.sh:
    #    title / description / color / fields[プロジェクト, ブランチ] / timestamp)
    if not args.no_discord:
        webhook = os.environ.get("DISCORD_WEBHOOK_URL", "")
        mention = os.environ.get("DISCORD_MENTION_USER", "")
        color = int(os.environ.get("DISCORD_COLOR", "5814783"))  # 0x58B0FF
        project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
        project_name = os.path.basename(os.path.abspath(project_dir))
        description = (f"お疲れ様です。\n"
                       f"**{parent_title}** タスクの実装が完了しました。\n"
                       f"レビューをお願いいたします。\n"
                       f"PR: {pr_url}")
        timestamp = datetime.datetime.now(
            datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        embed = {
            "title": "👀 レビュー依頼",
            "description": description,
            "color": color,
            "fields": [
                {"name": "プロジェクト", "value": project_name, "inline": True},
                {"name": "ブランチ", "value": head, "inline": True},
            ],
            "timestamp": timestamp,
        }
        payload = json.dumps({
            "content": f"<@{mention}>" if mention else "",
            "embeds": [embed],
            "allowed_mentions": {"users": [mention] if mention else []},
        }, ensure_ascii=False)
        if not webhook and not args.dry_run:
            die("DISCORD_WEBHOOK_URL not set")
        run(["curl", "-sS", "-X", "POST", webhook or "$DISCORD_WEBHOOK_URL",
             "-H", "Content-Type: application/json", "-d", payload], args.dry_run)

    print(f"\nHANDOFF: human approves -> set {parent_id} status Done, "
          f"commit `chore(joifup): approve {parent_id}`, merge PR.")


if __name__ == "__main__":
    main()
