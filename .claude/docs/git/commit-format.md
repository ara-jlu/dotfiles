# コミットメッセージ形式

## Semantic Commit Messages

```
<type>: <description>
```

### タイプ定義

| タイプ | 用途 | 例 |
|-------|------|-----|
| `feat` | 新機能（ユーザー向け） | `feat: ダッシュボード画面を追加` |
| `fix` | バグ修正（ユーザー向け） | `fix: ログアウト後のリダイレクトを修正` |
| `docs` | ドキュメント変更 | `docs: セットアップガイドを更新` |
| `style` | フォーマット等（機能変更なし） | `style: コードフォーマットを統一` |
| `refactor` | コード改善（機能変更なし） | `refactor: 認証ロジックをリファクタリング` |
| `test` | テスト追加・修正 | `test: ユーザー登録のテストを追加` |
| `chore` | ビルドタスク等の更新 | `chore: 依存関係を更新` |

## 注意点

- 簡潔で明確な説明（50文字以内目安）
- 1コミット = 1つの論理的変更（Atomic Commit）

## 参照

- Atomic Commit: `~/.claude/docs/git/atomic-commit.md`
- ブランチ命名: `~/.claude/docs/git/branch-naming.md`
- PR作成: `~/.claude/docs/git/pull-request.md`
