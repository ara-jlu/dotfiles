---
title: j-task の overview-level を実効化する — 設計
tag: [document]
Project: devops
Task: 004-j-task-overview-level
created_at: 2026-09-02
updated_at: 2026-09-02
---

# j-task の overview-level を実効化する — 設計

## 背景と問題

`j-task` は Overview で "Detailed requirements are deferred to each task's brainstorming — this only records title + an overview body." と述べ、Common Mistakes にも "Deep requirements at capture" を挙げている。にもかかわらず起票時に詳細が書き込まれた（2026-09-02、fde `tasks/027` が 7,455 B。同種の `003-j-recap-skill` は 1,447 B）。

原因は二つある。

1. **規定が散文に埋もれていた。** overview-level の指示は Overview 節の一文と Common Mistakes の一行にしか存在せず、「判断の余地のないルール」として立っていない。判断材料が無いので、書き手は他の材料を探す。
2. **既存タスクの粒度に引きずられた。** 参照した既存タスクが詳細に書かれていれば、それが事実上の基準になる。スキルの規定より目の前の実例が強い。

害は分量そのものではない。**タスク本文に分析・引用・トレードオフを書くと、着手側が起票時点の解釈に縛られ、認識齟齬が混入する。** 起票者の読み筋が、要件そのものであるかのように残ってしまう。

## 方針

**スキル規定の強化のみ**で対処する。md2joifup への機械チェックも、Flow への自己検査ステップも入れない。

- 機械チェック: `md2joifup` は全 DB 共通の永続化層であり、tasks 固有の本文ルールを持ち込むのは層の責務を越える。
- 自己検査ステップ: 起票のたびに本文を読み返す手順はトークンを消費する割に、規定が明確なら不要。

規定を独立見出しの塊として立て、「これはルールである」という強度を出すことで、原因 1 に直接当たる。原因 2 には「既存タスクの粒度に合わせない。この規定が優先」を明記して当たる。

### 却下した案

- **Overview に一文足す** — 今回の逸脱がまさにこの形で失敗している。散文一文は規定として認識されない、という実証がある。
- **Flow ステップ 2 に規定を書き足す** — Flow は 1 行 1 ステップの手順書であり、そこに規定 4 種を詰めると手順の可読性が落ちる。

## 変更対象

`.claude/skills/j-task/SKILL.md` の 1 ファイルのみ。既存タスク本文（fde/027 および本リポジトリの 001〜004）の遡及整形は行わない。

既存ファイルが全編英語なので、追記も英語で揃える。タスク本文の節名 `## 概要` / `## 背景` は、本文が日本語であるため日本語のまま扱う。

## 変更内容

### 1. 新設節 `## Body`（Flow と Identifier の間）

```md
## Body

Overview-level only. Detailed requirements belong to the task's brainstorming.

- **Sections:** `## 概要` (required) + `## 背景` (only when "why now" is not
  self-evident). No other sections.
- **Size guideline:** 概要 3-5 lines, 背景 3 lines or fewer, whole file around
  1,500 B. A guideline, not a cap — but when in doubt, cut.
- **Never write:** analysis, research findings, quotes, trade-off comparisons,
  implementation approach, acceptance criteria. All of it belongs to
  brainstorming and the plan.
- **Do not match an existing task's granularity.** A referenced task written in
  detail is not the standard — **this rule wins.**
```

分量は**上限ではなく目安**とする。上限にすると「あと 1 行なら書ける」という運用になり、規定の狙い（詳細を brainstorming に送る）とずれる。目安 ＋「迷ったら削る」で方向だけ決める。

### 2. Flow ステップ 2 を参照に変更

現行:

```md
2. **Generate content:** a Japanese `title` and an **overview-level** body (no deep requirements). Derive an English `--slug`.
```

変更後:

```md
2. **Generate content:** a Japanese `title` and a body per **Body** below. Derive an English `--slug`.
```

規定の実体を `## Body` 一か所に集約し、二重定義を避ける。

### 3. Common Mistakes の 1 行を 2 行に差し替え

現行の `- Deep requirements at capture — keep the body overview-level; detail belongs in brainstorming.` を削り、代わりに:

```md
- Analysis / quotes / trade-offs in the body — the implementer gets bound to the
  filer's reading of the problem, and a misunderstanding rides along.
- Pulled toward a referenced task's granularity — the Body rules win.
```

規定（`## Body`）が *何を* 定めるかを、Common Mistakes が *なぜ悪いか* で補う。害の記述を残すことで、規定を守る動機を与える。

## 検証

dotfiles にテストスイートは無く、この変更は実行可能なコードではないため RED → GREEN は成立しない。検証は変更後の `SKILL.md` の読み合わせで行う。

- Flow ステップ 2 / `## Body` / Common Mistakes の三者に、規定の重複定義も矛盾も無いこと。
- `## Body` の記述だけで、参照無しに本文が書けること（節・分量・禁止事項・優先順位が揃っている）。
- 既存の Overview・Identifier の記述と矛盾しないこと。

## スコープ外

- `md2joifup` の変更。
- 既存タスク本文の遡及整形。
- 同ファイル内の `Branch (later, in j-devflow) = feature/<filename-id>` という古い記述（現行の j-devflow はスラッシュを禁じ `feature-004-slug` を用いる）。齟齬は認識しているが、今回の変更対象外とする。
