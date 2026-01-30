# プルリクエスト（PR）ガイドライン

## PRテンプレート

```markdown
## 概要
この変更の目的と背景

## 変更内容
- 具体的な変更点をリスト形式で記載

## 変更理由
- なぜこの変更が必要なのか

## 関連リンク
- NotionページURL（例: https://notion.so/...）
```

## PR作成前のチェックリスト

### Docker環境でのテスト（必須）

```bash
docker-compose build
docker-compose up -d
docker-compose exec nextjs npm run lint
docker-compose exec nextjs npm run typecheck
docker-compose exec nextjs npm run test
docker-compose exec nextjs npm run build
docker-compose down
```

詳細: `~/.claude/docs/development/test-commands.md`

### Git規約の遵守

- [ ] Atomic Commitの原則に従っている
- [ ] Semantic Commit形式
- [ ] ブランチ名が命名規則に従っている

詳細: `~/.claude/docs/git/branch-naming.md`, `~/.claude/docs/git/commit-format.md`, `~/.claude/docs/git/atomic-commit.md`

### ブラウザ動作確認

```bash
docker-compose up
# http://localhost:3000 で確認
```

## レビュールール

- 少なくとも1名の承認が必要
- セルフマージ禁止
- すべてのCI/CDチェックが通過必須

## PR作成

```bash
git push origin feature/TASK-1-user-login
gh pr create --title "機能名" --body-file .github/pr_template.md
```

## マージ後

```bash
git checkout main
git pull origin main
git branch -d feature/TASK-1-user-login
```

## 参照

- テストコマンド: `~/.claude/docs/development/test-commands.md`
- Atomic Commit: `~/.claude/docs/git/atomic-commit.md`
- コミット形式: `~/.claude/docs/git/commit-format.md`
