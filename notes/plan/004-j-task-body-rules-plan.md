---
title: j-task Body 規定の実装計画
tag: [plan]
Project: devops
Task: 004-j-task-overview-level
created_at: 2026-09-02
updated_at: 2026-09-02
---

# j-task Body 規定の実装計画

**Goal:** `j-task` スキルに、タスク本文を overview-level に保つ規定を独立見出しとして立て、起票時に詳細要件が書き込まれるのを防ぐ。

**Architecture:** `.claude/skills/j-task/SKILL.md` の 1 ファイルに対する 3 つの相互依存する編集。新設節 `## Body` に規定の実体を置き、Flow ステップ 2 はそこを参照するだけにし、Common Mistakes は「なぜ悪いか」で補う。3 編集は分割不可（途中状態ではファイルが自己矛盾する — 例: Flow が存在しない `## Body` を参照する）。

**Tech Stack:** Markdown のみ。ビルド・実行系は無い。

## Global Constraints

- 変更対象は `.claude/skills/j-task/SKILL.md` の **1 ファイルのみ**。`md2joifup`、既存タスク本文（`tasks/001`〜`004`、他リポジトリを含む）には一切触れない。
- 追記は **英語**（既存ファイルが全編英語のため）。ただしタスク本文の節名 `## 概要` / `## 背景` は日本語のまま扱う。
- 分量は **上限ではなく目安**。「a guideline, not a cap」の語を落とさない。
- 自己検査ステップも機械チェックも **追加しない**（設計で明示的に却下済み）。
- 同ファイル内の `Branch (later, in j-devflow) = feature/<filename-id>` という古い記述には **触れない**（スコープ外と設計で明記）。
- 実行可能なテストは存在しない。検証は `grep` による記述の存在／不在の確認と、目視の一貫性チェックで行う。

---

### Task 1: j-task SKILL.md に Body 規定を導入する

**Files:**
- Modify: `.claude/skills/j-task/SKILL.md`（24 行目・31 行目直前・39 行目）
- Test: なし（実行可能なテストスイートが存在しないため。代わりに Step 2 / Step 4 の `grep` 検証を用いる）

**Interfaces:**
- Consumes: なし（先行タスク無し）
- Produces: なし（後続タスク無し）

**変更前の該当箇所**（確認用。行番号は編集前のもの）:

```
24:2. **Generate content:** a Japanese `title` and an **overview-level** body (no deep requirements). Derive an English `--slug`.
...
31:## Identifier
...
39:- Deep requirements at capture — keep the body overview-level; detail belongs in brainstorming.
```

---

- [ ] **Step 1: 検証スクリプトを用意し、現状で FAIL することを確認する**

スクリプトファイルは作らず、worktree ルートで以下をそのまま実行する。

Run:

```bash
F=".claude/skills/j-task/SKILL.md"
fail=0
grep -q '^## Body$' "$F"                        || { echo "NG: ## Body 節が無い"; fail=1; }
grep -q 'a guideline, not a cap' "$F"           || { echo "NG: 目安の但し書きが無い"; fail=1; }
grep -q "Do not match an existing task's granularity" "$F" || { echo "NG: 粒度優先の明記が無い"; fail=1; }
grep -q 'a body per \*\*Body\*\* below' "$F"    || { echo "NG: Flow が Body を参照していない"; fail=1; }
grep -q 'Deep requirements at capture' "$F"     && { echo "NG: 旧 Common Mistakes 行が残っている"; fail=1; }
grep -q "the filer's reading of the problem" "$F" || { echo "NG: 新 Common Mistakes 行が無い"; fail=1; }
grep -q "Pulled toward a referenced task's granularity" "$F" || { echo "NG: 新 Common Mistakes 行(2)が無い"; fail=1; }
grep -q 'Branch (later, in j-devflow) = `feature/<filename-id>`' "$F" || { echo "NG: スコープ外の記述を壊した"; fail=1; }
[ "$fail" = 0 ] && echo "ALL PASS" || echo "FAILED"
```

Expected（変更前）: 以下の 7 行の NG が出て `FAILED` で終わる。

```
NG: ## Body 節が無い
NG: 目安の但し書きが無い
NG: 粒度優先の明記が無い
NG: Flow が Body を参照していない
NG: 旧 Common Mistakes 行が残っている
NG: 新 Common Mistakes 行が無い
NG: 新 Common Mistakes 行(2)が無い
FAILED
```

（`Branch (later, ...)` の行は変更前から存在するので NG は出ない。これはスコープ外の記述を壊していないことを担保するためのガード。）

- [ ] **Step 2: Flow ステップ 2 を Body への参照に差し替える**

24 行目を、次の 1 行に置き換える。

変更前:

```markdown
2. **Generate content:** a Japanese `title` and an **overview-level** body (no deep requirements). Derive an English `--slug`.
```

変更後:

```markdown
2. **Generate content:** a Japanese `title` and a body per **Body** below. Derive an English `--slug`.
```

- [ ] **Step 3: `## Body` 節を新設する**

`## Identifier`（元 31 行目）の直前に、以下をそのまま挿入する。前後に空行を 1 行ずつ入れ、既存の節間の空け方に合わせる。

```markdown
## Body

Overview-level only. Detailed requirements belong to the task's brainstorming.

- **Sections:** `## 概要` (required) + `## 背景` (only when "why now" is not self-evident). No other sections.
- **Size guideline:** 概要 3-5 lines, 背景 3 lines or fewer, whole file around 1,500 B. A guideline, not a cap — but when in doubt, cut.
- **Never write:** analysis, research findings, quotes, trade-off comparisons, implementation approach, acceptance criteria. All of it belongs to brainstorming and the plan.
- **Do not match an existing task's granularity.** A referenced task written in detail is not the standard — **this rule wins.**
```

注意: 既存ファイルの箇条書きは 1 項目 1 行（折り返さない）で書かれている。上記もその形に揃えてあるので、途中で改行を入れないこと。

- [ ] **Step 4: Common Mistakes の 1 行を 2 行に差し替える**

元 39 行目を削除し、同じ位置に 2 行を置く。

変更前:

```markdown
- Deep requirements at capture — keep the body overview-level; detail belongs in brainstorming.
```

変更後:

```markdown
- Analysis / quotes / trade-offs in the body — the implementer gets bound to the filer's reading of the problem, and a misunderstanding rides along.
- Pulled toward a referenced task's granularity — the Body rules win.
```

箇条書きの並び順は変えない（`Degraded slug ...` の次、`Hand-writing children ...` の前）。

- [ ] **Step 5: 検証スクリプトを再実行し、PASS することを確認する**

Run: Step 1 と同一のワンライナー。

Expected: `ALL PASS` のみが出力される。NG 行が 1 つでも出たら、その項目を修正してから再実行する。

- [ ] **Step 6: 目視で一貫性を確認する**

Run: `cat .claude/skills/j-task/SKILL.md`

以下を確認する。`grep` では拾えないため人（または実装エージェント）が読む。

1. Flow ステップ 2 / `## Body` / Common Mistakes の三者に、規定の**重複定義も矛盾も無い**こと。特に Overview の "this only records title + an overview body" と `## Body` が言い分を違えていないこと。
2. `## Body` の記述だけで、他を参照せず本文が書けること（節・分量・禁止事項・優先順位の 4 点が揃っている）。
3. `## Identifier` 節が無傷であること（`Branch (later, in j-devflow) = feature/<filename-id>` を含め、一字も変えていない）。

- [ ] **Step 7: コミットする**

```bash
git add .claude/skills/j-task/SKILL.md
git commit -m "feat(j-task): add Body rules to keep task bodies overview-level"
```

---

## 検証（タスク完了後）

`.claude/skills/j-task/SKILL.md` と `tasks/004-j-task-overview-level.md` 以外に差分が無いことを確認する。

Run: `git diff --stat main...HEAD -- . ':!notes'`

Expected: `.claude/skills/j-task/SKILL.md` と `tasks/004-j-task-overview-level.md` の 2 ファイルが並ぶこと。後者は `status` frontmatter の変更のみ（タスク本文は無変更。これが Global Constraint の要求事項）。
