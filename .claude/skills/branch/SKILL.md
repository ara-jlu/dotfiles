---
description: ブランチ作成時に使用。命名規則に従いNotion URLまたは要件からブランチを生成する
user-invocable: true
argument-hint: "[notion-url or requirement text]"
---

# 動的コンテキスト

現在のGit状態:
```
!`git status --short`
```

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

引数 `$ARGUMENTS` がNotion URLかテキストかを判定し、それぞれ処理：

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

## ブランチ命名規則

**GitHub Flow**を採用。`main`ブランチが常にデプロイ可能な状態。

```
# タスクIDがある場合
<type>/<task-id>-<簡潔な説明>

# タスクIDがない場合
<type>/<簡潔な説明>
```

| タイプ | 用途 | 例 |
|-------|------|-----|
| `feature/` | 新機能開発 | `feature/TASK-1-user-authentication` |
| `hotfix/` | 緊急バグ修正 | `hotfix/TASK-2-critical-payment-error` |
| `docs/` | ドキュメント更新 | `docs/update-api-specification` |

### 4. ブランチ作成

```bash
git checkout -b <generated-branch-name>
```

### 5. 完了

作成したブランチ名を表示します。

## エラーハンドリング

- Notion URLが無効な場合: エラーを報告して停止
- git操作が失敗した場合: エラーを報告して停止
