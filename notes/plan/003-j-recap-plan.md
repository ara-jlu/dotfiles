---
ID: NOTE-120
title: j-recap スキル実装 Implementation Plan
tag: [plan]
Project: devops
Task: 003-j-recap-skill
created_at: 2026-07-26
updated_at: 2026-07-26
Tasks:
- 003-j-recap-skill

---

# j-recap スキル実装 Implementation Plan

**Goal:** 指定期間（デフォルト今日）の作業成果を episodic-memory から拾い、git/PR で裏取りし、外部公開できる「短文ポスト版＋まとめ段落版」をチャット出力する user-invocable スキル `j-recap` を1枚の SKILL.md として作る。

**Architecture:** 既存 `j-*` スキル（`j-log` 等）の SKILL.md 形式に倣った散文の手順書。実行時は (1) `episodic-memory:search-conversations` サブエージェントで横断検索 → (2) 対象リポジトリの `git log`/PR で完了ステータスを裏取り → (3) 内部識別子をサニタイズ → (4) 2形式のテキストを出力、という4段フローを規定する。コードは持たず、モデルへの指示のみ。

**Tech Stack:** Markdown（frontmatter + 散文）。実行時依存は `episodic-memory:search-conversations`、`git`、任意で `gh`、`currentDate` コンテキスト。

## Global Constraints

- 配置: `~/Joifup/dotfiles/.claude/skills/j-recap/SKILL.md`（単一ファイル）。
- frontmatter: `name: j-recap` / `description:`（"Use when …" 形式、既存 j-* に倣う）/ `user-invocable: true` / `argument-hint: "[期間 (省略時=今日)] [プロジェクト (任意)]"`。
- 出力はチャットのみ。Joifup ノート・ファイルへの永続化はしない。
- コミットハッシュ・PR 番号は完了判定の根拠に使うが、最終出力には出さない。
- 内部識別子（`TASK-<n>`・内部リポジトリ名・未公開固有名詞）はサニタイズして出力。
- 日付基準は `currentDate` コンテキスト。時刻取得 API は使わない。
- 設計の一次ソースは `notes/document/003-j-recap-design.md`（本 worktree 内）。

---

### Task 1: SKILL.md 本体を執筆

**Files:**
- Create: `.claude/skills/j-recap/SKILL.md`
- Reference: `~/.claude/skills/j-log/SKILL.md`（形式の手本）, `notes/document/003-j-recap-design.md`（設計の中身）

**Interfaces:**
- Produces: `/j-recap` スキル定義。`$ARGUMENTS` に「期間」「プロジェクト名」を受ける。

- [ ] **Step 1: 手本と設計を読む**
  - `~/.claude/skills/j-log/SKILL.md` と `~/.claude/skills/j-doc/SKILL.md` を読み、frontmatter キー・見出し構成・文体を把握。
  - `notes/document/003-j-recap-design.md` を読み、フロー/出力仕様/サニタイズ方針を確定。

- [ ] **Step 2: frontmatter と Overview を書く**
  - frontmatter は Global Constraints の通り。
  - `## Overview`: 目的（外部向け作業まとめ）と、既存 `j-log`/`j-doc` との違い（読み手が社外・記録ではなく成果）を1段落で。

- [ ] **Step 3: 引数仕様セクションを書く**
  - 省略=今日／`YYYY-MM-DD`／`this-week`・`last-week`・範囲／プロジェクト名で絞り込み／併用可、を明記。

- [ ] **Step 4: フロー（2段構え）セクションを書く**
  - 「1. 拾う」= `episodic-memory:search-conversations` サブエージェントに、対象期間の全セッションをタスク／リポジトリ／成果物単位で構造化させ、憶測禁止・記録ベース事実のみを求める依頼を出す。
  - 「2. 裏取り」= 各タスク候補について対象リポジトリで `git log --all --since/--until`（当日・全ブランチ）と PR/マージ状況を確認し、完了/進行中/設計 を実体で確定。当日コミットが無い候補は落とす。
  - 「3. サニタイズ」= 内部識別子・機微情報を一般化/伏字。
  - 「4. 出力」= A 短文ポスト版（各タスク1〜数本・140字目安・絵文字控えめ）と B まとめ段落版（数段落の読み物）を両方チャット出力。各タスクは「進捗ステータス＋概要」。

- [ ] **Step 5: ステータス判定ルールと出力フォーマット例を書く**
  - 完了=PR マージ済み/UAT 承認/ main 到達、進行中=未マージのコミットあり、設計=ドキュメントのみ、の表。
  - 記録と実体が食い違う場合は実体優先。
  - 出力例（設計ノートの例に準拠）。

- [ ] **Step 6: Common Mistakes セクションを書く**
  - 記録だけで完了判定しない／サニタイズ漏れ／コミットハッシュを出力に混ぜる、を挙げる。

- [ ] **Step 7: コミット**
```bash
git add .claude/skills/j-recap/SKILL.md
git commit -m "feat(skills): add j-recap skill for external-facing work recaps (003)"
```

---

### Task 2: dry-run 検証

**Files:**
- Reference: `.claude/skills/j-recap/SKILL.md`

**Interfaces:**
- Consumes: Task 1 の SKILL.md。

- [ ] **Step 1: 過去日でスキル手順を実行**
  - SKILL.md の手順どおり、既知の作業日（例 `2026-07-21`）を対象に (1) episodic 検索 →(2) git 裏取り →(3) サニタイズ →(4) 出力 を実際に通す。

- [ ] **Step 2: 出力が仕様を満たすか確認**
  - チェック: 2形式（短文＋まとめ）が出る／各タスクに完了・進行中の別が付く／コミットハッシュや `TASK-<n>` が出力に混ざっていない／内部リポジトリ名が一般化されている。
  - Expected: 全チェック PASS。欠けていれば Task 1 に戻して SKILL.md を修正。

- [ ] **Step 3: 検証結果を記録**
  - 通ったチェック項目と、実際の出力サンプルを実行ログとして残す（j-devflow の検証工程）。この検証は UI を含まないため UAT は不要。
