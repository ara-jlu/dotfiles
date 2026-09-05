---
title: UAT 証跡の PR 添付化に skill 側を合わせる (005) — 設計
tag: [document]
Project: devops
Task: 005-align-skills-with-pr-attached-uat-evidence
created_at: 2026-09-05
updated_at: 2026-09-05
---

# UAT 証跡の PR 添付化に skill 側を合わせる (005) — 設計

## 背景

joifup の tasks/295（PR #206, マージ済み）で UAT 証跡の扱いが変わった。

- `.uat-evidence/` は **gitignore され、commit しない**。
- 証跡（画像・動画）は **`gh pr comment --attach` で PR に添付**する。
- repo に残る資産は `apps/web/e2e/*.uat.spec.ts` の assertion と、PR 本文に転記される
  PASS/FAIL 表のテキスト。

295 の設計書は、この配線が **dotfiles 側の別 PR（Part B）** であることを明記している
（`notes/document/295-uat-e2e-split-evidence-to-pr-attachments.md` D5 / D10）。本設計が
その Part B である。

skill は全プロジェクト共通なので、旧運用の記述を残すと joifup 以外でも次の feature
セッションが間違った手順を踏む。joifup 側だけ直った状態は、joifup CLAUDE.md が禁じる
「運用が二重になる状態」そのもの。

## 着手時の実測（2026-09-05）

「使えるはず」で配線しない（295 が置いた規律、出典は joifup tasks/283）。

### `gh --attach` の下限バージョン

`cli/cli` の release を全件走査して特定した。

- **`--attach` の初出は v2.99.0（2026-09-01）。** `gh pr create` / `gh pr edit` /
  `gh pr comment` / `gh issue *` に同時に入った。50 ファイル/コマンドの上限も同 release。
- v2.100.0 は telemetry の追加のみ。手元は 2.100.0。
- **したがって下限は `2.99.0`。**
- release note の明記: 添付は **GitHub.com と GitHub Enterprise Cloud でのみ利用可能**
  （GHES は不可）。

### 形式（`gh pr comment --help` 実測）

- `--attach '<file>#<alt text>'`。`#` 以降を省くとファイル名が alt になる。
- body が `![alt](./login.png)` でローカルパスを参照していれば、**そのアドレスが
  アップロード先 URL に書き換わる**（＝コメント本文にインライン表示できる）。
- **body が参照しなかった添付は body の末尾に追記される。**
- 1 コマンドあたり最大 50 ファイル。

### 証跡ファイルの実体（joifup 側の実装）

`.uat-evidence/<task>/results.jsonl` に 1 行 1 JSON で落ちる。

| 行 | 形 | 意味 |
| --- | --- | --- |
| 判定行 | `{n, name, status}` | `step()` の PASS/FAIL |
| 証跡行 | `{n, name, file, kind:"shot"}` | `shot()` の PNG、または回収した `.webm` |

`file` は **evidence dir 内の basename**（`shot-01-....png` / `clip-01-....webm`）で、
パスを含まない。日本語の説明は `slug()` が非 ASCII を落とすためファイル名には乗らず、
`name` にしか無い。**これが alt text を必須にしている理由**（295 D5 の契約）。

## 直す対象（棚卸し）

| # | 場所 | 現状の誤り |
| --- | --- | --- |
| 1 | `j-devflow/SKILL.md` step 10 | 「`.uat-evidence/<id>/` に生成し commit する」 |
| 2 | `j-finish/SKILL.md` step 4 | 「commit し、screenshot は Files changed タブで閲覧」 |
| 3 | `j-finish/SKILL.md` What the script guarantees | 「未 commit なら警告」 |
| 4 | `j-finish/SKILL.md` Common Mistakes | 「commit せず PR を出すと証跡が空」 |
| 5 | `j_finish.py` `_warn_missing_uat_evidence` | 警告条件が反転（今は commit しないのが正） |
| 6 | `j-pr/references/pr-body.md` `## UAT 証跡` 節 | 「Files changed タブで確認する旨を明記」 |
| 7 | `j-pr/references/pr-body.md` ルール | 同上 |

加えて **添付を実行する配線そのものが未実装**（証跡コメントの投稿、`gh` のバージョン確認）。

## 検討した案

| 案 | 内容 | 判定 |
| --- | --- | --- |
| A | 添付を独立スクリプト `j-finish/scripts/uat_attach.py` に置き、`j_finish.py` が呼び、`j-pr` も同じものを叩く | **採用** |
| B | `j_finish.py` に内蔵する | 却下。`j-pr`（ad-hoc 経路）から使えず、契約が二重化する |
| C | 配線を作らず skill の文章で `gh pr comment --attach` を手打ちさせる | 却下。task の「配線も未実装」をそのまま残す。alt text 契約・50 件上限・バージョン下限が誰にも守られない |

A を採る理由は、守るべき契約（alt text = shot の `name` / 50 件上限 / `gh >= 2.99.0` /
部分失敗を握り潰さない）が **1 箇所に集まる**こと。`j-pr` と `j-finish` が同じ recipe を
共有する既存の構造（`references/pr-body.md`）と同じ形になる。

## 設計

### D1. `j-finish/scripts/uat_attach.py`（新規）

自己完結した CLI であり、かつ `j_finish.py` から import できる純粋関数を持つ。

```bash
python3 uat_attach.py --evidence-dir .uat-evidence/<id> --pr <url|number> [--dry-run]
```

処理順:

1. **`gh` のバージョン確認。** `gh --version` を parse し、`2.99.0` 未満なら
   **明示エラーで停止**する（黙って失敗させない — 295 のエラーハンドリング節）。
2. `results.jsonl` を読み、`kind:"shot"` 行を取り出す。**markdown の `summary.md` は
   parse しない**（`name` に `|` が入ると表がずれる。JSONL のほうが権威）。壊れた行は
   joifup の `parseResults` と同じ扱いで落とし、落とした本数を stderr に出す。
3. 証跡が 0 件なら **何もせず正常終了**（UI を変えない PR は証跡が無いのが正常）。
4. **50 件を超えていたら停止**（`gh` の上限。超過は分割ではなく `shot()` を減らす問題）。
5. コメント本文を組み立て、`gh pr comment <pr> --body-file <tmp> --attach ...` を実行。
6. コメント URL を stdout に返し、PR 本文の `## UAT 証跡` 節に
   `証跡コメント: <url>` の 1 行を追記する（`gh pr edit --body-file`）。

### D2. コメント本文の組み立て

- **画像は `![<name>](./<file>)` で本文から参照する** → gh が URL に書き換え、
  説明付きでインライン表示される。
- **動画は本文から参照しない** → gh が末尾に裸 URL として追記し、GitHub が
  プレイヤー化する（295 の実測）。`![]()` で参照すると画像として扱われ再生できない。
  代わりに「動画（以下に添付）: `<name>`」の行を本文に置き、対応を人が辿れるようにする。
- `--attach` には **必ず `#<name>` を付ける**（295 D5 の契約）。ファイル名は ASCII slug で
  日本語の説明を運べないため、alt を省くと区別のつかないファイル名が並ぶ。

### D3. PR 本文の `## UAT 証跡`

**判定（テキスト）は本文、画素はコメント**（295 D5 の軸をそのまま踏襲）。

- 本文には `summary.md` の **PASS/FAIL 表と `結果:` 行のみ**を転記する。**画像は入れない**
  （画像を本文に入れると `## レビュー観点` `## 関連` が画面の遥か下に押し出され、
  diff を見る前に読むべきものが読めなくなる）。
- 末尾に `証跡コメント: <url>`（D1 の 6 が追記する）。

**295 D5 からの逸脱を 1 点記録する。** 設計書は「本文の `## 証跡` 表の各行を、その
コメントの**アンカー**へリンクする」としているが、**GitHub はコメント内の行に個別の
アンカーを与えない**（アンカーはコメント単位）。行ごとのリンクは実現不能なので、
**コメント単位の 1 リンク**にする。これは表現の縮退であって、契約（PR 単体で証跡に
到達できる）は満たす。

### D4. `_warn_missing_uat_evidence` の反転修正

撤去ではなく **反転**させる。旧チェックの*意図*（UI を変えたなら証跡が要る）は今も
正しく、壊れているのは*機構*（diff に commit されているかを見ていた）だけだから。
撤去すると「`pnpm uat` を回し忘れたまま PR が出る」を誰も止めなくなる。

`_warn_uat_evidence(head_range, evidence_dir)` に改名し、2 つを警告する（どちらも
ブロックしない）:

1. `apps/web/`（`apps/web/e2e/` を除く）が変わっているのに `<evidence-dir>/results.jsonl`
   が**手元に無い** → `pnpm uat --task <id>` を回していない。
2. push 範囲の diff に `.uat-evidence/` の**パスが含まれている** → commit してはいけない
   ものを commit している（新しい失敗様式。gitignore が無い repo で起きうる）。

### D5. `j_finish.py` の実行順

295 D5 の指定どおり **`push → PR 作成 → 証跡コメント → status → Discord`**。
証跡コメントは `--no-pr` のときと `--dry-run` のときはスキップ／print に落とす。
新フラグ `--uat-evidence-dir <path>`（省略時は添付を行わない）。

### D6. skill 本文の書き換え（7 箇所）

棚卸し表のとおり。全プロジェクト共通の原則として書く:

> UAT 証跡は commit しない。`gh pr comment --attach` で PR に添付する。
> PR 本文には PASS/FAIL 表（テキスト）と証跡コメントへのリンクだけを置く。

`j-pr` は Joifup の副作用を持たない経路なので、`uat_attach.py` を**直接叩く**手順を
書く（`j-finish` を呼ばない）。

## エラーハンドリング

- **`gh` が古い（< 2.99.0）** — 明示エラーで停止。無言で失敗させない。
- **部分失敗** — `gh` は成功したぶんでコメントを作り非 0 で終了する。終了コードを
  握り潰さず、stderr をそのまま出して停止する。証跡が欠けたまま「PASS」と見える状態を作らない。
- **50 件超過** — 事前に検出して停止。分割しない（`shot()` を減らすべき問題）。
- **証跡 0 件** — 正常終了（UI を変えない PR）。
- **`results.jsonl` の壊れた行** — 落として続行し、落とした本数を stderr に出す
  （joifup `parseResults` と同じ扱い）。

## テスト戦略

dotfiles には test runner が無い。**stdlib の `unittest` だけ**で走る
`j-finish/scripts/test_uat_attach.py` を新設する（`python3 scripts/test_uat_attach.py`）。
副作用を注入し、純粋部分を固定する:

- バージョン比較（`2.98.0` < `2.99.0` <= `2.100.0`、`gh version 2.100.0 (…)` の parse）
- `results.jsonl` の parse（証跡行の抽出、壊れた行のスキップ）
- コメント本文の生成（画像はインライン参照、動画は非参照、alt text が `name`）
- `--attach` 引数の組み立て（`<path>#<name>`）
- 50 件上限
- `_warn_uat_evidence` の 2 条件

`j_finish.py` は `--dry-run` で実行順とコマンド列を目視確認する。

## 非スコープ

- **joifup 側の変更** — 295 で着地済み。
- **`.uat-evidence/` の履歴書き換え** — joifup の launch 後（295 非スコープ）。
- **skill の joifup 依存語（`apps/web/` / `pnpm uat`）の一般化** — 今回の誤りとは別軸。
  既存の形を保つ。
- **`gh issue` 側の添付** — 使っていない。

## 関連

- Task: `005-align-skills-with-pr-attached-uat-evidence`
- joifup `notes/document/295-uat-e2e-split-evidence-to-pr-attachments.md`（本設計の出典。D5 / D10 が Part B を指定）
- joifup `CLAUDE.md` §「UAT 証跡は commit しない（tasks/295 以降）」
