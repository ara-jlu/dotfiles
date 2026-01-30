---
description: PRテンプレート形式に従いプルリクエストを作成
---

## 準備

以下のドキュメントを読み込んでください：
- `~/.claude/docs/git/pull-request.md`

## 実行

1. git status, git diff main...HEAD, git log でブランチの変更内容を確認
2. Bashツールで以下を実行し、session IDを取得：
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
3. PRテンプレートに従って本文を生成：
   - 概要（変更の目的と背景）
   - 変更内容（具体的な変更点リスト）
   - 変更理由（なぜ必要か）
   - 関連リンク（NotionページURL、Claude Code SessionID）
4. 必要に応じて git push
5. gh pr create でPR作成

ドキュメントのフォーマットに従ってPRを作成してください。
