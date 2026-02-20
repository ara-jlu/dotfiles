# テスト実行パターン

プロジェクトの技術スタックを自動検出し、適切なテスト方法を選択する。

## パターンA: Docker プロジェクト

**検出条件**: `docker-compose.yml` が存在する

1. `docker-compose.yml` からサービス名を自動検出
2. 以下を順次実行（`package.json` の scripts に定義されているコマンドのみ）：

```bash
docker-compose build
docker-compose up -d
docker-compose exec <service> <pm> run lint
docker-compose exec <service> <pm> run typecheck
docker-compose exec <service> <pm> run test
docker-compose exec <service> <pm> run build
docker-compose down
```

**サービス名の検出**: `docker-compose.yml` を読み込み、メインのアプリケーションサービスを特定する（通常は `app`, `web`, `nextjs` 等）。

## パターンB: pnpm/Turborepo プロジェクト

**検出条件**: `pnpm-workspace.yaml` が存在する

```bash
pnpm lint
pnpm typecheck
pnpm test --filter=<affected-package>
pnpm build --filter=<affected-package>
```

## パターンC: npm/yarn プロジェクト

**検出条件**: 上記以外（`yarn.lock` → yarn、それ以外 → npm）

```bash
npm run lint    # / yarn lint
npm run typecheck  # / yarn typecheck
npm test        # / yarn test
npm run build   # / yarn build
```

## 共通ルール

- `package.json` の scripts を確認し、**存在するコマンドのみ実行**する
- すべてpass → 次のステップへ
- 1つでも失敗 → 処理を停止し、エラー内容を報告
