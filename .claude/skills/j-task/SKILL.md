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
   - Decomposed: create the parent first, capture its filename id, then each child with `--parent <parent-id>` (write `parent` on children only; the daemon is expected to sync `children` — Joifup Plan 079).
5. **Report** the created task path(s). No branch, no implementation.

## Identifier

The task's **filename id** (`NNN-slug`) is the single operational identifier — relations, branch, and `--task`/`--parent` all use it. The daemon's `ID: TASK-N` is a **separate** internal auto-increment that does **NOT** match the filename number (they diverge — e.g. file `085-…` vs `ID: TASK-48`); never use `ID` for relations, the branch, or `--task`. Branch (later, in j-devflow) = `feature/<filename-id>`.

## Common Mistakes

- Writing frontmatter or `ID` by hand — `md2joifup` owns it (daemon assigns `ID`).
- Degraded slug from a Japanese title — pass an English `--slug`.
- Deep requirements at capture — keep the body overview-level; detail belongs in brainstorming.
- Hand-writing `children` back-refs — write `parent` on children only.
