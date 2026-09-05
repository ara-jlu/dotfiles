#!/usr/bin/env python3
"""j-finish — output adapter that finishes a completed branch into the
pre-approval resting state, then hands off to the human approval gate.

It performs the FULL pre-approval finish, in a fixed order so the PR URL is
captured before it is referenced downstream:

  1. push the branch
  2. open the PR (body authored in Japanese by the caller; --pr-body-file)
  3. attach UAT evidence to the PR as a comment (--uat-evidence-dir; screenshots
     and videos, never committed to the repo)
  4. move the Joifup Task -> "In review" (SURGICAL: only the status line;
     every other frontmatter key/relation/body byte is preserved)
  5. notify Discord (Japanese, scoped mention, PR link)

It never marks the task Done and never merges — the human's approval session
owns status->Done + `chore(joifup): approve TASK-xxx` + merge.

Network/side-effect steps (git/gh/curl) are gated by --dry-run, which prints
the exact commands instead of running them. The local file mechanics (status
edit) runs in both modes so it can be verified. Two read-only steps also run
in both modes, because they change nothing and their answers are what makes
the dry run worth reading: the UAT evidence pre-flight, and the evidence
attach's own `gh --version` check, its read of results.jsonl, and its
containment check on every evidence path (which stats the filesystem and can
stop the run).
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uat_attach import AttachError, attach_evidence  # noqa: E402,F401

# gh pr create が stdout を返さなかった (dry-run / 空応答) ときの pr_url 初期値。
# この値のまま attach_evidence() に渡すと `gh pr comment <PR_URL> ...` が実行され、
# 本当の原因 (URL を取れなかったこと) ではなく無意味な placeholder 名でエラーになる。
PLACEHOLDER_PR_URL = "<PR_URL>"


def die(msg):
    sys.exit(f"j-finish: {msg}")


def _pr_url_missing(pr_url):
    """gh pr create から実際の PR URL を取得できていないかを判定する。"""
    return not pr_url or pr_url == PLACEHOLDER_PR_URL


def _skipped_attach_warning(evidence_dir):
    """--no-pr と --uat-evidence-dir を併せて渡されたときの警告文。

    --no-pr は「PR はもうある」の意味なので添付だけを飛ばす。ただし黙って
    飛ばすと、証跡を付け忘れたまま status と Discord まで進む。止めずに
    言うだけにするのは、添付失敗時の復旧手順 (手で uat_attach.py を叩いて
    から --no-pr で再実行) がまさにこの組み合わせを通るため。
    """
    return ("j-finish: WARNING — --no-pr のため証跡の添付は行いません。"
            f" {evidence_dir} を手で添付済みか確認してください:"
            " python3 scripts/uat_attach.py --evidence-dir"
            f" {evidence_dir} --pr <PR URL>")


def _attach_failure_message(exc, pr_url, evidence_dir, script_dir, dry_run):
    """UAT 証跡の添付が失敗したときの die() メッセージを組み立てる。

    real run では、この時点で push と PR 作成は完了していて、タスクの
    ステータス変更と Discord 通知はまだ実行していない (半端な「成功」に
    見える状態を作らないための意図的な停止)。人が残りを手で進められるよう
    復旧コマンドを示す。

    証跡がどこまで進んだかは 3 通りあり、案内が変わる。添付は取り消せない
    ので、コメントが既にある可能性がある限り「手動で証跡を添付しろ」とは
    言わない (二重にアップロードさせてしまう)。

      - comment_url あり: コメントは投稿済み。残りは本文リンクだけ。
      - comment_maybe_posted のみ: gh が部分失敗したか URL を返さなかった。
        コメントは在るかもしれないし無いかもしれない。人が PR を見て決める。
      - どちらも無い: コメントは作られていない。素直に再実行できる。

    --dry-run では push も PR 作成も実行されていない (run() がコマンドを
    印字するだけ) にもかかわらず、attach_evidence() 自体は gh のバージョン
    チェック・results.jsonl の読み取り・50 件上限・証跡パスの封じ込め検査を
    dry_run 分岐より先に行うため AttachError が実際に届きうる。real run と
    同じ文面を返すと「push 済み・PR 作成済み」という嘘になるので、dry_run
    のときは何も実行されていない・状態は変わっていないと明言する。
    """
    if dry_run:
        return (
            f"UAT 証跡の添付に失敗 (--dry-run): {exc}\n"
            f"証跡ディレクトリ: {evidence_dir}\n"
            "--dry-run 実行のため、ブランチは push されておらず PR も"
            "作成されていません。状態は何も変わっていません。"
        )
    uat_attach = os.path.join(script_dir, "uat_attach.py")
    posted = getattr(exc, "comment_url", None)
    maybe_posted = getattr(exc, "comment_maybe_posted", False)
    if not posted and maybe_posted:
        return (
            f"UAT 証跡の添付に失敗: {exc}\n"
            f"ブランチは push 済み、PR も作成済みです ({pr_url})。"
            "証跡コメントが作られているかどうかは判りません — gh は部分失敗の"
            "とき、成功したぶんでコメントを作ってから落ちます。添付は"
            "取り消せないので、**確認せずに再実行しないでください**。\n"
            "タスクのステータスは変更しておらず、Discord にも通知していません。\n"
            "復旧手順:\n"
            f"  1) {pr_url} を開き、証跡コメントの有無と添付の欠けを確認する\n"
            "  2) コメントが無い、または作り直す場合のみ:\n"
            f"     python3 {uat_attach} --evidence-dir {evidence_dir}"
            f" --pr {pr_url}\n"
            "  3) その後 j_finish.py を --no-pr 付きで再実行し、"
            "ステータス変更と Discord 通知を完了させてください。"
        )
    if posted:
        return (
            f"UAT 証跡の添付に失敗: {exc}\n"
            f"ブランチは push 済み、PR も作成済みです ({pr_url})。"
            f"証跡コメントは投稿済みです ({posted}) — 添付は取り消せないので、"
            "**もう一度添付しないでください**。残っているのは PR 本文の"
            " `## UAT 証跡` 節にこのコメントへのリンクを足すことだけです。\n"
            "タスクのステータスは変更しておらず、Discord にも通知していません。\n"
            "復旧手順:\n"
            f"  1) PR 本文の `## UAT 証跡` 節に `証跡コメント: {posted}` を"
            "手で足す\n"
            "  2) その後 j_finish.py を --no-pr 付きで再実行し、"
            "ステータス変更と Discord 通知を完了させてください。"
        )
    return (
        f"UAT 証跡の添付に失敗: {exc}\n"
        f"ブランチは push 済み、PR も作成済みです ({pr_url})。"
        "証跡はまだ添付されていません。"
        "タスクのステータスは変更しておらず、Discord にも通知していません。\n"
        "復旧手順:\n"
        f"  1) 手動で証跡を添付する:\n"
        f"     python3 {uat_attach} --evidence-dir {evidence_dir} --pr {pr_url}\n"
        "  2) その後 j_finish.py を --no-pr 付きで再実行し、"
        "ステータス変更と Discord 通知を完了させてください。"
    )


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


def _changed_paths(head_range):
    """push 範囲で変わったパス。git が失敗したら空 (チェックを黙って諦める)。"""
    try:
        return subprocess.run(
            ["git", "diff", "--name-only", head_range],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines()
    except (subprocess.CalledProcessError, OSError):
        return []


def _warn_uat_evidence(changed, evidence_dir, exists=os.path.isfile):
    """UAT 証跡まわりを警告する (never blocks)。返り値は出した警告の一覧。

    joifup tasks/295 で証跡は commit せず PR に添付する形になった。旧実装は
    「diff に .uat-evidence/ が無ければ警告」で、意味がちょうど反転していた。
    見るべきものは 2 つに変わる:

      1. UI を変えたのに `pnpm uat` を回した形跡 (results.jsonl) が手元に無い
         — 証跡ゼロの PR が出る
      2. .uat-evidence/ が commit されている — 新しい失敗様式。gitignore が
         無い repo で起きる

    ブロックしないのは旧実装と同じ: apps/web の diff が非 UI (config だけ)
    のこともあるため。
    """
    warnings = []
    touches_ui = any(p.startswith("apps/web/") and not p.startswith("apps/web/e2e/")
                     for p in changed)
    committed = [p for p in changed if p.startswith(".uat-evidence/")]
    if committed:
        warnings.append(
            "j-finish: WARNING — .uat-evidence/ が commit されています "
            f"（例: {committed[0]}）。証跡は commit せず PR に添付します。"
            " .gitignore を確認してください")
    if touches_ui:
        if not evidence_dir:
            warnings.append(
                "j-finish: WARNING — apps/web が変わっていますが "
                "--uat-evidence-dir が指定されていません。証跡が PR に付きません")
        elif not exists(os.path.join(evidence_dir, "results.jsonl")):
            warnings.append(
                f"j-finish: WARNING — apps/web が変わっていますが {evidence_dir}"
                "/results.jsonl がありません。`pnpm uat --task <id>` を回して"
                " ください")
    for w in warnings:
        print(w, file=sys.stderr)
    return warnings


def main():
    ap = argparse.ArgumentParser(prog="j-finish")
    ap.add_argument("--task-file", required=True, help="Joifup Task md to finish")
    ap.add_argument("--pr-title", required=True)
    ap.add_argument("--pr-body-file", required=True, help="Japanese PR body (file)")
    ap.add_argument("--base", default="main")
    ap.add_argument("--head", help="branch (default: current)")
    ap.add_argument("--status", default="In review", help="pre-approval status")
    ap.add_argument("--no-pr", action="store_true")
    ap.add_argument("--no-discord", action="store_true")
    ap.add_argument("--uat-evidence-dir",
                    help="UAT 証跡 dir（例: .uat-evidence/005）。"
                         "指定すると PR 作成後に証跡コメントを添付する")
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

    # Pre-flight (read-only, advisory): warn if apps/web changed without a
    # local UAT evidence run, or if .uat-evidence/ was committed. Runs even
    # under --dry-run; never blocks, since not every apps/web diff is UI-facing.
    _warn_uat_evidence(_changed_paths(f"origin/{args.base}...HEAD"),
                       args.uat_evidence_dir)

    # 1. push
    run(["git", "push", "-u", "origin", head], args.dry_run)

    # 2. PR
    pr_url = PLACEHOLDER_PR_URL
    if not args.no_pr:
        out = run(["gh", "pr", "create", "--base", args.base, "--head", head,
                   "--title", args.pr_title, "--body-file", args.pr_body_file],
                  args.dry_run)
        if not args.dry_run and out:
            pr_url = out.splitlines()[-1].strip()

    # 3. UAT 証跡コメント（画像・動画を PR に添付）
    if args.uat_evidence_dir and args.no_pr:
        print(_skipped_attach_warning(args.uat_evidence_dir), file=sys.stderr)
    if args.uat_evidence_dir and not args.no_pr:
        if not args.dry_run and _pr_url_missing(pr_url):
            die("gh pr create から PR URL を取得できませんでした。"
                f"証跡 ({args.uat_evidence_dir}) を添付できません")
        task_id = os.path.basename(args.uat_evidence_dir.rstrip("/"))
        try:
            # required=True: --uat-evidence-dir を明示的に渡した以上、
            # 証跡ゼロは「UI を変えない PR」ではなく指定ミスか uat の回し
            # 忘れ。黙って通すと PASS 表示のまま In review + Discord まで進む。
            comment_url = attach_evidence(pr_url, args.uat_evidence_dir, task_id,
                                          args.dry_run, required=True)
        except AttachError as exc:
            die(_attach_failure_message(
                exc, pr_url, args.uat_evidence_dir,
                os.path.dirname(os.path.abspath(__file__)), args.dry_run))
        if comment_url:
            print(f"UAT 証跡: {comment_url}")

    # 4. surgical status edit (runs in dry-run too, so it is verifiable)
    surgical_status(args.task_file, args.status)
    print(f"status -> {args.status}: {args.task_file}")

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
