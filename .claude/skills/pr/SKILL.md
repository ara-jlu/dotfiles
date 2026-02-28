---
description: PR作成・プルリクエスト作成時に使用。日本語テンプレートに従いPRを作成する
user-invocable: true
---

# 動的コンテキスト

コミット一覧:
```
!`git log main..HEAD --oneline`
```

変更統計:
```
!`git diff main...HEAD --stat`
```

## 実行

1. git status, git diff main...HEAD, git log でブランチの変更内容を確認
2. PRテンプレートに従って本文を生成（詳細は `references/pr-guidelines.md` を参照）
3. 必要に応じて git push -u origin <branch-name>
4. gh pr create でPR作成

## PRテンプレート

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
- Claude Code SessionID: `${CLAUDE_SESSION_ID}`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```
