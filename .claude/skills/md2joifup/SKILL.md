---
name: md2joifup
description: Use when a markdown file must become a Joifup Notes-DB entry — a superpowers plan/spec after brainstorming/writing-plans, or a hand-authored doc/log/research note that belongs in the repo's notes/ tree with correct frontmatter.
---

# md2joifup

## Overview

The persistence primitive for the Joifup memory layer: it turns a markdown file into a house-style **Notes-DB row** (frontmatter + body) filed under `notes/<type>/`, in place. It backs both the dev flow (`j-devflow` persists superpowers plans/specs) and the standalone note skills (`j-doc` / `j-log` / `j-research`).

It reads the **authoritative Notes schema** for tag/relation/title conventions — never hardcodes them.

## When to Use

- Persisting a `brainstorming`/`writing-plans` artifact, or a hand-authored doc/log/research note, into Joifup.
- NOT for reading Joifup, editing schema (Joifup owns `schema.yaml`), or human-facing output (that is `j-finish`).

## Usage

```bash
python3 scripts/md2joifup.py <source.md> --type <tag> \
  [--task ID]... [--new-task "TITLE"] [--new-task-slug SLUG] [--project ID]... \
  [--notes-dir DIR] [--tasks-dir DIR] [--slug SLUG] [--keep-source]
```

**Task creation (tasks db):**
`python3 scripts/md2joifup.py <body.md> --db tasks [--status "Not started"] [--parent ID] [--project ID] [--slug EN-SLUG]`
— creates `tasks/NNN-slug.md` with house-style frontmatter (title/status/Project/parent, timestamps, no ID). `--status` is validated against the tasks schema. `--db notes` (default) is unchanged.

- `--type` — a Notes **content tag** (`plan`, `document`, `log`, `research`, `memo`); validated against the schema's tag options.
- `--task` — link an existing Task by its **filename id** (`NNN-slug`; not a path, and **not** the daemon `ID: TASK-N` — those diverge). Branch detection is the caller's job: the branch is `feature/<filename-id>`, so strip the `feature/` prefix to get the id and pass it here. **md2joifup validates** that `--task` (and `--parent`) resolves to a real `tasks/` file and errors otherwise — a daemon `ID` or typo fails loudly instead of silently mis-numbering the note.
- `--new-task "TITLE"` — create a fresh house-style Task and link it; for a note that spawns its own task (e.g. a new investigation). Pass `--new-task-slug` (English) alongside a non-ASCII title, else the task filename slug degrades.
- `--project` — else inherited from the Task, else the sole project in `projects/`.
- `--slug` — override; default is a slug of the title (**pass an English slug for non-ASCII titles**, else it degrades to the type), else the type.
- `--keep-source` — copy instead of move (default: move / in-place).

Prints the destination path. Concept map: superpowers spec → `document`, plan → `plan`.

## What it does

- Extracts the H1 and **mirrors it into frontmatter `title`**; the H1 stays in the body.
- Strips superpowers agentic-worker scaffolding (no-op for hand-authored notes).
- **House-style frontmatter:** flow arrays (`tag: [log]`), single relation → scalar, 2+ → flow array; stamps `created_at`/`updated_at` (today) unless present.
- **Project always resolved:** explicit → new/linked Task's Project → sole `projects/` entry.
- **Filenames** `<NNN>-<slug>.md`: `NNN` = the linked task's id number, else the next number in `notes/<type>/`.
- Leaves only the auto-increment `ID` to the daemon; preserves any pre-existing source frontmatter keys.

## Common Mistakes

- Passing a state tag (`inbox`/`seed`/`archive`) as `--type` — use a content tag; state is a separate axis.
- Writing relation values as file paths — they are **ids** (`042-...`, `638-...`).
- Making the script detect the branch — resolve the TASK-id in the caller and pass `--task`.
- Hand-editing frontmatter conventions here — change the Joifup `schema.yaml` instead.
