---
description: 詳細なヒアリングを行いNotionにページを作成
argument-hint: [notion-url or initial task description]
---

## 設定

以下の環境変数を使用します（設定場所: `~/.claude/settings.json` または `.claude/settings.local.json`）：
- `NOTION_TASK_DB_URL`: TASKデータベースURL
- `NOTION_NOTES_DB_URL`: NotesデータベースURL
- `NOTION_PROJECT_ID`: プロジェクトのNotion ID
- `NOTION_PROJECT_NAME`: プロジェクト名（表示用）

## 前提条件

以下が事前に設定されていることを確認：
- Taskデータベースでサブアイテム機能が有効
- Notesデータベースでサブアイテム機能が有効
- TaskとNotesを紐付けるリレーションプロパティ（Notes）が存在
- TaskとNotesは同じProjectへのリレーションを持つ

## フロー

### 0. 引数判定

コマンド引数がNotion URLかテキストかを判定：

**Notion URLの場合:**
1. `notion-fetch` ツールでTASKページを取得
2. ページタイトルと既存内容を確認
3. **既存TASKモード**: TASKページは既に存在するため、Notesページのみ新規作成する
4. 次のステップ（詳細ヒアリング）でタイトルと既存内容をベースにヒアリングを開始

**テキストの場合:**
1. そのまま初期タスク説明として使用
2. **新規TASKモード**: 最終的に新しいTask + Notesページを両方作成する

### 1. 詳細ヒアリング

引数判定で取得した初期タスク説明をベースに、以下について認識齟齬がなくなるまで詳細にヒアリング：

- **概要**: 目的、何を実現するか、対象ユーザー
- **背景**: なぜこのタスクが必要か、現状の問題点、実施理由
- **詳細な要件**: 実装要件、機能仕様、UI/UX
- **受入条件（DoD）**: 完了定義、テスト、品質基準
- **技術的検討事項**: 技術スタック、アーキテクチャ、パフォーマンス、セキュリティ

### 2. タスク分割の提案

ヒアリング完了後、以下を総合的に判断し、分割の必要性を検討：

**判断材料**:
- 実装範囲の広さ（変更ファイル数、影響範囲）
- 作業の独立性（並行して進められる部分があるか）
- 見積もり工数（実装にかかる時間・日数）
- 技術的複雑さ（使用する技術スタックの多様性）

**分割を検討すべき例**:
- 新規機能開発でフロントエンド/バックエンドが独立している場合
- 複数の独立した機能が含まれる大規模実装
- 技術的に異なる領域（UI層/データ層/インフラなど）の実装が必要な場合

**注意**: 上記はあくまで参考例。タスクの種類（新規機能、リファクタ、バグ修正など）や規模感によって柔軟に判断する。

分割が適切と判断した場合、サブタスク構成を提案しユーザーの承認を得る。

### 3. サブタスクの詳細ヒアリング（分割時のみ）

各サブタスクについて個別に詳細ヒアリング：
- 概要
- 背景
- 詳細な要件
- 受入条件
- 技術的検討事項

### 3.5. Session ID取得

Bashツールで以下を実行し、session IDを取得してください：
```bash
cat << 'SCRIPT_END' | bash
SESSION_ID=$(ls -t ~/.claude/session-env 2>/dev/null | head -1)
if [ -z "$SESSION_ID" ]; then
  echo "N/A"
else
  echo "$SESSION_ID"
fi
SCRIPT_END
```

取得したSession IDをNotesページのコンテンツに含めます。

### 4. Notionページ作成

**プロパティ設定（共通）:**
- Task/Notes作成時は必ず「Project」リレーションに `$NOTION_PROJECT_NAME`（`$NOTION_PROJECT_ID`）を設定
- Notes作成時は必ず「tag」プロパティに「plan」を設定

**既存TASKモード（Notion URL指定時）:**
- 既存TASKページはそのまま使用（変更しない）
- Notesページのみ新規作成（詳細内容 + Claude Code SessionID）
- 既存TASKから新規Notesへリレーション設定（Notes）
- 新規NotesのProjectに既存TASKと同じProjectを設定

**新規TASKモード（テキスト指定時）:**

**分割なしの場合:**
- TASKページ作成（タイトル + Project: `$NOTION_PROJECT_NAME`）
- Notesページ作成（詳細内容 + Claude Code SessionID + Project: `$NOTION_PROJECT_NAME` + tag: plan）
- TASKからNotesへリレーション設定（Notes）

**分割ありの場合:**
- 親TASKページ作成（Project: `$NOTION_PROJECT_NAME`）
- 親Notesページ作成（全体概要 + Claude Code SessionID + Project: `$NOTION_PROJECT_NAME` + tag: plan）
- 各子TASKページ作成（サブアイテムとして親に紐付け + Project: `$NOTION_PROJECT_NAME`）
- 各子Notesページ作成（サブアイテムとして親に紐付け + Project: `$NOTION_PROJECT_NAME` + tag: plan）
- 各TASKから対応するNotesへリレーション設定（Notes）

**Notesページコンテンツフォーマット:**
Notesページには必ず以下のセクションを含めてください：
- 概要、背景、詳細な要件、受入条件、技術的検討事項
- **参考情報**セクション:
  ```
  ## 参考情報
  - Claude Code SessionID: `<session-id>`
  ```

**サブアイテム命名規則**:
- サブTASK/Notesページ名: **「{親タスク名} - {サブタスク内容}」** 形式で統一
- 例: 親「VTuber検索機能実装」→ サブ「VTuber検索機能実装 - フロントエンド実装」
- これにより、サブアイテム一覧で親子関係が明確になります

### 5. 完了

**既存TASKモード:**
- 既存TASKページURLを返す
- 新規作成したNotes URLを返す
- 「既存TASKにNotesを紐付けました」とメッセージを表示

**新規TASKモード:**
- 作成したページURLを返す：
  - 親タスクURL（または単一タスクURL）
  - 親Notes URL（または単一Notes URL）

NotesページURLは `/implementation` コマンドで使用できます。
