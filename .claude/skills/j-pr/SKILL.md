---
name: j-pr
description: Use when opening a pull request for ad-hoc development done outside j-devflow — you want the same house-style Japanese PR body without the full finish (no Joifup status change, approval task, or Discord).
user-invocable: true
argument-hint: "[base-branch (default: main)]"
---

# j-pr

## Overview

Opens a PR in the **house style** for ad-hoc work — the same Japanese PR body as the full flow, but nothing else. Use this when you developed without `j-devflow` and just need a consistent PR.

- **PR body** follows the shared recipe in `references/pr-body.md` — the single source of truth that `j-finish` also uses, so both paths stay identical.
- **Commits** are already governed by CLAUDE.md § Git (English, Semantic/Conventional, Atomic) — j-pr does not touch them.
- **No Joifup side-effects.** Status transition, approval task, and Discord belong to `j-finish` (the post-implementation finish). If this work has a Joifup Task and you want the full finish, use `j-finish` instead.

## When to Use

- Ad-hoc branch → PR, outside the j-devflow spine.
- NOT for merging, and NOT when you want the status/approval/notify finish (that is `j-finish`).

## Flow

1. **Pre-flight** (read-only): `git status --porcelain` (clean? stop and report if dirty), `git log <base>..HEAD --oneline`, `git diff --stat <base>...HEAD`. `<base>` = `$ARGUMENTS` or `main`.
2. **Push:** `git push -u origin <branch>`.
3. **Write the PR body** to a temp `.md` per `references/pr-body.md` (read it). Ground every section in the diff. If a Joifup Task/plan relates to this work, cite its id/path in `## 関連`; otherwise omit those lines.
4. **Create the PR:** `gh pr create --base <base> --head <branch> --title "<type>: <日本語要約>" --body-file <tmp>.md` (add `--draft` if requested).
5. **Report** the PR URL.

## Common Mistakes

- Reaching for the old `/pr` skill — it links Notion, not Joifup. Use this recipe.
- Writing the PR body in English, or the commits in Japanese — PR body is Japanese, commits are English (independent).
- Doing status/approval/Discord here — that is `j-finish`.
