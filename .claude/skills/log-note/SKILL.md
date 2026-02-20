---
description: 本セッションの作業ログを時系列でNotionのNotes DBに記録する。セッション終了時や作業の区切りで使用。
user-invocable: true
argument-hint: "[task-url (optional)]"
---

## フロー

### 1. 引数判定

引数 `$ARGUMENTS` を判定：

**Task URLあり:**
1. `mcp__notion__notion-fetch` でTaskページを取得
2. Taskのタイトル・Projectプロパティを取得
3. → ステップ2へ

**引数なし:**
1. 会話コンテキストから作業内容を要約し、タスクタイトルを生成
2. `mcp__notion__notion-create-pages` で新規Taskを作成：
   - data source: `$NOTION_TASK_COLLECTION_URL`
   - title: 生成したタイトル
   - status: `In progress`
   - Project: `$NOTION_PROJECT_NAME`（`$NOTION_PROJECT_ID`）
3. → ステップ2へ

### 2. 作業ログ生成

会話コンテキスト全体をスキャンし、作業ログを生成する。

**構成ルール:**
- 冒頭に `## 概要` で目的・結論・作業日を簡潔に記載
- `---` で各セクションを区切る
- 本文の構成は内容に応じて柔軟に決定する（固定テンプレートは使わない）
- 作業ステップは番号付き見出し（`### 1.`, `### 2.`）で論理的な単位ごとに記述
- 各ステップ内では箇条書き・コードブロック・テーブル等を適切に使い分ける
- 末尾に `## 参考情報` で Claude Code SessionID: `${CLAUDE_SESSION_ID}` を記載

**内容の書き方:**
- 調査ログの場合: 疑問→調査→結論の流れで、思考過程や試行錯誤も含める
- セットアップ作業の場合: 手順・コマンド・設定値をそのまま再現可能なレベルで記載
- トラブルシュートの場合: 問題→原因→試した方法→解決策の構成で、失敗した方法も記録
- 実装作業の場合: 変更内容・設計判断の理由・テーブルで変更ファイル一覧

**Notionリッチフォーマット活用:**
- 設定値・比較は `<table>` で整理
- コマンド・コード・設定ファイルは ``` で記載
- 重要な注意点は `::: callout` で強調
- 長い補足は `<details>` トグルで折りたたむ

**ログ生成のポイント:**
- 単なる会話の転記ではなく、第三者が読んで作業を追えるレベルに再構成する
- 意思決定の経緯（なぜその方針にしたか、他の選択肢を却下した理由）を記録する
- 具体的なコマンド・設定値・エラーメッセージを含め、再現可能にする

### 3. Notionページ作成

`mcp__notion__notion-create-pages` でNotesページを作成：

- data source: `$NOTION_NOTES_COLLECTION_URL`
- title: `[Taskタイトル] - 作業ログ [YYYY-MM-DD]`
- tag: `["log"]`
- Task: ステップ1で取得/作成したTaskページURL
- Project: `$NOTION_PROJECT_NAME`（`$NOTION_PROJECT_ID`）
- content: ステップ2で生成したログ

### 4. 完了

```
✅ 作業ログをNotionに記録しました

- Notes: [NotesページURL]
- Task: [TaskページURL]
```
