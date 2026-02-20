---
description: NotionタスクをブランチからPRまで完全自動実行
user-invocable: true
disable-model-invocation: true
argument-hint: "[notion-url or requirement text]"
---

## 完全自動実行スキル

このスキルは**ユーザーの入力を待たずに全ステップを自動実行**します。
各ステップ完了後、必ず次のステップに進んでください。

---

## 実行フロー

以下のステップを**順次自動実行**してください。各ステップ完了後、自動的に次のステップへ進んでください。

---

### ステップ1: ブランチ作成

#### 1.1 未コミット変更の確認

Bashツールで `git status` を実行し、未コミット変更を確認：
- 変更がある場合: 警告を表示し、ユーザーに確認を求める（処理停止）
- 変更がない場合: 次へ進む

#### 1.2 mainブランチへ切り替えと最新化

Bashツールで以下を実行：
```bash
git checkout main && git pull origin main
```

エラー時は処理を停止し、エラー内容を報告してください。

#### 1.3 ブランチ名生成

引数 `$ARGUMENTS` がNotion URLかテキストかを判定し、適切な方法でブランチ名を生成：

**パターンA: Notion URLの場合**
1. `mcp__notion__notion-fetch` ツールでページを取得
2. プロパティ「ID」からタスクID取得（例: TASK-1）
   - 取得できない場合はID無しで続行
3. ページタイトルを取得
4. タイトルの内容からブランチtypeを判定：
   - 「バグ」「修正」「hotfix」「エラー」含む → `hotfix/`
   - 「ドキュメント」「docs」「README」含む → `docs/`
   - その他 → `feature/`
5. タイトルをAIで英訳・要約してスラグ化（小文字、ハイフン区切り）
6. ブランチ名を組み立て：
   - IDあり: `<type>/<task-id>-<slug>`（例: `feature/TASK-1-<slug>`）
   - ID無し: `<type>/<slug>`

**パターンB: 要件テキストの場合**
1. テキストの内容からブランチtypeを判定：
   - 「バグ」「修正」「hotfix」「エラー」含む → `hotfix/`
   - 「ドキュメント」「docs」「README」含む → `docs/`
   - その他 → `feature/`
2. 要件テキストをAIで要約・英訳してスラグ化
3. ブランチ名を組み立て: `<type>/<slug>`

#### 1.4 ブランチ作成

Bashツールで以下を実行：
```bash
git checkout -b <generated-branch-name>
```

作成したブランチ名を表示し、**即座にステップ2へ進んでください**。

**エラー時**: 処理を停止し、エラー内容を報告してください。

---

### ステップ2: 実装

#### 2.1 準備

以下のドキュメントを読み込む（存在するもののみ）：
- `CLAUDE.md`（プロジェクトルート）
- `.claude/project/local-setup.md`
- `.claude/project/testing-strategy.md`

#### 2.2 環境確認

プロジェクトの技術スタックに応じて必要な環境のみ確認する:

- **Docker/Supabase**: `docker-compose.yml` または `supabase/` ディレクトリが存在する場合のみ確認
  - `docker ps` で Docker 起動状態を確認
  - `supabase status` で Supabase 起動状態を確認
- **pnpm/npm**: `package.json` が存在する場合、パッケージマネージャーの利用可否を確認
- **上記に該当しない場合**: 環境確認をスキップし次へ進む

#### 2.3 要件分析

引数がテキストの場合はそのまま要件として使用し、2.4へ進む。

引数がNotion URLの場合：
1. `mcp__notion__notion-fetch` でタスクページを取得（ステップ1.3で取得済みなら再取得不要）
2. プロパティ「Notes」からplanタグ付きNotesページをすべて `mcp__notion__notion-fetch` で取得する（**主要な仕様書**として必ず確認）
3. Notes内容を主要な仕様、タスクページ本文を補足情報として統合する

planタグ付きNotesが無い場合は、**処理を停止してユーザーに要件を確認**してください。

**`TaskCreate` ツールでタスク分解と計画を作成**してください。

#### 2.4 TDD実装

以下のサイクルで実装を進めてください：
1. テスト作成（推奨）
2. 実装
3. リファクタリング
4. Atomic Commit意識（論理的単位で分割可能な粒度を意識）
5. 最低限の動作確認

#### 2.5 E2E 動作確認（可能な範囲で）

実装完了後、AI が検証可能な項目を Playwright MCP で確認:

**AI が検証できるもの**:
- Web ページの表示確認（`mcp__playwright__browser_navigate` + `mcp__playwright__browser_snapshot`）
- DOM 要素の存在確認（セレクターで特定要素を検証）
- コンソールエラーの有無（`mcp__playwright__browser_console_messages`）
- ネットワークリクエストの確認（`mcp__playwright__browser_network_requests`）

**AI が検証できないもの（ユーザーに依頼）**:
- Chrome 拡張の実際のブラウザ上での動作（content script のページ注入等）
- 認証が必要な外部サービスとの連携（AWS/Azure コンソール等）
- ブラウザ拡張のインストール・有効化の確認

検証可能な項目がある場合は実行し、結果を報告に含める。
検証不可能な項目がある場合は「手動確認推奨」としてリストアップする。

#### 2.6 実装完了報告

実装が完了したら、以下の形式で報告。**ユーザーアクション項目**は後のステップでNotionタスク化するため、漏れなく列挙すること：

```
✅ 実装完了

## 実装内容
- [実装した内容の箇条書き]

## 変更ファイル
- [変更したファイルのリスト]

## 動作確認
- [AI検証結果（実施した場合）]

## ユーザーアクション必要（該当する場合）
以下はAIでは実行できないため、ユーザーが手動で行う必要がある作業：
- [ ] [アクション項目1: 具体的な内容]
- [ ] [アクション項目2: 具体的な内容]
```

**ユーザーアクションの例**:
- 外部サービスのクレデンシャル設定（GA4, Polar, AWS等）
- ブラウザ拡張のインストール・手動テスト
- CWS ストア提出
- 認証が必要なサービスでの動作確認

**重要**: 実装完了報告を出力したら、**即座にステップ3へ進んでください**。ここで停止しないでください。

**エラー時**: 処理を停止し、エラー内容を報告してください。

---

### ステップ3: 変更内容判定

#### 3.1 変更ファイル確認

Bashツールで以下を実行：
```bash
git diff --name-only
```

#### 3.2 テスト要否判定

変更ファイルが以下のいずれかに該当する場合は**テスト実行**：
- テストファイル（`.test.ts`, `.test.tsx`, `.spec.ts`, `.spec.tsx`）の変更がある
- TypeScript/JavaScriptファイル（`.ts`, `.tsx`, `.js`, `.jsx`）の変更がある
- テストスクリプトが `package.json` に定義されている

上記に該当しない場合は**テストスキップ**：
- 「コードファイルの変更がないため、テストをスキップします」と表示
- ステップ5へ進む

テスト実行が必要な場合は、**即座にステップ4へ進んでください**。

---

### ステップ4: テスト（条件付き）

**注意**: このステップはステップ3でテスト実行が必要と判断された場合のみ実行してください。

テスト実行パターンの詳細は `references/test-patterns.md` を参照。

#### 4.1 テスト実行

プロジェクトの技術スタックに応じたテスト方法を選択:

**パターンA: Docker プロジェクト**（`docker-compose.yml` が存在する場合）
1. `docker-compose.yml` からサービス名を自動検出
2. `docker-compose build` - Dockerイメージをビルド
3. `docker-compose up -d` - コンテナをバックグラウンドで起動
4. `docker-compose exec <service> <pm> run lint` - ESLintチェック
5. `docker-compose exec <service> <pm> run typecheck` - TypeScript型チェック
6. `docker-compose exec <service> <pm> run test` - ユニットテスト実行
7. `docker-compose exec <service> <pm> run build` - 本番ビルド
8. `docker-compose down` - コンテナ停止・削除

**パターンB: pnpm/Turborepo プロジェクト**（`pnpm-workspace.yaml` が存在する場合）
1. `pnpm lint` - ESLintチェック（定義されている場合）
2. `pnpm typecheck` - TypeScript型チェック（定義されている場合）
3. `pnpm test --filter=<affected-package>` - テスト実行
4. `pnpm build --filter=<affected-package>` - ビルド確認

**パターンC: npm/yarn プロジェクト**
1. `npm run lint` / `yarn lint` - Lintチェック
2. `npm run typecheck` / `yarn typecheck` - 型チェック
3. `npm test` / `yarn test` - テスト実行
4. `npm run build` / `yarn build` - ビルド確認

`package.json` の scripts を確認し、存在するコマンドのみ実行する。

#### 4.2 結果確認

- すべてpass: 「✅ テスト正常完了」と表示し、**即座にステップ5へ進んでください**
- 1つでも失敗: 処理を停止し、エラー内容を報告してください

**エラー時**: 処理を停止し、エラー内容を報告してください。

---

### ステップ5: コミット作成

コミットルールの詳細は `references/commit-rules.md` を参照。

#### 5.1 変更内容確認

Bashツールで以下を**並列実行**：
- `git status` - 変更ファイル一覧
- `git diff` - 変更差分
- `git log --oneline -5` - 最近のコミットメッセージ（スタイル参考）

#### 5.2 コミットメッセージ生成

Semantic Commit形式でメッセージを生成：
- `feat:` - 新機能追加
- `fix:` - バグ修正
- `docs:` - ドキュメント変更
- `style:` - コードスタイル変更
- `refactor:` - リファクタリング
- `test:` - テスト追加・修正
- `chore:` - ビルド・ツール設定変更

#### 5.3 コミット実行

**Atomic Commit原則**に従い、論理的単位でコミットを作成：

Bashツールで以下を実行：
```bash
git add <files>
git commit -m "<type>: <subject>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

複数の論理的変更がある場合は、それぞれ個別にコミットしてください。

#### 5.4 完了

コミット作成が完了したら、**即座にステップ6へ進んでください**。

**エラー時**: 処理を停止し、エラー内容を報告してください。

---

### ステップ6: PR作成

#### 6.1 リモートへpush

Bashツールで以下を実行：
```bash
git push -u origin <branch-name>
```

#### 6.2 変更内容確認

Bashツールで以下を**並列実行**：
- `git diff main...HEAD --name-only` - 変更ファイル一覧
- `git log main..HEAD --oneline` - コミット一覧

#### 6.3 UI変更のスクリーンショット取得（該当する場合のみ）

変更ファイルに UI 関連（`.tsx`, `.css`, `.html`, popup, content script 等）が含まれる場合：
- Playwright MCP（`mcp__playwright__browser_navigate` + `mcp__playwright__browser_take_screenshot`）で対象画面をキャプチャ
- キャプチャ取得できない場合はスキップし、PR 本文に「手動スクリーンショット添付推奨」と記載

#### 6.4 PR本文生成

PRテンプレートに従って本文を生成（詳細は `references/pr-template.md` を参照）：

```markdown
## 概要
[変更の目的と背景を簡潔に説明]

## 変更内容
- [変更点1]
- [変更点2]
...

## 変更理由
- [なぜこの変更が必要か]

## スクリーンショット
[UI変更がある場合のみ。キャプチャ画像またはchecklist]
- [ ] 手動スクリーンショット添付推奨（自動キャプチャ不可の場合）

## 関連リンク
- Notion要件: [引数がNotion URLの場合はここに記載]
- Claude Code SessionID: `${CLAUDE_SESSION_ID}`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

#### 6.5 PR作成

Bashツールで以下を実行：
```bash
gh pr create --title "<PR-title>" --body "<PR-body>"
```

PRタイトルは変更内容を簡潔に表現してください。

#### 6.6 Notionステータス更新

引数がNotion URLの場合、`mcp__notion__notion-update-page` でタスクのステータスを「In Review」に更新する。

#### 6.7 ユーザーアクションタスク起票

ステップ2.6で特定した「ユーザーアクション必要」項目がある場合、**Notionの Task DB にタスクとして起票**する。

**起票条件**: ユーザーアクション項目が1つ以上ある場合のみ実行。ない場合はスキップ。

**起票方法**:
1. ステップ1.3で取得済みのタスクページの `ancestor-path` から Task DB のデータソース URL（`collection://...`）を取得する
2. 同じくタスクページの `Project` プロパティから Project URL を取得する
3. `mcp__notion__notion-create-pages` で各アクション項目をタスク化し、同じ Project に紐づける

**タスク内容の書き方**:
- **タイトル**: 具体的なアクション名（例: 「GA4 プロパティ作成・クレデンシャル設定（拡張名）」）
- **本文**: 以下の構成で詳細手順を記載
  - `## 概要`: なぜこの作業が必要か（1-2行）
  - `## 前提`: 必要な前提知識や注意事項
  - `## 手順`: 番号付きのステップバイステップ手順（スクリーンショット不要だが、具体的なUI操作パスを記載）
  - `## 完了条件`: チェックリスト形式で完了基準を明示
- **status**: `Not started`

**タスク例**:
- クレデンシャル設定（GA4, Polar API等）→ 管理画面の操作手順 + `.env` 設定手順
- CWS 提出 → デベロッパーダッシュボードの操作手順
- 手動動作確認 → 拡張インストール手順 + 確認ポイントのチェックリスト

#### 6.8 Discord通知

PR作成が成功したら、Discord通知を送信：

Bashツールで以下を実行：
```bash
PR_URL="<gh pr createコマンドの出力URL>"
DISCORD_SCRIPT="~/.claude/skills/auto-workflow/scripts/discord-notify.sh"

if [ -x "$DISCORD_SCRIPT" ]; then
  "$DISCORD_SCRIPT" \
    "🎉 PR作成完了" \
    "プルリクエストが作成されました。レビューをお願いします！ ${PR_URL}" \
    5763719 || echo "⚠️ Discord通知の送信に失敗しました（処理は継続）"
else
  echo "⚠️ Discord通知スクリプトが見つかりません: $DISCORD_SCRIPT"
fi
```

**注意**: Discord通知の失敗は処理継続に影響しません。

#### 6.9 完了

Discord通知送信後、**即座にステップ7へ進んでください**。

**エラー時**: 処理を停止し、エラー内容を報告してください。

---

### ステップ7: 完了

作成されたPRのURLを以下の形式で報告：

```
🎉 自動ワークフロー完了

✅ ブランチ作成: <branch-name>
✅ 実装完了
✅ テスト: [実行 or スキップ]
✅ コミット作成: <commit-count>個
✅ PR作成: <PR-URL>
✅ Notionステータス: In Review [Notion URLの場合のみ]
✅ ユーザーアクションタスク: [起票数]件 [起票した場合のみ]
   - [タスク名1]: <Notion URL>
   - [タスク名2]: <Notion URL>

次のアクション：
- PR URLでレビュー依頼
- CIチェック結果を確認
- ユーザーアクションタスクを実施 [起票した場合のみ]
- レビュー後にマージ
```

---

## 注意事項

- **各ステップを明示的に進める**: 各ステップ完了後、必ず次のステップへ進んでください
- **自動進行**: ユーザーの入力を待たずに、すべてのステップを自動的に実行してください
- **エラー時は即座に停止**: エラーが発生した場合は処理を停止し、ユーザーに報告してください
