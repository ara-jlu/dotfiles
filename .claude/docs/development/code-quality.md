# コード品質管理

## ツール

- **ESLint**: コードスタイルとベストプラクティス
- **TypeScript**: 型安全性
- **Prettier**: コードフォーマット

## コマンド（Docker環境）

```bash
# Lint
docker-compose exec nextjs npm run lint
docker-compose exec nextjs npm run lint -- --fix

# Type Check
docker-compose exec nextjs npm run typecheck

# Format
docker-compose exec nextjs npm run format

# Build
docker-compose exec nextjs npm run build
```

## 品質基準

- Lintエラー: 0
- 型エラー: 0
- ビルド: 成功

## よくあるエラーと対処

### Lint

- 未使用の変数・import → 削除
- console.log → 削除または開発環境のみに制限

### Type Check

- 型の不一致 → 正しい型を定義
- nullableな値 → 型ガードを使用

## 参照

- テストコマンド: `~/.claude/docs/development/test-commands.md`
- Docker環境: `~/.claude/docs/development/docker-workflow.md`
