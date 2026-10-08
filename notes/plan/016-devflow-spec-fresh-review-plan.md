---
title: j-devflow の設計書の fresh レビュー 実装計画
tag: [plan]
Project: devops
Task: 016-devflow-spec-fresh-review
created_at: 2026-10-08
updated_at: 2026-10-08
---

# j-devflow の設計書の fresh レビュー 実装計画

**Goal:** j-devflow の手順 3 で、GATE 1 の前に設計書を fresh な subagent にレビューさせる（専用プロンプトの新設と SKILL.md の改訂）。097 の穴を再現した設計書で、新しいプロンプトが同梱のプロンプトより効くことを確かめる。

**確定した文面:** この計画の Task 2・Task 3 に書いた文面は、タスク毎レビューと最終レビューの指摘で改訂した。確定した文面は `.claude/skills/j-devflow/references/spec-review-prompt.md` と `.claude/skills/j-devflow/SKILL.md` にある。

**Architecture:** 新規ファイル `.claude/skills/j-devflow/references/spec-review-prompt.md` が dispatch の文面を持ち、`.claude/skills/j-devflow/SKILL.md` が「いつ・何を渡し・指摘をどう扱うか」を持つ。根拠は dotfiles の `notes/document/016-devflow-spec-fresh-review-design.md`（設計書）にだけ置き、SKILL.md とプロンプトにはポインタだけを書く。検証はコードのテストではなく、LLM の subagent に読ませる比較実験で、成果物は commit しない。

**Tech Stack:** Markdown（自作スキルの日本語の文書）、Claude Code の Agent（general-purpose の subagent）、git。

## Global Constraints

- 設計書（正典）: `notes/document/016-devflow-spec-fresh-review-design.md`。計画と食い違ったら設計書が勝つ。
- Worktree root（`<WT>`）: `/Users/ara/Joifup/dotfiles/.claude/worktrees/feature-016-devflow-spec-fresh-review`。すべての subagent は最初に `cd "<WT>"` し、`git rev-parse --show-toplevel` が `<WT>` と一致することを確かめる。一致しなければ STOP して BLOCKED を報告する。主チェックアウト（`/Users/ara/Joifup/dotfiles/` 直下で `.claude/worktrees/` を含まないパス）には絶対に書き込まない。
- 自作スキルの md は日本語で書く。細則は `<WT>/.claude/rules/skill-language.md`（作業前に開く）。日本語は桁数で折り返さない（文の切れ目 `。` での改行は可）。英数字と日本語の間に半角スペース。全角の `；` を使わない。
- why の置き場所は `<WT>/.claude/rules/comment-rationale.md` の考え方に従う（作業前に開く。`paths` がコード向けなので md の編集では自動で載らない）。SKILL.md とプロンプトには設計書へのポインタと、文面から復元できない最小の理由だけを書く。数・条件の列挙を設計書から写さない。ポインタは「dotfiles の `notes/document/016-devflow-spec-fresh-review-design.md`」とリポジトリ名付きで書く（SKILL.md は symlink で全リポジトリから読まれる）。
- 既に日本語で書かれた SKILL.md の段落は、改訂の対象箇所以外をバイト単位で保持する。
- dotfiles は public、fde は private。fde の設計書・タスク本文・その再現版・その所在（パス・ブランチ名）を dotfiles のリポジトリに入れない。検証の成果物は scratchpad（下記）に置き、commit しない。
- 検証の作業ディレクトリ（scratchpad）: `/private/tmp/claude-501/-Users-ara-Joifup-dotfiles/27829f9c-771c-4224-ab3e-22ee2d6dc787/scratchpad/016-verify/`。`/private/tmp` は数日で掃除されるので、検証は 1 セッションのうちに終える。
- コミットメッセージは英語の Semantic Commit。末尾に次の2行を付ける:
  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_014pUomp7Sy3TDqRgP4kxP5d
  ```
- superpowers のファイル（`/Users/ara/.claude/plugins/cache/superpowers-marketplace/superpowers/6.1.1/` 配下）は読むだけで、絶対に書き換えない。

---

### Task 1: 097 の穴を再現した設計書を作り、同梱のプロンプトで基準を取る（RED）

**Files:**
- Create（commit しない）: `<scratchpad>/016-verify/seeded-spec.md`
- Create（commit しない）: `<scratchpad>/016-verify/task-097.md`
- Create（commit しない）: `<scratchpad>/016-verify/results.md`
- Read: `<097 の設計書>`（fde の 097 の確定版の設計書。読み取りのみ。所在はリポジトリに書かず、orchestrator が dispatch で渡す）
- Read: `<097 のタスク本文>`（fde の 097 のタスク本文。読み取りのみ。所在は同上）
- Read: `/Users/ara/.claude/plugins/cache/superpowers-marketplace/superpowers/6.1.1/skills/brainstorming/spec-document-reviewer-prompt.md`

`<scratchpad>` = `/private/tmp/claude-501/-Users-ara-Joifup-dotfiles/27829f9c-771c-4224-ab3e-22ee2d6dc787/scratchpad`

**Interfaces:**
- Produces: `seeded-spec.md`（穴を再現した設計書）、`task-097.md`（097 のタスク本文の写し）、`results.md`（試行ごとの結果の表。Task 2 が行を足す）。

- [ ] **Step 1: 097 のタスク本文を写す**

```bash
mkdir -p /private/tmp/claude-501/-Users-ara-Joifup-dotfiles/27829f9c-771c-4224-ab3e-22ee2d6dc787/scratchpad/016-verify
cp <097 のタスク本文> /private/tmp/claude-501/-Users-ara-Joifup-dotfiles/27829f9c-771c-4224-ab3e-22ee2d6dc787/scratchpad/016-verify/task-097.md
```

- [ ] **Step 2: 穴を再現した設計書を作る**

`<097 の設計書>` を `seeded-spec.md` に写し、**添付のファイルで届く入力の扱いをすべて抜く**。抜いた後の設計書は、添付のファイルが届かない前提で書かれたものとして読める状態にする。作業の規則:

1. 添付のファイルで届く入力に関わる記述を、すべて抜くか、添付なしで成り立つ内容に書き換える。
2. **抜いた後に、設計書の中に矛盾・宙に浮いた参照・TBD を残さない。** 穴は「前提の抜け」としてだけ残し、文書の中の不整合からは見つけられないようにする（同梱のプロンプトが文書の不整合から穴に辿り着けてしまうと、比較が成り立たない）。
3. 下の grep で残りを探し、残っていれば規則 1・2 で処理する。

```bash
grep -n "添付\|PDF\|Excel\|CAD" /private/tmp/claude-501/-Users-ara-Joifup-dotfiles/27829f9c-771c-4224-ab3e-22ee2d6dc787/scratchpad/016-verify/seeded-spec.md
```

Expected: 何も出力されない（終了コード 1）。

- [ ] **Step 3: results.md を作る**

```markdown
# 016 検証の結果

| 試行 | プロンプト | 添付の入力を名指しした挙げ方 | 合否への寄与 |
|---|---|---|---|
```

- [ ] **Step 4: 同梱のプロンプトで2回試す（orchestrator が実行する）**

この step は subagent の中ではなく **orchestrator のセッションが** 行う（subagent から subagent を確実には dispatch できないため）。general-purpose の subagent を、互いに独立に2回 dispatch する。文面は「前置き」＋「`spec-document-reviewer-prompt.md` のコードフェンスの中身を、`[SPEC_FILE_PATH]` を `seeded-spec.md` の絶対パスに置き換えてそのまま」とする。前置き:

```
Worktree root: /Users/ara/Joifup/dotfiles/.claude/worktrees/feature-016-devflow-spec-fresh-review
最初の行動として次を別々に実行し、toplevel が一致しなければ STOP して BLOCKED と報告してください。
cd "/Users/ara/Joifup/dotfiles/.claude/worktrees/feature-016-devflow-spec-fresh-review"
git rev-parse --show-toplevel
読み取りだけを行い、何も書き換えないでください。
Task context (the goal the spec must serve): /private/tmp/claude-501/-Users-ara-Joifup-dotfiles/27829f9c-771c-4224-ab3e-22ee2d6dc787/scratchpad/016-verify/task-097.md
```

- [ ] **Step 5: 結果を記録する**

各試行について、**Issues（Recommendations ではない）**に「添付のファイル（注文書・図面の PDF や Excel など）で届く入力を扱えない」ことを名指しした指摘があるかを判定し、`results.md` に1行ずつ足す（例: `| B1 | 同梱 | なし | 捕まえない |`）。判定の根拠として、該当する指摘の文を短く引用する。

---

### Task 2: 専用プロンプトを書き、穴を捕まえることを確かめる（GREEN）

**Files:**
- Create: `.claude/skills/j-devflow/references/spec-review-prompt.md`
- Modify（commit しない）: `<scratchpad>/016-verify/results.md`

**Interfaces:**
- Consumes: Task 1 の `seeded-spec.md`・`task-097.md`・`results.md`。
- Produces: `.claude/skills/j-devflow/references/spec-review-prompt.md`。プレースホルダは `<WT>`・`<TASK_FILE_PATH>`・`<SPEC_FILE_PATH>`・`<PREVIOUS_ROUND_FILE_PATH>` の4つ。Task 3 の SKILL.md がこのファイルを `references/spec-review-prompt.md` として指す。

- [ ] **Step 1: プロンプトのファイルを作る**

`.claude/skills/j-devflow/references/spec-review-prompt.md` を次の内容で作る（このまま書く）。

````markdown
# 設計書の fresh レビューのプロンプト

## 概要

`j-devflow` 手順 3 で、GATE 1 の前に設計書を fresh な subagent に読ませるときの dispatch の文面。書いた本人は設計の対話で前提を共有しているので、その前提自体の抜けは自己レビューでは見えない。このプロンプトは、題材の実態に照らした前提の抜けを主に見させる。根拠と、superpowers 同梱の `spec-document-reviewer-prompt.md` を使わない理由は dotfiles の `notes/document/016-devflow-spec-fresh-review-design.md` にある。

## 使い方

general-purpose の subagent に、下のコードフェンスの中身をプレースホルダを埋めて渡す。会話は渡さない。

- `<WT>` — 手順 2 で取得した worktree の絶対ルート。
- `<TASK_FILE_PATH>` — タスク本文の絶対パス。
- `<SPEC_FILE_PATH>` — staging の設計書の絶対パス。
- `<PREVIOUS_ROUND_FILE_PATH>` — 再レビューのときだけ、前回の指摘と振り分けの表のパス。初回は「（初回のレビュー）」と書く。

```
あなたは設計書のレビュアーです。設計の対話には参加していません。読み取りだけを行い、何も書き換えないでください。

Worktree root: <WT>
最初の行動として次を別々に実行し、toplevel が一致しなければ STOP して BLOCKED と報告してください。
cd "<WT>"
git rev-parse --show-toplevel   （期待値: <WT>）

入力（読み取り専用。<WT> の外の絶対パスも読んでよい）:
- タスク本文: <TASK_FILE_PATH>
- 設計書: <SPEC_FILE_PATH>
- 前回の指摘と振り分け: <PREVIOUS_ROUND_FILE_PATH>
- 設計書が参照する既存のファイルは読んでよい。

タスク本文は概要レベルで、設計の権威ではありません。ただし、この設計が果たすべき目的の物差しとして使ってください。

観点（1 と 2 が主）:
1. 目的への適合 — タスク本文が果たしたいことを、この設計で果たせるか。
2. 前提の抜け — 設計書が暗に置いている前提を書き出し、それぞれが題材の実態（入力の届き方と形式・使う人・例外・規模）と合うかを問う。設計書が扱えない入力や場面が残っていないか。題材の実態がタスク本文やファイルから分からないときは、その分野で一般にどうであるかから推して、扱えない物を具体的に名指しする（例: 「この業種では予約の多くが電話で入るが、この設計は Web フォームからの予約しか受けない」）。
3. 自己完結 — TBD、内部の矛盾、二通りに読める要件、定義されていない語、既存のファイルの記述との食い違い。
4. スコープ — 1つの実装計画に収まるか。

設計書の中に矛盾が無くても、前提が題材の実態と合わなければ指摘してください。文体の好みや言い回しは指摘しないでください。目的を果たせなくなるもの、計画や実装で実害になるものだけを挙げてください。

再レビューのときは、新しい指摘より先に、前回の各指摘について「解消 / 未解消 / 部分的」と、「採らない」とした指摘の理由が成り立つかを、根拠付きで判定してください。

出力（日本語）:

## 前回の指摘の判定
（再レビューのときだけ。指摘ごとに 判定・根拠）

## 指摘
指摘ごとに 重さ・設計書の該当箇所・根拠（読んだファイルと行、または題材の実態からの推定であること）・なぜ問題か。無ければ「指摘なし」。
- Critical: このままでは目的を果たせない
- Important: 計画や実装で実害が出る
- Minor: 直すと良いが、このまま進めてよい

## 前提の一覧
| 前提 | 合う / 合わない / 不明 | 芯 |
芯の欄には、合わなかったら目的を果たせなくなる前提に ◎ を付ける。題材の実態がタスク本文やファイルから分からない前提は「不明」とし、推して分かる範囲を一言添える。
```
````

- [ ] **Step 2: 新しいプロンプトで2回試す（orchestrator が実行する）**

この step は **orchestrator のセッションが** 行う。general-purpose の subagent を、互いに独立に2回 dispatch する。文面は Step 1 のコードフェンスの中身で、プレースホルダを次のとおり埋める。

- `<WT>` = `/Users/ara/Joifup/dotfiles/.claude/worktrees/feature-016-devflow-spec-fresh-review`
- `<TASK_FILE_PATH>` = `<scratchpad>/016-verify/task-097.md`
- `<SPEC_FILE_PATH>` = `<scratchpad>/016-verify/seeded-spec.md`
- `<PREVIOUS_ROUND_FILE_PATH>` = 「（初回のレビュー）」

- [ ] **Step 3: 結果を記録し、合否を判定する**

各試行について、`results.md` に1行ずつ足す（例: `| N1 | 新 | Important の指摘で名指し | 合格に寄与 |`）。判定の基準（設計書の「検証」の節）:

- **合格に寄与:** 「添付のファイル（注文書・図面の PDF や Excel など）で届く入力を扱えるか」を名指しして、Critical か Important の指摘、または前提の一覧の「合わない」、または「不明」かつ ◎ で挙げている。
- **寄与しない:** 添付を名指ししない一般的な挙げ方（「入力の届き方: 不明」など）、または Minor だけ。

`results.md` の末尾に判定を書く:

```markdown
## 判定

- 新しいプロンプト: 2回中 N 回 合格に寄与 → 合格 / 不合格
- 同梱のプロンプト: 2回中 M 回 捕まえた
- 結論: （下の分岐のどれか）
```

分岐:

- **新が2回とも寄与、かつ同梱が2回とも捕まえたのではない:** 合格。Step 5 へ進む。
- **新が1回以上寄与しない:** プロンプトの観点 2 の文面を直し（例を変えない。添付や注文書を例に入れて答えを漏らさない）、Step 2 から再試験する。再試験は2周まで。2周で合格しなければ STOP し、orchestrator が依頼者に問う。
- **同梱が2回とも捕まえた:** STOP。プロンプトを直さず、orchestrator が依頼者に「決定（専用のプロンプトを持つ）の見直し」を問う（設計書の「不合格のときの扱い」）。

- [ ] **Step 4: （再試験したときだけ）直した文面を記録する**

`results.md` に、直した前後の観点 2 の文面と、再試験の行を足す。

- [ ] **Step 5: コミットする**

```bash
git add .claude/skills/j-devflow/references/spec-review-prompt.md
git commit -m "feat(j-devflow): add a fresh spec review prompt

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014pUomp7Sy3TDqRgP4kxP5d"
```

---

### Task 3: SKILL.md の手順 3・エスカレーション条件・手順 10・ガード・よくある失敗を改訂する

**Files:**
- Modify: `.claude/skills/j-devflow/SKILL.md`（手順 3 は `3. \`superpowers:brainstorming\` → 設計。` で始まる行、エスカレーション条件は `- fix ループが Critical/Important を解消しきれない。` の行、手順 10 は `10. **UAT 自動化 + \`j-finish\`**` で始まる行、ガードは `- **設計ゲート（手順 7 の前）:**` で始まる行、よくある失敗は `## よくある失敗` の節。行番号ではなく文字列で探す）

**Interfaces:**
- Consumes: Task 2 の `references/spec-review-prompt.md`（パス名だけ）。

- [ ] **Step 1: 改訂前の状態を確かめる（RED）**

```bash
grep -c "spec-review-prompt\|未確認の前提\|016-devflow-spec-fresh-review-design" .claude/skills/j-devflow/SKILL.md
```

Expected: `0`

- [ ] **Step 2: `-auto` のエスカレーション条件に1項目を足す**

`- fix ループが Critical/Important を解消しきれない。` の行の**直前**に、次の1行を挿入する。

```markdown
- 設計書の fresh レビュー（手順 3）の後に、「直した」以外に振り分けた Critical/Important、直すと前提や推奨アプローチが変わる指摘、または前提の一覧で「合わない」かつ芯の前提が残っている。「不明」かつ芯の前提はここに入らない — 止めずに手順 10 で PR 本文に運ぶ。
```

- [ ] **Step 3: 手順 3 の「subagent には絶対にしない」を書き分ける**

手順 3 の行の中の `subagent には絶対にしない（これは設計の対話である）。` を、次に置き換える（行のそれ以外はそのまま）。

```markdown
設計の対話そのものは subagent には絶対にしない（これは設計の対話である）。書いた設計書の読み取りレビューは、下のとおり fresh な subagent に出す。
```

- [ ] **Step 4: 手順 3 の直後に、設計書の fresh レビューの項を足す**

手順 3 の行の**直後**（手順 4 の行の前）に、次の1行（インデント3つの箇条書き）を挿入する。

```markdown
   - **設計書の fresh レビュー（GATE 1 の前）:** GATE 1 は brainstorming の checklist 8（書いた設計書を人間が読む）を指す。checklist 7（自己レビュー）の後、checklist 8 の前に、`references/spec-review-prompt.md` の文面で fresh な subagent に設計書を読ませる。渡すのはタスク本文と staging の設計書のパスだけで、会話は渡さない。dispatch は手順 7 の Worktree 固定の契約の (a)(b) に従う。何も書き換えないレビュアーなので、(c) の例外として staging の設計書・タスク本文・設計書が参照する `<WT>` の外のファイルを、読み取り専用の入力として絶対パスで渡してよい。指摘は1件ずつ「直した / 判断を仰ぐ / 採らない（理由）」に振り分ける。Critical/Important を直したら、前回の指摘と振り分けの表を渡して fresh に再レビューする（2回まで。修正したセッションの自己チェックにしない）。直した物が無ければ再レビューは回さない。Minor はブロックしない。attended → 振り分けの表と、前提の一覧の「合わない」「不明」を添えて GATE 1 に出す。推奨アプローチが崩れたら、人間の判断で checklist 5（節ごとの提示）に戻る。GATE 1 で人間が修正を求めたら、修正後にもう一度回す（人間が不要と言えば省く）。`-auto` → **モード**のエスカレーション条件に従う。「不明」かつ芯の前提では止めず、設計書に「未確認の前提」の節を設けて書き残す。根拠（097 の実例、superpowers v5.0.6 が subagent の spec レビューを廃止したこととの関係）は dotfiles の `notes/document/016-devflow-spec-fresh-review-design.md` にある。
```

- [ ] **Step 5: 手順 10 に転記の指定を足す**

手順 10 の行の中の `**機械はここで止まる。**` の**直前**に、次の文を挿入する（前の文の `。` の後に続ける）。

```markdown
`-auto` で設計書に「未確認の前提」の節があれば、PR 本文の冒頭に転記する（設計書のファイルが diff に入るだけでは人間の目に届かない）。
```

- [ ] **Step 6: ガードの「設計ゲート」に1文を足す**

`- **設計ゲート（手順 7 の前）:**` の行の末尾（`概要レベルのタスク本文から承認を捏造することは絶対にしない。` の後）に、次の文を足す。

```markdown
GATE 1 の前に、設計書の fresh レビュー（手順 3）を必ず通す — 書いた本人の自己レビューだけで GATE 1 に出さない。
```

- [ ] **Step 7: よくある失敗に1項目を足す**

`## よくある失敗` の節の最初の箇条（`- 計画が、明示されていない Phase A のコンテキストに依存する` で始まる行）の**直後**に、次の1行を挿入する。

```markdown
- 設計書を、書いた本人の自己レビューだけで GATE 1 に出す — 書いた本人は設計の対話で前提を共有しているので、前提自体の抜けが見えない（実例: fde の tasks/097 は、添付で届く入力を扱えない穴を残したまま自己レビューを通った）。手順 3 の fresh レビューを通す。
```

- [ ] **Step 8: 改訂後の状態を確かめる（GREEN）**

```bash
grep -c "spec-review-prompt" .claude/skills/j-devflow/SKILL.md
grep -c "未確認の前提" .claude/skills/j-devflow/SKILL.md
grep -c "016-devflow-spec-fresh-review-design" .claude/skills/j-devflow/SKILL.md
git diff --stat .claude/skills/j-devflow/SKILL.md
```

Expected: `1`、`2`（手順 3 の項と手順 10）、`1`。diff は SKILL.md の1ファイルだけで、削除行は手順 3・手順 10・設計ゲートの3行（それぞれ置き換え・追記のため）だけ。

```bash
git diff -U0 .claude/skills/j-devflow/SKILL.md | grep "^-[^-]" | wc -l
```

Expected: `3`

- [ ] **Step 9: 通しで読む**

`.claude/skills/j-devflow/SKILL.md` の「モード」の節と「手順書」の Phase A と「ガード」を頭から通して読み、次を確かめる: 手順 3 の新しい項と `-auto` のエスカレーション条件の記述が食い違っていない。GATE 1 を「設計承認」と書いている他の箇所（概要・モード）が、checklist 8 を指すという新しい定義と矛盾していない。食い違いがあれば、その箇所の最小の書き換えで直す。

- [ ] **Step 10: コミットする**

```bash
git add .claude/skills/j-devflow/SKILL.md
git commit -m "feat(j-devflow): run a fresh spec review before GATE 1

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014pUomp7Sy3TDqRgP4kxP5d"
```

---

### Task 4: tasks/017 の背景を直す

**Files:**
- Modify: `tasks/017-devflow-light-by-default.md`（`## 背景` の節の1文）

**Interfaces:**
- Consumes: なし。

- [ ] **Step 1: 改訂前の状態を確かめる（RED）**

```bash
grep -c "設計書と計画に fresh なレビューを入れる" tasks/017-devflow-light-by-default.md
```

Expected: `1`

- [ ] **Step 2: 書き換える**

`tasks/017-devflow-light-by-default.md` の `（Phase A の設計書と計画に fresh なレビューを入れる）` を `（Phase A の設計書に fresh なレビューを入れる）` に置き換える。frontmatter と他の行は触らない。

- [ ] **Step 3: 改訂後の状態を確かめる（GREEN）**

```bash
grep -c "設計書と計画に fresh なレビューを入れる" tasks/017-devflow-light-by-default.md
grep -c "（Phase A の設計書に fresh なレビューを入れる）" tasks/017-devflow-light-by-default.md
```

Expected: `0`、`1`

- [ ] **Step 4: コミットする**

```bash
git add tasks/017-devflow-light-by-default.md
git commit -m "docs(tasks): narrow 016 reference in 017 to the spec review

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_014pUomp7Sy3TDqRgP4kxP5d"
```
