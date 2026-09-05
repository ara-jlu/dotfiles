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

## Modes: two independent axes

j-devflow has two independent mode flags controlling two different risk axes. They compose freely: `/j-devflow <id>`, `-auto`, `-light`, or `-light -auto`.

- **`-auto`** controls **GATE 1 (design approval)** — attended (default) vs auto-approved.
- **`-light`** controls **Phase B review depth** — full (per-task subagent + **per-task review** + final review) vs light (per-task subagent, **no per-task review**, final review only). **Both keep SDD's fresh-subagent-per-task isolation**; `-light` drops only the per-task review layer (008 followup showed that layer is not load-bearing; SDD isolation is).

They target different risks and don't have to be used together, but in practice **`-light` alone is rarely useful**: its motivating case (a chain of follow-up tasks burning tokens on process overhead) only pays off when GATE 1 is also unattended, so `-light -auto` is the expected pairing.

### GATE 1: attended (default) vs `-auto`

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

### Phase B: full (default) vs `-light`

Both modes implement via `subagent-driven-development` (fresh subagent per task — SDD's per-task **isolation** is retained in both). They differ only in the **review layer**:

- **full (default):** SDD fresh subagent per task, `task-reviewer` **per task**, then a final whole-branch review. See Runbook step 7-8.
- **`-light`:** SDD fresh subagent per task (**same as full**), **no per-task `task-reviewer`**, followed by **one final whole-branch review only**. See Runbook step 7-8.

**Why `-light` is safe (008 followup evidence):** the correctness net that matters is SDD's **fresh-subagent-per-task isolation**, which `-light` retains. The per-task *review* that `-light` drops was measured (008 followup, task 195, cell-C=SDD-no-review vs cell-D=inline-with-review, 2 reps each) to be **not load-bearing**: the reviewed arm produced the only critical regression and *both* review layers missed it, while the no-per-task-review arm stayed correct on the core requirement. Caveat: n=2 — treat as directional, and keep the escalation triggers below. What `-light` must never weaken is the **final whole-branch review**: it is *always* a fresh subagent that receives only the diff, never any implementing subagent's or the orchestrator's context (self-review bias). Dropping the per-task early-catch layer is the accepted `-light` tradeoff; dropping SDD isolation (the old inline `-light`) or reviewer independence is not — that is why `-light` no longer means inline `executing-plans`.

**Who decides which tasks get `-light`:** the dispatching PM session, at launch time — j-devflow does not judge task eligibility itself (mirrors how `-auto`'s launch choice works). See `joifup-pm/SKILL.md`.

**`-light` escalation triggers — pause and ask the dispatcher, fall back to full Phase B for the rest of the task:**
- the diff touches auth / input / secrets / API / sensitive data — the same category that already requires `ecc:security-reviewer` in full mode; a single final review is not enough here;
- a schema change, data migration, deletion, or public API-contract change turns out to be needed — same irreversible/high-blast-radius category as the `-auto` triggers;
- the scope grows beyond what was expected (e.g. an assumed 1-2 file fix spreads into unrelated modules) — the "light is enough" premise no longer holds;
- the final whole-branch review returns any Critical/Important — work the fix-loop as usual, but note that `-light` skipped the earlier catch point.

Same pause-and-ask mechanism as `-auto`: stop, surface the question to the dispatcher, resume on the answer.

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
7. Read the persisted plan, then branch on Phase B mode:
   - **full (default):** `superpowers:subagent-driven-development` — fresh subagent per task, English atomic commits, `task-reviewer` per task; add `agentType: ecc:security-reviewer` on any task touching auth/input/secrets/API/sensitive data. The Driver keeps the orchestration/fix loop — only per-task units are subagents.
   - **`-light`:** `superpowers:subagent-driven-development` — fresh subagent per task, **same as full**, English atomic commits per task — **but do NOT dispatch `task-reviewer` per task.** The only review the change receives is the final whole-branch review (step 8). Watch for the `-light` escalation triggers below; if one fires, **restore per-task review (full behavior) for the rest of the task** and pause-and-ask the dispatcher.
   - **Worktree-pinning contract (every subagent dispatch — implementer, fix, reviewer; full and `-light` alike):** both modes dispatch SDD implementer subagents plus the final-review subagent, so the pinning contract applies **identically** in full and `-light`. Agent subagents do **not** inherit this session's `EnterWorktree` cwd — a fresh subagent starts in the primary checkout. So each dispatch MUST: (a) state `Worktree root: <WT>` (the `$WT` from step 2), never a blank/relative "Work from"; (b) make the subagent's **first action** `cd "<WT>"` then assert `test "$(git rev-parse --show-toplevel)" = "<WT>"` — on mismatch **STOP and report BLOCKED**, never edit or run cargo/pnpm in the fallback dir; (c) keep every path relative to `<WT>` (or `<WT>/…`) and **forbid literal primary paths** (`/Users/…/joifup/…` lacking the `.claude/worktrees/<branch>/` segment); (d) pin builds/tests to the worktree manifest — Rust: `cargo … --manifest-path "<WT>/apps/desktop/src-tauri/Cargo.toml"`; never a bare `cargo`/`cargo fmt`/`pnpm` that trusts cwd.
8. Whole-branch review: inject `ecc:<lang>-reviewer` by changed language (+ `ecc:security-reviewer` if the diff warrants), dispatched fresh with **only the diff** — never the implementing session's conversation context, in full mode or `-light` alike. Critical/Important are blocking → fix loop until clean; re-review after a fix goes through the same fresh-diff-only dispatch, not a self-check by the session that made the fix. **In `-light` mode this is the only review the change receives** — there is no per-task review preceding it.
9. `superpowers:verification-before-completion` + tests green.
10. **UAT 自動化 + `j-finish`**: UI 変更を含む branch は `pnpm uat --task <id>` を実行して `.uat-evidence/<id>/` に証跡を生成する（spec で確定した受け入れ基準を `apps/web/e2e/<id>.uat.spec.ts` に書いてから）。**証跡は commit しない** — `.uat-evidence/` は gitignore 済みで、画像・動画は `gh pr comment --attach` で PR に添付する（joifup tasks/295 以降）。PR 本文には pr-body recipe の `## 受け入れ基準` と `## UAT 証跡`（summary.md の PASS/FAIL 表＝テキストのみ）を載せ、画像・動画は証跡コメント側に置く。その後 `j-finish` に `--uat-evidence-dir .uat-evidence/<id>` を渡すと、push→PR→証跡コメント→Task→In review→Discord を行う。**UAT ユーザーアクション task は file しない**（旧 heavy 分岐は廃止）。UI を含まない変更では UAT を省略し `## テスト` のみで良い。**The machine stops here.**

**Phase C — Approve (human)**
11. Human reviews. On approval: Task → Done, commit `chore(joifup): approve <task-id>` (English), merge. Once merged, **remove the isolated worktree without prompting** (`ExitWorktree`, or `git worktree remove`) — it is disposable post-merge, so cleanup needs no separate approval; do not ask. **HUMAN GATE 2. Nothing auto-merges** — the human owns only the approval/merge decision; the post-merge worktree cleanup is automatic.

## Guards (all mode combinations)

- **Design gate (before step 7):** never write code before design approval. attended → the human approves; `-auto` → brainstorming's own recommendation is auto-approved **unless** an escalation trigger fires (see **Modes**), then pause-and-ask the dispatcher. Never fabricate approval from the overview-level task body.
- **Fix-loop exit (before step 10):** no open Critical/Important from any reviewer — neither `-auto` nor `-light` may lower this bar.
- **Before step 10's external actions:** PR/Discord/status are externally visible and hard to undo — checkpoint on green tests + clean review first.
- **Merge/Done:** structurally impossible for the machine — reserved for Phase C (human), in both modes.
- **Worktree isolation (every subagent, `-auto` included):** the dispatch is the only thing keeping a subagent out of the primary checkout — `EnterWorktree` moves only THIS session, not its subagents. No dispatch goes out without the `cd "<WT>"` + `git rev-parse --show-toplevel` equality assert as the subagent's first step; a subagent that can't confirm it is in `<WT>` BLOCKs rather than editing primary. Cheap (one shell check, once, at dispatch start) vs the far larger cost of a primary leak + recovery. Root cause: tasks/156.

## Common Mistakes

- Letting the plan lean on unstated Phase-A context — the plan must be a self-contained contract a fresh SDD orchestrator (or a future reader) can run without the design dialogue. (This, not a session boundary, is what matters; SDD isolates each task regardless.)
- Wrapping: editing what superpowers/adapters do instead of just sequencing them.
- Merging or marking Done from Phase B (the machine) — that is the human gate.
- Letting brainstorming/writing-plans commit the spec/plan at their superpowers defaults (`docs/superpowers/specs|plans/`) — those are not Joifup-indexed (`**/notes/**` only) or Task-linked. Stage them uncommitted; `md2joifup` is the only commit, into `notes/document/` and `notes/plan/`.
- Naming a branch with a slash (`feature/154-…`) or dispatching an SDD subagent without pinning it to `<WT>` — the subagent silently lands in the primary checkout and edits / `cargo fmt`s there (observed: tasks 154, 155). Hyphen-name the branch and carry `<WT>` + the toplevel assertion in every dispatch.
- **Reviving the old inline `-light`** — `-light` no longer means `executing-plans`/same-session inline. It is SDD (fresh subagent per task) minus the per-task review. Inline implementation was measured (008) to carry the correctness variance, so it is gone.
- **Letting the final whole-branch review see implementation context** — in `-light` it is the ONLY review, so it must always be a fresh subagent receiving only the diff, never any implementing subagent's or the orchestrator's conversation context (there is no per-task review preceding it to catch what a compromised final review misses).
