---
title: CLAUDE.md の書き方 — 2026-09 時点のベストプラクティス
tag: [research]
Project: devops
Task: 011-decision-principles-in-claude-md
created_at: 2026-09-22
updated_at: 2026-09-22
---

# CLAUDE.md の書き方 — 2026-09 時点のベストプラクティス

### 背景・目的

`tasks/011` で判断の原則を `~/.claude/CLAUDE.md` に載せるにあたり、「何をどの形で載せるか」の判断基準を外部の現行ソースに求めた。最初の案は原典の理由と手順を持ち込んで 5 行になり、それが長いと感じられたことが調査の直接の動機である。結果は設計書 `notes/document/011-decision-principles-in-claude-md-design.md` の線引きに使った。このノートは出典付きの記録として残す。

### 調査結果

#### Anthropic 公式 — Best practices for Claude Code

- 概要: CLAUDE.md は毎セッション読まれるので、**各行について「これを消すと Claude が間違えるか」を問い、そうでなければ削る**。肥大化した CLAUDE.md は実際の指示を無視させる。「短く、人が読める形で」。
- 載せるもの: Claude が推測できない bash コマンド、既定と異なるコードスタイル、テストの実行方法、リポジトリの作法、プロジェクト固有のアーキテクチャ判断、環境の癖、非自明な落とし穴。
- 載せないもの: コードを読めば分かること、言語の標準的な慣習、詳細な API 文書、頻繁に変わる情報、長い説明、「きれいなコードを書く」のような自明な practice。
- 「Claude が CLAUDE.md にあるはずの規則を破り続けるなら、ファイルが長すぎて規則が埋もれている可能性が高い」「CLAUDE.md をコードのように扱う: 問題が出たら見直し、定期的に刈り込み、変更は Claude の挙動が実際に変わるかで検証する」。
- 参考: https://code.claude.com/docs/en/best-practices（2026-09-22 取得）

#### Anthropic 公式 — How Claude remembers your project（memory）

- 概要: CLAUDE.md と auto memory は相補的で、どちらも「context であって強制される設定ではない」。確実に止めたい行為は `PreToolUse` hook で止める。
- サイズ: **1 ファイル 200 行以下を目標**。長いほど context を食い、遵守率が下がる。パスに紐づく規則は `.claude/rules/` に分けて、該当ファイルを扱うときだけ読ませる。`@import` で分けても起動時には全部読まれる。
- 追加のタイミング: 同じ間違いを 2 回目にした、レビューで指摘された、前回も同じ訂正を打った、新しいチームメイトにも同じ説明が要る。
- 「複数手順の手続き」や「コードベースの一部にしか関係しないもの」は CLAUDE.md ではなく skill か path-scoped rule に移す。
- 参考: https://code.claude.com/docs/en/memory（2026-09-22 取得）

#### Claude Code チーム（Thariq Shihipar）— The new rules of context engineering for Claude 5 models

- 概要: Claude 5 世代（Opus 5 / Fable 5 / Sonnet 5）向けに Claude Code のシステムプロンプトを 80% 以上削っても、コーディング評価で計測できる劣化は無かった。旧モデル向けの制約が、新モデルを過剰に縛っていた。
- 6 つの転換: ルールを与える → 判断を任せる / 例を並べる → インターフェースを設計する / 全部前置き → progressive disclosure / 繰り返す → tool description に一度だけ / CLAUDE.md にメモ → auto-memory / 簡素な spec → 豊かな参照。
- CLAUDE.md について: 「軽く保ち、リポジトリが何かを簡潔に書き、トークンの大半はコードベースの落とし穴に使う。ファイルシステムを見れば分かる自明なことは書かない」。詳細は skill に切り出して CLAUDE.md から参照する。
- skill について: 「過剰に制約しない — **ただし本当に重要な領域は例外**」。
- `/doctor` が CLAUDE.md と skill の rightsizing を自動で提案する。
- 参考: https://x.com/trq212/article/2080710971228918066（2026-07-24。転載 https://tool.lu/en_US/article/7Xk/preview で本文を確認）

#### 派生記事 — Context Engineering: What Anthropic's 80% Cut Means for Business（bosio.digital）

- 概要: 「書く量を減らせ」は半分しか正しくない。**削ってよいのは、周囲のコンテキストから導出でき、間違えても自動で検出されるもの**（旧モデル向けの足場）。価値観・リスク姿勢・「done」の定義・守秘の壁のように**リポジトリからは導出できず、間違えても何も赤くならないもの**は、常時読む側に短く残す。
- 本件との関係: 判断の原則はまさに後者である。したがって CLAUDE.md に載せる根拠はあるが、載せる形は「導出できない姿勢だけ」であって理由や手順ではない。
- 参考: https://bosio.digital/articles/context-engineering-rules（2026-07-24）

#### X の実務者投稿

- Nick Babich「5 Best practices for CLAUDE.md」: 100〜200 行以内、価値のある情報だけ、全部を 1 ファイルに入れず必要時に読むファイルの木にする。https://x.com/101babich/status/2039723575372927395
- Aakash Gupta「Claude Code 5: How to Update Your Setup」: safe mode（カスタマイズ無効）で素の挙動をベースラインにし、素のモデルが既にできることは指示から削る。「手順ではなく結果を定義する」ほうが 5 世代では良い出力になった。https://www.aibyaakash.com/p/claude-code-5
- Boris Cherny（Y Combinator 登壇、2026-07）: 「**半年ごとに CLAUDE.md・skills・hooks を消して、モデルが何をするか見ろ**。同じ所で繰り返しつまずいたときだけ、その指示を戻す」。https://www.youtube.com/watch?v=qyPCVqFUyDo

### 比較表

| 観点 | 旧来の書き方（2025） | 現行の推奨（2026-09） |
| --- | --- | --- |
| 判断基準 | 知っている practice を網羅する | 「消すと間違えるか」で 1 行ずつ選ぶ |
| 指示の形 | ルール・手順・例 | 判断の姿勢・結果・ガードレール |
| 長さ | 制限なし（肥大化） | 200 行以下。理想は 100 行以下 |
| 詳細の置き場 | CLAUDE.md 本体 | skill / `.claude/rules/` / 参照先（progressive disclosure） |
| 強制したい行為 | 「絶対に〜するな」を大文字で | hook（決定論的）に移す。CLAUDE.md は context |
| メモ | `#` で CLAUDE.md に書く | auto-memory に任せる |
| 見直し | 追記のみ | 定期的に削る。新モデルごとに全消しで再ベースライン |

### 結論・推奨

- CLAUDE.md に載せてよいのは「リポジトリから導出できず、間違えても自動では検出されない」種類の情報である。判断の原則はこれに当たる。
- 載せる形は姿勢 1 文。理由・経緯・運用の手順は載せない（Claude 5 世代では「手順ではなく判断を与える」）。
- 効いているかの検証は挙動の観察で行い、効かなければ文言を直す。行数は増やさない。
- dotfiles の `.claude/CLAUDE.md` は現在 70 行前後で、200 行の目標内にある。ただし「ハーネス構成」「レビュー統合」の節は手順に近いので、次に見直すときは skill 側への移動を検討する対象になる。

### 残課題

- `/doctor` を dotfiles の CLAUDE.md と自作 skill に対して実行し、提案を記録する（未実施）。
- 「半年ごとに全消しで再ベースライン」を運用に入れるか。次のメジャーモデルの時点で判断する。
