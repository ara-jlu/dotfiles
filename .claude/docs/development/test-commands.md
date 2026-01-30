# コミット前必須テストコマンド

## 完全なテストフロー

コミット前に以下をすべて実行し、**すべてpass**することを確認：

```bash
docker-compose build
docker-compose up -d
docker-compose exec nextjs npm run lint
docker-compose exec nextjs npm run typecheck
docker-compose exec nextjs npm run test
docker-compose exec nextjs npm run build
docker-compose down
```

## 各コマンドの目的

| コマンド | 目的 |
|---------|------|
| `build` | Dockerイメージをビルド |
| `up -d` | コンテナをバックグラウンドで起動 |
| `lint` | ESLintでコードスタイルをチェック |
| `typecheck` | TypeScriptの型チェック |
| `test` | ユニットテスト実行 |
| `build` | Next.js本番ビルド確認 |
| `down` | コンテナ停止・削除 |

## カバレッジ確認

```bash
docker-compose exec nextjs npm run test:coverage
```

## すべてpassしたら

Atomic Commitの原則に従って、論理的単位でコミット：

```bash
git add src/components/Login.tsx
git commit -m "feat: Loginコンポーネントを実装"
```

## 参照

- Docker環境: `~/.claude/docs/development/docker-workflow.md`
- PR作成: `~/.claude/docs/git/pull-request.md`
