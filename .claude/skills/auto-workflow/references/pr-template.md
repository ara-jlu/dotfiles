# PRテンプレート

## テンプレート

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
[UI変更がある場合のみ]
- [ ] 手動スクリーンショット添付推奨（自動キャプチャ不可の場合）

## 関連リンク
- Notion要件: [Notion URLがある場合]
- Claude Code SessionID: `<session-id>`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## PR作成前のチェックリスト

### Git規約の遵守

- [ ] Atomic Commitの原則に従っている
- [ ] Semantic Commit形式
- [ ] ブランチ名が命名規則に従っている

### テスト

- [ ] lint, typecheck, test, build が全pass

## レビュールール

- 少なくとも1名の承認が必要
- セルフマージ禁止
- すべてのCI/CDチェックが通過必須
