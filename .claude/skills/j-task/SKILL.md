---
name: j-task
description: タスクやアイデアを Joifup に backlog として起票する、あるいは開発の入口として記録するときに使う。「あとで詳細を詰めるので今は記録だけしたい」「j-devflow を始める前の起票」に該当する場合。
user-invocable: true
argument-hint: "[タスク/アイデアの文（省略可）]"
---

# j-task

## Overview

Joifup の **Task**（`Not started`）を `tasks/` に記録する。単体で完結する軽量な操作で、見つけた課題を backlog として一時置きする場合や、`j-devflow` の入口として使う。詳細な要件は各タスクの brainstorming に委ね、ここでは title と概要のみを記録する。永続化は `md2joifup --db tasks` に委譲する。

## When to Use

- 見つけた課題やアイデアを backlog タスクにするとき、あるいは作業を始める前にタスク記録が必要なとき。
- ブランチ作成・設計・実装（それは `j-devflow`）には使わない。既存タスクの選択（id を `j-devflow` に渡す）にも使わない。

## Flow

1. **粒度を見極める。** タスク = 1つの「要件精緻化ユニット」（j-devflow の1サイクル：brainstorming→plan→implement）。
   - 1ユニットに収まる → **単一タスク**（即時作成）。
   - 大きすぎる、または独立した複数の要素がある → **粗く分解する**：親（umbrella）と子タイトルを提案し、素早く確認を得てから作成する。
2. **内容を生成する：** 日本語の `title` と、下記の**本文**に従った本文。`--slug` は英語で導出する。
3. **Project を解決する：** 分かっていれば `--project` を渡す。無ければ `md2joifup` が `projects/` の単一エントリにフォールバックする。
4. **作成する：**
   - 単体：`python3 ~/.claude/skills/md2joifup/scripts/md2joifup.py <tmp>.md --db tasks --status "Not started" --slug <en-slug>`。
   - 分解：先に親を作成して filename id を控え、各子タスクを `--parent <parent-id>` 付きで作成する（`parent` は子側にのみ書く。`children` の同期は daemon が行う想定 — Joifup Plan 079）。
5. **報告する** 作成したタスクのパス。ブランチも実装も行わない。

## Body

概要レベルのみ。詳細な要件はタスクの brainstorming に属する。

- **節構成：** `# <title>`（H1 — `md2joifup` がここからタスクタイトルを取得する。無いと実行が落ちる）＋ `## 概要`（必須）＋ `## 背景`（「なぜ今か」が自明でないときのみ）。他の `##` 節は置かない。
- **サイズの目安：** 概要は3〜5行、背景は3行以内、ファイル全体でおよそ1,500B。目安であって上限ではない — 迷ったら削る。
- **絶対に書かないもの：** 分析、調査結果、引用、トレードオフの比較、実装方針、受け入れ基準。これらはすべて brainstorming と plan に属する。
- **既存タスクの粒度に合わせない。** 詳細に書かれた参照先タスクは基準ではない — **このルールが勝つ。**

## Identifier

タスクの**filename id**（`NNN-slug`）が唯一の運用上の識別子であり、リレーション・ブランチ・`--task`/`--parent` はすべてこれを使う。daemon の `ID: TASK-N` は**別物**の内部連番で、filename の番号とは**一致しない**（食い違う — 例：file `085-…` vs `ID: TASK-48`）。リレーション・ブランチ・`--task` に `ID` を使ってはならない。ブランチ（後で j-devflow 内で）＝ `feature/<filename-id>`。

## Common Mistakes

- frontmatter や `ID` を手で書く — `md2joifup` が管理する（`ID` は daemon が割り振る）。
- 日本語タイトルから壊れた slug が生成される — 英語の `--slug` を渡す。
- 本文に分析・引用・トレードオフを書く — 実装者が起票者の問題理解に縛られ、誤解までそのまま引き継がれる。
- 参照先タスクの粒度に引き寄せられる — 本文の規則が勝つ。
- `children` の逆参照を手で書く — 子には `parent` のみを書く。
