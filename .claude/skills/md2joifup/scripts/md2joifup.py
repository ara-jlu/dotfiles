#!/usr/bin/env python3
"""md2joifup — markdown ファイルを Joifup の Notes-DB row（frontmatter + 本文）として、その場で永続化する。source は superpowers の成果物（plan / spec）でも手書きの note（doc / log / research）でもよい。

何をするか、引数の意味、Task と Project の解決順の正典は `.claude/skills/md2joifup/SKILL.md` である。

frontmatter・tag・リレーションの規約は**絶対にハードコードしない** —— 実行時に正典の Notes schema を読む。
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
    """(frontmatter の dict, 本文の str) を返す。frontmatter が無ければ ({}, text) を返す。"""
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
    """superpowers の引用ブロックによる scaffolding を取り除き、連続する空行を1つにまとめる。"""
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
    """YAML の scalar を書き出す。必要なときだけ quote する（house style に合わせる）。"""
    if not isinstance(v, str):
        return str(v)
    if v == "" or v[0] in _QUOTE_START or v[-1] == " " or ":" in v or "#" in v:
        return "'" + v.replace("'", "''") + "'"
    return v


def emit_frontmatter(items):
    """順序どおりの (key, value) の組を出力する。list は flow array に、それ以外は scalar にする。"""
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
    """紐づけた Task の Project を読む。どの note も Project を持つようにするためである（house style）。"""
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
    """`projects/` の単一の top-level project。Project の最後のフォールバックとして使う。"""
    root = os.path.dirname(os.path.abspath(notes_dir))
    pdir = os.path.join(root, "projects")
    if not os.path.isdir(pdir):
        return []
    files = [f for f in os.listdir(pdir) if f.endswith(".md")]
    return [os.path.splitext(files[0])[0]] if len(files) == 1 else []


def create_task(tasks_dir, title, project, status="In progress", slug=None):
    """house-style の Joifup Task を作成し、その id（ファイル名の stem）を返す。"""
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


def require_task(tasks_dir, task_id, flag):
    """relation の id が実在する task ファイルに解決できなければ、明示的にエラーで落ちる。

    filename id ではなく daemon の `ID: TASK-N`（あるいは裸の数値）を渡した場合を捕まえる —— それらは task_number() を通って、黙って note の番号を誤らせる。
    """
    if not os.path.isfile(os.path.join(tasks_dir, f"{task_id}.md")):
        die(f"{flag} '{task_id}' does not resolve to a file in {tasks_dir} — "
            f"use the task's filename id (NNN-slug), not the daemon ID (TASK-N)")


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

    for t in tasks:
        require_task(tasks_dir, t, "--task")
    if args.db == "tasks" and args.parent:
        require_task(tasks_dir, args.parent, "--parent")

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
        # --- Task と Project を解決する ---
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

        # --- 順序を決めた frontmatter を組み立てる（house style） ---
        items = [("title", title), ("tag", [args.type])]
        if projects:
            items.append(("Project", rel_val(projects)))
        if tasks:
            items.append(("Task", rel_val(tasks)))
        if "created_at" not in src_fm:
            items.append(("created_at", today))
        if "updated_at" not in src_fm:
            items.append(("updated_at", today))
        # source が元から持っていた残りのキーは保持する（source 自身の created_at/updated_at も含む）。`ID` は自動採番なので除く。
        used = {k for k, _ in items}
        for k, v in src_fm.items():
            if k not in used and k != "ID":
                items.append((k, v))

        # --- ファイル名を決める ---
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
