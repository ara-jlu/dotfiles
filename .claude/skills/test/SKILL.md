---
description: プロジェクト環境を自動検出しテストスイートを実行
user-invocable: true
---

# 動的コンテキスト

プロジェクト環境:
```
!`ls docker-compose.yml pnpm-workspace.yaml 2>/dev/null`
```

## 環境自動検出とテスト実行

プロジェクトの技術スタックを自動検出し、適切なテスト方法を選択します。

### パターンA: Docker プロジェクト（`docker-compose.yml` が存在する場合）

1. `docker-compose.yml` からサービス名を自動検出する
2. 以下を順次実行（`package.json` の scripts に定義されているコマンドのみ）：
   - `docker-compose build` - Dockerイメージをビルド
   - `docker-compose up -d` - コンテナをバックグラウンドで起動
   - `docker-compose exec <service> <pm> run lint` - ESLintチェック
   - `docker-compose exec <service> <pm> run typecheck` - TypeScript型チェック
   - `docker-compose exec <service> <pm> run test` - ユニットテスト実行
   - `docker-compose exec <service> <pm> run build` - 本番ビルド
   - `docker-compose down` - コンテナ停止・削除

**サービス名の検出方法**: `docker-compose.yml` を読み込み、メインのアプリケーションサービスを特定する（通常は `app`, `web`, `nextjs` 等）。

### パターンB: pnpm/Turborepo プロジェクト（`pnpm-workspace.yaml` が存在する場合）

1. 以下を順次実行（定義されているコマンドのみ）：
   - `pnpm lint` - ESLintチェック
   - `pnpm typecheck` - TypeScript型チェック
   - `pnpm test` - テスト実行（変更パッケージがある場合 `--filter=<affected-package>`）
   - `pnpm build` - ビルド確認（変更パッケージがある場合 `--filter=<affected-package>`）

### パターンC: npm/yarn プロジェクト

1. `package.json` を確認し、パッケージマネージャーを判定（`yarn.lock` → yarn、それ以外 → npm）
2. 以下を順次実行（`package.json` の scripts に定義されているコマンドのみ）：
   - `npm run lint` / `yarn lint` - Lintチェック
   - `npm run typecheck` / `yarn typecheck` - 型チェック
   - `npm test` / `yarn test` - テスト実行
   - `npm run build` / `yarn build` - ビルド確認

## 結果確認

- すべてpass: 「✅ テスト正常完了」と表示
- 1つでも失敗: 処理を停止し、エラー内容を報告
