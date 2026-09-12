---
name: j-research
description: 技術調査の会話後、ライブラリ・フレームワーク選定・アーキテクチャ選択肢・トレードオフ分析を調査ノートとして Joifup に記録するときに使う。「調査した内容をまとめて」「比較検討をノートに残して」に該当する場合。
user-invocable: true
argument-hint: "[task-id（任意）]"
---

# j-research

## 概要

技術的な**調査ノート**（タグ `research`）を、リポジトリ内 Joifup の `notes/research/` に記録する — 構造化された比較・トレードオフ・推奨案を含む。単体で完結する。

永続化・frontmatter は `md2joifup` に委譲する。このスキルが持つのは**根拠づけられた調査**と**タスク**である。

## 流れ

1. **調査を現行のソースに根拠づける（ECC）** — 会話の記憶だけに頼ってはならない：
   - ライブラリ・フレームワーク・API・CLI については、Context7 経由で**現行**のドキュメントを取得する：`agentType: ecc:docs-lookup` を dispatch する（または context7 MCP ツールを直接使う）。
   - 比較・landscape・最近の変更については `WebSearch` を使う。
   - 具体的なバージョンを控え、すべてのソース URL を引用する。
2. **Task を解決する**（調査はそれ自身のタスクを生むことが多い）：
   - `$ARGUMENTS` に Task id があれば → `--task <id>`。
   - なければ、新規の調査なら → `--new-task "<title>" --new-task-slug <english-slug>`（タスクを作成する。英語の slug が、日本語タイトルのタスクの filename をきれいに保つ）。
   - それも無く、明らかに現在の作業の延長なら → ブランチ `TASK-<n>` → `--task <n>`。
3. **ノートを書く**（規定を参照）— 一時 `.md` に出力する（H1 = title）。
4. **永続化する：** `python3 ~/.claude/skills/md2joifup/scripts/md2joifup.py <tmp>.md --type research <task-flag> --slug <english-slug>`。
5. `notes/research/…md` のパスを**報告する**。

## 調査ノートの内容規定

H1 title。続けて：

- `### 背景・目的` — なぜこの調査が必要だったか。
- `### 調査結果` — 選択肢・技術ごとに1節：概要 / メリット / デメリット / 参考(URL, version)。
- `### 比較表` — 重要な軸を横断する GFM テーブル（比較可能な場合）。
- `### 結論・推奨` — 根拠を伴う推奨案。
- `### 残課題` — さらに検討が必要な未解決の問い。
- 標準 GFM のみ。ライブラリに関する主張はすべて、引用された現行ソースに遡れなければならない。

## ECC の活用

ここでの価値は **accuracy over recall**（記憶より正確さ）である：Context7（`ecc:docs-lookup`）はバージョンの正しい API・設定の事実を与え、`WebSearch` は現行の landscape を与える — いずれも学習データのカットオフの記憶より優る。記憶からの断定より、ドキュメントの引用を優先する。依拠したドキュメントのバージョンを記す。

## よくある失敗

- 根拠づけなしに記憶だけで書く — 古い・幻覚の API になる。現行のドキュメントを取得する。
- 引用のない主張 — 選択肢はすべてソースが必要。
- frontmatter を手で書く — それは `md2joifup` の役割。
