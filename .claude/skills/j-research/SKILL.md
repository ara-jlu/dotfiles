---
name: j-research
description: Use when recording technical investigation or comparison — library/framework selection, architecture options, trade-off analysis — into Joifup after a research conversation.
user-invocable: true
argument-hint: "[task-id (optional)]"
---

# j-research

## Overview

Records a technical **research note** (tag `research`) into the repo's Joifup `notes/research/`: structured comparison, trade-offs, and a recommendation. Standalone.

Persistence/frontmatter are delegated to `md2joifup`; this skill owns the **grounded research** and the **task**.

## Flow

1. **Ground the research in current sources (ECC)** — do not rely on conversation memory alone:
   - For any library/framework/API/CLI, fetch **current** docs via Context7: dispatch `agentType: ecc:docs-lookup` (or use the context7 MCP tools directly).
   - For comparisons, landscape, or recent changes, use `WebSearch`.
   - Capture concrete versions and cite every source URL.
2. **Resolve the Task** (research often spawns its own task):
   - Task id in `$ARGUMENTS` → `--task <id>`.
   - Else, if this is a new investigation → `--new-task "<title>" --new-task-slug <english-slug>` (creates the task; the English slug keeps the Japanese-titled task's filename clean).
   - Else, if it clearly extends current work → branch `TASK-<n>` → `--task <n>`.
3. **Write the note** (see spec) to a temp `.md` (H1 = title).
4. **Persist:** `python3 ~/.claude/skills/md2joifup/scripts/md2joifup.py <tmp>.md --type research <task-flag> --slug <english-slug>`.
5. **Report** the `notes/research/…md` path.

## Research content spec

H1 title. Then:

- `### 背景・目的` — why this investigation was needed.
- `### 調査結果` — one subsection per option/technology: 概要 / メリット / デメリット / 参考(URL, version).
- `### 比較表` — a GFM table across the axes that matter (when comparable).
- `### 結論・推奨` — the recommendation with its grounds.
- `### 残課題` — open questions needing further work.
- Standard GFM only. Every claim about a library should trace to a cited current source.

## ECC knowledge

The value here is **accuracy over recall**: Context7 (`ecc:docs-lookup`) gives version-correct API/config facts and `WebSearch` gives the current landscape — both beat training-cutoff memory. Prefer citing docs to asserting from memory; note the doc version you relied on.

## Common Mistakes

- Writing from memory without grounding — stale/hallucinated APIs. Fetch current docs.
- Uncited claims — every option needs a source.
- Hand-writing frontmatter — `md2joifup` owns it.
