---
ID: NOTE-79
Project: devops
Task: '002-jfinish-uat-review'
created_at: '2026-07-14'
tag:
- document
title: j-finish のレビュー依頼を UAT 手順提示型に改善 — 設計
updated_at: '2026-07-14'
---

# j-finish のレビュー依頼を UAT 手順提示型に改善 — 設計

## 目的

j-devflow の出口（j-finish）でのレビュー依頼を、現状のエンジニア向けコードレビュー前提から、**UAT（受け入れテスト）的な検証手順の提示**へと改める。承認ゲートに立つ人間は「コードを読む人」ではなく「動かして確かめる人」である、という前提に寄せる。

## 現状（改善前）

`j_finish.py` の `main()` は finish 時に固定順で5ステップを実行する:

| # | ステップ | 成果物 | 抑制フラグ |
|---|---|---|---|
| 1 | `git push -u origin <head>` | ブランチ push | — |
| 2 | `gh pr create` | PR（日本語本文） | `--no-pr` |
| 3 | `surgical_status` | Task status → In review | — |
| 4 | `file_user_action` | **`承認待ち: <title>` タスク1枚** | `--no-user-action` |
| 5 | curl → Discord | embed「👀 レビュー依頼」 | `--no-discord` |

問題点:

- **step 4** が「承認だけを管理する」Joifup タスク（`tasks/NNN-approve-*.md`、本文「レビュー承認をお願いします」）を常に自動起票する。実運用ではこの承認専用タスクは不要と判断された。
- レビュー依頼の成果物（Discord embed・承認待ちタスク）が**コードレビュー前提**で、人間が実際に行う受け入れ検証の手順も、検証を始めるための準備も示していない。

## 改善後の設計

### 決定事項

1. **承認専用タスクの廃止** — `j_finish.py` から step 4（`file_user_action`）と `--no-user-action` フラグを削除する。j-finish はもう承認専用タスクを起票しない。

2. **分業は不変** — UAT の中身の判断（何を・どう動かして確かめるか、手順の軽重）は PR 本文と同じく**実装直後のセッションの責務**。`j_finish.py` はメカニクス（push / PR / status / Discord）専任のまま。

3. **検証準備は「設定なし・セッションが都度実施」** — 「ユーザーが検証を始められる準備を済ませておく」（デーモン再起動・dev server 起動など）は、プロジェクト・変更ごとに異なる内容判断であり、実装直後のセッションが最も文脈を持つ。専用スキーマや projects 本文パースといった新しい永続・設定面は設けない（YAGNI、かつ Joifup 所有スキーマに触れない）。

### 軽い／重いの分岐

UAT レビュー依頼は手順の重さで出し分ける。判断と実行はセッションが行い、スキルの手順記述がそれを規定する。

| | 軽い場合 | 重い場合（検証ケースが多い等） |
|---|---|---|
| UAT 手順 | セッションのテキストで提示 | **検証タスクを起票してファイル提示** |
| 検証準備 | セッションが実施（デーモン再起動・起動等） | 同左＋タスク本文に前提として記載 |
| Joifup タスク | 起票しない | 起票する（UAT ケースを本文に持つ user-action タスク） |

重い場合の検証タスクは、**`j_finish.py` ではなく既存の `md2joifup --db tasks` で起票**する（内容＝セッション著述）。これにより「メカニクス＝スクリプト／内容＝セッション」の分業が崩れず、`j_finish.py` からタスク生成ロジックを完全に除去できる。

「軽い／重い」の閾値は機械的な数値ではなくセッションの判断とする。目安として、検証が「準備＋数手順で口頭提示でき、承認者がその場で追える」なら軽い。検証ケースが多い・順序依存が強い・複数環境にまたがる・後から参照したくなる規模なら重い。

### Discord 通知

embed「👀 レビュー依頼」は据え置き（PR リンク付き）。文面「実装が完了しました。レビューをお願いいたします」は UAT でもそのまま通るため変更しない。承認専用タスク廃止に伴う Discord 側の変更はない（Discord は元々タスクを参照していない）。

## 影響範囲（変更対象ユニット）

境界の明確な3ユニットに閉じる:

1. **`.claude/skills/j-finish/scripts/j_finish.py`**
   - `main()` の step 4 呼び出しブロックを削除。
   - `file_user_action()` 関数を削除。
   - `--no-user-action` 引数を削除。
   - `file_user_action` 専用ヘルパを削除する。コード確認済みで、以下は `file_user_action` からのみ参照され他ステップでは未使用のため安全に除去できる: `slugify` / `next_number` / `emit_frontmatter` / `fmt_scalar` / `_QUOTE_START`。
   - `import datetime` / `import json` は Discord step（timestamp・payload）で使うため**残す**。
   - 末尾の `HANDOFF:` メッセージ（承認→Done→マージ）は人間ゲートの案内として維持。

2. **`.claude/skills/j-finish/SKILL.md`**
   - "Approval task — a child `承認待ち` Task…" の記述（Steps / What the script guarantees / Common Mistakes）を削除。
   - UAT レビュー依頼の分岐（軽＝セッションテキスト＋検証準備／重＝`md2joifup --db tasks` で検証タスク起票してファイル提示）を追記。
   - 「レビュー＝コードレビュー」ニュアンスを UAT（受け入れ検証）ニュアンスへ改める。

3. **`.claude/skills/j-devflow/SKILL.md`**
   - Phase B step 10 の j-finish 説明から「承認待ち task」を除去。
   - UAT レビュー依頼の分岐と検証準備をセッションが行う旨を反映。

## スコープ外

- 具体的な検証準備コマンド・検証ケースの中身（プロジェクト依存。セッションが都度判断）。
- Discord 文面・色・fields の変更。
- Joifup スキーマ（tasks/notes）の変更（Joifup 所有。触れない）。
- `md2joifup.py` の変更（既存の `--db tasks` をそのまま使う）。

## テスト方針

このリポジトリは skills/docs 主体で標準テストスイートを持たない。検証は以下で行う:

- `j_finish.py` は `--dry-run` を持つ。step 4 削除後、`--dry-run` で push/PR/status/Discord の4系統のみが出力され、承認待ちタスクが生成されないこと（`tasks/` に新規 approve ファイルが増えないこと）を確認する。
- `python3 -c "import ast; ast.parse(open('...').read())"` 相当で構文健全性を確認、または `python3 j_finish.py --help` が正常終了することを確認する。
- SKILL.md 2件は記述の整合（承認待ち記述の消滅・UAT 分岐の追加）を目視レビューで確認する。
