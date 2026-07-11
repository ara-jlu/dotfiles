---
name: j-log
description: Use when recording what was actually done in this session as a detailed, time-ordered work log into Joifup — at a session end or a natural stopping point on a task.
user-invocable: true
argument-hint: "[task-id (optional)]"
---

# j-log

## Overview

Records the session's work as a **detailed, reproducible log** (tag `log`) into the repo's Joifup `notes/log/`. This is a *record*, not a summary — do not compress information away. Standalone: callable any time, inside or outside the dev flow.

Persistence and frontmatter are delegated to `md2joifup`; this skill's job is the **content** and the **task it attaches to**.

## Flow

1. **Resolve the Task** (this log almost always documents current work):
   - If `$ARGUMENTS` names a Task id → link it (`--task <id>`).
   - Else `git rev-parse --abbrev-ref HEAD`; if the branch has `TASK-<n>` → `--task <n>`.
   - Else omit — `md2joifup` falls back to the sole `projects/` Project.
2. **Generate the log** (see spec) to a temp `.md` file whose H1 is the title.
3. **Persist:** `python3 ~/.claude/skills/md2joifup/scripts/md2joifup.py <tmp>.md --type log --task <id> --slug <english-slug>` (drop `--task` if unresolved). Prefer an English `--slug`; the H1 title stays Japanese.
4. **Report** the resulting `notes/log/…md` path.

## Log content spec

Title H1: `<task/topic> 作業ログ [YYYY-MM-DD]`. Then:

- `## 概要` — purpose, outcome, date (this section only may be brief).
- `---`, then time-ordered steps as `### 1.`, `### 2.` … Structure flexibly; no fixed template.
- **Record, do not summarize.** Include:
  - commands run and their output (including errors)
  - files read / places investigated and what was learned
  - approaches tried (successes *and* failures) and results
  - files changed with concrete diffs/explanations
  - **decision rationale** — why this path, why alternatives were rejected
  - problems hit, gotchas, and how they were resolved
  - concrete values: settings, params, versions
- Use standard GFM: tables for settings/comparisons, code fences for commands/config, blockquotes for warnings. No Notion-specific syntax.

## ECC knowledge

Write the decision rationale and gotchas at a grain that ECC **instincts** (continuous-learning) can learn from — an explicit "why" per non-obvious choice. The log complements the instincts the hooks capture automatically; make the reasoning legible, not just the actions.

## Common Mistakes

- Summarizing instead of recording — information must be reconstructable later.
- Notion rich-format syntax — Joifup notes are standard markdown (+ optional `joifup` fences).
- Hand-writing frontmatter — let `md2joifup` own it.
