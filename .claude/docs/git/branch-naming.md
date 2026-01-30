# ブランチ戦略と命名規則

## ブランチ戦略

**GitHub Flow**を採用。`main`ブランチが常にデプロイ可能な状態。

## 命名規則

```
# タスクIDがある場合
<type>/<task-id>-<簡潔な説明>

# タスクIDがない場合
<type>/<簡潔な説明>
```

### タイプ

| タイプ | 用途 | 例 |
|-------|------|-----|
| `feature/` | 新機能開発 | `feature/TASK-1-user-authentication` |
| `hotfix/` | 緊急バグ修正 | `hotfix/TASK-2-critical-payment-error` |
| `docs/` | ドキュメント更新 | `docs/update-api-specification` |

### タスクIDなしの例

```
feature/user-authentication
hotfix/critical-payment-error
docs/update-setup-guide
```

## ブランチ作成

```bash
git checkout main
git pull origin main

# タスクIDがある場合
git checkout -b feature/TASK-1-user-login

# タスクIDがない場合
git checkout -b feature/user-login
```

## 参照

- コミット規則: `~/.claude/docs/git/commit-format.md`, `~/.claude/docs/git/atomic-commit.md`
- PR作成: `~/.claude/docs/git/pull-request.md`
