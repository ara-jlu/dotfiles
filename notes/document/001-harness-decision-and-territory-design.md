---
ID: NOTE-3
title: superpowers+ECC構成の意思決定と棲み分け設計
tag: [document]
Project: devops
Task: 001-ai-harness
created_at: 2026-07-11
updated_at: 2026-07-11
---

# superpowers+ECC構成の意思決定と棲み分け設計

> Notion(INB-489)から移行。2026-07-11 時点の設計記録。以降の実装差分は as-built ドキュメント(`notes/document/001-harness-as-built-architecture.md`)を参照。

## 概要

AIコーディングハーネスの構成方針を検討し、**「superpowers（背骨）＋ ECC（専門ライブラリ）」の併用**を採用することを決定した。あわせて、両者のワークフローが競合しないための棲み分け設計と、記憶層（Joifupへの移行を前提とした永続化）の方針を整理した。本ドキュメントは一連の議論と結論をトピック別に再構成したもの。

> 前提スコープ: 開発だけでなく、マーケティング・営業・顧客対応・分析・スケジューリング等、事業・生活・人生の全域でClaudeを活用する。導入コストは判断基準に含めず、能力とカバレッジを優先。

---

## 1. ECCとは

**ECC = "the agent harness operating system"**。AIコーディングエージェントの性能を最適化するインフラ層（MITライセンスOSS）。Claude Codeを中心に複数ハーネスへ横断対応する。

- **Skills 278** … 主要ワークフロー面（旧slashコマンドを置換）
- **Agents 67** … 委譲用サブエージェント（planner / architect / 言語別reviewer 等）
- **Commands 94（legacy）** … 後方互換シム
- **Hooks / Rules** … イベント駆動の自動化と常時遵守ガイドライン（22言語）
- 特徴: クロスハーネス分離（`ECC_AGENT_DATA_HOME`）、Continuous Learning v2（instincts）、AgentShield連携

---

## 2. セキュリティの二層構造

### AgentShield（エージェント設定を守る）

AIエージェントの**設定ファイル自体**が攻撃面になるという前提で、それを審査する専用ツール。別リポジトリ（`affaan-m/agentshield`）・別npm（`ecc-agentshield`）。ECCからは `/security-scan` で起動。

- 対象: `CLAUDE.md` / `settings.json` / `mcp.json` / `hooks/` / `agents/*.md`
- `--opus` フラグで **Opus 3体（attacker / defender / auditor）の敵対的パイプライン**を実行し、パターンマッチではなく推論でリスクを洗い出す
- 出力: A〜F評価 / JSON / MD / HTML、クリティカル検出でexit code 2（CIゲート）

### アプリコード側セキュリティ（実コードを守る）

- `ecc:security-reviewer`（エージェント, OWASP Top 10軸）/ `security-review`（スキル, チェックリスト）
- `rules/*/security.md`（22言語の常時ルール）
- 言語別reviewer（21種）に組み込まれたセキュリティ観点
- ドメイン特化: `hipaa-compliance` / `defi-amm-security` / `django-security` 等

→ 「設定 → 汎用コード → 言語固有 → ドメイン固有」の多層防御。

---

## 3. 記憶・永続化層の設計（Notion → Joifup 移行前提）

自作のNotion連携スキル（plan2notion / research-note / log-note / doc-note）を、自作サービス **Joifup**（frontmatter付きmdをディレクトリ保存、`/workspace/joifup/` で開発中）へ移行する方針。

### 原則: 「計算」と「永続化」を分離する

自作スキルでECCを内部呼び出しする**ラッパー方式は非推奨**（wrapper regressionでECCの品質が劣化する）。代わりに横に並べて連結する。

- **Layer 1 計算**: ECC / superpowers（無改変）→ 成果物を作業ファイルに出力
- **Layer 2 永続化**: Joifupシンクスキル（宛先=ファイル）
- **Layer 3 連結**: オーケストレータがL1→L2を連結

> schema.yaml はJoifup側に既存ルールがあるため、こちらでは設計しない（読むだけ）。

### 記憶の三層（Memory Triad）

事業・生活を横断する「Life OS」の背骨は記憶。役割の異なる3つで固める。

| 種類 | 担当 | 性質 |
|---|---|---|
| 意図的な記録 | **Joifup**（md+frontmatter） | 人間所有の"正典"。可搬・grep可能。全ドメイン共通 |
| エピソード記憶 | **obra episodic-memory** | 全会話を自動アーカイブ→セマンティック検索。判断理由まで遡れる |
| 手続き記憶（本能） | **ECC instincts** | 繰り返しパターンを学習し挙動を最適化 |

---

## 4. 最終意思決定: superpowers ＋ ECC 併用

選択肢を比較した結果、**併用**を採用。

| 選択肢 | 判定 | 理由 |
|---|---|---|
| superpowers 一本 | ✗ | 開発方法論特化。マーケ・営業・顧客対応・分析・生活を**カバーしない** |
| ECC 一本 | ○（最シンプル） | 単体で全域＋独自ワークフロー＋instinctsを持つ。1メンタルモデルで完結 |
| **superpowers ＋ ECC** | **◎（採用）** | 進め方の規律はsuperpowersが最洗練、ECCは専門ライブラリに徹する。追加コストは"原則1文"のみ |

- **superpowers = 背骨（1つだけ）**: 計画→実行→検証の規律（brainstorming→plan→2段階レビュー、RED/GREEN、git worktree）。ファイルベースでJoifupと相性が良い
- **ECC = 専門ライブラリ**: 言語別reviewer / security / マーケ・営業・顧客対応・分析等のドメインスキル
- 記憶層に **obra episodic-memory** も併せて導入

---

## 5. 棲み分け設計（テリトリー別 OFF / KEEP）

**原則（守るべきはこの1文）**: 計画・実行・レビューの"進め方"＝superpowers。それ以外の"専門作業"＝ECC。

| テリトリー | 所有 | ECC: OFF（自動起動させない） | ECC: KEEP（専門として残す） |
|---|---|---|---|
| 計画・アイデア | superpowers | plan, plan-prd, plan-orchestrate, plan-canvas, multi-plan, prp-plan, prp-prd, council | code-explorer, architect（計画の入力） |
| 実行オーケストレーション | superpowers | feature-dev, orch-*, prp-implement, multi-workflow/execute/frontend/backend, gan-build/design, dynamic-workflow-mode, ralphinho-rfc-pipeline | （なし） |
| TDD | superpowers | tdd-workflow, tdd-guide | 言語別test（go-test, react-test, springboot-tdd 等） |
| レビュー・検証ゲート | superpowers | code-review, review-pr, orch-review, santa-loop/method, verification-loop, delivery-gate | 言語別reviewer全部, security-reviewer, security-scan, pr-test-analyzer, silent-failure-hunter, type-design-analyzer |
| Git / PR | 自作スキル | pr, prp-pr, git-workflow, github-ops, prp-commit | 自作 branch / commit / pr |
| 記憶・セッション | Joifup ＋ obra ＋ instincts | save-session, resume-session, sessions, continuous-learning(v1) | continuous-learning-v2, instinct-*, learn, learn-eval, evolve, recursive-decision-ledger, growth-log, architecture-decision-records |
| ビルド解決 | 競合なし | — | build-fix, react-build, go-build, rust-build 等（全KEEP） |
| ドメイン/事業 | 競合なし | — | marketing / seo / chief-of-staff / email-ops / lead-intelligence / dashboard-builder / knowledge-ops 等（全KEEP） |

> 微妙な分岐点: **エピソード記憶（会話）=obra、手続き記憶（本能）=ECC** と層で分ける。
> レビューは superpowers が「いつ」を仕切り、実体はECCの専門reviewerに委譲する。

---

## 6. 実装機構（set-once-forget）

ECCのプラグインスキルはdescription依存でモデルが自動起動する。プラグインファイルの書き換え（`disable-model-invocation`付与）は更新で上書きされるため非推奨。

**主: グローバル `CLAUDE.md` にルーティング"原則"を記載**。列挙式ではなく原則式にすることで、ECCが新スキルを追加してもドリフトせず、set-once-forgetが成立する。

```
- ワークフローの背骨は superpowers。計画→実行→レビューは superpowers を使う。
- ECCスキルは専門作業（言語レビュー/セキュリティ/マーケ/運用等）でのみ使用し、ワークフロー駆動には使わない。
- レビュー時は superpowers から ECC 言語別reviewer / security-reviewer を委譲呼び出しする。
- Git/PR は自作アダプタを使う。
- 記憶: 会話再生=obra episodic-memory / 本能=ECC instincts / 正典=Joifup。
```

**補**: 構造的に外したい場合はECCを選択インストールに切替え `orchestration` モジュールを除外（ただし二重管理になるため、まずはCLAUDE.md方針を推奨）。

---

## 7. 今後のビルド順（当時のTODO）

1. 記憶層を先に固める … Joifup（既存schema.yaml準拠）→ obra episodic-memory 導入 → ECC instincts 有効化
2. 背骨 … superpowers 導入、ECCを専門ライブラリとして接続
3. グローバル `CLAUDE.md` にルーティング原則を追記
4. ドメインを1つずつ有効化（顧客対応/開発から）。ディレクトリ別 CLAUDE.md でスコープ起動
5. コネクタ確認 … 既存MCP（Gmail/Calendar/Drive/GA/GSC）で不足するCRM/Slackを追加

---

## 補遺: 記憶の三層の位置づけと instincts の定義

> セクション3のMemory Triadを、instinctsの実装確認（ECC `continuous-learning-v2` を精読）を踏まえて明確化したもの。

### 三層の役割の違い（同じ「記憶」でも層が違う）

| 記憶 | 何を覚えるか | 例え |
|---|---|---|
| **Joifup**（md+frontmatter） | あなたが選んだ**正典** | 意図して書いたノート |
| **episodic-memory**（obra） | **過去会話そのもの**（何が起きたか）を検索 | 「Xの時どうやったっけ」を議事録から引く |
| **instincts**（ECC） | **蒸留された挙動ルール**（どう振る舞うべきか）＋確信度 | 「自分はこう書く癖がある」を自動適用 |

**要点**: episodic = 出来事の再生（生ログ）、instincts = そこから抽出した習慣（行動則）。層が違うので両方入れる価値がある。

### instincts とは（ECC Continuous Learning v2.1）

セッションから自動抽出される「小さな学習済み挙動」の最小単位。原子的なルール＋確信度スコアで表現。

1つのinstinctの形:

```yaml
id: prefer-functional-style
trigger: "when writing new functions"   # いつ発火するか
confidence: 0.7                          # 確信度 0.3〜0.9
domain: "code-style"
scope: project                           # project or global
## Action: Use functional patterns over classes when appropriate.
## Evidence: Observed 5 instances of functional pattern preference
```

仕組み:

1. **観測** — `PreToolUse` / `PostToolUse` フックが操作を監視
2. **分析** — バックグラウンドの Haiku エージェントがパターン抽出（メイン会話を邪魔しない）
3. **確信度** — 繰り返すほど confidence が上がる（0.3→0.9）
4. **進化** — instinct → クラスタ化 → skill / command / agent へ昇格（`evolve`）
5. **スコープ** — 既定はプロジェクト単位で隔離。2プロジェクト以上で出たら global へ `promote`
6. **保存先** — `${XDG_DATA_HOME:-~/.local/share}/ecc-homunculus/projects/<hash>/`

操作コマンド: `instinct-status` / `evolve` / `export` / `import` / `promote` / `projects` / `prune`（30日放置を削除）

> instincts はフック経由で**自動的に裏で動く**ため、普段は意識せず蓄積される。状態確認は `/ecc:instinct-status`。

## 参照元（Web調査）

- obra/superpowers, obra/superpowers-marketplace, obra/episodic-memory, obra/private-journal-mcp (GitHub)
- Superpowers / episodic-memory 解説 (blog.fsck.com)
- Best Claude Code Plugins 2026 (buildtolaunch) / Claude Cowork Plugins Complete Guide
- ECCローカルチェックアウト: `~/.claude/plugins/marketplaces/ecc`（Skills 278 / Commands 94 / Agents 67 実測）
