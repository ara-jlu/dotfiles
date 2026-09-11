---
title: 自作スキルの記述言語を日本語に統一する — 設計
tag: [document]
Project: devops
Task: 009-unify-skill-language-ja
created_at: 2026-09-12
updated_at: 2026-09-12
---

# 自作スキルの記述言語を日本語に統一する — 設計

## 概要

現役の自作スキル 9 個の SKILL.md を日本語に統一する。散文・見出し・`description`・`argument-hint` を日本語にし、**節構成・順序・項目数は一切変えない**。訳すだけで、言い回しの改善や節の統廃合は本タスクでは行わない。あわせて `.claude/CLAUDE.md` § 言語 に記述言語の規約を置き、再発を防ぐ。

訳と内容改善を同じ pass で混ぜないのは、**全行が変わる差分の上に内容変更を重ねるとレビューで「訳の誤り」と「意図した変更」が区別できなくなる**ため。とくに `j-devflow` は 16 KB の密なルール集で、ここで混ぜるのが最も危険である。内容を削って短くする作業（調査 006 が支持する方向）は別タスクに切る。

## 現状

| 系統 | 記述言語 |
|---|---|
| `j-*` 7 個（j-recap 除く）+ `md2joifup` | ほぼ英語（日本語は出力文例・固有名詞のみ） |
| `j-recap` | 日本語。ただし `## Overview` / `## Flow` / `## Common Mistakes` は英語のまま混在 |
| 旧 Notion 系 9 個 | ほぼ日本語 |
| `j-pr/references/pr-body.md` | 全文日本語 |

新しく作った `j-*` が英語、古いものが日本語という分かれ方である。`j-recap` だけが例外的に日本語で、frontmatter と本文の作りが本タスクの目標形にほぼ一致している。

行数と日本語を含む行数の実測（`SKILL.md`）:

| スキル | 行数 | 日本語を含む行 | サイズ |
|---|---|---|---|
| j-devflow | 110 | 1 | 16,163 B |
| j-recap | 73 | 45 | 7,396 B |
| j-finish | 53 | 6 | 4,909 B |
| md2joifup | 54 | 0 | 3,850 B |
| j-task | 50 | 2 | 3,525 B |
| j-log | 50 | 2 | 2,704 B |
| j-research | 49 | 5 | 2,636 B |
| j-doc | 52 | 4 | 2,491 B |
| j-pr | 36 | 3 | 2,468 B |

## 対象と除外

**対象 — 9 ファイル。** `.claude/skills/{j-devflow,j-doc,j-finish,j-log,j-pr,j-recap,j-research,j-task,md2joifup}/SKILL.md`

**除外:**

- **スクリプトの docstring・コメント**（`md2joifup.py` / `j_finish.py` / `uat_attach.py` とそのテスト）。ここも混在している（`j_finish.py` は日本語、`md2joifup.py` は英語）が、コードコメントは `tasks/007`（一次情報の二重化をやめる）が対象ブロックをどのみち書き換える。先に訳すと 007 で削除する行を触って二重になる。**007 へ申し送る**（下記「申し送り」参照）。
- `j-pr/references/pr-body.md` — 全文すでに日本語。変更なし。
- 旧 Notion 系 9 スキル（`branch` / `doc-note` / `log-note` / `research-note` / `plan2notion` / `setup-project` / `implementation` / `auto-workflow` / `test`）。範囲外と決定済み。
- `.agents/skills/find-skills`（他者製）、superpowers / ECC のスキル（無改変で使う方針）。

## 日本語にするもの / 英語で残すもの

**日本語にする:** 散文、`##` および `###` 見出し、frontmatter の `description`、frontmatter の `argument-hint` の値。

**英語のまま残す:**

- `name`（識別子）、frontmatter のキー名
- コマンド・パス・フラグ・環境変数（`python3 scripts/j_finish.py --task-file …`、`.uat-evidence/<id>`、`DISCORD_COLOR`）
- 他スキル名と `agentType`（`superpowers:brainstorming`、`ecc:docs-lookup`）
- Joifup の status 値（`Not started` / `In progress` / `In review` / `Done` / `Cancelled`）とタグ名（`plan` / `document` / `log` / `research` / `memo`）
- コミットメッセージ例（`chore(joifup): approve <task-id>`）— コミットは英語という規約に従う
- コードフェンスの中身（出力例・コマンド例）
- 技術識別子（`frontmatter` / `diff` / `worktree` / `subagent` 等、原語のまま使われている語）

### `description` の型

`description` はスキル起動の判定に使われ、superpowers・ECC の全スキルは英語である。日本語化しても判定は LLM が行うので機能するが、**起動率の変化は実測できない**。そこで `j-recap` の現状を実績のある形として踏襲する:

- 日本語の文で「〜するときに使う」と書く
- ユーザーが実際に打つ**日本語の起動語**を含める（例: 「作業まとめ」「振り返り」）
- 固有語は英語のまま（`Joifup` / `PR` / `UAT` / `Discord` / `superpowers`）

`argument-hint` も日本語にする（例: `[task-id (optional)]` → `[task-id（任意）]`）。`j-recap` は既に `[期間 (省略時=今日)]` である。

## 見出しの語彙表

各ファイルで訳を発明させないために、全スキル共通の写像を固定する。

| 英語 | 日本語 |
|---|---|
| Overview | 概要 |
| When to Use | 使う場面 |
| Flow | 流れ |
| Steps | 手順 |
| Usage | 使い方 |
| Runbook | 手順書 |
| Modes: two independent axes | モード — 独立した二軸 |
| Guards (all mode combinations) | ガード（全モード共通） |
| What it does | 何をするか |
| What the script guarantees | スクリプトが保証すること |
| ECC knowledge | ECC の活用 |
| Document content spec | ドキュメントの内容規定 |
| Log content spec | ログの内容規定 |
| Research content spec | 調査ノートの内容規定 |
| Body | 本文 |
| Identifier | 識別子 |
| Common Mistakes | よくある失敗 |

`j-devflow` の `###` 小見出し 2 つ（GATE 1 と Phase B のモード対比）は、モード名・フラグ名（`attended` / `-auto` / `full` / `-light` / `GATE 1` / `Phase B`）が識別子なので英語のまま残し、`(default)` のみ `（既定）` にする。

`j-recap` の `## 出力フォーマット` / `## 出力例` は既に日本語なので変更しない。出力例のコードフェンス内の `## 2026-07-26 の作業` / `### joifup` は出力の見本であり、見出しではない — 触らない。

## 文体の規定

- 規定文は「〜する」「〜してはならない」で書く。丁寧語にしない。
- 原文の `**…**` 強調は意味の強調なので保持する。`never` / `MUST` / `ABSOLUTELY` は否定形と強調を保って訳す（`**never** set Done` → `**絶対に** Done にしない`）。**訳で規定の強さを落とさない。**
- 主語の `you` は落とす（日本語の規定文として自然な形にする）。
- **ハード折り返しをしない**（`tasks/008` の原則）。桁数で改行を入れず、1 段落 1 行で書く。
- 補足の `—` は既存の日本語ノート・`j-recap` の文体に合わせて使ってよい。読みにくくなる箇所では文を割る。

## 構造不変の検査

全行が変わる差分なので「訳しただけ」は目視では検査できない。旧版（`git show <base>:<file>`）と新版を比べる 6 つの不変条件を置き、機械で確認する。

1. `##` / `###` 見出しの**個数と順序**が一致し、語彙表の写像どおりであること
2. 節ごとの箇条書きの**項目数**が一致すること（ネストした階層も含め、行頭マーカー `- ` / `1. ` で始まる行の数を節単位で数える）
3. **コードフェンスの中身がバイト一致**すること
4. frontmatter の**キー集合**が一致すること（値が変わるのは `description` と `argument-hint` のみ）
5. インラインコード `` `…` `` の**多重集合**が一致すること（語順の入れ替えは許す）
6. `**…**` 強調の**個数**が一致すること

検査スクリプトは **scratchpad の使い捨て**とし、コミットしない。統一後に再利用する場面が無く、リポジトリに資産を増やす理由がない（CLAUDE.md の実装前チェック①②）。検査の出力は PR 本文に載せて証跡とする。

不変条件が落ちた場合、**訳を直して条件を満たす**のが原則である。条件そのものを緩めるのは、原文側に明白な不備（例: 箇条書きの重複）があり、それを直すことが訳と独立に正しいと言える場合に限る。その場合は理由をコミットメッセージに書く。

## 規約の追記

`.claude/CLAUDE.md` § 言語 に、自作スキルの記述言語を明記する。

起票時に未決だった論点 —「SKILL.md は『機械が扱う面』か『人が読む面』か」— に答えを出す必要がある。字面どおりなら SKILL.md は Claude が読むので機械側だが、これを「人が読む面」に押し込むと原則が歪む。**第三の面として書く**: SKILL.md は機械が実行し**人が保守する**面であり、保守する側の言語に合わせる。

追記の内容:

- 自作スキル（`.claude/skills/j-*` と `md2joifup`）の SKILL.md は**本文・見出し・`description` を日本語**で書く。
- ただし `name`、コマンド・パス・フラグ、他スキル名・`agentType`、status 値・タグ名、コミットメッセージ例、コードフェンスの中身は英語のまま。
- 理由は一言添える（機械が実行し人が保守する面なので、保守する側の言語に合わせる）。

既存の「原則: 機械が扱う面 = 英語、人が読む面 = 日本語」は残し、そこへの例外・補足として置く。

## 分割と順序

1 スキル 1 コミット。訳の差分は全行なので、分けるとレビューが成立する。

1. `j-task` — 50 行・自己完結。ここで**文体を確定**する。以降のスキルはこの訳に合わせる。
2. `j-pr`（36 行）→ `j-doc`（52）→ `j-research`（49）→ `j-log`（50）→ `md2joifup`（54）→ `j-finish`（53）
3. `j-recap` — 見出しと `description` のみ（本文は既に日本語）
4. `j-devflow` — 110 行・16 KB。最も密なルール集なので、語彙と文体が固まった**最後**に行う。
5. `.claude/CLAUDE.md` の規約追記 — 独立したコミット。

## 受け入れ基準

1. 9 ファイルの散文・`##`/`###` 見出し・`description`・`argument-hint` が日本語であり、見出しは語彙表の写像どおりであること。
2. 不変条件 1〜6 が 9 ファイル全部で pass すること（検査出力を PR 本文に載せる）。
3. `.claude/CLAUDE.md` § 言語 に規約が追記されていること。
4. 既存テスト 65 件（`test_j_finish.py` 14 件 + `test_uat_attach.py` 51 件）が green のままであること。
5. **マージ後**に `j-recap` を 1 回起動し、正しくトリガーして手順どおり動くこと。

### 基準 5 の制約

`~/.claude/skills` は**主チェックアウトへの symlink**（`/Users/ara/.claude/skills -> /Users/ara/Joifup/dotfiles/.claude/skills`）である。worktree の SKILL.md は Claude Code から見えないため、**このブランチの日本語版スキルはマージされるまで実際には起動されない**。したがって:

- マージ前にできる検証は、不変条件の検査と読み合わせまでである。
- 実機確認は Phase C（マージ後）に行う。副作用の無い `j-recap` を選ぶ（`j-finish` / `j-pr` は PR・Discord の副作用があるため実機確認に使わない）。
- UI の変更は無く、このリポジトリに `pnpm` も無いので UAT 証跡の生成（`pnpm uat`）は行わない。PR 本文は `## テスト` のみとする。

## 申し送り

`tasks/007`（一次情報の二重化をやめる）へ: **スクリプトの docstring・コメントも言語が混在している。** `j_finish.py` / `uat_attach.py` は日本語、`md2joifup.py` は英語。007 がコメントブロックを書き換えるときに、言語もそろえること。009 はスクリプトを触っていない。
