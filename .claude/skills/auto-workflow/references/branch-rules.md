# ブランチ命名ルール

## ブランチ戦略

**GitHub Flow**を採用。`main`ブランチが常にデプロイ可能な状態。

## 命名規則

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

## ブランチ作成

```bash
git checkout main
git pull origin main
git checkout -b <type>/<slug>
```
