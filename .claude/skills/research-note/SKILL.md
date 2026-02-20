---
description: 技術調査・比較検討の結果をNotionのNotes DBに記録する。技術選定、ライブラリ比較、アーキテクチャ検討など調査系の会話後に使用。
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
1. 会話コンテキストから調査テーマを特定し、タスクタイトルを生成
2. `mcp__notion__notion-create-pages` で新規Taskを作成：
   - data source: `$NOTION_TASK_COLLECTION_URL`
   - title: 生成したタイトル
   - status: `In progress`
   - Project: `$NOTION_PROJECT_NAME`（`$NOTION_PROJECT_ID`）
3. → ステップ2へ

### 2. リサーチノート生成

会話コンテキストをスキャンし、以下の構成で調査結果を生成：

```markdown
## [調査テーマ]

### 背景・目的
[なぜこの調査が必要になったか]

### 調査結果

#### [選択肢A / 技術A]
- 概要: [何か]
- メリット: [利点]
- デメリット: [欠点]
- 参考: [URLがあれば]

#### [選択肢B / 技術B]
...

### 比較表（該当する場合）
| 観点 | A | B | C |
|------|---|---|---|
| ... | ... | ... | ... |

### 結論・推奨
[調査結果に基づく推奨事項や意思決定]

### 残課題
[追加調査が必要な項目があれば]

## 参考情報
- Claude Code SessionID: `${CLAUDE_SESSION_ID}`
```

**生成のポイント:**
- 会話中の調査・比較・検討内容を構造化する
- 比較可能な項目は表形式でまとめる
- 結論が出ている場合はその根拠も記載する
- 参考URLやソースがあれば含める

### 3. Notionページ作成

`mcp__notion__notion-create-pages` でNotesページを作成：

- data source: `$NOTION_NOTES_COLLECTION_URL`
- title: `[Taskタイトル] - リサーチノート [YYYY-MM-DD]`
- tag: `["research"]`
- Task: ステップ1で取得/作成したTaskページURL
- Project: `$NOTION_PROJECT_NAME`（`$NOTION_PROJECT_ID`）
- content: ステップ2で生成したリサーチノート

### 4. 完了

```
✅ リサーチノートをNotionに記録しました

- Notes: [NotesページURL]
- Task: [TaskページURL]
```
