---
title: j-task タスク起票スキル Implementation Plan
tag: [plan]
Project: devops
Task: 001-ai-harness
created_at: 2026-07-11
updated_at: 2026-07-11
---

# j-task タスク起票スキル Implementation Plan

**Goal:** Joifup Task をいつでも起票できる `/j-task` スキルを作り、j-devflow の入口を整備する。

**Architecture:** house-style の Task 生成は `md2joifup` に `--db tasks` モードを追加して第一級化（DRY）。`/j-task` は薄いスキルで、粒度評価・概要 body 生成・（大課題時の）親＋子分解を判断し、md2joifup を呼んで永続化する。識別子はファイル名 id を単一の運用正とする。

**Tech Stack:** Python 3 + PyYAML（md2joifup）、Markdown SKILL.md、Joifup（repo 内 md + frontmatter）。

## Global Constraints

- スキーマは Joifup が正典。`~/.joifup/databases/<db>/schema.yaml`（or repo `.joifup/`）を**読むだけ**、ハードコードしない。
- frontmatter は house-style: flow 配列、単一関係はスカラー、`created_at`/`updated_at` は当日、`ID` は書かない（daemon 採番）。
- 関係値・ブランチ・参照の識別子は**ファイル名 id**（`NNN-slug`）で統一。
- 日本語 title の slug 劣化を避けるため英語 slug を明示（`--slug` / `--new-task-slug`）。
- コミット=英語 Semantic/Atomic、Co-Authored-By トレーラ付き。
- 検証は scratchpad の一時 dir で `--keep-source` を用い実データを汚さない。

---

### Task 1: md2joifup に `--db tasks` モードを追加

**Files:**
- Modify: `~/.claude/skills/md2joifup/scripts/md2joifup.py`（argparse ＋ main の frontmatter 組立を db で分岐）
- Test: 一時 dir で CLI 実行して frontmatter を検証（pytest 不使用・bash アサート）

**Interfaces:**
- Consumes: 既存 `find_schema(db, start_dir)`, `load_schema`, `split_frontmatter`, `extract_h1`, `emit_frontmatter`, `fmt_scalar`, `rel_val`, `primary_project`, `next_number`, `slugify`。
- Produces: CLI `md2joifup <body.md> --db tasks [--status S] [--parent ID] [--project ID] [--slug SLUG] [--tasks-dir DIR] [--keep-source]` → `tasks/NNN-slug.md` を作成、パスを stdout。既定 `--db notes`（既存挙動不変）。

- [ ] **Step 1: 失敗するテストを書く（tasks モードの CLI 検証スクリプト）**

Create `/private/tmp/.../scratchpad/t1.sh`:
```bash
set -e
SP=$(mktemp -d); cd "$SP"; mkdir -p projects
: > projects/devops.md            # sole project -> fallback
printf '# 認証リファクタ\n\n概要のみ。\n' > body.md
python3 ~/.claude/skills/md2joifup/scripts/md2joifup.py body.md \
  --db tasks --status "Not started" --slug auth-refactor --keep-source
fm() { awk '/^---$/{c++} c<=2{print} c==2&&/^---$/{exit}' "$1"; }
out=tasks/001-auth-refactor.md
grep -q '^status: Not started$' "$out"
grep -q '^Project: devops$' "$out"
grep -q '^title: 認証リファクタ$' "$out"
grep -q '^created_at: ' "$out"
! grep -q '^tag:' "$out"          # tasks は tag を持たない
! grep -q '^ID:' "$out"           # ID は daemon
grep -q '# 認証リファクタ' "$out" # body 保持
echo "T1 OK"
```

- [ ] **Step 2: 実行して失敗を確認**

Run: `bash t1.sh`
Expected: FAIL（`--db` 未対応で argparse エラー、または tasks/ に出力されない）

- [ ] **Step 3: argparse に db/status/parent を追加**

`md2joifup.py` の `main()` の argparse に追記（`--type` を required から任意へ緩和）:
```python
    ap.add_argument("--db", choices=["notes", "tasks"], default="notes",
                    help="target Joifup DB (default: notes)")
    ap.add_argument("--type",
                    help="Notes content tag (notes db)")
    ap.add_argument("--status", default="Not started",
                    help="Task status (tasks db)")
    ap.add_argument("--parent", help="parent Task id (tasks db)")
```
（既存の `--type` 定義行を上記へ置換。`required=True` を外す。）

- [ ] **Step 4: main の検証と frontmatter 組立を db で分岐**

`schema = load_schema(find_schema("notes", args.notes_dir))` 以降を分岐に置換:
```python
    if args.db == "notes" and not args.type:
        die("--type is required for --db notes")

    if args.db == "tasks":
        tasks_dir = args.tasks_dir or os.path.join(
            os.path.dirname(os.path.abspath(args.notes_dir)), "tasks")
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
```
`title = extract_h1(body) ...` と `body = strip_scaffolding(body)` は共通のまま残す。
`# --- resolve Task + Project ---` 〜 `out = ...` を db 分岐に置換:
```python
    today = datetime.date.today().isoformat()
    if args.db == "tasks":
        projects = parse_csv(args.project) or primary_project(args.notes_dir)
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
        # （既存の notes 組立をそのまま：--new-task 継承・Project継承・tag/Task・番号）
        ...既存コード...
        dest_dir = os.path.join(args.notes_dir, args.type)
    slug = args.slug or slugify(title) or (args.type or "task")
    dest = os.path.join(dest_dir, f"{num}-{slug}.md")
    os.makedirs(dest_dir, exist_ok=True)
    out = f"---\n{emit_frontmatter(items)}\n---\n\n{body}"
```
（notes 側の既存ブロックは変更しない。tasks 側を新設し、`items`/`dest_dir`/`num` を分岐で用意してから共通の write に合流。）

- [ ] **Step 5: 実行して通過を確認**

Run: `bash t1.sh`
Expected: `T1 OK`

- [ ] **Step 6: 親子（--parent）と既定 notes 不変を確認**

Append to `t1.sh` and run:
```bash
python3 ~/.claude/skills/md2joifup/scripts/md2joifup.py body.md \
  --db tasks --slug auth-child --parent 001-auth-refactor --keep-source
grep -q '^parent: 001-auth-refactor$' tasks/002-auth-child.md
# 既定 notes 不変（回帰）
printf '# メモ\n本文\n' > n.md
python3 ~/.claude/skills/md2joifup/scripts/md2joifup.py n.md --type memo --slug memo1 --keep-source
grep -q '^tag: \[memo\]$' notes/memo/001-memo1.md
echo "T1 parent+notes OK"
```
Expected: `T1 parent+notes OK`

- [ ] **Step 7: Commit**

```bash
git -C ~/Documents/workspace/dotfiles add .claude/skills/md2joifup/scripts/md2joifup.py
git -C ~/Documents/workspace/dotfiles commit -m "feat(md2joifup): add --db tasks mode for first-class task creation" \
  -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: md2joifup SKILL.md に tasks モードを追記

**Files:**
- Modify: `~/.claude/skills/md2joifup/SKILL.md`（Usage/What it does に `--db tasks` を追記）

**Interfaces:**
- Consumes: Task 1 の CLI。
- Produces: なし（ドキュメント）。

- [ ] **Step 1: RED — 現状に tasks モード記述が無いことを確認**

Run: `grep -c 'db tasks' ~/.claude/skills/md2joifup/SKILL.md`
Expected: `0`

- [ ] **Step 2: Usage に tasks モードを追記**

`## Usage` の bash ブロック直後に追記:
```markdown
**Task creation (tasks db):**
`python3 scripts/md2joifup.py <body.md> --db tasks [--status "Not started"] [--parent ID] [--project ID] [--slug EN-SLUG]`
— creates `tasks/NNN-slug.md` with house-style frontmatter (title/status/Project/parent, timestamps, no ID). `--status` is validated against the tasks schema. `--db notes` (default) is unchanged.
```

- [ ] **Step 3: GREEN 確認**

Run: `grep -c 'db tasks' ~/.claude/skills/md2joifup/SKILL.md`
Expected: `1` 以上

- [ ] **Step 4: Commit**

```bash
git -C ~/Documents/workspace/dotfiles add .claude/skills/md2joifup/SKILL.md
git -C ~/Documents/workspace/dotfiles commit -m "docs(md2joifup): document --db tasks mode" \
  -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: j-task スキル（SKILL.md）を作成

**Files:**
- Create: `~/.claude/skills/j-task/SKILL.md`
- Test: RED ベースライン（skill 無しで capture させギャップ観察）→ GREEN（skill で単一/分解を検証）

**Interfaces:**
- Consumes: Task 1 の `md2joifup --db tasks`。
- Produces: user-invocable `/j-task [text]` → `tasks/NNN-slug.md`（単一）or 親＋子（分解）。

- [ ] **Step 1: RED ベースライン**

general-purpose サブエージェントに「skill 無しで、この課題を Joifup Task 化して」と指示（schema と md2joifup の存在のみ伝える）。観察ポイント: house-style を守るか / ファイル名 id を使うか / 大課題で分解の発想が出るか / `ID` を書かないか。
Expected: いくつか外す（分解しない・slug 劣化・ID 記入など）。ギャップを記録。

- [ ] **Step 2: SKILL.md を書く（GREEN）**

Create `~/.claude/skills/j-task/SKILL.md`:
````markdown
---
name: j-task
description: Use when capturing a task or idea into Joifup as a backlog item or as the entry point to development — quickly recording work to detail later, or before starting j-devflow.
user-invocable: true
argument-hint: "[task/idea text (optional)]"
---

# j-task

## Overview

Captures a Joifup **Task** (status `Not started`) into `tasks/`. Standalone and lightweight: for stashing a found issue as backlog, or as the entry to `j-devflow`. Detailed requirements are deferred to each task's brainstorming — this only records title + an overview body. Persistence is delegated to `md2joifup --db tasks`.

## When to Use

- A found issue/idea should become a backlog task, or you are about to start work and need the task record.
- NOT for branching/design/implementation (that is `j-devflow`), and NOT for selecting an existing task (pass its id to `j-devflow`).

## Flow

1. **Assess granularity.** A task = one "requirements-refinement unit" (one j-devflow cycle: brainstorming→plan→implement).
   - Fits one unit → **single task** (create immediately).
   - Too large / multiple independent pieces → **coarse-decompose**: propose a parent (umbrella) + child titles, get quick confirmation, then create.
2. **Generate content:** a Japanese `title` and an **overview-level** body (no deep requirements). Derive an English `--slug`.
3. **Resolve Project:** pass `--project` if known; else `md2joifup` falls back to the sole `projects/` entry.
4. **Create:**
   - Single: `python3 ~/.claude/skills/md2joifup/scripts/md2joifup.py <tmp>.md --db tasks --status "Not started" --slug <en-slug>`.
   - Decomposed: create the parent first, capture its filename id, then each child with `--parent <parent-id>` (write `parent` on children only; the daemon syncs `children`).
5. **Report** the created task path(s). No branch, no implementation.

## Identifier

The task's **filename id** (`NNN-slug`) is the single operational identifier (relations, branch, references). The daemon's `ID: TASK-N` is Joifup-internal and naturally aligns. Branch (later, in j-devflow) = `feature/<filename-id>`.

## Common Mistakes

- Writing frontmatter or `ID` by hand — `md2joifup` owns it (daemon assigns `ID`).
- Degraded slug from a Japanese title — pass an English `--slug`.
- Deep requirements at capture — keep the body overview-level; detail belongs in brainstorming.
- Hand-writing `children` back-refs — write `parent` on children only.
````

- [ ] **Step 3: GREEN 検証（単一）**

一時 dir で「小さな課題」を capture させ、`tasks/001-*.md` が status=Not started / Project fallback / 英語slug / ID 無し / house-style であることを確認。
Expected: 単一 Task が house-style で作成。

- [ ] **Step 4: GREEN 検証（分解）**

「大きな課題（複数の独立塊を含む）」を capture させ、親＋子の提案が出て、確認後に `parent` 一方向で作成されることを確認。
Expected: 親1＋子N、子は `parent: <親id>`。

- [ ] **Step 5: Commit**

```bash
git -C ~/Documents/workspace/dotfiles add .claude/skills/j-task/SKILL.md
git -C ~/Documents/workspace/dotfiles commit -m "feat: add j-task skill for Joifup task capture" \
  -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: j-devflow と CLAUDE.md を配線更新

**Files:**
- Modify: `~/.claude/skills/j-devflow/SKILL.md`（Session A step1）
- Modify: `~/.claude/CLAUDE.md`（TASK-id 定義・ブランチ例）

**Interfaces:**
- Consumes: Task 3 の `/j-task`。
- Produces: なし（配線ドキュメント）。

- [ ] **Step 1: RED — 現状に j-task 参照が無いことを確認**

Run: `grep -c 'j-task' ~/.claude/skills/j-devflow/SKILL.md`
Expected: `0`

- [ ] **Step 2: j-devflow Session A step1 を更新**

`j-devflow/SKILL.md` の Runbook「Session A — Plan」の項目1を置換:
```markdown
1. Prepare the Joifup **Task** under `tasks/`: new → run `/j-task`; existing backlog → use its filename id. Capture that id — everything keys off it.
```

- [ ] **Step 3: CLAUDE.md の TASK-id 定義を更新**

`.claude/CLAUDE.md` の Git セクションの Branch 行を置換:
```markdown
- Branch: superpowers 準拠命名 ＋ **Joifup タスクのファイル名 id を注入**（例: `feature/001-slug`。TASK-id = tasks/ のファイル名 id。type 分類は superpowers に委ねる）
```

- [ ] **Step 4: GREEN 確認**

Run:
```bash
grep -c 'j-task' ~/.claude/skills/j-devflow/SKILL.md
grep -c 'ファイル名 id' ~/.claude/CLAUDE.md
```
Expected: 両方 `1` 以上

- [ ] **Step 5: Commit**

```bash
git -C ~/Documents/workspace/dotfiles add .claude/skills/j-devflow/SKILL.md .claude/CLAUDE.md
git -C ~/Documents/workspace/dotfiles commit -m "docs: wire j-task into j-devflow entry and define TASK-id as Joifup filename id" \
  -m "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## 完了条件

- `/j-task` で単一/分解の Task 起票ができ、house-style・ファイル名 id・ID 省略が守られる。
- `md2joifup --db tasks` が第一級で、既定 notes 挙動は不変（回帰なし）。
- j-devflow 入口と CLAUDE.md の TASK-id 定義が新方針に更新。
