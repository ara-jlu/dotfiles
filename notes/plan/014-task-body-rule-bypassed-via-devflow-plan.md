---
title: 起票を j-task に集約する実装計画
tag: [plan]
Project: devops
Task: 014-task-body-rule-bypassed-via-devflow
created_at: 2026-09-22
updated_at: 2026-09-22
---

# 起票を j-task に集約する実装計画

**Goal:** 流れの中の起票（ユーザーの「タスク起票して」・j-devflow の分解・最終レビューの残余・PM の申し送り）がすべて `j-task` を経由し、本文が `## 概要` / `## 背景` / `## 起票時のメモ（未検証）` の 3 節に収まるようにする。

**Architecture:** 機械検査は置かず、規則を持つ `j-task` の起動条件を強め、起票が起こりうる 3 つのスキル（`j-devflow` / `j-finish` / `md2joifup`）から `j-task` へのポインタを置く。`j-task` の本文規則には未検証の事前調査を置ける第 3 の節を足す。別リポジトリ（joifup）の `joifup-pm` に残る矛盾は、新しい規則の形で joifup 側に起票して申し送る。設計は `notes/document/014-task-body-rule-bypassed-via-devflow-design.md`。

**Tech Stack:** markdown（SKILL.md）のみ。コードは無い。検証は `grep` と目視。

## Global Constraints

- 編集するファイルはすべて worktree 内の `.claude/skills/<name>/SKILL.md`。`~/.claude/skills` は `/Users/ara/Joifup/dotfiles/.claude/skills`（主チェックアウト）への symlink なので、**`~/.claude/skills/...` を編集してはならない**。必ず `<WT>/.claude/skills/...` を編集する。
- 日本語の記述規約は `<WT>/.claude/rules/skill-language.md` に従う。要点: 見出しは語彙表の語のみ（`## よくある失敗` 等の既存見出しを変えない）、`description` の末尾は「…に該当する場合。」、**日本語を桁数で折り返さない**（1 文は改行せずに書く）、英数字と日本語の間に半角スペース、全角 `；` を使わない。
- 既に日本語で書かれている既存の段落は、計画が指定した箇所以外バイト単位で保持する。
- コミットメッセージは英語・Semantic Commit・1 commit = 1 logical change。
- `md2joifup` の `description` には起動語を足さない（`user-invocable` を持たないため）。
- 既存の fde タスクは触らない。`joifup-pm/SKILL.md` は編集しない（申し送りのみ）。

---

### Task 1: j-task — 起動語と第 3 の節

**Files:**
- Modify: `.claude/skills/j-task/SKILL.md:3`（`description`）
- Modify: `.claude/skills/j-task/SKILL.md:31-38`（`## 本文`）
- Modify: `.claude/skills/j-task/SKILL.md:44-50`（`## よくある失敗`）

**Interfaces:**
- Consumes: なし
- Produces: 節名 `## 起票時のメモ（未検証）`（Task 2〜5 がこの文字列をそのまま参照する）

- [ ] **Step 1: 現状を確認する**

Run: `grep -n '^description:' .claude/skills/j-task/SKILL.md && grep -c '起票時のメモ' .claude/skills/j-task/SKILL.md`
Expected: description の 1 行が表示され、続けて `0`（節名はまだ無い）。

- [ ] **Step 2: `description` を置き換える**

3 行目の `description:` 行全体を次の 1 行に置き換える（1 行のまま。折り返さない）:

```yaml
description: タスクやアイデアを Joifup に backlog として起票する、あるいは開発の入口として記録するときに使う。ユーザーの「タスク起票して」「タスクにしておいて」「別タスクに切り出して」「follow-up を起票」「残余を起票」「申し送りのタスクを作って」、および j-devflow・brainstorming・最終レビュー・PM セッションの流れの中で新しい Task を作る場面（`md2joifup --db tasks` を直接叩く前に必ずここを通る）、「あとで詳細を詰めるので今は記録だけしたい」「j-devflow を始める前の起票」に該当する場合。
```

- [ ] **Step 3: `## 本文` の節構成と禁止事項を置き換える**

`## 本文` 配下の 4 つの箇条書きのうち、1 つ目（`- **節構成：**` で始まる行）と 3 つ目（`- **絶対に書かないもの：**` で始まる行）を置き換え、3 つ目の直後に 1 項目を足す。2 つ目（サイズの目安）と 4 つ目（既存タスクの粒度）は変えない。置き換え後の `## 本文` 全体:

```markdown
## 本文

概要レベルのみ。詳細な要件はタスクの brainstorming に属する。

- **節構成：** `# <title>`（H1 — `md2joifup` がここからタスクタイトルを取得する。無いと実行が落ちる）＋ `## 概要`（必須）＋ `## 背景`（「なぜ今か」が自明でないときのみ）＋ `## 起票時のメモ（未検証）`（捨てると再取得に費用がかかる事前調査があるときのみ）。他の `##` 節は置かない。
- **サイズの目安：** 概要は3〜5行、背景は3行以内、ファイル全体でおよそ1,500 B。目安であって上限ではない — 迷ったら削る。
- **絶対に書かないもの：** 受け入れ基準、実装方針、確定した設計判断、トレードオフの比較の結論。これらは brainstorming・plan・PR 本文に置き場所がある。「決めること」「やらないこと」を独立した `##` 節にしない — 候補としてメモ節の箇条書きに留める。
- **`## 起票時のメモ（未検証）` に置いてよいもの：** 一次資料の引用と行番号、探索の手がかり（どのファイル・どのタスク・どの決定を先に読むか）、危ないところ（壊しやすい既存の資源）、決めることの候補、やらないことの候補、出どころ（どのレビュー・実験から出たか。実験なら方法も）。**この節は brainstorming の出発点の材料であって結論ではない。** 実装セッションは検証してから使う。行番号は目安なので文字列で探す。上限は置かないが、再取得に費用がかかるものだけを置く。
- **既存タスクの粒度に合わせない。** 詳細に書かれた参照先タスクは基準ではない — **このルールが勝つ。**
```

- [ ] **Step 4: `## よくある失敗` に 2 項目を足す**

`- 本文に分析・引用・トレードオフを書く — …` の行を次の 1 行に置き換え、その直後に 2 行を足す（他の項目は変えない）:

```markdown
- 本文に受け入れ基準・実装方針・確定した判断を書く — 実装者が起票者の問題理解に縛られ、誤解までそのまま引き継がれる。引用や手がかりは `## 起票時のメモ（未検証）` に置く。
- 流れの中の起票で `j-task` を飛ばして `md2joifup --db tasks` を直接叩く — 本文の規則を通らない（fde の 043・049・050・057・058 で実際に起きた）。
- メモ節の内容を検証済みとして brainstorming を省く — 節名の「未検証」が契約である。
```

- [ ] **Step 5: 検証する**

Run: `grep -c '起票時のメモ（未検証）' .claude/skills/j-task/SKILL.md; grep -n '^description:' .claude/skills/j-task/SKILL.md | grep -c 'に該当する場合。$'; grep -c '^## ' .claude/skills/j-task/SKILL.md; grep -n '；' .claude/skills/j-task/SKILL.md | wc -l`
Expected: `3`（節構成・置いてよいもの・よくある失敗の 1 項目）、`1`（description の末尾）、`6`（`##` 見出しの数は改訂前と同じ: 概要/使う場面/流れ/本文/識別子/よくある失敗）、`0`（全角セミコロン無し）。

改訂前の `##` 見出し数と比べる: `git show HEAD:.claude/skills/j-task/SKILL.md | grep -c '^## '` も `6` であること。

- [ ] **Step 6: Commit**

```bash
git add .claude/skills/j-task/SKILL.md
git commit -m "docs(j-task): widen triggers and allow an unverified filing-memo section"
```

---

### Task 2: j-devflow — 流れの中の起票を j-task へ

**Files:**
- Modify: `.claude/skills/j-devflow/SKILL.md:75`（手順書 Phase A 手順 1）
- Modify: `.claude/skills/j-devflow/SKILL.md:103-112`（`## よくある失敗`）

**Interfaces:**
- Consumes: Task 1 の節名 `## 起票時のメモ（未検証）`
- Produces: なし

- [ ] **Step 1: 現状を確認する**

Run: `sed -n 75p .claude/skills/j-devflow/SKILL.md | cut -c1-60; grep -c 'j-task' .claude/skills/j-devflow/SKILL.md`
Expected: `1. \`tasks/\` の下に Joifup の **Task** を用意する: 新規 → ...` と、`2`（既存の j-task 言及は 2 箇所: 手順 1 と `-auto` の説明）。

- [ ] **Step 2: 手順 1 の末尾に 1 文を足す**

75 行目（`1. \`tasks/\` の下に Joifup の **Task** を用意する: …すべてがこれを起点にする。`）の末尾に、同じ行のまま次を足す:

```markdown
 **流れの中で生まれる Task も同じ経路である** — brainstorming の分解で出る子タスク、最終レビュー・fix ループで本ブランチでは閉じない残余は `/j-task` で起票し、`md2joifup --db tasks` を直接叩かない。事前調査は `j-task` の `## 起票時のメモ（未検証）` に置く。
```

- [ ] **Step 3: `## よくある失敗` に 1 項目を足す**

`- Phase B（機械）からマージする、あるいは Done にする — …` の行の直後に次の 1 行を足す:

```markdown
- 残余や子タスクを `md2joifup --db tasks` で直接起票する — `j-task` の本文規則を通らず、受け入れ基準や確定した判断を持つ Task ができる（fde の 043・049・050・057・058）。起票は常に `/j-task` 経由。
```

- [ ] **Step 4: 検証する**

Run: `grep -c 'j-task' .claude/skills/j-devflow/SKILL.md; grep -c '起票時のメモ（未検証）' .claude/skills/j-devflow/SKILL.md; git diff --stat`
Expected: `3`（`grep -c` は行数を数える: `-auto` の説明行・手順 1 の行・追加した失敗の項目の 3 行）、`1`、`1 file changed, 2 insertions(+), 1 deletion(-)`（手順 1 の行は置換、失敗の項目は追加）。

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/j-devflow/SKILL.md
git commit -m "docs(j-devflow): route in-flight task filing through j-task"
```

---

### Task 3: j-finish と md2joifup — j-task へのポインタ

**Files:**
- Modify: `.claude/skills/j-finish/SKILL.md:53`（`## よくある失敗` の最終項目の直後）
- Modify: `.claude/skills/md2joifup/SKILL.md:27`（「Task 作成（tasks db）」の段落）

**Interfaces:**
- Consumes: Task 1 の節名は参照しない（ポインタのみ）
- Produces: なし

- [ ] **Step 1: 現状を確認する**

Run: `grep -c 'j-task' .claude/skills/j-finish/SKILL.md .claude/skills/md2joifup/SKILL.md`
Expected: `.claude/skills/j-finish/SKILL.md:0` と `.claude/skills/md2joifup/SKILL.md:0`。

- [ ] **Step 2: j-finish の `## よくある失敗` に 1 項目を足す**

`- UAT ユーザーアクション task を新規 file する — 廃止済み。…` の行の直後に次の 1 行を足す:

```markdown
- 残余タスクを `j-task` を経由せず起票する — 本文の規則を通らない。本ブランチで閉じない残余は `/j-task` で起票し、設計文書にも理由を残す。
```

- [ ] **Step 3: md2joifup の「Task 作成」段落に 1 文を足す**

27 行目の段落（`**Task 作成（tasks db）：** …\`--db notes\`（既定）は変わらない。`）の末尾に、同じ行のまま次を足す:

```markdown
 **本文の規則は `j-task` が持つ。** `--db tasks` と `--new-task` を呼ぶのは `j-task` の内部からに限る — 他のスキルやセッションが直接叩くと本文の規則を通らない。
```

- [ ] **Step 4: 検証する**

Run: `grep -c 'j-task' .claude/skills/j-finish/SKILL.md .claude/skills/md2joifup/SKILL.md; grep -n '^description:' .claude/skills/md2joifup/SKILL.md | grep -c '起票'`
Expected: `.claude/skills/j-finish/SKILL.md:1`、`.claude/skills/md2joifup/SKILL.md:1`、`0`（md2joifup の description に起動語を足していない）。

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/j-finish/SKILL.md .claude/skills/md2joifup/SKILL.md
git commit -m "docs(skills): point j-finish and md2joifup at j-task for task filing"
```

---

### Task 4: joifup-pm の矛盾を joifup リポジトリに申し送る

**Files:**
- Create: `/Users/ara/Joifup/joifup/tasks/<NNN>-pm-filing-rule-conflicts-with-j-task.md`（番号は `pnpm run task:new` が採番する）
- 読むだけ: `/Users/ara/Joifup/joifup/.claude/skills/joifup-pm/SKILL.md`（§4 起票）、`<WT>/.claude/skills/j-task/SKILL.md`（Task 1 で改訂済み）

**Interfaces:**
- Consumes: Task 1 の本文規則（3 節）。本文はこの規則の最初の実例になる。
- Produces: joifup 側の起票ファイルのパス（PR 本文と最終レビューのパッケージに載せる）

このタスクだけ別リポジトリ（`/Users/ara/Joifup/joifup`、main）に書く。joifup-pm の規定で Task の起票は main への直接 commit が許されているが、**番号は必ず `pnpm run task:new` で採番する**（ローカル max+1 では他レーンの番号と衝突する）。**push はしない** — commit まで行い、パスを報告する。

- [ ] **Step 1: joifup が clean であることを確認する**

Run: `cd /Users/ara/Joifup/joifup && git status --porcelain | wc -l && git branch --show-current`
Expected: `0` と `main`。0 でなければ STOP して BLOCKED を報告する（他人の作業中の差分に相乗りしない）。

- [ ] **Step 2: 本文を scratchpad に書く**

`/private/tmp/claude-501/-Users-ara-Joifup-dotfiles/b7abbd33-c3ca-430b-86e4-9274855232d2/scratchpad/joifup-pm-filing-rule.md` に次を書く（frontmatter は書かない。`md2joifup` が付ける）:

```markdown
# joifup-pm の起票の書き方が j-task の本文規則と衝突している

## 概要

`joifup-pm/SKILL.md` §4 起票は「残余の起票は『着手時に設計し直さない』粒度で書く。復帰先を要素レベルで確定し、代替案を却下する理由まで書く」と定めている。一方 `j-task` は本文を `## 概要` / `## 背景` / `## 起票時のメモ（未検証）` の 3 節に限り、確定した設計判断と実装方針を禁じている（dotfiles `tasks/014`）。PM が起票するたびにどちらかの規則を破ることになるので、§4 の書き方を `j-task` の規則に合わせて書き直す。

## 背景

`j-task` の規則の目的は、実装者が起票者の問題理解に縛られないことである。復帰先と却下理由を確定して書くと、実装セッションはそれを検証済みの結論として受け取る。dotfiles `tasks/014` は事前調査を「未検証」の印付きで残す節を用意したので、PM の起票もその形に乗せられる。

## 起票時のメモ（未検証）

- 衝突箇所: `joifup-pm/SKILL.md` §4 起票 の「**残余の起票は「着手時に設計し直さない」粒度で書く。** 復帰先を要素レベルで確定し、代替案を却下する理由まで書く。」の 1 項目。同じ §4 の「原因未特定のバグは、観測を正確に・推測は推測と明示して書く」「実験から起票するときは方法も書かせる」は `j-task` のメモ節の規定と方向が同じで、衝突しない。
- 設計の根拠: dotfiles `notes/document/014-task-body-rule-bypassed-via-devflow-design.md` の「joifup-pm の矛盾は申し送る」。
- 決めることの候補: §4 の当該項目を「復帰先の候補と却下した代替案はメモ節に置き、確定はさせない」と書き換えるか、項目ごと削って `j-task` を参照するか。
- 出どころ: dotfiles `tasks/014` の brainstorming（2026-09-22）で見つけた。
```

- [ ] **Step 3: 本文が規則に収まっていることを確認する**

Run: `grep '^## ' /private/tmp/claude-501/-Users-ara-Joifup-dotfiles/b7abbd33-c3ca-430b-86e4-9274855232d2/scratchpad/joifup-pm-filing-rule.md`
Expected: ちょうど 3 行 — `## 概要` / `## 背景` / `## 起票時のメモ（未検証）`。

- [ ] **Step 4: joifup で起票する**

Run:
```bash
cd /Users/ara/Joifup/joifup && pnpm run task:new --status "Not started" --project joifup --slug pm-filing-rule-conflicts-with-j-task --keep-source -- /private/tmp/claude-501/-Users-ara-Joifup-dotfiles/b7abbd33-c3ca-430b-86e4-9274855232d2/scratchpad/joifup-pm-filing-rule.md
```
Expected: stdout に `tasks/<NNN>-pm-filing-rule-conflicts-with-j-task.md`（stderr に `renumbered … (origin-aware allocation)` が出ればよい。`could not fetch origin` なら続けて `pnpm run task:id:check` を回す）。`--project joifup` は必須 — `projects/` に `joifup.md` と `joifup-poc-001-duckdb.md` の 2 つがあり、単一エントリのフォールバックが効かない。

- [ ] **Step 5: 生成物を確認する**

Run: `cd /Users/ara/Joifup/joifup && f=$(ls tasks/*-pm-filing-rule-conflicts-with-j-task.md) && head -8 "$f" && grep -c '^## ' "$f"`
Expected: frontmatter に `title:` / `status: Not started` / `Project: joifup` があり、`## ` の数は `3`。

- [ ] **Step 6: joifup で commit する（push はしない）**

```bash
cd /Users/ara/Joifup/joifup && git add tasks/*-pm-filing-rule-conflicts-with-j-task.md && git commit -m "chore(joifup): file task to align joifup-pm filing rule with j-task"
```

報告には joifup 側のファイルパスと commit hash を含める。**push はしない**。

**Fallback:** サンドボックスが `/Users/ara/Joifup/joifup` での git 操作を拒む場合は Step 2 と 3 まで行い、Step 4 のコマンドをそのまま報告して BLOCKED とする（orchestrator が人間に引き継ぐ）。

---

### Task 5: 改訂後の j-task で起票の試行（検証のみ・commit なし）

**Files:**
- Create: `/private/tmp/claude-501/-Users-ara-Joifup-dotfiles/b7abbd33-c3ca-430b-86e4-9274855232d2/scratchpad/trial-058.md`（試行の出力。commit しない）
- 読むだけ: `<WT>/.claude/skills/j-task/SKILL.md`

**Interfaces:**
- Consumes: Task 1 の本文規則
- Produces: 試行の出力ファイル（orchestrator が `## ` 見出しを検査する）

fresh subagent に、改訂後の `j-task/SKILL.md` **だけ**を読ませてから、fde `tasks/058` 相当の起票依頼を渡す。`md2joifup` は実行させず、本文を scratchpad に書かせるだけにする。

- [ ] **Step 1: subagent に渡す依頼文**

```
<WT>/.claude/skills/j-task/SKILL.md を読み、その「本文」の規則に従って次の Task の本文を /private/tmp/claude-501/-Users-ara-Joifup-dotfiles/b7abbd33-c3ca-430b-86e4-9274855232d2/scratchpad/trial-058.md に書け。md2joifup は実行するな。frontmatter は書くな。

依頼: 「document/043-prohibited-phrases §1 の 85 行と 93 行が、証憑の経路について食い違っている（85 行は『ただ、別の経路が 1 つあります。保守のための入り口で…』と限定を添え、93 行は『こちらが管理する設備を、証憑が通ることはありません』と限定が無い）。tasks/046 の最終レビューで見つけた。046 では 043 は触らない制約だったので直していない。93 行を 85 行に合わせるか、参照に畳むかは未定。行番号は 046 が行を足しているのでずれているかもしれない。あわせて 85 行の『常時開いています』も 046 で『外さずに置いておきます』に変えた確定文とぶつかる。これをタスクにして。」
```

- [ ] **Step 2: 出力を検査する**

Run: `grep '^## ' /private/tmp/claude-501/-Users-ara-Joifup-dotfiles/b7abbd33-c3ca-430b-86e4-9274855232d2/scratchpad/trial-058.md; grep -c '受け入れ基準\|^## 決めること\|^## やらないこと\|^## 出どころ' /private/tmp/claude-501/-Users-ara-Joifup-dotfiles/b7abbd33-c3ca-430b-86e4-9274855232d2/scratchpad/trial-058.md`
Expected: `## ` 見出しは `## 概要` / `## 背景` / `## 起票時のメモ（未検証）` の部分集合（`## 概要` は必須）。2 つ目のカウントは `0`。

- [ ] **Step 3: 結果を記録する**

合格なら PR 本文の `## テスト` に「改訂後の j-task を読んだ fresh subagent が 058 相当の依頼を 3 節に収めた」と書く。不合格（規則外の節が出た）なら、Task 1 の `## 本文` の文言を見直して再試行する — 規則の側を緩めるのではなく、文言の曖昧さを潰す。

---

## 実装後（orchestrator）

- ブランチ全体の最終レビュー: 変更は markdown のみなので言語別 reviewer は無い。fresh subagent に diff と、申し送り先の joifup 側の起票ファイル（Task 4 の生成物）を渡し、次を確認させる: ①設計文書の決定事項がすべて diff に現れている ②`skill-language.md` の規約（見出し語彙・description 末尾・折り返し無し・半角スペース） ③申し送りタスクの本文が 3 節に収まっている。
- j-finish: UI 変更なし → UAT 省略、`## テスト` に Task 5 の結果と grep の結果を書く。PR 本文に joifup 側の起票ファイルのパスと commit hash（未 push）を明記する。
