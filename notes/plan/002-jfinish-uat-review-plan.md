---
ID: NOTE-80
Project: devops
Task: '002-jfinish-uat-review'
created_at: '2026-07-14'
tag:
- plan
title: j-finish UAT 手順提示型への改善 Implementation Plan
updated_at: '2026-07-14'
---

# j-finish UAT 手順提示型への改善 Implementation Plan

**Goal:** j-finish のレビュー依頼を、承認専用タスクの自動起票をやめて UAT（受け入れテスト）手順提示型に改める。

**Architecture:** 変更は3ユニットに閉じる。(1) `j_finish.py` から step 4（承認専用タスク起票）と専用ヘルパを除去しメカニクス専任に純化。(2) `j-finish/SKILL.md` を UAT 分岐（軽=セッションテキスト+検証準備／重=`md2joifup --db tasks` で検証タスク起票してファイル提示）に書き換え。(3) `j-devflow/SKILL.md` の Phase B step 10 記述を同期。UAT の中身判断はセッション責務、スクリプトはメカニクス専任という既存分業を維持する。

**Tech Stack:** Python 3（PyYAML）、bash、Joifup adapters（md2joifup）、superpowers 背骨。標準テストスイート無し → 検証は `--dry-run` / `--help` / `ast.parse` 構文チェック / grep で行う。

## Global Constraints

- スクリプト＝メカニクス専任、UAT の内容判断＝セッション責務（PR 本文と同じ分業）。スクリプトに UAT 内容を埋めない。
- 検証準備は「設定なし・セッションが都度実施」。専用スキーマ・projects 本文パース等の新しい永続/設定面を追加しない（YAGNI）。
- Joifup スキーマ（tasks/notes の schema.yaml）は Joifup 所有。**一切変更しない**。
- `md2joifup.py` は変更しない。重い場合の検証タスクは既存の `md2joifup --db tasks` をそのまま使う。
- Discord embed（title「👀 レビュー依頼」・description・color・fields・timestamp）は変更しない。`import datetime` / `import json` は Discord step で使うため残す。
- コミットメッセージは英語・Semantic Commit・Atomic。
- 削除して良いのは `file_user_action` からのみ参照されるヘルパ（コード確認済み）: `slugify` / `next_number` / `emit_frontmatter` / `fmt_scalar` / `_QUOTE_START`。`datetime`/`json` import は残す。
- 作業ディレクトリ: worktree `.worktrees/002-jfinish-uat-review`（ブランチ `feature/002-jfinish-uat-review`）。スクリプトの実体パスは `.claude/skills/j-finish/scripts/j_finish.py`。

---

## File Structure

- `.claude/skills/j-finish/scripts/j_finish.py` — メカニクス専任スクリプト。step 4 と専用ヘルパを除去。
- `.claude/skills/j-finish/SKILL.md` — j-finish のスキル記述。承認待ち記述を削除し UAT 分岐を追記。
- `.claude/skills/j-devflow/SKILL.md` — シーケンサ記述。Phase B step 10 の j-finish 説明を同期。

---

### Task 1: j_finish.py から承認専用タスク起票を除去

**Files:**
- Modify: `.claude/skills/j-finish/scripts/j_finish.py`

**Interfaces:**
- Consumes: なし（既存スクリプトの編集）
- Produces: 変更後の `j_finish.py` は5→4ステップ（push / PR / status / Discord）。`--no-user-action` 引数と `file_user_action()`・専用ヘルパ（`slugify`/`next_number`/`emit_frontmatter`/`fmt_scalar`/`_QUOTE_START`）は存在しない。`--no-pr`/`--no-discord`/`--dry-run`/`--head`/`--base`/`--status`/`--project`/`--task-file`/`--pr-title`/`--pr-body-file` は不変。

**参考：現状の該当行（編集前の目印）**
- `import datetime`(24) / `import json`(25) は残す。
- 削除対象ヘルパ定義: `next_number`(102-107)、`slugify`(110-111)、`_QUOTE_START`(114)、`fmt_scalar`(117-122)、`emit_frontmatter`(125-132)、`file_user_action`(135-153)。
- 削除対象 argparse: `ap.add_argument("--no-user-action", action="store_true")`。
- 削除対象呼び出しブロック: `main()` 内の「# 4. user-action task」ブロック（`if not args.no_user_action:` の3行）。
- 維持: `datetime` は Discord step の timestamp（223-224）で、`json` は payload（235）で使用。

- [ ] **Step 1: 削除前ベースラインを記録（RED 相当）**

worktree ルートで実行し、現状の承認待ちタスク起票を確認する:

```bash
cd .worktrees/002-jfinish-uat-review
grep -n "no-user-action\|file_user_action\|承認待ち" .claude/skills/j-finish/scripts/j_finish.py
```

Expected: `--no-user-action` 引数・`file_user_action` 定義/呼び出し・`承認待ち` 文字列がヒットする（除去前の状態）。

- [ ] **Step 2: 専用ヘルパ関数群を削除**

`.claude/skills/j-finish/scripts/j_finish.py` から次の関数・定数定義を削除する（`file_user_action` からのみ使用、確認済み）:
- `next_number(d)` 関数定義（現 102-107 行相当）
- `slugify(text)` 関数定義（現 110-111 行相当）
- `_QUOTE_START = ...` 定数（現 114 行相当）
- `fmt_scalar(v)` 関数定義（現 117-122 行相当）
- `emit_frontmatter(items)` 関数定義（現 125-132 行相当）
- `file_user_action(...)` 関数定義（現 135-153 行相当）

`read_title`・`surgical_status`・`valid_status_values`・`find_schema`・`run`・`die` は**残す**（他ステップで使用）。`import datetime`・`import json`・`import yaml` も残す。

- [ ] **Step 3: argparse から --no-user-action を削除**

`main()` の引数定義から次の1行を削除:

```python
    ap.add_argument("--no-user-action", action="store_true")
```

`--no-pr` と `--no-discord` の行は残す。

- [ ] **Step 4: main() の step 4 呼び出しブロックを削除**

次のブロックを丸ごと削除する:

```python
    # 4. user-action task
    if not args.no_user_action:
        dest = file_user_action(tasks_dir, parent_id, parent_title,
                                args.project, pr_url)
        print(f"user-action task: {dest}")
```

削除後、`# 3. surgical status edit` ブロックの直後が `# 5. Discord` ブロックになる。**Discord ブロックのコメント番号「5」は変更しない**（変更するとレビューで無関係な差分になる。番号の連続性より diff 最小を優先）。ただし step の実体はもう4つなので、`# 3.` の次が `# 5.` で番号が飛ぶことになる。可読性のため Discord ブロックのコメントを `# 4. Discord — rich embed ...` に振り直すのは許容（この振り直しをする場合はコメント行のみ変更、コード本体は不変）。

**この計画では番号を振り直す**方針とする: `# 5. Discord` を `# 4. Discord` に変更（コメントのみ）。

- [ ] **Step 5: 構文チェック（GREEN 相当）**

```bash
cd .worktrees/002-jfinish-uat-review
python3 -c "import ast; ast.parse(open('.claude/skills/j-finish/scripts/j_finish.py').read()); print('syntax OK')"
python3 .claude/skills/j-finish/scripts/j_finish.py --help
```

Expected: `syntax OK` が出力され、`--help` が正常終了して usage を表示し、その usage に `--no-user-action` が**含まれない**こと。

- [ ] **Step 6: 除去の確認（回帰確認）**

```bash
cd .worktrees/002-jfinish-uat-review
grep -n "no-user-action\|file_user_action\|承認待ち\|slugify\|emit_frontmatter\|_QUOTE_START" .claude/skills/j-finish/scripts/j_finish.py || echo "ALL REMOVED"
grep -n "import datetime\|import json" .claude/skills/j-finish/scripts/j_finish.py
```

Expected: 1つ目は `ALL REMOVED`（`next_number` は自然文に出ないので対象外だが、必要なら追加確認）。2つ目で `import datetime` と `import json` が残っていること。

- [ ] **Step 7: dry-run で4系統のみになったことを確認**

`--dry-run` は git/gh/curl を実行せず表示する。task ファイルは実在の `tasks/002-jfinish-uat-review.md` を使い、PR 本文はダミーを用意する。**status 副作用を避けるため、実行後に git で戻す**。

```bash
cd .worktrees/002-jfinish-uat-review
printf '# dummy\n本文\n' > /tmp/uat-dry-body.md
before=$(grep '^status:' tasks/002-jfinish-uat-review.md)
python3 .claude/skills/j-finish/scripts/j_finish.py \
  --task-file tasks/002-jfinish-uat-review.md \
  --pr-title "dummy" --pr-body-file /tmp/uat-dry-body.md --dry-run
# 副作用（status 行の書き換え）を戻す
git checkout -- tasks/002-jfinish-uat-review.md
echo "restored: $before"
# tasks/ に承認待ちファイルが増えていないこと
ls tasks/ | grep -i approve && echo "UNEXPECTED approve task" || echo "no approve task (OK)"
```

Expected: dry-run 出力に `[dry-run] git push ...` / `[dry-run] gh pr create ...` / `[dry-run] curl ... POST`（Discord）の3系統＋`status -> In review` が出る。`user-action task:` の行は**出ない**。`tasks/` に approve ファイルが増えていない（`no approve task (OK)`）。`git checkout` で status が元に戻る。

- [ ] **Step 8: Commit**

```bash
cd .worktrees/002-jfinish-uat-review
git add .claude/skills/j-finish/scripts/j_finish.py
git commit -m "refactor(j-finish): drop approval-only task creation from finish script

The 承認待ち user-action task is no longer filed at finish time. Removes
file_user_action() and its now-unused helpers (slugify, next_number,
emit_frontmatter, fmt_scalar, _QUOTE_START) and the --no-user-action flag.
Script is now push / PR / status / Discord only. datetime and json imports
stay (used by the Discord embed)."
```

---

### Task 2: j-finish/SKILL.md を UAT 手順提示型に書き換え

**Files:**
- Modify: `.claude/skills/j-finish/SKILL.md`

**Interfaces:**
- Consumes: Task 1 で確定した「スクリプトは4ステップ（push/PR/status/Discord）、承認待ちタスク起票なし」という事実。
- Produces: 承認待ちタスクへの言及が無く、UAT 分岐（軽/重）と検証準備の責務が明記された SKILL.md。

- [ ] **Step 1: 現状の承認待ち記述箇所を特定（RED 相当）**

```bash
cd .worktrees/002-jfinish-uat-review
grep -n "承認待ち\|Approval task\|user-action\|user action\|no-user-action" .claude/skills/j-finish/SKILL.md
```

Expected: Overview 分業説明・Steps・"What the script guarantees" の Approval task 項・Common Mistakes 等に承認待ち系の記述がヒットする。

- [ ] **Step 2: "What the script guarantees" から Approval task 項を削除し UAT 記述に差し替え**

現状（該当箇所）:
```markdown
- **Approval task** — a child `承認待ち: <title>` Task (status Not started, `parent` = the finished task's id) so the approval surfaces in Joifup.
- **Scoped Discord** — a Japanese rich embed titled 「👀 レビュー依頼」 ...
```

これを次に変更（Approval task 行を削除、Discord 行は残す）:
```markdown
- **Surgical status edit** — （既存のまま）
- **Scoped Discord** — （既存のまま）
```

つまり "What the script guarantees" は「Surgical status edit」と「Scoped Discord」の2項のみになる（Approval task 項を除去）。

- [ ] **Step 3: Steps セクションの step 3 の列挙から承認待ちを除去**

現状の step 3 は「push → PR → status→In review → approval task → Discord, in that order」と記述している。これを「push → PR → status→In review → Discord, in that order」に変更（`approval task →` を削除）。

- [ ] **Step 4: UAT レビュー依頼の分岐セクションを追加**

Steps の step 4（Report）を、UAT 手順提示を含む形に拡張する。現状:
```markdown
4. **Report** the PR URL and hand off: tell the user it awaits their approval.
```

これを次に置き換える:
```markdown
4. **Present the UAT (acceptance-test) review request.** The approver *runs* the change, they do not read code. The *content* of the UAT is yours (like the PR body); the script does not carry it. Judge how heavy the verification is and branch:
   - **Light** (a few steps the approver can follow inline): first do the verification prep yourself so they can start immediately — restart the daemon, start the dev server, seed data, whatever this change needs (project-specific; decide it in-session, there is no config for it). Then present the UAT steps as session text.
   - **Heavy** (many cases, order-dependent, multi-environment, or worth keeping): file a user-action Task carrying the verification cases via `md2joifup --db tasks` (content authored by you), and present its file path. Do the prep as in the light case.
5. **Report** the PR URL and hand off: tell the user it awaits their approval (after they run the UAT).
```

- [ ] **Step 5: Common Mistakes / Overview の承認待ち言及を掃除**

`grep` で残存を確認し、承認待ちタスクを前提にした記述（あれば Overview の分業説明の「approval-task creation」等）を UAT 文脈に合わせて修正、または承認待ち特有の文言を除去する。Overview の「the *mechanics* (surgical status edit, approval-task creation, relation-id format, PR→notify ordering)」は「approval-task creation」を削り「the *mechanics* (surgical status edit, relation-id format, PR→notify ordering)」にする。

- [ ] **Step 6: 整合確認（GREEN 相当）**

```bash
cd .worktrees/002-jfinish-uat-review
grep -n "承認待ち\|Approval task\|approval-task\|no-user-action\|user-action Task" .claude/skills/j-finish/SKILL.md
grep -n "UAT\|acceptance-test\|verification prep\|Light\|Heavy" .claude/skills/j-finish/SKILL.md
```

Expected: 1つ目は「承認待ち」「Approval task」「approval-task creation」「no-user-action」が**消えている**こと（`user-action Task` は step 4 の md2joifup 記述で1回だけ残ってよい）。2つ目で UAT 分岐の記述がヒットすること。

- [ ] **Step 7: Commit**

```bash
cd .worktrees/002-jfinish-uat-review
git add .claude/skills/j-finish/SKILL.md
git commit -m "docs(j-finish): reframe review request as UAT, drop approval-only task

SKILL.md no longer documents an auto-filed 承認待ち task. Adds the UAT
review-request branch: light -> in-session prep + UAT steps as text;
heavy -> file a verification user-action task via md2joifup and present it.
Verification content is the session's job; the script stays mechanics-only."
```

---

### Task 3: j-devflow/SKILL.md の Phase B step 10 を同期

**Files:**
- Modify: `.claude/skills/j-devflow/SKILL.md`

**Interfaces:**
- Consumes: Task 1・2 で確定した j-finish の新挙動（承認待ちタスクなし・UAT 分岐）。
- Produces: Phase B step 10 の j-finish 説明が新挙動と一致した j-devflow/SKILL.md。

- [ ] **Step 1: 該当記述を特定（RED 相当）**

```bash
cd .worktrees/002-jfinish-uat-review
grep -n "承認待ち\|approval task\|In review → 承認\|Discord" .claude/skills/j-devflow/SKILL.md
```

Expected: Phase B の step 10「`j-finish`: push → PR (Japanese) → Task → In review → 承認待ち task → Discord.」がヒットする。

- [ ] **Step 2: step 10 の記述を更新**

現状:
```markdown
10. `j-finish`: push → PR (Japanese) → Task → In review → 承認待ち task → Discord. **The machine stops here.**
```

これを次に置き換える:
```markdown
10. `j-finish`: push → PR (Japanese) → Task → In review → Discord, then present the UAT (acceptance-test) review request — light = do the verification prep and show the steps as text; heavy = file a verification user-action task (`md2joifup --db tasks`) and present its file. No approval-only task is filed. **The machine stops here.**
```

- [ ] **Step 3: 整合確認（GREEN 相当）**

```bash
cd .worktrees/002-jfinish-uat-review
grep -n "承認待ち task\|UAT\|verification user-action\|No approval-only" .claude/skills/j-devflow/SKILL.md
```

Expected: 「承認待ち task」が step 10 から消え、「UAT」「verification user-action」「No approval-only task」がヒットすること。他箇所（Phase C の human 承認説明など）の「承認」は正当なので残ってよい。

- [ ] **Step 4: Commit**

```bash
cd .worktrees/002-jfinish-uat-review
git add .claude/skills/j-devflow/SKILL.md
git commit -m "docs(j-devflow): sync Phase B step 10 with j-finish UAT behavior

Phase B's finish step no longer files an approval-only task; it presents a
UAT review request (light = in-session prep + text steps, heavy = a
verification user-action task via md2joifup)."
```

---

## Self-Review

**1. Spec coverage:**
- 承認専用タスク廃止 → Task 1（スクリプト）＋ Task 2/3（ドキュメント）。✓
- 分業不変（スクリプト=メカニクス、内容=セッション）→ Global Constraints ＋ Task 2 step 4 の文言。✓
- 検証準備は設定なし・セッション都度 → Task 2 step 4「decide it in-session, there is no config」。✓
- 軽/重分岐 → Task 2 step 4、Task 3 step 2。✓
- Discord 据え置き → Global Constraints、Task 1 で Discord ブロック不変（コメント番号のみ）。✓
- SKILL.md 2件更新 → Task 2・3。✓
- Joifup スキーマ・md2joifup 不変 → Global Constraints で明記、どのタスクも触れない。✓

**2. Placeholder scan:** TBD/TODO/曖昧語なし。各コード変更は現状スニペット＋置換後を明示。✓

**3. Type consistency:** 関数名（`file_user_action`/`surgical_status`/`read_title`）・フラグ名（`--no-user-action`）・削除ヘルパ名は全タスクで一貫。Task 1 が削除し Task 2/3 がその事実に依存する順序も整合。✓
