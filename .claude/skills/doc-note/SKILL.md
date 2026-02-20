---
description: 既存のlog/memoなどのNotion Notesを参照し、整理・統合したドキュメントをNotes DBに作成する。「これらをまとめて」「ドキュメント化して」のような依頼で使用。
user-invocable: true
argument-hint: "[notion-urls...] (Notes URLs to reference, optionally include a Task URL)"
---

## フロー

### 1. 引数解析

引数 `$ARGUMENTS` に含まれるNotion URLを分類：

- **Notes URL**: 参照元として `mcp__notion__notion-fetch` で内容を取得
- **Task URL**: 紐付け先Taskとして使用（ancestor-pathにTask DBのcollection URLが含まれるかで判別）

**Task URLあり:**
- Taskのタイトル・Projectプロパティを取得
- → ステップ2へ

**Task URLなし:**
- 参照Notesの内容からドキュメントの主題を推定し、タスクタイトルを生成
- `mcp__notion__notion-create-pages` で新規Taskを作成：
  - data source: `$NOTION_TASK_COLLECTION_URL`
  - title: 生成したタイトル
  - status: `In progress`
  - Project: `$NOTION_PROJECT_NAME`（`$NOTION_PROJECT_ID`）
- → ステップ2へ

### 2. 参照Notesの取得・分析

各参照Notes URLを `mcp__notion__notion-fetch` で取得し、以下を把握：
- 各Notesのtag（log, memo, research等）
- 内容の時系列・トピック構造
- 重複情報・補完関係

### 3. ドキュメント生成

参照Notesの内容を整理・統合し、以下の構成でドキュメントを生成：

```markdown
## [ドキュメントタイトル]

### 概要
[ドキュメント全体のサマリ]

### [トピック別セクション]
[参照元の情報を論理的に再構成]
...

### 参照元
- [参照Notes 1のタイトル](URL)
- [参照Notes 2のタイトル](URL)
...

## 参考情報
- Claude Code SessionID: `${CLAUDE_SESSION_ID}`
```

**ドキュメント生成のポイント:**
- 単なるコピペではなく、情報を論理的に再構成する
- 重複を排除し、矛盾があれば最新情報を優先する
- 参照元のログ的な時系列構造を、トピック別の構造に変換する
- 第三者が読んで理解できるレベルの完成度を目指す

### 4. Notionページ作成

`mcp__notion__notion-create-pages` でNotesページを作成：

- data source: `$NOTION_NOTES_COLLECTION_URL`
- title: `[Taskタイトル] - [ドキュメント主題]`
- tag: `["document"]`
- Task: ステップ1で取得/作成したTaskページURL
- Project: `$NOTION_PROJECT_NAME`（`$NOTION_PROJECT_ID`）
- content: ステップ3で生成したドキュメント

### 5. 完了

```
✅ ドキュメントをNotionに作成しました

- Notes: [NotesページURL]
- Task: [TaskページURL]
- 参照元: [N]件のNotesを統合
```
