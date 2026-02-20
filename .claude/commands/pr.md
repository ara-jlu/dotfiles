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
3. **UI変更のスクリーンショット取得**（該当する場合のみ）：
   変更ファイルに UI 関連（`.tsx`, `.css`, `.html`, popup, content script 等）が含まれる場合：
   - Playwright MCP（`mcp__playwright__browser_navigate` + `mcp__playwright__browser_take_screenshot`）で対象画面をキャプチャ
   - 拡張の場合: `pnpm dev --filter=<ext-name>` で起動後、`chrome-extension://<id>/popup.html` をキャプチャ
   - Web ページの場合: 該当ページをキャプチャ
   - キャプチャ取得できない場合（拡張の Popup 等でブラウザロード不可）はスキップし、PR 本文に「手動スクリーンショット添付推奨」と記載
   - 取得できた場合は PR 本文の「## スクリーンショット」セクションに画像を添付
4. PRテンプレートに従って本文を生成：
   - 概要（変更の目的と背景）
   - 変更内容（具体的な変更点リスト）
   - 変更理由（なぜ必要か）
   - スクリーンショット（UI 変更がある場合）
   - 関連リンク（NotionページURL、Claude Code SessionID）
5. 必要に応じて git push
6. gh pr create でPR作成

ドキュメントのフォーマットに従ってPRを作成してください。
