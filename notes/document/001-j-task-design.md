---
title: j-task 設計 — Joifup タスク起票スキル
tag: [document]
Project: devops
Task: 001-ai-harness
created_at: 2026-07-11
updated_at: 2026-07-11
---

# j-task 設計 — Joifup タスク起票スキル

> 2026-07-11 brainstorming で確定した設計。j-devflow の前段（入口＝タスク起票）を整備する。実装は writing-plans → SDD へ。

## 目的

いつでも Joifup Task を起票できる standalone スキル `/j-task` を用意する。用途は2つ:

1. **バックログ投下** — 開発中に見つけた課題/アイデアを、その場で素早く Task 化して溜める。
2. **j-devflow の入口** — 起票した Task を後で j-devflow が拾い、設計→計画→実装へ進める。

capture に徹し、詳細な要件詰めは各 Task の brainstorming（j-devflow Session A）に委ねる。

## スコープ

**やること:**
- Task の新規起票（title ＋ 概要 body ＋ status=Not started ＋ Project）。
- **粒度対応の分解** — 大きすぎる課題は親＋子タスクに粗く分解。
- house-style frontmatter での永続化（md2joifup 再利用）。

**やらないこと（YAGNI）:**
- ブランチ作成・brainstorming・実装（それらは j-devflow）。
- 既存タスクの「選択」（j-devflow に id を渡すだけ。検索は j-devflow / Joifup WebUI に委譲）。
- 起票時の deadline / priority / sub-task 必須化（後で md 編集 or 引数）。

## `/j-task` の挙動

- **起動**: `/j-task [課題/アイデアのテキスト]`。引数なしなら会話文脈から推定。
- **生成内容**:
  - `title`: 日本語・人間可読。
  - `body`: **概要レベル**（詳細は後で brainstorming）。
  - frontmatter: `status: Not started` / `Project`（fallback: 明示 > `projects/` の唯一の Project）/ `created_at`・`updated_at`（当日）。`ID` は書かない（Joifup daemon が採番）。
- **ファイル名**: `NNN-slug.md`。`slug` は英語（日本語 title は slug 劣化するため自動英語 slug or `--slug`）。
- **副作用なし**: ブランチを切らない・実装しない。出力＝作成した Task のパス（＋分解時は一覧）。

## 識別子（重要な設計判断）

Joifup には識別子が2系統ある:

| 識別子 | 決定タイミング | 用途 |
|---|---|---|
| **ファイル名 id**（`001-ai-harness`） | スキルが即座に決定 | frontmatter 関係値・ブランチ・参照（**運用の単一の正**） |
| daemon の `ID: TASK-N` | daemon が非同期採番 | Joifup 内部の auto_increment（WebUI 通番）。運用では使わない |

**決定: ファイル名 id を単一の運用識別子とする。**

- 理由: 即時・daemon 非依存（自動化が堅牢）／識別子1つで frontmatter・ブランチ・plan/PR を貫通／人間可読（番号＋slug）。
- daemon の `TASK-N` は **ファイル名番号とは別物で一致しない**（採番機構が違う。実例: task `085-…` / daemon `TASK-48`）。運用は常にファイル名 id を正とし、関係・ブランチ・`--task`/`--parent` に daemon `ID` を使わない（使うと `task_number()` がノートを誤番号化する）。
- **ブランチ** = `feature/<ファイル名id>`（例 `feature/001-ai-harness`）。
- **CLAUDE.md 更新**: 「TASK-id」の定義を「Joifup タスクのファイル名 id」に再定義（現 `feature/TASK-123-slug` の記述を更新）。

## 粒度対応（タスク分解）

- `/j-task` は捕捉した課題/アイデアの**粒度を評価**する。基準 = 「**1回の j-devflow サイクル（brainstorming→plan→implement）で回せる要件詰め単位か**」。
- **単一単位に収まる** → 単一 Task を**即作成**（軽量 capture）。
- **大きすぎる／独立した複数塊を含む** → **親タスク（アンブレラ）＋子タスク**に**粗く分解**。各子 = 要件詰め単位（`status: Not started`、`parent: <親のファイル名id>` で紐づけ）。深い要件は各子の brainstorming に委ねる（/j-task は"塊の識別"まで）。
- **確認の粒度**: 単一タスクは即作成。**分解が発生する場合のみ**、提案（親＋子のタイトル一覧）を提示して確認してから作成（複数ファイル作成は非自明なため）。
- 割り方の判断は SKILL.md（LLM）、作成（親＋子 md・`parent` リンク）は md2joifup。
- **逆参照の方針**: `parent` は子側にのみ書く。`children` の逆参照は Joifup daemon（parent/children 同期・Plan 079）に委ね、手書きしない（Notes 逆参照と同じ一方向方針。両側書きの食い違いバグを避ける）。

## 裏側（機械）— md2joifup の task 作成を第一級化

- house-style の Task 作成ロジックは **md2joifup が既に `create_task` として保持**（現状 `--new-task` の副作用でのみ使用）。これを**第一級コマンドとして公開**し、`/j-task` から使う。
- インターフェース（案）: `md2joifup <body.md> --db tasks --status "Not started" [--parent <id>] [--project <id>] [--slug <en-slug>]`。
  - notes モードとの違い: `tag` の代わりに `status`、関係は `Project`（単一）／`parent`。`ID` は省略（daemon）。それ以外（title の H1 ミラー・Project fallback・`created_at`/`updated_at`・ファイル名 `NNN-slug`・house-style flow/scalar）は notes と共通。
- これにより Task 生成コピーを3つ目に増やさず DRY（現 md2joifup.create_task / j-finish.file_user_action と統一の方向）。
- 代替案（不採用）: `/j-task` 専用の小スクリプト → house-style エミッタ重複。

## j-devflow 統合・status ライフサイクル

- **j-devflow Session A step1** を更新: 「Task を用意」＝ **新規なら `/j-task`、既存ならバックログの id を指定**。
- **status ライフサイクル**:
  - `Not started`（/j-task 起票・バックログ）
  - → `In progress`（実装開始・j-devflow Session B、または plan 永続後）
  - → `In review`（j-finish）
  - → `Done`（人間の承認コミット）
- j-task は **Not started の起票**のみを所有。以降の遷移は j-devflow / j-finish / 承認セッション。

## 実装で触れるもの（plan の対象）

1. `md2joifup` — task 作成の第一級化（`--db tasks` モード ＋ `--parent`）。
2. 新規スキル `~/.claude/skills/j-task/SKILL.md`（user-invocable。粒度評価・分解・md2joifup 呼び出しを記述）。
3. `j-devflow/SKILL.md` — Session A step1 に `/j-task` 参照を追記。
4. `.claude/CLAUDE.md` — 「TASK-id ＝ Joifup タスクのファイル名 id」、ブランチ例を `feature/<ファイル名id>` に更新。

## テスト観点（writing-skills RED→GREEN）

- 単一課題 → 単一 Task（house-style・Not started・Project fallback・英語slug）。
- 大課題 → 親＋子（`parent` 一方向・確認提示）。
- md2joifup task モード: status/Project/parent/timestamps 付与、`ID` 省略、ファイル名 `NNN-slug`。
- 日本語 title でも slug が劣化しない（英語 slug 明示）。
