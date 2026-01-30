---
description: Docker環境でテストスイート一式を実行
---

## 準備

以下のドキュメントを読み込んでください：
- `~/.claude/docs/development/test-commands.md`
- `~/.claude/docs/development/docker-workflow.md`

## 実行

Docker環境で以下を順次実行し、すべてpassすることを確認：

1. `docker-compose build` - Dockerイメージをビルド
2. `docker-compose up -d` - コンテナをバックグラウンドで起動
3. `docker-compose exec nextjs npm run lint` - ESLintチェック
4. `docker-compose exec nextjs npm run typecheck` - TypeScript型チェック
5. `docker-compose exec nextjs npm run test` - ユニットテスト実行
6. `docker-compose exec nextjs npm run build` - Next.js本番ビルド
7. `docker-compose down` - コンテナ停止・削除

1つでも失敗した場合は中断し、エラー内容を報告してください。
すべてpassした場合、テストが正常に完了したことを報告してください。
