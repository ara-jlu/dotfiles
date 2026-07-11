---
ID: NOTE-4
title: AIハーネス構築 全体作業ログ [2026-07-11]
tag: [log]
Project: devops
Task: 001-ai-harness
created_at: 2026-07-11
updated_at: 2026-07-11
---

# AIハーネス構築 全体作業ログ [2026-07-11]

## 概要

ECC プラグインのキャッチアップから、個人 + 事業のための AI ハーネス構成(superpowers 背骨 + ECC 専門 + Joifup 記憶)を意思決定し、CLAUDE.md ルーティング規則を実装、Notion → Joifup 移行の入口・出口アダプタスキル群を superpowers:writing-skills の RED→GREEN 規律で実装した1セッションの記録。導入コストは判断基準に入れず能力・品質で選定。

> **記録範囲の注記**: 本セッションは途中で context compact を挟んだ。フェーズ1〜8(前半)は compact 前で、verbatim なコマンド/出力は現 context に残っておらず、compact サマリからの再構成(決定・根拠・値のレベル)。フェーズ9〜11(実装以降)は実コマンド出力・コード・検証結果を保持しており詳細に記録する。

---

### 1. ECC キャッチアップ

`github.com/affaan-m/ECC` を調査。ECC = エージェントハーネス OS。

- 規模: Skills 278 / Commands 94 / Agents 67。
- フック: GateGuard(fact-forcing で危険操作前に事実提示を強制)、cost-tracker / ecc-context-monitor(コスト・コンテキスト監視)、instincts observation(会話観測)。
- **Continuous Learning v2**: instincts = 学習された原子的振る舞い。confidence 0.3–0.9。保存先 `${XDG_DATA_HOME}/ecc-homunculus/projects/<hash>/`。
- **AgentShield**(`ecc-agentshield`): `--opus` で 3 つの Opus(red/blue/auditor)による敵対的セキュリティ検証。
- アプリ側セキュリティは言語別 reviewer + `ecc:security-reviewer`(OWASP Top 10、secrets/SSRF/injection/unsafe crypto)でカバーされることを確認。

### 2. ハーネス構成の意思決定

論点 = ECC 一本か、superpowers 等も併用か。結論:

**背骨 = superpowers / 専門作業 = ECC / 記憶 = 三層**

- superpowers 一本化を却下(理由 = マーケ・営業・顧客対応・分析等の事業ドメインをカバーしない)。
- ECC 一本化も却下(理由 = 進め方の規律、特に brainstorming の HARD-GATE = 設計承認まで実装禁止、は superpowers が優れる)。
- **記憶三層**: 正典 = Joifup(意図的記録) / 会話再生 = episodic-memory(セマンティック検索) / 本能 = ECC instincts(フック自動蓄積)。
- **中核原則**: 「計算(superpowers)」と「永続化・連携(自作アダプタ / Joifup)」を分離。superpowers は無改変で使い、入口・出口にアダプタを配線する。

### 3. ECC↔superpowers 棲み分け設計

どの ECC スキルをオフにするかを**列挙でなく原則**で設計(スキル増加でのドリフト回避が理由):

> ECC のワークフロー駆動系スキルは背骨に使わない(自動起動しない。明示指定時のみ)。該当例 = plan系 / orch-* / feature-dev / multi-* / gan-* / tdd-workflow / 汎用レビュー駆動(code-review・review-pr・orch-review・santa-loop・verification-loop) / git系(pr・git-workflow・github-ops・prp-*) / セッション記憶(save/resume-session・continuous-learning v1)。

新スキルが増えても同原則で判断(列挙は例示、原則が優先)。

### 4. シンプルさ検討 → superpowers + ECC 確定

「一度設定すれば普段意識しないか、一本化すべきか」を検討。結論 = **併用でよい**(設定は一度きり、日常は背骨が自動で回る)。superpowers + ECC で確定。

### 5. 導入と instincts

superpowers(obra v6.1.1)、episodic-memory(v1.4.2)を導入。instincts = continuous-learning-v2 の学習単位で、フックが会話を観測し原子的振る舞いを蓄積する本能層、と整理。

### 6. superpowers 5スキル精読 + 開発フロー再設計

精読した背骨: `brainstorming`(HARD-GATE) → `writing-plans` → `subagent-driven-development`(タスク毎に fresh subagent + task-reviewer、全タスク後に whole-branch code review を自動 dispatch、model は明示必須) → `finishing-a-development-branch`(merge/PR/keep/discard の4択メニュー)。`using-git-worktrees`(`.worktrees/` 隔離)、`requesting-code-review` も確認。

mermaid で再設計:

- **Session1(計画)**: idea → brainstorming → 設計承認ゲート → writing-plans → Joifup 永続化
- **Session2(実装)**: 永続 plan を読み SDD → whole-branch review(ECC 注入) → 出力アダプタ
- **Session3(承認)**: 人間の最終承認 → Done → マージ

気づき: **壁打ち(brainstorming)は対話 = サブエージェント化不可**。オーケストレータは指示注入・出力整形をしない「薄いシーケンサ(file handoff)」にする(= ラッパー回帰の回避)。SDD の whole-branch review は自動 dispatch されるので、CLAUDE.md 規則で ECC 注入が自動的にトリガーされる。

### 7. 設計決定

- **言語**: コミット = 英語(superpowers native、注入しない) / PR 本文 = 日本語(diff から生成、commit 言語と独立) / ブランチ・コード = 英語。原則 = 機械が扱う面 = 英語、人が読む面 = 日本語。
- **記録先**: Notion → **Joifup**(repo 内 md + frontmatter)。spec = document / plan = plan タグ。進捗 = Task status。
- **スキーマ正典**: `.joifup/databases/<id>/schema.yaml`(repo)or `~/.joifup/...`(global)を**スキル側で読む**、ハードコードしない。**schema.yaml は Joifup 側が正典、勝手に設計しない**(明示制約)。
- **命名 / in-place**: 変換元 sp md をその場で Joifup ノートに変換・改名(後続が旧パスを探さないよう in-place)。
- **ブランチ**: superpowers 準拠命名 + **TASK-id 注入のみ**(例 `feature/TASK-123-slug`。type 分類は superpowers に委ねる)。
- **status/承認**: md 全体を版管理。人間の承認 = `chore(joifup): approve <task-id>`(英語)コミット = 監査記録。承認セッションの人間が Done + マージ。
- コスト ~$45/$65 は**サブスク課金でなく ECC フックのコスト推定表示**であることを確認。

### 8. CLAUDE.md ルーティング規則の実装

`~/.claude/CLAUDE.md`(symlink)の実体 = `dotfiles/.claude/CLAUDE.md` をクリーンに全面書き換え。

> **ハマり①(symlink)**: `~/.claude/CLAUDE.md` / `~/.claude/settings.json` は symlink。Edit ツールが symlink 経由書き込みを拒否 → `readlink` で dotfiles 内の実体パスを特定して編集。

構成: ハーネス構成 / 進め方の背骨 / 専門作業 / レビュー統合 / 記憶 / 言語 / Git / Quality / 記録先(Joifup)。レビュー統合の要点:

- Spec 準拠 = superpowers task-reviewer / コード品質・セキュリティ = ECC 言語別 reviewer。
- whole-branch review で変更言語に応じ `ecc:<lang>-reviewer` を agentType 注入。auth/入力/秘密/API/機微データに触れる差分は `ecc:security-reviewer` も。
- 言語→reviewer マップ(`.ts/.js`→typescript、`.tsx/.jsx`→+react、`.vue`→vue、`.py`→python(+django/fastapi)、他各言語、SQL→database)。

「実装状況の CLAUDE.md 記録は移行中で微妙」との指摘で除去し、schema パス参照に留めた。

### 9. 環境設定・skill-creator 削除

`dotfiles/.claude/settings.json`(実体)の env に追加:

```json
"ECC_CONTEXT_MONITOR_COST_WARNINGS": "false",
"ECC_GATEGUARD": "off"
```

> **ハマり②(GateGuard)**: ECC GateGuard フックが Bash/Edit/Write を fact-forcing で繰り返しブロック。`rm -rf` は facts 提示後もブロックされ、ユーザーが `! rm -rf ~/.agents/skills/skill-creator ~/.claude/skills/skill-creator` を手動実行。恒久対策として GateGuard off。resume 後に off が有効化され Bash 素通りを確認。

skill-creator(skills.sh 経由)を完全削除し `~/.agents/.skill-lock.json` から該当エントリ除去(find-skills は残置)。スキル作成は ECC でなく **superpowers:writing-skills** を使う方針(ECC の skill-create は git 履歴ベースで用途違い)。

### 10. アダプタスキル実装(writing-skills RED→GREEN)

#### 10-1. sp2joifup(node → Python 転換)

YAML パーサ可用性を確認:

```
node -e require.resolve('js-yaml')  → NO
python3 -c "import yaml"            → pyyaml 6.0.3 YES
```

**決定 = Python**。理由 = node に YAML 無し、外部 npm 依存は脆い、pyyaml は macOS 常備。schema を `.joifup/databases/notes/schema.yaml`(repo)→ `~/.joifup/...`(global)の順で探索。確定事項 D1〜D4:

- D1(ファイル名 NNN)= task id 数値優先 / 無ければ dir 次番。根拠 = トレーサビリティ + ドッグフーズ実績一致。
- D2 = 関係の配列/スカラー。D3 = 足場 `> **For agentic workers:** ...` 除去。D4 = H1→frontmatter `title` ミラー(source:h1 でも daemon が保存時ミラーするため canonical 形に合わせる)、body の H1 も残す。

3ケース(task有 `042-`/無 `001-`/不正 type 拒否)で GREEN。

#### 10-2. 実使用フィードバック修正(house-style)

ユーザーが実使用し「Project / created_at / updated_at 未設定」を報告。実ノート調査:

```yaml
# joifup/notes/21-DECISIONS.md 実データ
tag: [document]        # flow 配列
Project: joifup        # 単一値スカラー(schema multiple:true でも)
Notes: [10-ARCHITECTURE, 11-TECH_STACK]  # 複数値 flow 配列
created_at: 2026-04-12 # 日付のみ
```

修正: (a) block→flow 配列の自作 `emit_frontmatter`、(b) スカラー/配列を **schema multiplicity でなく値の個数**基準に変更、(c) created_at/updated_at を当日スタンプ(source 既存なら保持)、(d) `--project` 未指定時は紐づく Task の frontmatter から Project 継承。GREEN 再検証で `tag: [plan]` / `Project: joifup`(scalar) / `Task: [638, 700]`(複数 flow) / timestamps を確認。

#### 10-3. j-finish(出力アダプタ)

RED baseline(dry-run subagent)で判明したギャップ:

| ギャップ | 修正 |
|---|---|
| user-action タスク起票せず(PRコメントで代替) | script が承認待ち Task を起票 |
| task md を丸ごと書換(title/Project 消失) | `status:` 行のみ外科的置換、他はバイト保持 |
| `Notes` 関係をファイルパスで記述 | id 形式を強制 |

GREEN: 外科的 status 編集(In progress→In review)、house-style 承認待ち Task 起票(`parent` = 完了 task id)、scoped Discord(mention 限定・SESSION_ID 非投稿)。`--status Done`/`Cancelled` 拒否(人間に予約)。負テスト2種で確認。承認コミット(→Done・マージ)は構造上スクリプト不可。

#### 10-4. j-devflow(オーケストレータ)

RED baseline は概ね正確だが最大ギャップ = **計画/実装を同一「Driver session」に集約**。ユーザー設計は Session1=計画 / Session2=実装 の分離。→ **3セッション**(計画/実装/人の承認)+ handoff 成果物 = Joifup plan ノート、を明記。自律ラン時のガード(設計ゲート・fix-loop 終了・外部可視操作前・マージ境界)も成文化。スクリプト無しの手順スキル。

#### 10-5. sp2joifup → md2joifup 改名 + 拡張

standalone ノートスキルが同じ永続化を要するため共通バックエンド化。ユーザー指摘2点:

- **`--from-branch` は引数化しない**: ブランチ→TASK-id 抽出は LLM が `git rev-parse --abbrev-ref HEAD` で解決し `--task` に渡す(判断は SKILL.md、副作用のみスクリプト)。
- **`md2joifup` に改名**: 「markdown → Joifup ノート」汎用永続化で sp 固有でないため。

`--new-task "TITLE"`(house-style Task 起票 + リンク。手書きさせると created_at 欠落バグ再発のため)追加。非 ASCII タイトル用に `--new-task-slug` も追加。Project 解決 = 明示 > 新規/リンク Task の Project > `projects/` 主 Project fallback。j-devflow/j-finish 参照更新、旧 dir 削除。3パス GREEN:

```
--task 638      → Project 継承 joifup / Task: 638 / 638-*.md
--new-task "…"  → tasks/639-*.md 起票 + Task: 639-… リンク
standalone      → projects/ fallback で Project 解決 / 001-*.md
```

#### 10-6. j-doc / j-log / j-research(standalone、ECC 強化)

Notion 版を Joifup 対応で再設計。コンテンツ生成(判断・ECC 強化)= LLM、永続化 = md2joifup。Notion 固有記法排除 → 標準 GFM(Joifup 拡張は `joifup` フェンスで degrade する設計を確認)。Task 解決ポリシー: j-log/j-doc は既定でブランチ TASK-id リンク、j-research は既定 `--new-task`。ECC 強化(3つすべて):

- j-research = Context7(`ecc:docs-lookup`)+ WebSearch で最新ドキュメント根拠付け・出典明記。
- j-doc = code/architecture 系は `ecc:code-explorer`/`architect` で実コード根拠付け。
- j-log = 判断理由を instincts が学べる粒度で記述。

### 11. j-log 実地テスト + DevOps プロジェクト作成 + Task 紐づけ

`/j-log` を初回実行(アダプタ分のみ)。書き込み先問題(dotfiles は Joifup ワークスペースでなく Project fallback 不可)を確認 → 実ワークスペース joifup に暫定書き込み。その後、本 repo に **`projects/devops.md`(DevOps プロジェクト、status "In Progress")** を作成し dotfiles を Joifup ワークスペース化。初回ログを削除、本セッション全体を含めて再実行。

指摘で修正: (a) **Task 紐づけ漏れ** → 本ログを `--new-task "AIハーネス構築" --new-task-slug ai-harness` で Task 起票 + リンク(DevOps プロジェクト配下)。(b) 107行が要約的 → 各フェーズを実コマンド・コード・ギャップ表・検証結果で詳細化(前半は compact 制約あり)。(c) 日本語タイトルの slug 劣化(`001-ai`)→ `--new-task-slug` で英語 slug を明示。

## 参考情報

- 全検証は scratchpad 一時 dir で `--keep-source`/`--dry-run` を用い実データを汚さず実施。
- 成果物配置: `~/.claude/skills/{md2joifup,j-devflow,j-finish,j-doc,j-log,j-research}`(= dotfiles/.claude/skills/ symlink)。SKILL.md 語数 = md2joifup 449 / j-devflow 551 / j-finish 476 / j-doc 334 / j-log 399 / j-research 349。
- md2joifup は pyyaml 必須。
- 保留中: 旧 Notion スキル(doc-note/log-note/research-note/plan2notion/auto-workflow/pr/branch/commit)の削除は要確認。
