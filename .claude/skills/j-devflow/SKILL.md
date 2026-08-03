---
name: j-devflow
description: Use when taking a feature or bugfix from a one-line idea through to the human approval gate in this harness — starting end-to-end development that spans design, planning, implementation, and pre-approval finish.
---

# j-devflow

## Overview

A **thin sequencer** over the superpowers spine and the Joifup adapters. It orchestrates — it does not wrap: it never injects instructions into the underlying skills or reshapes their output. It only decides **order, session boundaries, handoff artifacts, and gates**. Compute (superpowers) and persistence (Joifup) stay separate.

The flow has **three phases**, connected by file handoff (the persisted `notes/plan/` entry is the contract):

- **Phase A — Plan** (interactive): idea → design → plan, persisted to Joifup.
- **Phase B — Implement**: reads the persisted plan, builds and reviews.
- **Phase C — Approve** (human): the approval gate. Merge lives only here.

**Same session by default.** Run A → B → C in one session. SDD already gives each task a fresh subagent (isolated context), so implementation isolation does **not** need a session boundary. Open a **fresh session for Phase B only when** Phase A's dialogue was long or context is tight — a fresh Phase B additionally forces the plan to be self-contained and keeps the planning dialogue out of the orchestrator's context, but the cost (copy the handoff, `/clear`, paste) is usually not worth it for a solo run.

## When to Use

- Any non-trivial feature/bugfix that should follow the full spine.
- NOT for a quick one-file edit (just do it), and NOT to merge (that is Phase C, human-owned).

## Modes: attended (default) vs `-auto`

Invoked as `/j-devflow <id>` (attended) or `/j-devflow <id> -auto` (autonomous). The flag changes **only HUMAN GATE 1 (design approval)** — never GATE 2 (merge), which is human in both modes.

- **attended (default):** brainstorming presents its recommended approach; the **human** approves at GATE 1.
- **`-auto`:** brainstorming runs fully (codebase exploration, alternatives, design doc) and the session **auto-approves its own recommended approach** at GATE 1, then proceeds — no human wait. The task body is only the starting idea (overview-level by j-task design), **not** the design authority; the design comes from brainstorming.

**Why `-auto` is safe:** the design is still persisted to `notes/document/` and surfaced in the PR, and **GATE 2 (merge) is always human**. Auto-approving GATE 1 therefore risks only *rework* (a design rejected at PR review), never an unsafe merge.

**`-auto` escalation triggers — pause and ask the dispatcher (do NOT auto-approve):**
- schema change / data migration / deletion / security・auth policy / public API-contract change — irreversible, high blast-radius (GATE 2 is too late);
- brainstorming judges the work does not fit a single spec / needs decomposition — a scope decision, not a design one;
- the recommended approach is a genuine close call or carries a material tradeoff (e.g. data integrity vs speed) — a call a human should make;
- the fix-loop cannot clear all Critical/Important.

Otherwise (recommendation clearly dominant, low-risk) auto-approve and continue. Escalation is **pause-and-ask to the dispatcher** (the launching PM/session), not a hard fail: stop, surface the question, resume on the answer. The dispatcher must therefore watch for a session that has stopped on a question, not only for the finished PR.

## Runbook

Read the Joifup schema (`.joifup/databases/<id>/schema.yaml`) for status/tag/folder names — never hardcode them.

**Phase A — Plan (interactive)**
1. Prepare the Joifup **Task** under `tasks/`: new → run `/j-task`; existing backlog → use its filename id. Capture that id — everything keys off it.
2. Branch: **hyphen naming (no slash)** + inject the TASK-id — `feature-001-slug`, **not** `feature/001-slug`. Native `EnterWorktree` sanitizes `/`→`+` in the worktree directory, and slash-derived worktrees have leaked SDD-subagent writes into the primary checkout (tasks/154, 155, root cause 156). Isolate via `superpowers:using-git-worktrees`. Do not use the repo `branch` skill (Notion-oriented). **After isolation, capture the worktree absolute root once as canonical for the whole run: `WT="$(git rev-parse --show-toplevel)"`** (record it in the SDD progress-ledger header). Every SDD dispatch pins to `<WT>` — see step 7 and Guards → Worktree isolation.
3. `superpowers:brainstorming` → design. **HUMAN GATE 1: design approval — no code until approved** (attended: the human approves; `-auto`: the session auto-approves brainstorming's own recommended approach, escalating per **Modes**). Never a subagent (it is the design dialogue). When it writes the design doc, target a **staging path** (scratchpad) — **not** `docs/superpowers/specs/` — and do **not** commit it there. Step 4 is the spec's only commit.
4. `md2joifup` the staged spec → `notes/document/` (`--type document --task <id>`). This move + frontmatter is the **single commit** of the spec. (If brainstorming already committed it under `docs/superpowers/specs/`, md2joifup's default move removes it — commit that relocation.)
5. `superpowers:writing-plans` → task-decomposed plan. Same rule: write it to a **staging path**, **not** `docs/superpowers/plans/`, and do **not** commit it there.
6. `md2joifup` the staged plan → `notes/plan/` (`--type plan --task <id>`) — the **single commit** of the plan. Optionally move the Task to In progress. **This is the handoff artifact. Phase A ends.**

**Phase B — Implement (same session by default; fresh session only if context is heavy)**
7. Read the persisted plan. `superpowers:subagent-driven-development`: fresh subagent per task, English atomic commits, `task-reviewer` per task; add `agentType: ecc:security-reviewer` on any task touching auth/input/secrets/API/sensitive data. The Driver keeps the orchestration/fix loop — only per-task units are subagents.
   - **Worktree-pinning contract (every SDD dispatch — implementer, fix, reviewer; both modes):** Agent subagents do **not** inherit this session's `EnterWorktree` cwd — a fresh subagent starts in the primary checkout. So each dispatch MUST: (a) state `Worktree root: <WT>` (the `$WT` from step 2), never a blank/relative "Work from"; (b) make the subagent's **first action** `cd "<WT>"` then assert `test "$(git rev-parse --show-toplevel)" = "<WT>"` — on mismatch **STOP and report BLOCKED**, never edit or run cargo/pnpm in the fallback dir; (c) keep every path relative to `<WT>` (or `<WT>/…`) and **forbid literal primary paths** (`/Users/…/joifup/…` lacking the `.claude/worktrees/<branch>/` segment); (d) pin builds/tests to the worktree manifest — Rust: `cargo … --manifest-path "<WT>/apps/desktop/src-tauri/Cargo.toml"`; never a bare `cargo`/`cargo fmt`/`pnpm` that trusts cwd.
8. SDD auto whole-branch review: inject `ecc:<lang>-reviewer` by changed language (+ `ecc:security-reviewer` if the diff warrants). Critical/Important are blocking → fix loop until clean.
9. `superpowers:verification-before-completion` + tests green.
10. **UAT 自動化 + `j-finish`**: UI 変更を含む branch は `pnpm uat --task <id>` を実行して `.uat-evidence/<id>/` に証跡を生成し commit する（spec で確定した受け入れ基準を `apps/web/e2e/<id>.uat.spec.ts` に書いてから）。PR には pr-body recipe の `## 受け入れ基準` と `## UAT 証跡`（summary.md の PASS/FAIL 表）を載せる。その後 `j-finish` が push→PR→Task→In review→Discord を行う。**UAT ユーザーアクション task は file しない**（旧 heavy 分岐は廃止）。UI を含まない変更では UAT を省略し `## テスト` のみで良い。**The machine stops here.**

**Phase C — Approve (human)**
11. Human reviews. On approval: Task → Done, commit `chore(joifup): approve <task-id>` (English), merge. Once merged, **remove the isolated worktree without prompting** (`ExitWorktree`, or `git worktree remove`) — it is disposable post-merge, so cleanup needs no separate approval; do not ask. **HUMAN GATE 2. Nothing auto-merges** — the human owns only the approval/merge decision; the post-merge worktree cleanup is automatic.

## Guards (both modes)

- **Design gate (before step 7):** never write code before design approval. attended → the human approves; `-auto` → brainstorming's own recommendation is auto-approved **unless** an escalation trigger fires (see **Modes**), then pause-and-ask the dispatcher. Never fabricate approval from the overview-level task body.
- **Fix-loop exit (before step 10):** no open Critical/Important from any reviewer — `-auto` must not lower this bar.
- **Before step 10's external actions:** PR/Discord/status are externally visible and hard to undo — checkpoint on green tests + clean review first.
- **Merge/Done:** structurally impossible for the machine — reserved for Phase C (human), in both modes.
- **Worktree isolation (every subagent, `-auto` included):** the dispatch is the only thing keeping a subagent out of the primary checkout — `EnterWorktree` moves only THIS session, not its subagents. No dispatch goes out without the `cd "<WT>"` + `git rev-parse --show-toplevel` equality assert as the subagent's first step; a subagent that can't confirm it is in `<WT>` BLOCKs rather than editing primary. Cheap (one shell check, once, at dispatch start) vs the far larger cost of a primary leak + recovery. Root cause: tasks/156.

## Common Mistakes

- Letting the plan lean on unstated Phase-A context — the plan must be a self-contained contract a fresh SDD orchestrator (or a future reader) can run without the design dialogue. (This, not a session boundary, is what matters; SDD isolates each task regardless.)
- Wrapping: editing what superpowers/adapters do instead of just sequencing them.
- Merging or marking Done from Phase B (the machine) — that is the human gate.
- Letting brainstorming/writing-plans commit the spec/plan at their superpowers defaults (`docs/superpowers/specs|plans/`) — those are not Joifup-indexed (`**/notes/**` only) or Task-linked. Stage them uncommitted; `md2joifup` is the only commit, into `notes/document/` and `notes/plan/`.
- Naming a branch with a slash (`feature/154-…`) or dispatching an SDD subagent without pinning it to `<WT>` — the subagent silently lands in the primary checkout and edits / `cargo fmt`s there (observed: tasks 154, 155). Hyphen-name the branch and carry `<WT>` + the toplevel assertion in every dispatch.
