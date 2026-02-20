# プルリクエスト（PR）ガイドライン

## PR作成前のチェックリスト

### テスト（プロジェクト環境に応じて実行）

プロジェクトの `package.json` の scripts を確認し、存在するコマンドのみ実行する。

- lint: ESLintチェック
- typecheck: TypeScript型チェック
- test: ユニットテスト実行
- build: 本番ビルド確認

### Git規約の遵守

- [ ] Atomic Commitの原則に従っている
- [ ] Semantic Commit形式
- [ ] ブランチ名が命名規則に従っている

## レビュールール

- 少なくとも1名の承認が必要
- セルフマージ禁止
- すべてのCI/CDチェックが通過必須

## マージ後

```bash
git checkout main
git pull origin main
git branch -d <branch-name>
```
