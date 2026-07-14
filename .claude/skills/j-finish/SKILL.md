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

4. **Present the UAT (acceptance-test) review request.** The approver *runs* the change, they do not read code. The *content* of the UAT is yours (like the PR body); the script does not carry it. Judge how heavy the verification is and branch:
   - **Light** (a few steps the approver can follow inline): first do the verification prep yourself so they can start immediately — restart the daemon, start the dev server, seed data, whatever this change needs (project-specific; decide it in-session, there is no config for it). Then present the UAT steps as session text.
   - **Heavy** (many cases, order-dependent, multi-environment, or worth keeping): file a user-action Task carrying the verification cases via `md2joifup --db tasks` (content authored by you), and present its file path. Do the prep as in the light case.
5. **Report** the PR URL and hand off: tell the user it awaits their approval (after they run the UAT).

## What the script guarantees

- **Surgical status edit** — only the `status:` line flips (validated against the tasks schema); every other frontmatter key, relation, and body byte is preserved. It refuses `Done`/`Cancelled`.
- **Scoped Discord** — a Japanese rich embed titled 「👀 レビュー依頼」 (same shape as `auto-workflow/scripts/discord-notify.sh`: description + color + プロジェクト/ブランチ fields + timestamp), with the PR link and `allowed_mentions` limited to the owner; `CLAUDE_SESSION_ID` is never posted. Overridable via `DISCORD_COLOR`.

## Common Mistakes

- Rewriting the whole task file (title/relations/body) — only status moves; narrative belongs in a log note.
- Writing relation values as file paths — they are **ids** (e.g. `042-...`, `638-...`).
- Setting Done or merging — that is the human approval gate, not j-finish.
- Commit language: the approval commit is **English**; the PR body is **Japanese**.
