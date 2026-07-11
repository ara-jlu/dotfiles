---
ID: NOTE-2
title: AIハーネス as-built アーキテクチャとスキルカタログ
tag: [document]
Project: devops
Task: 001-ai-harness
created_at: 2026-07-11
updated_at: 2026-07-11
---

# AIハーネス as-built アーキテクチャとスキルカタログ

> 設計2ドキュメント(意思決定・棲み分け / 開発フロー再設計)の**実装後の確定状態**。設計時からの差分もここに集約する。2026-07-11 実装。

## 全体像

```
背骨(計算)   = superpowers   … brainstorming → writing-plans → subagent-driven-development → finishing
専門(委譲)   = ECC           … 言語別reviewer / security / build-fix / 事業ドメイン(agentType でdispatch)
記憶(永続)   = Joifup(正典) / episodic-memory(会話) / ECC instincts(本能)
接着(自作)   = md2joifup(永続化) / j-devflow(配線) / j-finish・j-pr(出口) / j-doc・j-log・j-research(記録)
```

原則: **計算(superpowers 無改変)と 永続化・連携(自作アダプタ / Joifup)を分離**。superpowers は触らず、入口・出口にアダプタを配線する(ラッパー化しない)。

## スキルカタログ(自作アダプタ)

| スキル | 種別 | 役割 | 起動 |
|---|---|---|---|
| `md2joifup` | 永続化プリミティブ(script) | markdown → Joifup Notes 行(frontmatter付与・house-style・リネーム)。全ノート系が使う共有バックエンド | 内部(他スキルから) |
| `j-devflow` | オーケストレータ(手順) | idea→merge を3セッションで配線する薄いシーケンサ | user |
| `j-finish` | 出口アダプタ(script) | 実装後の pre-approval finish: PR / status→In Review / 承認待ちTask起票 / Discord | フロー内/明示 |
| `j-pr` | 出口アダプタ(手順) | ad-hoc 開発の house-style 日本語PRのみ(副作用なし) | user |
| `j-doc` | 記録(手順) | 既存Notesを統合したドキュメント。code/arch系は ecc:code-explorer で根拠付け | user |
| `j-log` | 記録(手順) | セッションの詳細作業記録。判断理由を instincts が学べる粒度で | user |
| `j-research` | 記録(手順) | 技術調査・比較。Context7(ecc:docs-lookup)+WebSearch で最新ドキュメント根拠付け | user |

配置: `~/.claude/skills/`(= `dotfiles/.claude/skills/` symlink)。`md2joifup` は Python + pyyaml。

## 3セッション開発フロー(j-devflow)

- **Session A(計画・対話)**: Task確認/作成 → ブランチ(superpowers命名+TASK-id注入) → `brainstorming`(HARD-GATE:設計承認まで実装禁止) → `md2joifup` で spec を `notes/document/` → `writing-plans` → `md2joifup` で plan を `notes/plan/`。**plan ノートが handoff 成果物。ここでSession A終了**。
- **Session B(実装・自律)**: plan を読み `subagent-driven-development`(タスク毎 fresh subagent + task-reviewer、英語 atomic commit)。セキュリティ該当タスクは `ecc:security-reviewer` 追加。全タスク後に whole-branch review 自動dispatch → 変更言語の `ecc:<lang>-reviewer` 注入。`verification-before-completion` → `j-finish`(PR/status→In Review/起票/Discord)。**機械はここで停止**。
- **Session C(承認・人間)**: レビュー → OKなら status→Done + `chore(joifup): approve <task-id>`(英語) + マージ。**何も自動マージしない**。

自律ラン時のガード: 設計ゲート / fix-loop終了(未解決Critical/Importantなし) / 外部可視操作(PR/Discord)前 / マージ境界。

壁打ち(brainstorming)は対話なのでサブエージェント化不可。オーケストレータは指示注入・出力整形をせず順序付けのみ(ラッパー回帰の回避)。

## 言語・Git 規約

- コミット=**英語**(Semantic Commit・Atomic・superpowers native、注入しない) / PR本文=**日本語** / ブランチ・コード=英語。原則「機械が扱う面=英語、人が読む面=日本語」。
- PR本文規約は `~/.claude/skills/j-pr/references/pr-body.md` が単一の真実。`j-pr`(ad-hoc)と `j-finish`(フル)が共有。
- GitHub Flow。ブランチ=superpowers命名+TASK-id注入のみ。worktree は `.worktrees/`。

## レビュー統合(superpowers × ECC)

- Spec準拠 = superpowers task-reviewer(plan/briefに紐づく。ECCには無い)。
- コード品質・セキュリティ = ECC 言語別reviewer(イディオム・フレームワーク固有・OWASP)。
- 最終 whole-branch(SDD自動dispatch)で `ecc:<lang>-reviewer` を agentType 注入、review-package の diff を渡し diff集中を指示。auth/入力/秘密/API/機微データ差分は `ecc:security-reviewer` も。
- タスク毎はセキュリティ該当タスクのみ security-reviewer 追加。Critical/Important はどの由来でもブロッキング、fix-dispatch ループに合流。
- 非侵襲: superpowers ファイルは無改変。差し込みは CLAUDE.md ルーティング規則のみ。

## Joifup house-style(md2joifup が保証)

実 Joifup データ(joifup repo)から確定した frontmatter 規約:

- 配列は **flow**(`tag: [log]`、`Notes: [a, b]`)。関係は **値の個数**で分岐(単一→スカラー `Project: joifup` / 複数→flow配列)。← schema の multiple 基準ではなく実データの個数基準。
- `created_at`/`updated_at` は**当日日付でスタンプ**(source に既存なら保持)。auto は `ID` のみ daemon 管理。
- **title** は H1 をミラー(source:h1 でも daemon が保存時ミラーするため)。body の H1 も残す。
- **Project は必ず解決**: 明示 `--project` > 紐づくTaskから継承 > `projects/` の唯一のProject fallback。
- ファイル名 `NNN-slug.md`: NNN=紐づくTaskのid数値、無ければdir次番。**日本語タイトルは slug が劣化するので `--slug`/`--new-task-slug` に英語slugを明示**。
- schema.yaml は Joifup が正典。スキル側は `.joifup/databases/<id>/schema.yaml`(repo)or `~/.joifup/...`(global)を**読むだけ**、ハードコードしない。

## Task 解決ポリシー(ノート系)

文脈依存: j-log/j-doc は既定で**現ブランチのTASK-idにリンク**(タスク作業のキリで残す)。j-research は既定で**新規Task起票**(`--new-task`、別調査になりがち)。明示引数で上書き。ブランチ→TASK-id 抽出は LLM が `git rev-parse` で解決し `--task` に渡す(スクリプトに `--from-branch` は持たせない=判断はSKILL.md、副作用のみスクリプト)。

## 設計時からの主な差分(as-built)

| 設計時 | 実装後 | 理由 |
|---|---|---|
| `sp2joifup` | **`md2joifup`** に改名 | superpowers専用でなく「markdown→Joifupノート」汎用永続化のため |
| (未定)アダプタ発火 | **`j-devflow`** 薄いオーケストレータ | hook でなくシーケンサ手順スキル |
| 変換ツールは node 想定 | **Python + pyyaml** | js-yaml 不在、外部npm依存は脆い、pyyaml常備 |
| ブランチ検出をツールに | **LLMが解決し `--task`** | 判断はSKILL.md、副作用のみスクリプト |
| ad-hoc PR は旧 pr | **`j-pr` 新設**(規約を j-finish と共有) | 旧pr は Notion依存。単一の真実化 |
| doc/log/research-note(Notion) | **j-doc/j-log/j-research**(Joifup・ECC強化) | standalone移行 |
| Notion Task(TASK-638) | Joifup Task `001-ai-harness`(Project devops) | 本 repo を Joifup ワークスペース化 |

## 環境・運用メモ

- `ECC_GATEGUARD: "off"`(fact-forcingの反復ブロック回避。自律ラン再開時に再検討) / `ECC_CONTEXT_MONITOR_COST_WARNINGS: "false"`(コスト表示はサブスク課金でなく推定)。`.claude/settings.json` は gitignore(secrets)。
- skill作成は superpowers:writing-skills(RED→GREEN)。ECCのskill-createは git履歴ベースで用途違い、skill-creatorは削除。
- 保留(段階移行): 旧 Notion スキル(auto-workflow/branch/plan2notion 等)は、新スキルの複数回試用で問題なし + Joifup daemon の横断インデックス確認ができてから削除。
