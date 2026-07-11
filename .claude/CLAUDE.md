# Development Rules

## ハーネス構成

- **背骨 = superpowers**（進め方の規律）
- **専門作業 = ECC**（言語レビュー・セキュリティ・ビルド・事業ドメイン）
- **記憶 = Joifup（正典）/ episodic-memory（会話）/ ECC instincts（本能）**

原則: 「計算（superpowers）」と「永続化・連携（自作アダプタ / Joifup）」を分離する。superpowers は無改変で使い、入口・出口にアダプタを配線する。

## 進め方の背骨 = superpowers

- 計画・実行・レビューの"進め方"は superpowers を使う:
  `brainstorming`（設計・HARD-GATE: 設計承認まで実装禁止）→ `writing-plans` → `subagent-driven-development` → `finishing-a-development-branch`。
- **ECC のワークフロー駆動系スキルは背骨に使わない**（＝自動起動しない。明示指定時のみ可）。
  該当例: plan系 / orch-* / feature-dev / multi-* / gan-* / tdd-workflow / 汎用レビュー駆動（code-review・review-pr・orch-review・santa-loop・verification-loop）/ git系（pr・git-workflow・github-ops・prp-*）/ セッション記憶（save/resume-session・continuous-learning v1）。
- 新しい類似スキルが増えても「**ワークフロー駆動系は背骨に使わない**」の原則で判断する（列挙は例示。原則が優先）。

## 専門作業 = ECC

- 言語別 reviewer / security / build-fix 系 / ドメイン（マーケ・営業・顧客対応・分析等）は ECC を使う。
- ECC の専門 agent は superpowers から `agentType` 指定で dispatch して委譲する。

## レビュー統合（superpowers × ECC）

- **Spec準拠 = superpowers task-reviewer**（plan/brief に紐づく判定。ECC には無い）。
- **コード品質・セキュリティ = ECC 言語別 reviewer**（言語イディオム・フレームワーク固有の罠・OWASP）。
- **最終 whole-branch レビュー**（SDD が全タスク後に自動 dispatch）で、変更言語に対応する `ecc:<lang>-reviewer` を `agentType` 指定で dispatch。review-package の diff を渡し、diff 集中を指示する（コードベースを漁らせない）。
- 差分が auth / 入力 / 秘密 / API / 機微データに触れる場合は `ecc:security-reviewer` も dispatch。
- **タスク毎レビュー**は superpowers task-reviewer を維持し、上記セキュリティ該当タスクのみ `ecc:security-reviewer` を追加。
- Critical / Important はどの reviewer 由来でもブロッキング。修正は superpowers の fix-dispatch ループに合流。
- 言語→reviewer: `.ts/.js`→typescript / `.tsx/.jsx`→typescript + react / `.vue`→vue / `.py`→python（+ django/fastapi 検出時）/ `.go/.rs/.java/.kt/.swift/.cs/.php/.cpp`→各言語 / `.dart`→flutter / SQL・migrations→database。

## 記憶

- 会話再生 = obra `episodic-memory`（セマンティック検索）
- 本能 = ECC `instincts`（continuous-learning-v2。フックで自動蓄積）
- 正典 = Joifup（意図的な記録）

## 言語

- **コミットメッセージ: 英語**（superpowers native・注入しない）
- **PR本文: 日本語**（diff から生成。commit 言語と独立）
- ブランチ名・コード: 英語
- 原則: **機械が扱う面 = 英語、人が読む面 = 日本語**（人が読む面 = PR本文・Discord・Joifup の doc/plan/log 本文・brainstorm 対話）

## Git

- Strategy: GitHub Flow（main が常にデプロイ可能）
- Commit: Semantic Commit 形式（英語）。Atomic Commit（1 commit = 1 logical change）
- Branch: superpowers 準拠命名 ＋ **Joifup タスクのファイル名 id を注入**（例: `feature/001-slug`。TASK-id = tasks/ のファイル名 id。daemon の `ID: TASK-N` とは**別物で一致せず**、関係・ブランチ・`--task` には使わない。type 分類は superpowers に委ねる）
- Worktree: superpowers `using-git-worktrees`（`.worktrees/` に隔離）

## Quality

- TDD: superpowers の RED → GREEN（各タスクにテスト埋込）を背骨とする
- レビュー: 上記「レビュー統合」に従う
- 独立した Lint/TypeCheck/Test/Build ゲートは撤廃（問題が出たら再検討）

## 記録先（Joifup）

- 記録は Joifup（repo 内 md + frontmatter）。設計・計画・ログ・調査を Task / Notes 相当で管理する。
- **スキーマの正典** = `.joifup/databases/<id>/schema.yaml`（repo 内）または `~/.joifup/databases/<id>/schema.yaml`（global）。
- frontmatter・tag・status・リレーションの仕様はこのスキーマを参照する。**ハードコードせず、スキル側でスキーマを読む**。
- 概念対応: superpowers の spec = 仕様書 / plan = 実装計画 / 進捗 = Task status。実際のタグ名・値・status はスキーマに従う。
