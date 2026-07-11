---
name: j-devflow
description: Use when taking a feature or bugfix from a one-line idea through to the human approval gate in this harness — starting end-to-end development that spans design, planning, implementation, and pre-approval finish.
---

# j-devflow

## Overview

A **thin sequencer** over the superpowers spine and the Joifup adapters. It orchestrates — it does not wrap: it never injects instructions into the underlying skills or reshapes their output. It only decides **order, session boundaries, handoff artifacts, and gates**. Compute (superpowers) and persistence (Joifup) stay separate.

The flow runs across **three sessions**, connected by file handoff (not shared context):

- **Session A — Plan** (interactive): idea → design → plan, persisted to Joifup.
- **Session B — Implement** (mostly autonomous): reads the persisted plan, builds and reviews.
- **Session C — Approve** (human): the approval gate. Merge lives only here.

**Why separate A and B:** a fresh Session B forces the plan to be a complete, self-contained contract (the persisted `notes/plan/` entry is the handoff), and keeps the planning dialogue out of the implementation context.

## When to Use

- Any non-trivial feature/bugfix that should follow the full spine.
- NOT for a quick one-file edit (just do it), and NOT to merge (that is Session C, human-owned).

## Runbook

Read the Joifup schema (`.joifup/databases/<id>/schema.yaml`) for status/tag/folder names — never hardcode them.

**Session A — Plan (interactive)**
1. Confirm/create the Joifup **Task** under `tasks/`; capture its id — everything keys off it.
2. Branch: superpowers naming **+ inject the TASK-id** (e.g. `feature/TASK-638-slug`); isolate via `superpowers:using-git-worktrees`. Do not use the repo `branch` skill (Notion-oriented).
3. `superpowers:brainstorming` → design. **HUMAN GATE 1: design approval — no code until approved.** Never a subagent (it is the design dialogue).
4. `md2joifup` the approved spec → `notes/document/` (type `document`).
5. `superpowers:writing-plans` → task-decomposed plan.
6. `md2joifup` the plan → `notes/plan/` (type `plan`). Optionally move the Task to In progress. **This is the handoff artifact. Session A ends.**

**Session B — Implement (fresh session)**
7. Read the persisted plan. `superpowers:subagent-driven-development`: fresh subagent per task, English atomic commits, `task-reviewer` per task; add `agentType: ecc:security-reviewer` on any task touching auth/input/secrets/API/sensitive data. The Driver keeps the orchestration/fix loop — only per-task units are subagents.
8. SDD auto whole-branch review: inject `ecc:<lang>-reviewer` by changed language (+ `ecc:security-reviewer` if the diff warrants). Critical/Important are blocking → fix loop until clean.
9. `superpowers:verification-before-completion` + tests green.
10. `j-finish`: push → PR (Japanese) → Task → In review → 承認待ち task → Discord. **The machine stops here.**

**Session C — Approve (human)**
11. Human reviews. On approval: Task → Done, commit `chore(joifup): approve <task-id>` (English), merge. **HUMAN GATE 2. Nothing auto-merges.**

## Guards for autonomous runs

- **Design gate (before step 7):** hard stop — never write code before design approval, even unattended.
- **Fix-loop exit (before step 10):** no open Critical/Important from any reviewer.
- **Before step 10's external actions:** PR/Discord/status are externally visible and hard to undo — checkpoint on green tests + clean review first.
- **Merge/Done:** structurally impossible for the machine — reserved for Session C.

## Common Mistakes

- Collapsing Sessions A and B into one context — defeats the plan-as-contract handoff.
- Wrapping: editing what superpowers/adapters do instead of just sequencing them.
- Merging or marking Done from Session B — that is the human gate.
