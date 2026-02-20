# Global Development Rules

## Language
- コミットメッセージ・PR本文: 日本語
- ブランチ名・コード: 英語

## Git
- Strategy: GitHub Flow（mainが常にデプロイ可能）
- Commit: Semantic Commit形式 (`<type>: <description>`)
  - types: feat, fix, docs, style, refactor, test, chore
- Branch: `<type>/<task-id>-<slug>` or `<type>/<slug>`
- Atomic Commit: 1 commit = 1 logical change

## Workflow
- 利用可能なスキル: /auto-workflow, /branch, /commit, /pr, /implementation, /plan2notion, /setup-project, /test, /log-note, /doc-note, /research-note
- 推奨フロー: /plan2notion → /auto-workflow
- 個別実行: /branch → /implementation → /test → /commit → /pr

## Notion Integration
- 2DB構成: Task DB + Notes DB
- Notesのtagは用途に応じて使い分け:
  - `plan`: 計画・仕様書（/plan2notionで作成）
  - `document`: まとめられたドキュメント（/doc-noteで作成）
  - `log`: 作業ログ・調査ログ（/log-noteで作成）
  - `research`: 技術調査・比較検討（/research-noteで作成）
- Task/NotesはProjectリレーションで紐付け
- 環境変数: NOTION_TASK_COLLECTION_URL, NOTION_NOTES_COLLECTION_URL, NOTION_PROJECT_ID, NOTION_PROJECT_NAME

## Quality
- TDD推奨: Red → Green → Refactor
- Lint/TypeCheck/Test/Build を全passしてからコミット
