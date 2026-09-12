---
name: j-finish
description: 実装とテストが完了した feature ブランチを、人間の承認ゲート手前の状態に仕上げるときに使う — PR を開き、Joifup Task を In review に移し、UAT レビュー依頼を提示し、通知する。マージには使わない。「実装が終わったので終了処理して」「PR を出してレビュー依頼したい」に該当する場合。
---

# j-finish

## 概要

superpowers の背骨と外部世界の間の出力アダプタ。**承認前の終了処理を一気通貫で**実行し、人間の承認ゲートで停止する。計算（superpowers）は無改変である。その結果を PR・Joifup のステータス遷移・UAT レビュー依頼・通知に変換する。

**分担:** *判断*（diff から日本語の PR 本文を書くこと）は自分の役割である。*機構*（外科的な status 編集、relation-id の形式、PR→通知の順序）はスクリプトの役割である — 手作業でやると壊れるのはまさにそこだから。

**承認コミットの主体は人間である。** j-finish は Done を絶対に設定しないし、絶対にマージしない。レビュー後、人間のセッションが status → Done に変更し、`chore(joifup): approve <task-id>`（英語）をコミットして、マージする。

## 使う場面

- 実装とレビューが完了し、ブランチを人間に渡せる状態になったとき。
- マージ・Done への変更・ノート生成には使わない（それは `md2joifup` の役割）。

## 手順

1. **Pre-flight**（読み取りのみ）: `git status --porcelain`（clean か？dirty なら停止して報告する）、`git log origin/main..HEAD`、`git diff --stat origin/main...HEAD`。
2. **日本語の PR 本文を書く** — `j-pr` スキルの `references/pr-body.md` にある共通レシピに従い、ファイルに出力する（両経路が同じ規約を使う）。
3. **スクリプトを実行する**（push → PR 作成 → 証跡コメント → status→In review → Discord の順に行う）:

```bash
python3 scripts/j_finish.py --task-file <tasks/NNN-*.md> \
  --pr-title "<ja title>" --pr-body-file <body.md> \
  [--uat-evidence-dir .uat-evidence/<id>] \
  [--head <branch>] [--status "In review"] [--dry-run]
```

`--no-pr` / `--no-discord` で各部分を無効にできる。`--dry-run` はローカルのファイル編集は実行しつつ、実行するはずの git/gh/curl を出力する。

4. **UAT 証跡を PR に載せる。** 承認者はコードを読まず、証跡を見て承認する。UI 変更を含む場合は `pnpm uat --task <id>` を回し、**`--uat-evidence-dir .uat-evidence/<id>` を渡す**。**証跡は commit しない** — 画像・動画は `gh pr comment --attach` で PR に添付され（joifup tasks/295 以降。`.uat-evidence/` は gitignore 済み）、PR 本文の `## UAT 証跡` には `summary.md` の PASS/FAIL 表（テキスト）と証跡コメントへのリンクだけが載る。受け入れ基準は `## 受け入れ基準` に inline 展開する。**UAT ユーザーアクション task は新規 file しない**（旧 light/heavy 分岐・md2joifup --db tasks による UAT task 発行は廃止）。UI を含まない変更では UAT を省略してよい。
5. PR の URL を**報告**して引き渡す。UAT を実行した後、承認待ちであることをユーザーに伝える。

## スクリプトが保証すること

- **外科的な status 編集** — 変わるのは `status:` 行だけ（tasks のスキーマに対して検証される）。それ以外の frontmatter のキー・リレーション・本文のバイトはすべて保持される。`Done`/`Cancelled` は拒否する。
- **範囲を絞った Discord** — 「👀 レビュー依頼」というタイトルの日本語 rich embed（`auto-workflow/scripts/discord-notify.sh` と同じ形: description + color + プロジェクト/ブランチ fields + timestamp）に PR リンクを載せ、`allowed_mentions` は owner のみに限定する。`CLAUDE_SESSION_ID` は絶対に投稿しない。`DISCORD_COLOR` で上書きできる。
- **UAT 証跡の添付** — `--uat-evidence-dir` を指定すると、PR 作成直後に証跡コメント（`gh pr comment --attach`、alt text は各ショットの `name`）を投稿し、本文の `## UAT 証跡` からリンクする。`gh >= 2.99.0` を要求し、それ未満では明示的に停止する。証跡が一部欠けたアップロードは、黙って証跡不足の PASS を出すのではなく、終了処理自体を失敗させる。
- **UAT 証跡チェック** — `apps/web/` に変更があるのにローカルで `pnpm uat` を回していない場合、または `.uat-evidence/` が commit されている場合（commit してはならない）、警告する（絶対にブロックしない）。読み取りのみなので `--dry-run` 下でも実行される。

## よくある失敗

- タスクファイル全体（title・relations・本文）を書き直す — 動くのは status だけ。経緯はログノートに属する。
- relation の値をファイルパスとして書く — それらは**id**である（例: `042-...`、`638-...`）。
- Done に設定する、あるいはマージする — それは人間の承認ゲートの役割であり、j-finish の役割ではない。
- コミット言語: 承認コミットは**英語**、PR 本文は**日本語**。
- UI 変更なのに `pnpm uat` を回さず PR を出す — 証跡が空になる。逆に `.uat-evidence/` を **commit** するのも誤り（gitignore 対象。PR には添付する）。
- UAT ユーザーアクション task を新規 file する — 廃止済み。受け入れ基準は PR の `## 受け入れ基準` に inline する。
