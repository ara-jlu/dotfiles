---
description: 詳細なヒアリングを行いNotionにページを作成
user-invocable: true
disable-model-invocation: true
argument-hint: "[notion-url or initial task description]"
---

## 設定

以下の環境変数を使用します（設定場所: `~/.claude/settings.json` または `.claude/settings.local.json`）：
- `NOTION_TASK_COLLECTION_URL`: Task DBのdata source URL（`collection://...`形式）
- `NOTION_NOTES_COLLECTION_URL`: Notes DBのdata source URL（`collection://...`形式）
- `NOTION_PROJECT_ID`: プロジェクトのNotion ID
- `NOTION_PROJECT_NAME`: プロジェクト名（表示用）

## 前提条件

以下が事前に設定されていることを確認：
- Taskデータベースでサブアイテム機能が有効
- Notesデータベースでサブアイテム機能が有効
- TaskとNotesを紐付けるリレーションプロパティ（Notes）が存在
- TaskとNotesは同じProjectへのリレーションを持つ

## 重要: ヒアリング実行規則

**このスキルのフェーズ1〜3では、必ず `AskUserQuestion` ツールを使用してユーザーに質問すること。**

- 質問は必ず `AskUserQuestion` ツールで行い、ユーザーの回答を待ってから次に進むこと
- **自分で回答を推測・生成して先に進むことは厳禁**（dangerous-permissionsモードでも同様）
- 各質問のユーザー回答を受け取ってから、次の質問または次のフェーズに進むこと
- ヒアリングが不十分と判断した場合は、追加の `AskUserQuestion` で深掘りすること

## フロー

### 0. 引数判定

引数 `$ARGUMENTS` がNotion URLかテキストかを判定：

**Notion URLの場合:**
1. `notion-fetch` ツールでTASKページを取得
2. ページタイトルと既存内容を確認
3. **既存TASKモード**: TASKページは既に存在するため、Notesページのみ新規作成する
4. 次のステップ（詳細ヒアリング）でタイトルと既存内容をベースにヒアリングを開始

**テキストの場合:**
1. そのまま初期タスク説明として使用
2. **新規TASKモード**: 最終的に新しいTask + Notesページを両方作成する

### 1. 詳細ヒアリング

引数判定で取得した初期タスク説明をベースに、以下の6ステップで `AskUserQuestion` を使い詳細にヒアリングする。各ステップでユーザーの回答を待ってから次に進むこと。

#### 1.1 概要の確認

初期説明から推測したタスク概要（目的、何を実現するか、対象ユーザー）を提示し、認識が合っているか確認する。

- `AskUserQuestion` で確認
  - header: `Overview`
  - options: "この理解で合っている" / "修正がある"
- 「修正がある」またはOther入力時は内容を反映し、必要に応じて追加の `AskUserQuestion` で深掘り

#### 1.2 背景

背景・問題点・実施理由について質問する。

- `AskUserQuestion` で質問
  - header: `Background`
  - options: "特になし（概要で説明済み）" / "背景情報あり"
- 「背景情報あり」またはOther入力時は内容を反映し、必要に応じて追加の `AskUserQuestion` で深掘り

#### 1.3 詳細な要件

実装要件・機能仕様・UI/UXについて質問する。

- `AskUserQuestion` で質問
  - header: `Reqs`
  - options: "お任せ（概要から判断）" / "具体的な要件あり"
- 「具体的な要件あり」またはOther入力時は内容を反映し、必要に応じて追加の `AskUserQuestion` で深掘り

#### 1.4 受入条件（DoD）

完了定義・テスト要件・品質基準について質問する。

- `AskUserQuestion` で質問
  - header: `DoD`
  - options: "標準的な基準でOK" / "特定の基準あり"
- 「特定の基準あり」またはOther入力時は内容を反映し、必要に応じて追加の `AskUserQuestion` で深掘り

#### 1.5 技術的検討事項

技術スタック・アーキテクチャ・パフォーマンス・セキュリティ等の考慮点について質問する。

- `AskUserQuestion` で質問
  - header: `Tech`
  - options: "特になし" / "検討事項あり"
- 「検討事項あり」またはOther入力時は内容を反映し、必要に応じて追加の `AskUserQuestion` で深掘り

#### 1.6 ヒアリング結果の最終確認

ステップ1.1〜1.5で収集した情報をまとめて提示し、最終確認する。

- `AskUserQuestion` で確認
  - header: `Confirm`
  - options: "問題なし、次に進む" / "修正がある"
- 「修正がある」またはOther入力時は内容を反映し、必要に応じて前のステップに戻って再ヒアリング

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

分割が適切と判断した場合、以下の確認ステップに進む。

#### 2.1 分割提案の確認（分割が必要と判断した場合）

サブタスク構成案を提示し、`AskUserQuestion` で確認する。

- header: `Split`
- options: "この構成でOK" / "分割不要"
- Other入力時は内容を反映し、必要に応じて追加の `AskUserQuestion` で構成を調整

#### 2.2 分割不要の確認（分割不要と判断した場合）

分割不要と判断した理由を提示し、`AskUserQuestion` で確認する。

- header: `Split`
- options: "分割不要でOK" / "分割してほしい"
- 「分割してほしい」またはOther入力時は分割案を作成し、2.1に進む

### 3. サブタスクの詳細ヒアリング（分割時のみ）

Phase 1で全体の要件は収集済みのため、各サブタスク**固有の差分**に絞って `AskUserQuestion` でヒアリングする。

各サブタスクについて以下の2ステップを実施：

#### ステップA: 要件確認

サブタスクの概要・要件・受入条件をPhase 1の内容から抽出して提示し、`AskUserQuestion` で確認する。

- header: `Sub:{番号}`（例: `Sub:1`, `Sub:2`）
- options: "フェーズ1の内容で十分" / "追加の要件あり"
- 「追加の要件あり」またはOther入力時は内容を反映し、必要に応じて追加の `AskUserQuestion` で深掘り

#### ステップB: 技術的詳細

サブタスク固有の技術的な考慮点について `AskUserQuestion` で質問する。

- header: `Sub:{番号}`（例: `Sub:1`, `Sub:2`）
- options: "お任せ" / "技術的な指定あり"
- 「技術的な指定あり」またはOther入力時は内容を反映し、必要に応じて追加の `AskUserQuestion` で深掘り

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
  - Claude Code SessionID: `${CLAUDE_SESSION_ID}`
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

NotesページURLは `/implementation` スキルで使用できます。
