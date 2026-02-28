# Atomic Commit原則（CRITICAL）

## 重要性

- **レビュアビリティ**: 各コミットが独立して理解可能
- **リバート可能性**: 問題があれば特定のコミットだけを元に戻せる
- **デバッグ効率**: git bisectで問題の原因を特定しやすい

## 基本原則: 1 Task = 1 Commit

Claude Codeの`Task`（TaskCreateで作成される単位）を「1つの論理的変更」の基準とする。

Taskは実装時に自然と適切な粒度に分解されるため、**Task完了 = コミット**のリズムで進める。

### 粒度の目安

```
✅ Task粒度（適切）:
- "UserServiceクラスを作成" → feat: UserServiceクラスを作成
- "ログインフォームにバリデーションを追加" → feat: ログインフォームにバリデーションを追加
- "UserServiceのユニットテストを追加" → test: UserServiceのユニットテストを追加

✗ 大きすぎる（複数Taskをまとめている）:
- "ユーザー認証機能を実装"（サービス + フォーム + テストが混在）

✗ 小さすぎる（Taskとして分ける意味がない）:
- "import文を追加"（実装の一部であってTaskではない）
```

### Task完了ごとにコミット

```bash
# Task: "Heroiconsライブラリをインストール"
npm install @heroicons/react
git add package.json package-lock.json
git commit -m "feat: Heroiconsライブラリを追加"

# Task: "Buttonコンポーネントを実装"
git add src/components/Button.tsx
git commit -m "feat: Buttonコンポーネントを実装"

# Task: "Buttonコンポーネントのテストを追加"
git add src/components/Button.test.tsx
git commit -m "test: Buttonコンポーネントのテストを追加"
```

**重要**: バグだらけの状態でコミットしない。最低限正しく実装されている状態でコミットする。

## コミット粒度の判断基準

### 1つのコミット（= 1 Task）にすべき変更

- ✅ 1つのTaskで実装した全ファイル（実装 + それに伴うimport追加等）
- ✅ TaskCreateで1つのTaskとして定義された作業

### 分割すべき変更（別のTaskにすべき）

- ❌ 新機能の実装 + バグ修正
- ❌ 複数の独立した機能追加
- ❌ リファクタリング + 新機能追加

## チェックリスト

コミット前に確認：

- [ ] 1つのTaskの変更のみを含むか？
- [ ] コミットメッセージで変更内容を簡潔に説明できるか？
- [ ] このコミット単体でレビュー可能か？

## まとめ

**TaskCreateでタスクを分解**し、**各Task完了ごとに即コミット（最低限動作する状態で）**する。後からまとめて分割しない。
