#!/usr/bin/env python3
"""md2joifup — persist a markdown file as a Joifup Notes-DB row (frontmatter +
body), in place. The source may be a superpowers artifact (plan/spec) or a
hand-authored note (doc/log/research); either way it becomes a house-style
Joifup note.

The tool reads the *authoritative* Notes schema (never hardcodes
frontmatter/tag/relation conventions) and:
  - extracts the H1 -> mirrors it into frontmatter `title`
  - strips superpowers agentic-worker scaffolding from the body (no-op for
    hand-authored notes)
  - matches the Joifup house frontmatter style: flow arrays (`tag: [plan]`),
    a single relation value as a scalar and 2+ as a flow array
  - stamps `created_at`/`updated_at` (today) unless the source already has them
  - names the file `<NNN>-<slug>.md` under `notes/<type>/`
    (NNN = related task's id number, else next number in the dir)
  - moves the source into place (use --keep-source to copy instead)

Task/Project resolution:
  - `--task <id>`: link an existing Task (branch-detection is the caller's job;
    resolve the current TASK-id and pass it here).
  - `--new-task "<title>"`: create a fresh Joifup Task (house style) and link
    it — for a note that spawns its own task (e.g. a new investigation).
  - Project: `--project` > the new/linked Task's Project > the sole project in
    `projects/`, so every note carries a Project.

Only the auto-increment `ID` is left to the daemon.
"""
import argparse
import datetime
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("md2joifup: PyYAML is required (pip install pyyaml)")


def die(msg):
    sys.exit(f"md2joifup: {msg}")


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


def load_schema(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def split_frontmatter(text):
    """Return (frontmatter_dict, body_str). No frontmatter -> ({}, text)."""
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            fm = yaml.safe_load(text[4:end + 1]) or {}
            body = text[end + 5:]
            return fm, body
    return {}, text


def extract_h1(body):
    for line in body.splitlines():
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip()
    return None


SCAFFOLD_MARKERS = ("For agentic workers", "REQUIRED SUB-SKILL", "superpowers:")


def strip_scaffolding(body):
    """Drop superpowers blockquote scaffolding and collapse blank runs."""
    kept = []
    for line in body.splitlines():
        if line.lstrip().startswith(">") and any(
            marker in line for marker in SCAFFOLD_MARKERS
        ):
            continue
        kept.append(line)
    out = "\n".join(kept)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip() + "\n"


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


_QUOTE_START = "-?:#&*!|>'\"%@`,[]{} "


def fmt_scalar(v):
    """Render a YAML scalar, quoting only when needed (matches house style)."""
    if not isinstance(v, str):
        return str(v)
    if v == "" or v[0] in _QUOTE_START or v[-1] == " " or ":" in v or "#" in v:
        return "'" + v.replace("'", "''") + "'"
    return v


def emit_frontmatter(items):
    """Emit ordered (key, value) pairs: lists as flow arrays, else scalars."""
    lines = []
    for k, v in items:
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(fmt_scalar(x) for x in v)}]")
        else:
            lines.append(f"{k}: {fmt_scalar(v)}")
    return "\n".join(lines)


def rel_val(ids):
    return ids[0] if len(ids) == 1 else ids


def task_number(task_ids):
    for t in task_ids:
        m = re.search(r"\d+", str(t))
        if m:
            return str(int(m.group())).zfill(3)
    return None


def next_number(dest_dir):
    if not os.path.isdir(dest_dir):
        return "001"
    nums = []
    for name in os.listdir(dest_dir):
        m = re.match(r"^(\d+)-", name)
        if m:
            nums.append(int(m.group(1)))
    return str((max(nums) + 1) if nums else 1).zfill(3)


def inherit_project(tasks_dir, task_ids):
    """Read the linked Task's Project so every note carries one (house style)."""
    num = task_number(task_ids)
    if not num or not os.path.isdir(tasks_dir):
        return []
    for name in sorted(os.listdir(tasks_dir)):
        m = re.match(r"^0*(\d+)-", name)
        if m and int(m.group(1)) == int(num):
            src, _ = split_frontmatter(
                open(os.path.join(tasks_dir, name), encoding="utf-8").read())
            p = src.get("Project")
            if p is None:
                return []
            return p if isinstance(p, list) else [p]
    return []


def primary_project(notes_dir):
    """The sole top-level project in projects/, used as the last-resort Project."""
    root = os.path.dirname(os.path.abspath(notes_dir))
    pdir = os.path.join(root, "projects")
    if not os.path.isdir(pdir):
        return []
    files = [f for f in os.listdir(pdir) if f.endswith(".md")]
    return [os.path.splitext(files[0])[0]] if len(files) == 1 else []


def create_task(tasks_dir, title, project, status="In progress", slug=None):
    """Create a house-style Joifup Task and return its id (filename stem)."""
    os.makedirs(tasks_dir, exist_ok=True)
    num = next_number(tasks_dir)
    slug = slug or slugify(title) or "task"
    task_id = f"{num}-{slug}"
    today = datetime.date.today().isoformat()
    items = [("title", title), ("status", status)]
    if project:
        items.append(("Project", rel_val(project)))
    items += [("created_at", today), ("updated_at", today)]
    out = f"---\n{emit_frontmatter(items)}\n---\n\n# {title}\n"
    with open(os.path.join(tasks_dir, f"{task_id}.md"), "w",
              encoding="utf-8") as f:
        f.write(out)
    return task_id


def parse_csv(values):
    out = []
    for v in values or []:
        out.extend(part.strip() for part in v.split(",") if part.strip())
    return out


def main():
    ap = argparse.ArgumentParser(prog="md2joifup")
    ap.add_argument("source", help="source markdown (sp artifact or hand-authored)")
    ap.add_argument("--db", choices=["notes", "tasks"], default="notes",
                    help="target Joifup DB (default: notes)")
    ap.add_argument("--type",
                    help="Notes content tag (notes db)")
    ap.add_argument("--status", default="Not started",
                    help="Task status (tasks db)")
    ap.add_argument("--parent", help="parent Task id (tasks db)")
    ap.add_argument("--project", action="append",
                    help="Project id(s); repeat or comma-separate")
    ap.add_argument("--task", action="append",
                    help="existing Task id(s) to link; repeat or comma-separate")
    ap.add_argument("--new-task", metavar="TITLE",
                    help="create a fresh Task with this title and link it")
    ap.add_argument("--new-task-slug", metavar="SLUG",
                    help="English slug for the created Task filename "
                         "(recommended for non-ASCII titles)")
    ap.add_argument("--notes-dir", default="notes",
                    help="Notes root dir (default: ./notes)")
    ap.add_argument("--tasks-dir",
                    help="Tasks dir (default: sibling ../tasks of notes-dir)")
    ap.add_argument("--slug", help="override slug (default: from title, else type)")
    ap.add_argument("--keep-source", action="store_true",
                    help="copy instead of moving the source")
    args = ap.parse_args()

    if not os.path.isfile(args.source):
        die(f"source not found: {args.source}")

    if args.db == "notes" and not args.type:
        die("--type is required for --db notes")

    tasks_dir = args.tasks_dir or os.path.join(
        os.path.dirname(os.path.abspath(args.notes_dir)), "tasks")

    if args.db == "tasks":
        schema = load_schema(find_schema("tasks", tasks_dir))
        groups = schema.get("properties", {}).get("status", {}).get("groups", {})
        valid = {o["value"] for g in groups.values() for o in g}
        if valid and args.status not in valid:
            die(f"--status '{args.status}' not in schema: {sorted(valid)}")
    else:
        schema = load_schema(find_schema("notes", args.notes_dir))
        props = schema.get("properties", {})
        valid_tags = {o["value"] for o in props.get("tag", {}).get("options", [])}
        if valid_tags and args.type not in valid_tags:
            die(f"--type '{args.type}' not in schema tags: {sorted(valid_tags)}")

    projects = parse_csv(args.project)
    tasks = parse_csv(args.task)

    with open(args.source, "r", encoding="utf-8") as f:
        raw = f.read()
    src_fm, body = split_frontmatter(raw)

    title = extract_h1(body) or src_fm.get("title")
    if not title:
        die("no H1 or title found in source")
    body = strip_scaffolding(body)

    today = datetime.date.today().isoformat()
    if args.db == "tasks":
        projects = projects or primary_project(args.notes_dir)
        items = [("title", title), ("status", args.status)]
        if projects:
            items.append(("Project", rel_val(projects)))
        if args.parent:
            items.append(("parent", args.parent))
        items += [("created_at", today), ("updated_at", today)]
        for k, v in src_fm.items():
            if k not in {kk for kk, _ in items} and k != "ID":
                items.append((k, v))
        dest_dir = tasks_dir
        num = next_number(dest_dir)
    else:
        # --- resolve Task + Project ---
        if args.new_task:
            proj = projects or primary_project(args.notes_dir)
            new_id = create_task(tasks_dir, args.new_task, proj,
                                 slug=args.new_task_slug)
            tasks.append(new_id)
            if not projects:
                projects = proj
        if tasks and not projects:
            projects = inherit_project(tasks_dir, tasks)
        if not projects:
            projects = primary_project(args.notes_dir)

        # --- assemble ordered frontmatter (house style) ---
        items = [("title", title), ("tag", [args.type])]
        if projects:
            items.append(("Project", rel_val(projects)))
        if tasks:
            items.append(("Task", rel_val(tasks)))
        if "created_at" not in src_fm:
            items.append(("created_at", today))
        if "updated_at" not in src_fm:
            items.append(("updated_at", today))
        # preserve source's extra keys (incl. its own created_at/updated_at); ID is auto
        used = {k for k, _ in items}
        for k, v in src_fm.items():
            if k not in used and k != "ID":
                items.append((k, v))

        # --- filename: task number wins, else next in dir ---
        dest_dir = os.path.join(args.notes_dir, args.type)
        num = task_number(tasks) or next_number(dest_dir)

    slug = args.slug or slugify(title) or (args.type or "task")
    dest = os.path.join(dest_dir, f"{num}-{slug}.md")

    os.makedirs(dest_dir, exist_ok=True)
    out = f"---\n{emit_frontmatter(items)}\n---\n\n{body}"
    with open(dest, "w", encoding="utf-8") as f:
        f.write(out)

    if not args.keep_source and os.path.abspath(dest) != os.path.abspath(args.source):
        os.remove(args.source)

    print(dest)


if __name__ == "__main__":
    main()
