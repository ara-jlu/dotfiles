---
title: Claude Code の機能別ベストプラクティス — skills / hooks / subagents / memory / 検証（2026-09 時点）
tag: [research]
Project: devops
Task: 015-harness-review-2026-09
created_at: 2026-09-22
updated_at: 2026-09-22
---

# Claude Code の機能別ベストプラクティス — skills / hooks / subagents / memory / 検証（2026-09 時点）

### 背景・目的

`tasks/011` で CLAUDE.md の書き方を調べた際（`notes/research/011-claude-md-writing-best-practices.md`）、CLAUDE.md 単体ではなく、skills・hooks・subagents・auto-memory・検証の仕組みを含めた全体で「何をどこに置くか」が変わっていることが分かった。`notes/research/006-harness-principles.md` の論点（ルール列挙 vs 少数原則）の続きとして、2026-09 時点の公式ドキュメントと実務者の発言を機能別に整理し、dotfiles のハーネス（superpowers + ECC + Joifup）を見直すための材料にする。

出発点にした X の投稿が 2 つある。1 つは Boris Cherny の Y Combinator 登壇の紹介（「まず全部消してみろ」）、もう 1 つは OpenAI Developers の「GPT-6 Astra 向けに skills / AGENTS.md / プロンプトを見直せ」への反応である。後者は Claude ではなく Codex の話だが、主張は Anthropic 側と同じ方向を向いているので併記する。

### 調査結果

#### 1. 全体の方向 — 「削って、素のモデルを見て、つまずいた所だけ戻す」

- Boris Cherny（Claude Code 作者、Y Combinator Startup School 2026-07）: Opus 5 でシステムプロンプトの 80% を削った。内部では `CLAUDE_CODE_SIMPLE=1` でシステムプロンプトとツールプロンプトを全部剥がす「simple mode」を ablation に使う。「**半年ごとに CLAUDE.md・skills・hooks を消して、モデルが何をするか見ろ**」。再構築は「削る → 使う → 同じ所で繰り返しつまずいたときだけ、その指示を戻す」の順で、推測で書かない。「モデルは指示を毎回読むので、本当に必要な指示だけを入れる」。
- 同登壇: 「プロンプトエンジニアリングより、少し難しすぎる課題を与えて、自分で検証できる手段を持たせることが重要。**検証が、人が最も正しくやれていない唯一のこと**」。「タスク・ガードレール・終了条件を書いて、あとはモデルに任せる」。「LinkedIn や Twitter の一発テクニックは無い。経験的にやるしかない」。
- OpenAI Developers「Rethinking skills and prompts for GPT-6 Astra」（2026-09-11）: skill の description は「いつ使うか」が明確な範囲で**できるだけ短く**（悪い例「DB・クエリ・モデル・永続化を扱うときに使う」→ 良い例「migration を追加・変更・レビューするときに使う」）。skill の root は最小のルーターにして支援文書へ振る（progressive disclosure）。「毎回 architecture.md を読め」ではなく「サービス境界なら architecture.md」のように文脈で指す。旧モデル向けの「まず確認しろ」は新モデルを萎縮させるので見直す。**「done」を先に定義する**。
- 参考: https://www.youtube.com/watch?v=qyPCVqFUyDo / https://sozai.app/transcript/boris-cherny-cut-80-percent-claude-code-prompt/ / https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra / X の投稿 https://x.com/AiAircle34052/status/2096459879955550518 、 https://x.com/gigabit_million/status/2099264412876247359

#### 2. Skills

- 読み込みは 3 段階: 起動時は `name` と `description` だけ（1 skill あたり約 100 トークン）、発火時に SKILL.md 本体（5k トークン以下が目安）、参照ファイルは読まれるまでコスト 0、スクリプトは実行され出力だけが context に入る。
- `description` が発火の唯一の手がかり。**何をするかと、いつ使うかの両方**を三人称で書く。Anthropic の skill-creator は「Claude は skill を under-trigger しがちなので、description は少し押しの強い書き方にする」としている一方、OpenAI は「長すぎる description は切り詰められ、互いに矛盾する」と反対側から釘を刺す。両立させるなら「トリガー条件を具体的に、文は短く」。
- SKILL.md 本体は 500 行以下。超えるなら階層を足して参照先を明示する。参照は SKILL.md から 1 段だけ。100 行を超える参照ファイルには目次を置く。
- 決定論的な作業はスクリプトに固定し、「実行しろ」と「参照として読め」を区別して書く。
- 「skill は特定の意見・知識・ベストプラクティスを符号化するときに最も価値がある。過剰に制約しない — **ただし本当に重要な領域は例外**」（Thariq）。
- Claude Code 側: カスタムコマンド（`.claude/commands/*.md`）は skill に統合された。`/doctor` `/code-review` `/verify` `/run` `/debug` `/batch` `/loop` などが bundled skill として同梱される。
- 参考: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices / https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills / https://x.com/trq212/article/2080710971228918066 / bundled skill とコマンド統合は https://code.claude.com/docs/en/best-practices

#### 3. Hooks

- CLAUDE.md と skill は「context であって強制ではない」。**例外なく毎回起きてほしいことは hook に置く**（フォーマッタ、lint、危険コマンドの遮断、migrations フォルダへの書き込み禁止）。`PreToolUse` で exit code 2 を返せば tool 呼び出しが遮断され、stderr がモデルに返る。
- 「Stop hook で検証スクリプトを回し、通るまでターンを終わらせない」が無人実行の決定論的ゲート。8 回連続で block されると Claude Code が hook を上書きして終了する。
- hook は subagent の中でも発火する（`settings.json` のものは全 subagent に、subagent の frontmatter に書いたものはその subagent の間だけ）。
- 参考: https://code.claude.com/docs/en/best-practices / https://code.claude.com/docs/en/sub-agents

#### 4. Subagents

- 用途は 2 つ: **context の節約**（探索・ログ読み・要約を別窓で行い、要約だけ戻す）と**独立したレビュー**（実装した文脈を持たない fresh な reviewer が diff と基準だけを見る）。公式も「作業を done と数える前に、subagent に fresh context で diff をレビューさせて gap を報告させる」を推奨する。
- ただし「reviewer は言われたとおり何か見つけようとする。全部の指摘を追うと over-engineering になる」ので、何を finding とするかを reviewer に伝える。
- `tools` を絞れば reviewer は物理的に編集できない。高頻度・低リスクの subagent は安いモデルに固定する。
- `memory` フィールドで subagent 自身の永続メモリを持たせられる（auto memory の一部。auto memory を切ると無効）。
- 参考: https://code.claude.com/docs/en/sub-agents / https://code.claude.com/docs/en/best-practices

#### 5. Memory（CLAUDE.md と auto memory）

- CLAUDE.md（人が書く指示）と auto memory（Claude が書く学習。先頭 200 行 / 25KB が毎セッション読まれる）は相補的。「`#` で CLAUDE.md にメモを書く」運用は auto memory に置き換わった。CLAUDE.md には**セッション前に分かっているプロジェクト文脈**（アーキテクチャ・落とし穴・規約）だけを置く。
- CLAUDE.md 自体のサイズ・分割・書き方の基準は `notes/research/011-claude-md-writing-best-practices.md` に記録した。
- 参考: https://code.claude.com/docs/en/memory

#### 6. 検証と自律実行

- 公式 best practices の第一項目が「Claude が自分で回せる検証を与える」。テスト・ビルドの exit code・lint・fixture との diff・スクリーンショット比較のどれでもよい。プロンプト内で回す → `/goal` で毎ターン評価 → Stop hook で決定論的に止める → 別の subagent に反証させる、の順に設定コストが上がり、無人で完走できる範囲が広がる。
- 「成功したと主張させるのではなく、証拠（テスト出力・実行したコマンドと結果・スクリーンショット）を出させる」。
- 参考: https://code.claude.com/docs/en/best-practices

### 比較表

| 置き場 | 性質 | 何を置くか | 何を置かないか |
| --- | --- | --- | --- |
| CLAUDE.md | 毎回読まれる context。強制ではない | 導出できない姿勢・規約・落とし穴。200 行以下 | 手順、例の羅列、コードから分かること、メモ |
| `.claude/rules/` | 該当パスを扱うときだけ読まれる | ファイル種別に紐づく規則 | 全体に関わる規約 |
| skill | 発火時だけ読まれる。description で選ばれる | 特定の workflow の知識と意見。ルーター + 参照 + スクリプト | 長い手順書（500 行超）、曖昧な description |
| hook | 決定論的。モデルの判断を経ない | 毎回必ず起きてほしいこと、遮断したいこと | モデルに判断させたいこと |
| subagent | 別 context。要約だけ戻る | 探索、独立レビュー、高頻度の安い作業 | 親と密結合な作業 |
| auto memory | Claude が書く | 訂正・好み・ビルドコマンドの学習 | 人が書くべき規約 |

### 結論・推奨

dotfiles のハーネスに照らすと、次の点が見直し候補になる。

1. **CLAUDE.md の「ハーネス構成」「レビュー統合」は手順に近い。** 公式の基準では skill か rule に移す対象で、CLAUDE.md には「superpowers が背骨、ECC が専門作業」という一文と落とし穴だけ残す形になる。ただし 006 の結論（少数原則 + 上書き可能な既定）と整合するかを先に確かめる。
2. **「例外なく毎回」の規則は hook に移す。** 自作 skill（例: `j-devflow` の「`docs/superpowers/` に commit しない」「subagent を worktree に固定する」）に「絶対に〜しない」で書いているもののうち、機械的に判定できるものは `PreToolUse` hook の候補である。CLAUDE.md 自体にはこの種の規則は無い。
3. **自作 skill の description を「短く、トリガー条件を具体的に」で見直す。** `j-*` の description は「〜に該当する場合」の列挙が長い。OpenAI の指摘（長い description は切り詰められ矛盾する）と Anthropic の指摘（under-trigger する）を両立させる書き方に揃える。
4. **`/doctor` を実行して提案を記録する。** 手で見直す前に、公式の rightsizing を一度通す。
5. **半年ごとの全消し再ベースラインを運用に入れるかを決める。** 次のメジャーモデルの時点で `CLAUDE_CODE_SIMPLE=1` 相当の比較を行い、素のモデルが既にできることを指示から削る。

### 残課題

- 上記 1〜5 はそれぞれ別のタスクになる規模である。このノートに紐づけた Task で優先順位を決め、個別に起票する。
- `/doctor` の実行結果（未実施）。
- Agent Teams / dynamic workflows（`use a workflow`）は今回調べていない。superpowers の SDD と役割が重なる可能性があるので、別途調べる。
