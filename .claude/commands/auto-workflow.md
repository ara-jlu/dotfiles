---
description: NotionタスクをブランチからPRまで完全自動実行
argument-hint: [notion-url or requirement text]
---

## ⚠️ 完全自動実行コマンド

このコマンドは**ユーザーの入力を待たずに全ステップを自動実行**します。
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

引数がNotion URLかテキストかを判定し、適切な方法でブランチ名を生成：

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

以下のドキュメントを読み込む：
- `.claude/project/local-setup.md`
- `.claude/project/testing-strategy.md`
- `~/.claude/docs/development/docker-workflow.md`
- `CLAUDE.md`

#### 2.2 環境確認

Bashツールで以下を確認：
- Supabase起動状態: `supabase status` で確認
- Docker起動状態: `docker ps` で確認

#### 2.3 要件分析

引数がテキストの場合はそのまま要件として使用し、2.4へ進む。

引数がNotion URLの場合：
1. `mcp__notion__notion-fetch` でタスクページを取得（ステップ1.3で取得済みなら再取得不要）
2. プロパティ「Notes」からplanタグ付きNotesページをすべて `mcp__notion__notion-fetch` で取得する（**主要な仕様書**として必ず確認）
3. Notes内容を主要な仕様、タスクページ本文を補足情報として統合する

planタグ付きNotesが無い場合は、**処理を停止してユーザーに要件を確認**してください。

**TodoWriteツールでタスク分解と計画を作成**してください。

#### 2.4 TDD実装

以下のサイクルで実装を進めてください：
1. テスト作成（推奨）
2. 実装
3. リファクタリング
4. Atomic Commit意識（論理的単位で分割可能な粒度を意識）
5. 最低限の動作確認

#### 2.5 実装完了報告

実装が完了したら、以下の形式で報告：

```
✅ 実装完了

## 実装内容
- [実装した内容の箇条書き]

## 変更ファイル
- [変更したファイルのリスト]
```

**⚠️ 重要**: 実装完了報告を出力したら、**即座にステップ3へ進んでください**。ここで停止しないでください。

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
- `app/nextjs/src/` 配下のファイル変更がある
- テストファイル（`.test.ts`, `.test.tsx`, `.spec.ts`, `.spec.tsx`）の変更がある
- TypeScript/JavaScriptファイル（`.ts`, `.tsx`, `.js`, `.jsx`）の変更がある

上記に該当しない場合は**テストスキップ**：
- 「コードファイルの変更がないため、テストをスキップします」と表示
- ステップ5へ進む

テスト実行が必要な場合は、**即座にステップ4へ進んでください**。

---

### ステップ4: テスト（条件付き）

**注意**: このステップはステップ3でテスト実行が必要と判断された場合のみ実行してください。

#### 4.1 準備

以下のドキュメントを読み込む：
- `~/.claude/docs/development/test-commands.md`
- `~/.claude/docs/development/docker-workflow.md`

#### 4.2 テスト実行

Bashツールで以下を**順次実行**し、すべてpassすることを確認：

1. `docker-compose build` - Dockerイメージをビルド
2. `docker-compose up -d` - コンテナをバックグラウンドで起動
3. `docker-compose exec nextjs npm run lint` - ESLintチェック
4. `docker-compose exec nextjs npm run typecheck` - TypeScript型チェック
5. `docker-compose exec nextjs npm run test` - ユニットテスト実行
6. `docker-compose exec nextjs npm run build` - Next.js本番ビルド
7. `docker-compose down` - コンテナ停止・削除

#### 4.3 結果確認

- すべてpass: 「✅ テスト正常完了」と表示し、**即座にステップ5へ進んでください**
- 1つでも失敗: 処理を停止し、エラー内容を報告してください

**エラー時**: 処理を停止し、エラー内容を報告してください。

---

### ステップ5: コミット作成

#### 5.1 準備

以下のドキュメントを読み込む：
- `~/.claude/docs/git/commit-format.md`
- `~/.claude/docs/git/atomic-commit.md`

#### 5.2 変更内容確認

Bashツールで以下を**並列実行**：
- `git status` - 変更ファイル一覧
- `git diff` - 変更差分
- `git log --oneline -5` - 最近のコミットメッセージ（スタイル参考）

#### 5.3 コミットメッセージ生成

Semantic Commit形式でメッセージを生成：
- `feat:` - 新機能追加
- `fix:` - バグ修正
- `docs:` - ドキュメント変更
- `style:` - コードスタイル変更
- `refactor:` - リファクタリング
- `test:` - テスト追加・修正
- `chore:` - ビルド・ツール設定変更

#### 5.4 コミット実行

**Atomic Commit原則**に従い、論理的単位でコミットを作成：

Bashツールで以下を実行：
```bash
git add <files>
git commit -m "<type>: <subject>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

複数の論理的変更がある場合は、それぞれ個別にコミットしてください。

#### 5.5 完了

コミット作成が完了したら、**即座にステップ6へ進んでください**。

**エラー時**: 処理を停止し、エラー内容を報告してください。

---

### ステップ6: PR作成

#### 6.1 準備

以下のドキュメントを読み込む：
- `~/.claude/docs/git/pull-request.md`

#### 6.2 リモートへpush

Bashツールで以下を実行：
```bash
git push -u origin <branch-name>
```

#### 6.3 変更内容確認

Bashツールで以下を**並列実行**：
- `git diff main...HEAD --name-only` - 変更ファイル一覧
- `git log main..HEAD --oneline` - コミット一覧

#### 6.3.5 Session ID取得

Bashツールで以下を実行し、session IDを取得してください：
```bash
cat << 'SCRIPT_END' | bash
SESSION_ID=$(ls -t ~/.claude/session-env 2>/dev/null | head -1)
if [ -z "$SESSION_ID" ]; then
  echo "N/A"
else
  echo "$SESSION_ID"
fi
SCRIPT_END
```

#### 6.4 PR本文生成

PRテンプレートに従って本文を生成：

```markdown
## 概要
[変更の目的と背景を簡潔に説明]

## 変更内容
- [変更点1]
- [変更点2]
...

## 変更理由
- [なぜこの変更が必要か]

## 関連リンク
- Notion要件: [引数がNotion URLの場合はここに記載]
- Claude Code SessionID: `<session-id>`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

#### 6.5 PR作成

Bashツールで以下を実行：
```bash
gh pr create --title "<PR-title>" --body "<PR-body>"
```

PRタイトルは変更内容を簡潔に表現してください。

#### 6.5.5 Notionステータス更新

引数がNotion URLの場合、`mcp__notion__notion-update-page` でタスクのステータスを「In Review」に更新する。

#### 6.6 Discord通知

PR作成が成功したら、Discord通知を送信：

Bashツールで以下を実行：
```bash
# 前のコマンドで取得したPR URLを変数に格納（例: https://github.com/user/repo/pull/123）
PR_URL="<gh pr createコマンドの出力URL>"

# Discord通知スクリプトのパス
DISCORD_SCRIPT="~/.claude/commands/discord-notify.sh"

# Discord通知を送信（エラーでも処理継続）
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

#### 6.7 完了

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

次のアクション：
- PR URLでレビュー依頼
- CIチェック結果を確認
- レビュー後にマージ
```

---

## 注意事項

- **各ステップを明示的に進める**: 各ステップ完了後、必ず次のステップへ進んでください
- **自動進行**: ユーザーの入力を待たずに、すべてのステップを自動的に実行してください
- **エラー時は即座に停止**: エラーが発生した場合は処理を停止し、ユーザーに報告してください
- **SlashCommandツール使用禁止**: このコマンド内では他のslashコマンドを呼び出さないでください
