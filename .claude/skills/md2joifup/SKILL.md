---
name: md2joifup
description: markdown ファイルを Joifup の Notes-DB エントリにする必要があるときに使う。brainstorming/writing-plans 後の superpowers plan/spec、または repo の notes/ 配下に正しい frontmatter で入るべき手書きの doc/log/research note に該当する場合。
---

# md2joifup

## 概要

Joifup のメモリ層の永続化プリミティブである：markdown ファイルを house-style の **Notes-DB row**（frontmatter + 本文）に変換し、`notes/<type>/` 配下にその場で配置する。開発フロー（`j-devflow` が superpowers の plan/spec を永続化する）と、単体の note 系スキル（`j-doc` / `j-log` / `j-research`）の両方を支える。

tag/relation/title の規約については**正典の Notes schema**を読む — 絶対にハードコードしない。

## 使う場面

- `brainstorming`/`writing-plans` の成果物、または手書きの doc/log/research note を Joifup に永続化するとき。
- Joifup を読むこと、schema を編集すること（`schema.yaml` は Joifup が所有する）、人向けの出力（それは `j-finish` の役割）には使わない。

## 使い方

```bash
python3 scripts/md2joifup.py <source.md> --type <tag> \
  [--task ID]... [--new-task "TITLE"] [--new-task-slug SLUG] [--project ID]... \
  [--notes-dir DIR] [--tasks-dir DIR] [--slug SLUG] [--keep-source]
```

**Task 作成（tasks db）：**
`python3 scripts/md2joifup.py <body.md> --db tasks [--status "Not started"] [--parent ID] [--project ID] [--slug EN-SLUG]`
— house-style の frontmatter（title/status/Project/parent、timestamps、ID なし）で `tasks/NNN-slug.md` を作成する。`--status` は tasks schema に対して検証される。`--db notes`（デフォルト）は変わらない。

- `--type` — Notes の**content タグ**（`plan`、`document`、`log`、`research`、`memo`）。schema のタグ選択肢に対して検証される。
- `--task` — 既存の Task をその**filename id**（`NNN-slug`、パスではなく、daemon の `ID: TASK-N` **でもない** — これらは別物で一致しない）で紐づける。ブランチの判定は呼び出し側の責務である：ブランチは `feature/<filename-id>` なので、`feature/` の接頭辞を外して id を取り出し、ここに渡す。**md2joifup は `--task`（および `--parent`）が実在する `tasks/` ファイルに解決できるかを検証する**。できなければエラーにする — daemon の `ID` や typo は、黙って note の番号を誤るのではなく、明示的にエラーで落ちる。
- `--new-task "TITLE"` — 新しい house-style の Task を作成して紐づける。note がそれ自身の task を生む場合に使う（例：新しい調査）。非 ASCII の title と併せて `--new-task-slug`（英語）を渡す。渡さなければ task のファイル名 slug が劣化する。
- `--project` — 無ければ Task から継承し、それも無ければ `projects/` の単一の project にフォールバックする。
- `--slug` — 上書き、デフォルトは title を slug 化したもの（**非 ASCII の title には英語の slug を渡す**。渡さなければ type に劣化する）、それも無ければ type。
- `--keep-source` — move ではなく copy にする（デフォルト：move / in-place）。

配置先のパスを出力する。対応関係：superpowers の spec → `document`、plan → `plan`。

## 何をするか

- H1 を抽出し、**frontmatter の `title` に反映する**。H1 自体は本文に残る。
- superpowers の agentic-worker の scaffolding を取り除く（手書きの note では no-op）。
- **house-style の frontmatter：** flow array（`tag: [log]`）、単一の relation → scalar、2 個以上 → flow array、`created_at`/`updated_at` が無ければ（今日の日付で）スタンプする。
- **Project は常に解決される：** 明示指定 → 新規/紐づけた Task の Project → `projects/` の単一エントリ。
- **ファイル名** `<NNN>-<slug>.md`：`NNN` = 紐づけた task の id 番号、無ければ `notes/<type>/` の次の番号。
- 自動採番の `ID` だけを daemon に委ねる。元から存在した source の frontmatter キーは保持する。

## よくある失敗

- state タグ（`inbox`/`seed`/`archive`）を `--type` に渡す — content タグを使う。state は別の軸である。
- relation の値をファイルパスとして書く — それらは**id**である（`042-...`、`638-...`）。
- スクリプトにブランチを検出させる — 呼び出し側で TASK-id を解決し、`--task` に渡す。
- ここで frontmatter の規約を手で編集する — 代わりに Joifup の `schema.yaml` を変更する。
