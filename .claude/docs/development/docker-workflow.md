# Docker環境でのワークフロー

## なぜDocker環境でテストするか

本番環境との一貫性を保証し、ローカル環境の差異を排除するため

## コミット前の必須手順

```bash
# 1. ビルド
docker-compose build

# 2. 起動
docker-compose up -d

# 3. テスト実行
docker-compose exec nextjs npm run lint
docker-compose exec nextjs npm run typecheck
docker-compose exec nextjs npm run test
docker-compose exec nextjs npm run build

# 4. クリーンアップ
docker-compose down
```

## ブラウザ動作確認

```bash
docker-compose up
# http://localhost:3000 で確認
```

確認項目：
- ページが正しく表示される
- ブラウザコンソールにエラーがない
- 基本操作が動作する

## 参照

- テストコマンド: `~/.claude/docs/development/test-commands.md`
- コード品質: `~/.claude/docs/development/code-quality.md`
