---
description: Notion URLまたは要件テキストに基づいてTDDで機能を実装
argument-hint: [notion-url or requirement text]
---

## 準備

実装前に以下のドキュメントを読み込んでください：
- `.claude/project/local-setup.md`
- `.claude/project/testing-strategy.md`
- `~/.claude/docs/development/docker-workflow.md`
- `CLAUDE.md`

## 実装フロー

1. **環境確認**: Supabase、Docker起動状態を確認
2. **要件分析**: TodoWriteツールでタスク分解と計画
3. **TDD実装**: テスト → 実装 → リファクタリング（推奨）
4. **Atomic Commit意識**: 論理的単位でコミット可能な粒度を意識
5. **最低限動作確認**: 実装後、動作確認してから次へ
6. **完了報告**: 実装内容の概要を報告

## 完了後

実装が完了したら、以下の形式で報告してください：

```
✅ 実装完了

## 実装内容
- [実装した内容の箇条書き]

## 変更ファイル
- [変更したファイルのリスト]

---
**注意**: この後、テストやコミット作成が必要な場合があります。
`/auto-workflow` から呼ばれた場合は、自動的に次のステップに進みます。
```
