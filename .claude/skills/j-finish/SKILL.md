---
name: j-finish
description: Use when wrapping up a completed, tested feature branch into the pre-approval state — opening the PR, moving the Joifup Task to In review, presenting the UAT review request, and notifying, before the human's approval gate. Use after implementation finishes, not to merge.
---

# j-finish

## Overview

Output adapter between the superpowers spine and the outside world. It performs the **full pre-approval finish** in one shot, then stops at the human approval gate. Compute (superpowers) is unmodified; this reshapes its result into a PR, a Joifup status transition, a UAT review request, and a notification.

**Division of labor:** the *judgment* (writing the Japanese PR body from the diff) is yours; the *mechanics* (surgical status edit, relation-id format, PR→notify ordering) are the script's — because those are exactly what goes wrong when done by hand.

**The human owns the approval commit.** j-finish never sets Done and never merges. After review, the human's session sets status → Done, commits `chore(joifup): approve <task-id>` (English), and merges.

## When to Use

- Implementation + review are done and the branch is ready to hand to the human.
- NOT for merging, marking Done, or generating notes (that is `md2joifup`).

## Steps

1. **Pre-flight** (read-only): `git status --porcelain` (clean?), `git log origin/main..HEAD`, `git diff --stat origin/main...HEAD`. Stop and report if the tree is dirty.
2. **Write the Japanese PR body** to a file per the shared recipe in the `j-pr` skill's `references/pr-body.md` (same convention both paths use).
3. **Run the script** (does push → PR → status→In review → Discord, in that order):

```bash
python3 scripts/j_finish.py --task-file <tasks/NNN-*.md> \
  --pr-title "<ja title>" --pr-body-file <body.md> \
  [--head <branch>] [--status "In review"] [--dry-run]
```

Toggle off parts with `--no-pr` / `--no-discord`. `--dry-run` prints the git/gh/curl it would run while still performing the local file edits.

4. **UAT 証跡を PR に載せる。** 承認者はコードを読まず、証跡を見て承認する。UI 変更を含む場合は `pnpm uat --task <id>` を回して `.uat-evidence/<id>/` を commit し、PR 本文の `## UAT 証跡` に `summary.md` の PASS/FAIL 表を転記する（screenshot は private repo のため Files changed タブで閲覧）。受け入れ基準は `## 受け入れ基準` に inline 展開する。**UAT ユーザーアクション task は新規 file しない**（旧 light/heavy 分岐・md2joifup --db tasks による UAT task 発行は廃止）。UI を含まない変更では UAT を省略してよい。
5. **Report** the PR URL and hand off: tell the user it awaits their approval (after they run the UAT).

## What the script guarantees

- **Surgical status edit** — only the `status:` line flips (validated against the tasks schema); every other frontmatter key, relation, and body byte is preserved. It refuses `Done`/`Cancelled`.
- **Scoped Discord** — a Japanese rich embed titled 「👀 レビュー依頼」 (same shape as `auto-workflow/scripts/discord-notify.sh`: description + color + プロジェクト/ブランチ fields + timestamp), with the PR link and `allowed_mentions` limited to the owner; `CLAUDE_SESSION_ID` is never posted. Overridable via `DISCORD_COLOR`.
- **UAT evidence check** — warns (never blocks) if `apps/web/` changed but no `.uat-evidence/` was committed in the push range; runs under `--dry-run` too, since it is read-only.

## Common Mistakes

- Rewriting the whole task file (title/relations/body) — only status moves; narrative belongs in a log note.
- Writing relation values as file paths — they are **ids** (e.g. `042-...`, `638-...`).
- Setting Done or merging — that is the human approval gate, not j-finish.
- Commit language: the approval commit is **English**; the PR body is **Japanese**.
- UI 変更なのに `.uat-evidence/<id>/` を commit せず PR を出す — 証跡が空になる（`pnpm uat` を回す）。
- UAT ユーザーアクション task を新規 file する — 廃止済み。受け入れ基準は PR の `## 受け入れ基準` に inline する。
