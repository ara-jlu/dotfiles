---
name: j-doc
description: Use when synthesizing existing logs/memos/notes into a coherent, third-party-readable document into Joifup — "まとめて" / "ドキュメント化して" style requests.
user-invocable: true
argument-hint: "[note-ids... and/or task-id (optional)]"
---

# j-doc

## Overview

Synthesizes scattered notes (logs/memos/research) into a structured **document** (tag `document`) in the repo's Joifup `notes/document/`. Not a copy-paste: it reorganizes source material logically for a reader who wasn't there. Standalone.

Persistence/frontmatter are delegated to `md2joifup`; this skill owns the **synthesis** and the **task link**.

## Flow

1. **Gather sources:** note ids/paths in `$ARGUMENTS`, or the relevant `notes/**` entries for the topic. Read each; note its tag, chronology, and overlaps/contradictions.
2. **Resolve the Task** (a document usually belongs to current work):
   - Task id in `$ARGUMENTS` → `--task <id>`.
   - Else branch `TASK-<n>` (`git rev-parse --abbrev-ref HEAD`) → `--task <n>`.
   - Else, if it is a genuinely new topic → `--new-task "<title>" --new-task-slug <english-slug>`; otherwise omit (projects fallback).
3. **Write the document** (see spec) to a temp `.md` (H1 = title).
4. **Persist:** `python3 ~/.claude/skills/md2joifup/scripts/md2joifup.py <tmp>.md --type document <task-flag> --slug <english-slug>`.
5. **Report** the `notes/document/…md` path and how many sources were merged.

## Document content spec

H1 title. Then:

- `### 概要` — a summary of the whole document.
- Topic-based sections (not the sources' chronology) — reorganize logically.
- Deduplicate; on contradiction prefer the newest information.
- Aim for third-party completeness.
- `### 参照元` — list the source notes. For live cross-refs, a Joifup `ref` fence may be used:
  ````
  ```joifup
  type: ref
  id: <note-id>
  ```
  ````
- Standard GFM only (tables, code fences). No Notion-specific syntax.

## ECC knowledge

When the document concerns **code or architecture**, ground it in the real codebase before writing — dispatch `agentType: ecc:code-explorer` (trace the actual execution paths/structure) or `ecc:architect` (design rationale) so the document reflects the code as it is, not memory. For pure decision/process docs, skip.

## Common Mistakes

- Pasting sources verbatim instead of reorganizing by topic.
- Losing the source links — always keep `参照元`.
- Hand-writing frontmatter — `md2joifup` owns it.
