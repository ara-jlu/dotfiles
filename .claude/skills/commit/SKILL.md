---
description: コミット作成時に使用。Atomic Commit原則とSemantic Commit形式に従う
user-invocable: true
---

# 動的コンテキスト

現在の変更状態:
```
!`git status --short`
```

変更統計:
```
!`git diff --stat`
```

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

### 注意点

- 簡潔で明確な説明（50文字以内目安）
- 1コミット = 1 Task（Atomic Commit）
- 詳細なAtomic Commit原則は `references/atomic-commit.md` を参照

## 実行

1. `TaskList` ツールで完了済みTaskを確認（Taskがある場合）
2. `git status` と `git diff` で変更内容を確認
3. **Task単位でコミットを分割**：
   - Taskがある場合: 各Taskに対応するファイル変更を特定し、Taskごとに個別コミット
   - Taskがない場合: 変更内容を分析し、論理的単位ごとにコミット
4. Semantic Commit形式でコミットメッセージを生成し、コミット実行
