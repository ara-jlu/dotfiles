# Joifup PR 本文規約（単一の真実）

`j-pr`（ad-hoc）と `j-finish`（フロー）の両方がこの規約に従って PR を生成する。ここを変えれば両経路が揃う。

## 言語

- **PR タイトル・本文 = 日本語**。**コミットメッセージ = 英語**（独立。CLAUDE.md § Git）。
- 本文は **diff から生成**する（憶測でなく実変更を書く）。

## タイトル

```
<type>: <日本語の要約>[（TASK-xxx）]
```

- `<type>` は Semantic Commit のタイプ（feat/fix/docs/refactor/chore/test/style）。
- Joifup Task があれば末尾に `（TASK-xxx）` を付す。

## 本文（この順・positive recipe）

```markdown
## 概要
[変更の目的と背景を簡潔に。Joifup Task / 実装計画があれば併記]

## 変更内容
- [変更点]
- [変更点]

## テスト
- [実行したテストと結果（グリーン等）。未実行ならその旨]

## レビュー観点
- [diff の焦点。特に auth / 入力 / 秘密 / API / 機微データに触れる箇所は明記]

## 関連
- Task: [Joifup Task id（あれば）]
- Plan: [notes/plan/… パス（あれば）]

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## ルール

- **関連リンクは Joifup**（Task id / plan ノートのパス）。Notion URL は使わない。
- `## レビュー観点` は diff の実面から起こす（テンプレ文でなく変更に即して）。
- 該当セクションが空なら省いてよい（`## テスト` を除く。テストは必ず状態を書く）。
- フッタ `🤖 Generated with [Claude Code](https://claude.com/claude-code)` は必須。

## 例

```markdown
## 概要
ユーザーがプロフィール画像（アバター）をアップロードできる機能を実装。
Joifup Task: TASK-638 / 実装計画: notes/plan/042-avatar-upload.md

## 変更内容
- アップロード UI とエンドポイントを追加
- 画像バリデーション（形式・サイズ）を実装

## テスト
- 追加した自動テストはすべてグリーン

## レビュー観点
- ファイル入力のバリデーション（形式・サイズ・拡張子）が十分か
- 保存パス・ファイル名に外部入力が安全に扱われているか

## 関連
- Task: 042-avatar-upload
- Plan: notes/plan/042-avatar-upload.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```
