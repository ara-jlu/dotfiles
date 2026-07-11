---
name: j-finish
description: Use when wrapping up a completed, tested feature branch into the pre-approval state — opening the PR, moving the Joifup Task to In review, filing the approval task, and notifying, before the human's approval gate. Use after implementation finishes, not to merge.
---

# j-finish

## Overview

Output adapter between the superpowers spine and the outside world. It performs the **full pre-approval finish** in one shot, then stops at the human approval gate. Compute (superpowers) is unmodified; this reshapes its result into a PR, a Joifup status transition, an approval task, and a notification.

**Division of labor:** the *judgment* (writing the Japanese PR body from the diff) is yours; the *mechanics* (surgical status edit, approval-task creation, relation-id format, PR→notify ordering) are the script's — because those are exactly what goes wrong when done by hand.

**The human owns the approval commit.** j-finish never sets Done and never merges. After review, the human's session sets status → Done, commits `chore(joifup): approve <task-id>` (English), and merges.

## When to Use

- Implementation + review are done and the branch is ready to hand to the human.
- NOT for merging, marking Done, or generating notes (that is `md2joifup`).

## Steps

1. **Pre-flight** (read-only): `git status --porcelain` (clean?), `git log origin/main..HEAD`, `git diff --stat origin/main...HEAD`. Stop and report if the tree is dirty.
2. **Write the Japanese PR body** to a file per the shared recipe in the `j-pr` skill's `references/pr-body.md` (same convention both paths use).
3. **Run the script** (does push → PR → status→In review → approval task → Discord, in that order):

```bash
python3 scripts/j_finish.py --task-file <tasks/NNN-*.md> \
  --pr-title "<ja title>" --pr-body-file <body.md> \
  [--head <branch>] [--project <id>] [--status "In review"] [--dry-run]
```

Toggle off parts with `--no-pr` / `--no-user-action` / `--no-discord`. `--dry-run` prints the git/gh/curl it would run while still performing the local file edits.

4. **Report** the PR URL and hand off: tell the user it awaits their approval.

## What the script guarantees

- **Surgical status edit** — only the `status:` line flips (validated against the tasks schema); every other frontmatter key, relation, and body byte is preserved. It refuses `Done`/`Cancelled`.
- **Approval task** — a child `承認待ち: <title>` Task (status Not started, `parent` = the finished task's id) so the approval surfaces in Joifup.
- **Scoped Discord** — a Japanese rich embed titled 「👀 レビュー依頼」 (same shape as `auto-workflow/scripts/discord-notify.sh`: description + color + プロジェクト/ブランチ fields + timestamp), with the PR link and `allowed_mentions` limited to the owner; `CLAUDE_SESSION_ID` is never posted. Overridable via `DISCORD_COLOR`.

## Common Mistakes

- Rewriting the whole task file (title/relations/body) — only status moves; narrative belongs in a log note.
- Writing relation values as file paths — they are **ids** (e.g. `042-...`, `638-...`).
- Setting Done or merging — that is the human approval gate, not j-finish.
- Commit language: the approval commit is **English**; the PR body is **Japanese**.
