---
description: 新規ブランチ作成（Notion URLまたは要件から自動生成）
argument-hint: [notion-url or requirement text]
---

## 準備

以下のドキュメントを読み込んでください：
- `~/.claude/docs/git/branch-naming.md`

## 実行手順

### 1. 未コミット変更の確認

git statusで未コミットの変更がないか確認します。
変更がある場合は警告を表示し、処理を継続するか確認してください。

### 2. mainブランチへ切り替えと最新化

```bash
git checkout main
git pull origin main
```

### 3. ブランチ名生成

引数がNotion URLかテキストかを判定し、それぞれ処理：

#### パターンA: Notion URLの場合

1. **notion-fetchツールでページ取得**
2. **タスクID取得**: プロパティ「ID」から（例: TASK-1）
   - 取得できない場合はID無しで続行
3. **タイトル取得**: ページタイトル
4. **ブランチtype判定**: タイトルの内容から自動判定
   - 「バグ」「修正」「hotfix」「エラー」含む → `hotfix/`
   - 「ドキュメント」「docs」「README」含む → `docs/`
   - その他 → `feature/`
5. **スラグ生成**: タイトルをAIで英訳・要約してスラグ化
   - 例: "Vダッシュボードリファクタリング Server Component移行" → "dashboard-server-component"
6. **ブランチ名組み立て**:
   - IDあり: `<type>/<task-id>-<slug>`（例: `feature/TASK-1-dashboard-server-component`）
   - ID無し: `<type>/<slug>`（例: `feature/dashboard-server-component`）

#### パターンB: 要件テキストの場合

1. **ブランチtype判定**: テキストの内容から自動判定
   - 「バグ」「修正」「hotfix」「エラー」含む → `hotfix/`
   - 「ドキュメント」「docs」「README」含む → `docs/`
   - その他 → `feature/`
2. **スラグ生成**: 要件テキストをAIで要約・英訳してスラグ化
   - 例: "ユーザー認証機能を追加する" → "user-authentication"
3. **ブランチ名組み立て**: `<type>/<slug>`
   - 例: `feature/user-authentication`

### 4. ブランチ作成

```bash
git checkout -b <generated-branch-name>
```

### 5. 完了

作成したブランチ名を表示します。

## エラーハンドリング

- Notion URLが無効な場合: エラーを報告して停止
- git操作が失敗した場合: エラーを報告して停止
