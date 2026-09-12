---
name: j-doc
description: 散在する log/memo/research を整理・統合し、第三者が読める1つの document として Joifup に記録するときに使う。「まとめて」「ドキュメント化して」に該当する場合。
user-invocable: true
argument-hint: "[note-id...／task-id（任意）]"
---

# j-doc

## 概要

散在するノート（log/memo/research）を統合し、構造化された **document**（タグ `document`）としてリポジトリ内 Joifup の `notes/document/` に記録する。コピペではない。そこに居なかった読者のために、元の材料を論理的に再構成する。単体で完結する。

永続化・frontmatter は `md2joifup` に委譲する。このスキルが持つのは**統合**と**タスクへの紐付け**である。

## 流れ

1. **ソースを集める：** `$ARGUMENTS` のノート id/path、あるいは該当トピックの `notes/**` エントリ。各ノートを読み、タグ・時系列・重複や矛盾を控える。
2. **Task を解決する**（document は通常、進行中の作業に属する）：
   - `$ARGUMENTS` に Task id があれば → `--task <id>`。
   - なければブランチ `TASK-<n>`（`git rev-parse --abbrev-ref HEAD`）→ `--task <n>`。
   - それも無く、かつ本当に新規のトピックなら → `--new-task "<title>" --new-task-slug <english-slug>`、そうでなければ省く（projects へフォールバック）。
3. **document を書く**（規定を参照）。一時 `.md` に出力する（H1 = title）。
4. **永続化する：** `python3 ~/.claude/skills/md2joifup/scripts/md2joifup.py <tmp>.md --type document <task-flag> --slug <english-slug>`。
5. `notes/document/…md` のパスと、統合したソースの数を**報告する**。

## ドキュメントの内容規定

H1 title。続けて：

- `### 概要` — ドキュメント全体の要約。
- トピック単位の節（ソースの時系列ではない）— 論理的に再構成する。
- 重複を除く。矛盾があれば最新の情報を優先する。
- 第三者が読んで完結する水準を目指す。
- `### 参照元` — ソースノートを列挙する。ライブな相互参照には Joifup の `ref` フェンスを使ってよい：
  ````
  ```joifup
  type: ref
  id: <note-id>
  ```
  ````
- 標準 GFM のみ（テーブル・コードフェンス）。Notion 固有の記法は使わない。

## ECC の活用

document が**コードやアーキテクチャ**に関わる場合、書く前に実際のコードベースに根拠を置く — `agentType: ecc:code-explorer`（実際の実行パス・構造を追う）または `ecc:architect`（設計の根拠）を dispatch し、記憶ではなく現状のコードを反映させる。純粋な意思決定・プロセス文書ではこの手順を省く。

## よくある失敗

- ソースをそのまま貼るだけで、トピック単位に再構成していない。
- ソースへのリンクを失う — `参照元` は必ず保持する。
- frontmatter を手で書く — それは `md2joifup` の役割。
