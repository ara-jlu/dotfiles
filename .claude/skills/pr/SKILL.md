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
2. **UI変更のスクリーンショット取得**（該当する場合のみ）：
   変更ファイルに UI 関連（`.tsx`, `.css`, `.html`, popup, content script 等）が含まれる場合：
   - Playwright MCP（`mcp__playwright__browser_navigate` + `mcp__playwright__browser_take_screenshot`）で対象画面をキャプチャ
   - 拡張の場合: `pnpm dev --filter=<ext-name>` で起動後、`chrome-extension://<id>/popup.html` をキャプチャ
   - Web ページの場合: 該当ページをキャプチャ
   - キャプチャ取得できない場合はスキップし、PR 本文に「手動スクリーンショット添付推奨」と記載
   - 取得できた場合は PR 本文の「## スクリーンショット」セクションに画像を添付
3. PRテンプレートに従って本文を生成（詳細は `references/pr-guidelines.md` を参照）
4. 必要に応じて git push -u origin <branch-name>
5. gh pr create でPR作成

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

## スクリーンショット
[UI変更がある場合のみ。キャプチャ画像またはchecklist]
- [ ] 手動スクリーンショット添付推奨（自動キャプチャ不可の場合）

## 関連リンク
- Notion要件: [引数がNotion URLの場合はここに記載]
- Claude Code SessionID: `${CLAUDE_SESSION_ID}`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```
