---
title: UAT 証跡の PR 添付化に skill 側を合わせる — 実装計画
tag: [plan]
Project: devops
Task: 005-align-skills-with-pr-attached-uat-evidence
created_at: 2026-09-05
updated_at: 2026-09-05
---

# UAT 証跡の PR 添付化に skill 側を合わせる — 実装計画

**Goal:** UAT 証跡を `gh pr comment --attach` で PR に添付する配線を作り、旧「証跡を commit する」運用を指す 3 skill・計 7 箇所の記述を新運用に合わせる。

**Architecture:** 添付の契約（alt text / 50 件上限 / `gh` 下限バージョン / 部分失敗の扱い）を新規スクリプト `uat_attach.py` 1 箇所に集める。`j_finish.py` はそれを import して `push → PR → 証跡コメント → status → Discord` の順に呼ぶ。`j-pr`（Joifup 副作用なしの ad-hoc 経路）は同スクリプトを直接叩く。skill 本文は 3 ファイルを書き換える。

**Tech Stack:** Python 3（`uat_attach.py` は**標準ライブラリのみ**。`j_finish.py` の既存 PyYAML 依存はそのまま）／`unittest`（stdlib）／`gh` CLI。

## Global Constraints

- **`gh` の下限バージョンは `2.99.0`**（`--attach` の初出。50 ファイル上限も同 release）。
- **`--attach` は 1 コマンドあたり最大 50 ファイル。**
- **`--attach` には必ず `#<alt text>` を付ける。** alt text は証跡行の `name`（日本語）。ファイル名は ASCII slug なので説明を運べない。
- `uat_attach.py` は **標準ライブラリのみ**（PyYAML を import しない）。
- 証跡の読み取り元は `<evidence-dir>/results.jsonl`。**`summary.md` の markdown 表は parse しない。**
- 証跡行の形は `{"n":N,"name":"説明","file":"shot-01-x.png","kind":"shot"}`。`file` は evidence dir 内の **basename**。
- 動画は `.webm` / `.mp4`。**コメント本文から参照しない**（gh が末尾に裸 URL として追記し、GitHub がプレイヤー化する）。画像は `![name](./file)` で参照する（gh が URL に書き換える）。
- コミットメッセージは**英語**、Semantic Commit、Atomic。
- 対象リポジトリは `~/Joifup/dotfiles`。`~/.claude/skills/` は deploy 先であって編集対象ではない。

---

### Task 1: `uat_attach.py` の純粋部分

添付の判断・組み立てをすべて副作用なしの関数に閉じ込め、テストで固定する。

**Files:**
- Create: `.claude/skills/j-finish/scripts/uat_attach.py`
- Test: `.claude/skills/j-finish/scripts/test_uat_attach.py`

**Interfaces:**
- Consumes: なし
- Produces（Task 2 / 3 が依存する）:
  - `MIN_GH_VERSION: tuple[int, int, int] = (2, 99, 0)`
  - `MAX_ATTACH: int = 50`
  - `parse_gh_version(text: str) -> tuple[int, int, int] | None`
  - `parse_results(text: str) -> tuple[list[dict], int]` — `(rows, skipped)`
  - `shot_rows(rows: list[dict]) -> list[dict]`
  - `is_video(file: str) -> bool`
  - `render_comment(task: str, shots: list[dict]) -> str`
  - `attach_args(evidence_dir: str, shots: list[dict]) -> list[str]`
  - `body_with_evidence_link(body: str, url: str) -> str | None` — `None` なら `## UAT 証跡` 節が無く追記しなかった

- [ ] **Step 1: Write the failing test**

`.claude/skills/j-finish/scripts/test_uat_attach.py`:

```python
#!/usr/bin/env python3
"""uat_attach.py の純粋部分を固定する。stdlib の unittest のみ。

  python3 .claude/skills/j-finish/scripts/test_uat_attach.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uat_attach as ua

class TestParseGhVersion(unittest.TestCase):
    def test_parses_the_real_gh_output(self):
        text = "gh version 2.100.0 (2026-09-03)\nhttps://github.com/cli/cli/releases/tag/v2.100.0"
        self.assertEqual(ua.parse_gh_version(text), (2, 100, 0))

    def test_returns_none_when_unparseable(self):
        self.assertIsNone(ua.parse_gh_version("command not found"))

    def test_version_floor_is_2_99_0(self):
        self.assertEqual(ua.MIN_GH_VERSION, (2, 99, 0))
        self.assertLess(ua.parse_gh_version("gh version 2.98.1 (2026-08-01)"),
                        ua.MIN_GH_VERSION)
        self.assertGreaterEqual(ua.parse_gh_version("gh version 2.99.0 (2026-09-01)"),
                                ua.MIN_GH_VERSION)
        # 2.100.0 > 2.99.0 — 文字列比較なら逆転する組み合わせ
        self.assertGreaterEqual(ua.parse_gh_version("gh version 2.100.0 (2026-09-03)"),
                                ua.MIN_GH_VERSION)

class TestParseResults(unittest.TestCase):
    def test_keeps_valid_rows_and_counts_broken_ones(self):
        text = (
            '{"n":1,"name":"開く","status":"PASS"}\n'
            '{"n":1,"name":"初期表示","file":"shot-01-.png","kind":"shot"}\n'
            '{"n":2,"name":"壊れた行\n'
            '\n'
            '"just a string"\n'
        )
        rows, skipped = ua.parse_results(text)
        self.assertEqual(len(rows), 2)
        self.assertEqual(skipped, 2)

    def test_shot_rows_drops_judgement_rows(self):
        rows = [
            {"n": 1, "name": "開く", "status": "PASS"},
            {"n": 1, "name": "初期表示", "file": "a.png", "kind": "shot"},
        ]
        self.assertEqual(ua.shot_rows(rows), [rows[1]])

class TestIsVideo(unittest.TestCase):
    def test_classifies_by_extension(self):
        self.assertTrue(ua.is_video("clip-01-drag.webm"))
        self.assertTrue(ua.is_video("clip-01-drag.MP4"))
        self.assertFalse(ua.is_video("shot-01-open.png"))

class TestRenderComment(unittest.TestCase):
    def setUp(self):
        self.shots = [
            {"name": "初期表示", "file": "shot-01-shot.png"},
            {"name": "ドラッグ中", "file": "clip-01-drag.webm"},
        ]

    def test_images_are_referenced_inline_with_their_name_as_alt(self):
        body = ua.render_comment("005", self.shots)
        self.assertIn("![初期表示](./shot-01-shot.png)", body)

    def test_videos_are_not_referenced_so_gh_appends_a_player(self):
        body = ua.render_comment("005", self.shots)
        self.assertNotIn("(./clip-01-drag.webm)", body)
        self.assertIn("ドラッグ中", body)

    def test_escapes_brackets_in_the_alt_text(self):
        body = ua.render_comment("005", [{"name": "[重要] 表示", "file": "a.png"}])
        self.assertIn("![\\[重要\\] 表示](./a.png)", body)

class TestAttachArgs(unittest.TestCase):
    def test_pairs_each_path_with_its_name(self):
        args = ua.attach_args(".uat-evidence/005",
                              [{"name": "初期表示", "file": "shot-01-shot.png"}])
        self.assertEqual(
            args, ["--attach", ".uat-evidence/005/shot-01-shot.png#初期表示"])

    def test_falls_back_to_the_filename_when_name_is_empty(self):
        args = ua.attach_args(".uat-evidence/005", [{"name": "", "file": "a.png"}])
        self.assertEqual(args, ["--attach", ".uat-evidence/005/a.png"])

    def test_cap_is_50(self):
        self.assertEqual(ua.MAX_ATTACH, 50)

class TestBodyWithEvidenceLink(unittest.TestCase):
    def test_appends_inside_the_uat_section(self):
        body = "## UAT 証跡\n\n| step |\n\n## レビュー観点\n\n- x\n"
        out = ua.body_with_evidence_link(body, "https://example/pr#issuecomment-1")
        self.assertIn("証跡コメント: https://example/pr#issuecomment-1", out)
        self.assertLess(out.index("証跡コメント:"), out.index("## レビュー観点"))

    def test_appends_at_end_when_the_section_is_last(self):
        body = "## 概要\n\nx\n\n## UAT 証跡\n\n| step |\n"
        out = ua.body_with_evidence_link(body, "URL")
        self.assertTrue(out.rstrip().endswith("証跡コメント: URL"))

    def test_returns_none_when_there_is_no_uat_section(self):
        self.assertIsNone(ua.body_with_evidence_link("## 概要\n\nx\n", "URL"))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 .claude/skills/j-finish/scripts/test_uat_attach.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'uat_attach'`

- [ ] **Step 3: Write minimal implementation**

`.claude/skills/j-finish/scripts/uat_attach.py`（この Task では純粋部分のみ。CLI は Task 2）:

```python
#!/usr/bin/env python3
"""UAT 証跡を PR に添付する — `gh pr comment --attach` の配線。

joifup tasks/295 以降、UAT 証跡 (画像・動画) は repo に commit せず PR に
添付する。守るべき契約をこの 1 ファイルに集める:

  - `gh` は 2.99.0 以上 (--attach の初出。50 ファイル上限も同 release)
  - --attach は `<file>#<alt text>` 形式。alt は証跡行の `name`。
    ファイル名は ASCII slug なので日本語の説明を運べない (295 D5)
  - 1 コマンドあたり 50 ファイルまで
  - 画像はコメント本文から `![name](./file)` で参照する
    (gh がアップロード先 URL に書き換え、インライン表示される)
  - 動画は本文から参照しない。gh が末尾に裸 URL として追記し、GitHub が
    プレイヤー化する。`![]()` で参照すると画像扱いになり再生できない

証跡の読み取り元は `<evidence-dir>/results.jsonl` であって summary.md では
ない。`name` に `|` が入ると markdown の表はずれるが JSONL はずれない。

標準ライブラリのみに依存する (j_finish.py と違い PyYAML を要求しない)。
"""
import json
import re

MIN_GH_VERSION = (2, 99, 0)
MAX_ATTACH = 50
VIDEO_EXTS = (".webm", ".mp4")

def parse_gh_version(text):
    """`gh --version` の出力から (major, minor, patch) を取り出す。

    数値の tuple で返すのは、2.100.0 と 2.99.0 を文字列で比べると逆転する
    ため。判定できなければ None。
    """
    m = re.search(r"gh version (\d+)\.(\d+)\.(\d+)", text or "")
    if not m:
        return None
    return tuple(int(g) for g in m.groups())

def parse_results(text):
    """results.jsonl を行ごとに parse する。

    Playwright の worker が 1 行ずつ追記するファイルなので、途中で切れた行が
    残りうる。壊れた行は落として残りで進み、落とした本数を返す
    (joifup scripts/uat-summary.mjs の parseResults と同じ扱い)。
    """
    rows = []
    skipped = 0
    for line in (text or "").split("\n"):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except ValueError:
            skipped += 1
            continue
        if not isinstance(value, dict):
            skipped += 1
            continue
        rows.append(value)
    return rows, skipped

def shot_rows(rows):
    """証跡行 (kind == "shot") だけを取り出す。残りは step() の判定行。"""
    return [r for r in rows if r.get("kind") == "shot"]

def is_video(file):
    return str(file or "").lower().endswith(VIDEO_EXTS)

def _escape_alt(name):
    """markdown の alt text 内で `[` `]` を殺す (リンク構文が壊れるため)。"""
    return str(name or "").replace("[", "\\[").replace("]", "\\]")

def render_comment(task, shots):
    """証跡コメントの本文を組み立てる。

    画像は参照して説明付きでインライン表示させ、動画は参照せず gh の追記に
    任せる (docstring 冒頭の契約)。
    """
    images = [s for s in shots if not is_video(s.get("file"))]
    videos = [s for s in shots if is_video(s.get("file"))]
    lines = [f"## UAT 証跡 — {task}", ""]
    for i, s in enumerate(images, 1):
        lines += [f"**{i}. {s.get('name', '')}**", "",
                  f"![{_escape_alt(s.get('name'))}](./{s.get('file')})", ""]
    if videos:
        lines += ["### 動画", "",
                  "プレイヤーはこのコメントの末尾に表示されます。", ""]
        lines += [f"- {v.get('name', '')}（`{v.get('file')}`）" for v in videos]
        lines += [""]
    return "\n".join(lines)

def attach_args(evidence_dir, shots):
    """`--attach <path>#<alt>` の引数列を作る。

    `name` が空のときだけ `#` を落とす (gh はその場合ファイル名を alt に使う)。
    """
    args = []
    for s in shots:
        path = f"{evidence_dir.rstrip('/')}/{s.get('file')}"
        name = str(s.get("name") or "")
        args += ["--attach", f"{path}#{name}" if name else path]
    return args

def body_with_evidence_link(body, url):
    """PR 本文の `## UAT 証跡` 節の末尾に証跡コメントへのリンクを足す。

    節が無ければ None を返す (本文の別の場所に押し込むと、読み手が探す場所と
    ずれる)。GitHub のアンカーはコメント単位なので、証跡表の行ごとにリンクを
    張ることはできない — リンクは 1 本 (設計 D3)。
    """
    lines = (body or "").split("\n")
    start = None
    for i, line in enumerate(lines):
        if line.strip() == "## UAT 証跡":
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    tail = end
    while tail > start + 1 and not lines[tail - 1].strip():
        tail -= 1
    return "\n".join(lines[:tail] + ["", f"証跡コメント: {url}", ""] + lines[end:])
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 .claude/skills/j-finish/scripts/test_uat_attach.py`
Expected: PASS（`OK`、16 tests 前後）

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/j-finish/scripts/uat_attach.py .claude/skills/j-finish/scripts/test_uat_attach.py
git commit -m "feat(j-finish): add the pure core of the UAT evidence attach wiring"
```

---

### Task 2: `uat_attach.py` の CLI と `gh` 呼び出し

副作用側（バージョン検査・`gh pr comment` / `gh pr edit`・部分失敗の扱い）を足し、スクリプト単体で使えるようにする。

**Files:**
- Modify: `.claude/skills/j-finish/scripts/uat_attach.py`（Task 1 の末尾に追記）
- Test: `.claude/skills/j-finish/scripts/test_uat_attach.py`（クラスを追記）

**Interfaces:**
- Consumes: Task 1 の全関数
- Produces（Task 3 が依存する）:
  - `attach_evidence(pr, evidence_dir, task, dry_run=False, runner=None, reader=None) -> str | None`
    — 証跡コメントの URL。証跡 0 件なら `None`。
  - `AttachError(Exception)`

- [ ] **Step 1: Write the failing test**

`test_uat_attach.py` の `if __name__` より前に追記:

```python
class FakeRunner:
    """`gh` の代わり。呼ばれたコマンド列を記録し、決めた応答を返す。"""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, cmd):
        self.calls.append(cmd)
        out = self.responses.pop(0)
        if isinstance(out, Exception):
            raise out
        return out

class TestAttachEvidence(unittest.TestCase):
    RESULTS = (
        '{"n":1,"name":"開く","status":"PASS"}\n'
        '{"n":1,"name":"初期表示","file":"shot-01-shot.png","kind":"shot"}\n'
    )

    def test_stops_when_gh_is_too_old(self):
        runner = FakeRunner(["gh version 2.98.0 (2026-08-01)"])
        with self.assertRaises(ua.AttachError) as cm:
            ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                               runner=runner, reader=lambda p: self.RESULTS)
        self.assertIn("2.99.0", str(cm.exception))
        self.assertEqual(len(runner.calls), 1)  # gh --version だけで止まる

    def test_does_nothing_when_there_is_no_evidence(self):
        runner = FakeRunner(["gh version 2.100.0 (2026-09-03)"])
        out = ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                                 runner=runner,
                                 reader=lambda p: '{"n":1,"name":"x","status":"PASS"}\n')
        self.assertIsNone(out)
        self.assertEqual(len(runner.calls), 1)

    def test_returns_none_when_results_jsonl_is_missing(self):
        runner = FakeRunner(["gh version 2.100.0 (2026-09-03)"])

        def missing(path):
            raise FileNotFoundError(path)

        self.assertIsNone(ua.attach_evidence("https://pr/1", ".uat-evidence/005",
                                             "005", runner=runner, reader=missing))

    def test_stops_over_the_50_file_cap(self):
        rows = "".join(
            '{"n":%d,"name":"s%d","file":"shot-%02d.png","kind":"shot"}\n' % (i, i, i)
            for i in range(1, 52))
        runner = FakeRunner(["gh version 2.100.0 (2026-09-03)"])
        with self.assertRaises(ua.AttachError) as cm:
            ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                               runner=runner, reader=lambda p: rows)
        self.assertIn("51", str(cm.exception))

    def test_posts_the_comment_and_links_it_from_the_body(self):
        runner = FakeRunner([
            "gh version 2.100.0 (2026-09-03)",
            "## UAT 証跡\n\n| step |\n",                 # gh pr view --json body
            "https://github.com/o/r/pull/1#issuecomment-9",  # gh pr comment
            "",                                              # gh pr edit
        ])
        url = ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                                 runner=runner, reader=lambda p: self.RESULTS)
        self.assertEqual(url, "https://github.com/o/r/pull/1#issuecomment-9")
        comment = runner.calls[2]
        self.assertIn("--attach", comment)
        self.assertIn(".uat-evidence/005/shot-01-shot.png#初期表示", comment)
        self.assertEqual(runner.calls[3][:3], ["gh", "pr", "edit"])

    def test_does_not_swallow_a_failing_gh(self):
        runner = FakeRunner([
            "gh version 2.100.0 (2026-09-03)",
            "## UAT 証跡\n",
            ua.AttachError("gh exited 1: upload failed for shot-01-shot.png"),
        ])
        with self.assertRaises(ua.AttachError):
            ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                               runner=runner, reader=lambda p: self.RESULTS)

    def test_dry_run_touches_nothing_after_the_version_check(self):
        runner = FakeRunner(["gh version 2.100.0 (2026-09-03)"])
        url = ua.attach_evidence("https://pr/1", ".uat-evidence/005", "005",
                                 dry_run=True, runner=runner,
                                 reader=lambda p: self.RESULTS)
        self.assertIsNone(url)
        self.assertEqual(len(runner.calls), 1)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 .claude/skills/j-finish/scripts/test_uat_attach.py`
Expected: FAIL — `AttributeError: module 'uat_attach' has no attribute 'AttachError'`

- [ ] **Step 3: Write minimal implementation**

`uat_attach.py` の末尾に追記:

```python
import argparse
import os
import subprocess
import sys
import tempfile

class AttachError(Exception):
    """添付が成立しなかった。握り潰さず呼び出し側を止めるための例外。"""

def _run(cmd):
    """`gh` を実行し stdout を返す。非 0 は AttachError にする。

    gh は部分失敗のとき「成功したぶんでコメントを作り、非 0 で終了する」ので、
    終了コードを握り潰すと証跡が欠けたまま PASS に見える (設計のエラー
    ハンドリング節)。stderr をそのまま載せて止める。
    """
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise AttachError(
            f"{' '.join(cmd)} が exit {res.returncode} で失敗\n{res.stderr.strip()}")
    return res.stdout.strip()

def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()

def attach_evidence(pr, evidence_dir, task, dry_run=False, runner=None, reader=None):
    """UAT 証跡を PR にコメントとして添付し、そのコメント URL を返す。

    証跡が 1 つも無ければ何もせず None を返す — UI を変えない PR は証跡が
    無いのが正常だから。runner / reader は差し替え可能 (テスト用)。
    """
    run = runner or _run
    read = reader or _read

    version = parse_gh_version(run(["gh", "--version"]))
    if version is None or version < MIN_GH_VERSION:
        floor = ".".join(str(n) for n in MIN_GH_VERSION)
        raise AttachError(
            f"gh {floor} 以上が必要です (--attach の初出)。検出: {version}。"
            " `brew upgrade gh` などで更新してください")

    try:
        text = read(os.path.join(evidence_dir, "results.jsonl"))
    except OSError:
        print(f"uat-attach: {evidence_dir}/results.jsonl が無いので添付をスキップ",
              file=sys.stderr)
        return None

    rows, skipped = parse_results(text)
    if skipped:
        print(f"uat-attach: results.jsonl の壊れた行を {skipped} 行スキップしました"
              " — 証跡が不完全な可能性があります", file=sys.stderr)
    shots = shot_rows(rows)
    if not shots:
        print("uat-attach: 証跡が 0 件のため添付しません", file=sys.stderr)
        return None
    if len(shots) > MAX_ATTACH:
        raise AttachError(
            f"証跡が {len(shots)} 件あり gh の上限 {MAX_ATTACH} を超えています。"
            " 分割ではなく shot() を減らしてください")

    body = render_comment(task, shots)
    args = attach_args(evidence_dir, shots)
    if dry_run:
        print(f"[dry-run] gh pr comment {pr} --body-file <tmp> {' '.join(args)}")
        return None

    pr_body = run(["gh", "pr", "view", pr, "--json", "body", "--jq", ".body"])

    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(body)
        body_file = fh.name
    try:
        url = run(["gh", "pr", "comment", pr, "--body-file", body_file] + args)
    finally:
        os.unlink(body_file)
    url = url.splitlines()[-1].strip() if url else ""

    linked = body_with_evidence_link(pr_body, url)
    if linked is None:
        print("uat-attach: PR 本文に `## UAT 証跡` 節が無いためリンクを追記しません",
              file=sys.stderr)
    else:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                         encoding="utf-8") as fh:
            fh.write(linked)
            edit_file = fh.name
        try:
            run(["gh", "pr", "edit", pr, "--body-file", edit_file])
        finally:
            os.unlink(edit_file)
    return url

def main():
    ap = argparse.ArgumentParser(
        prog="uat-attach",
        description="UAT 証跡を gh pr comment --attach で PR に添付する")
    ap.add_argument("--evidence-dir", required=True,
                    help="例: .uat-evidence/005")
    ap.add_argument("--pr", required=True, help="PR の URL / 番号 / ブランチ名")
    ap.add_argument("--task", help="コメント見出しに出す task id"
                                   "（既定: evidence-dir の basename）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    task = args.task or os.path.basename(args.evidence_dir.rstrip("/"))
    try:
        url = attach_evidence(args.pr, args.evidence_dir, task, args.dry_run)
    except AttachError as exc:
        sys.exit(f"uat-attach: {exc}")
    if url:
        print(url)

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 .claude/skills/j-finish/scripts/test_uat_attach.py`
Expected: PASS（`OK`）

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/j-finish/scripts/uat_attach.py .claude/skills/j-finish/scripts/test_uat_attach.py
git commit -m "feat(j-finish): wire uat_attach to gh pr comment --attach"
```

---

### Task 3: `j_finish.py` の統合と警告の反転

**Files:**
- Modify: `.claude/skills/j-finish/scripts/j_finish.py`
- Test: `.claude/skills/j-finish/scripts/test_j_finish.py`（新規）

**Interfaces:**
- Consumes: `uat_attach.attach_evidence` / `uat_attach.AttachError`
- Produces: `j_finish._warn_uat_evidence(changed, evidence_dir, exists=os.path.isfile) -> list[str]`（出した警告の一覧。テストのため戻り値を持つ）

- [ ] **Step 1: Write the failing test**

`.claude/skills/j-finish/scripts/test_j_finish.py`:

```python
#!/usr/bin/env python3
"""j_finish.py の UAT 証跡チェックを固定する。

  python3 .claude/skills/j-finish/scripts/test_j_finish.py
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import j_finish as jf

class TestWarnUatEvidence(unittest.TestCase):
    def test_warns_when_ui_changed_without_a_local_evidence_run(self):
        warnings = jf._warn_uat_evidence(
            ["apps/web/src/App.tsx"], ".uat-evidence/005", exists=lambda p: False)
        self.assertEqual(len(warnings), 1)
        self.assertIn("pnpm uat", warnings[0])

    def test_quiet_when_the_evidence_run_exists(self):
        self.assertEqual(
            jf._warn_uat_evidence(["apps/web/src/App.tsx"], ".uat-evidence/005",
                                  exists=lambda p: True),
            [])

    def test_warns_when_no_evidence_dir_was_given_for_a_ui_change(self):
        warnings = jf._warn_uat_evidence(["apps/web/src/App.tsx"], None,
                                         exists=lambda p: True)
        self.assertEqual(len(warnings), 1)
        self.assertIn("--uat-evidence-dir", warnings[0])

    def test_e2e_only_changes_do_not_count_as_ui(self):
        self.assertEqual(
            jf._warn_uat_evidence(["apps/web/e2e/005.uat.spec.ts"], None,
                                  exists=lambda p: False),
            [])

    def test_warns_when_evidence_was_committed(self):
        warnings = jf._warn_uat_evidence(
            [".uat-evidence/005/shot-01.png"], ".uat-evidence/005",
            exists=lambda p: True)
        self.assertEqual(len(warnings), 1)
        self.assertIn("commit", warnings[0])

    def test_reports_both_problems_at_once(self):
        warnings = jf._warn_uat_evidence(
            ["apps/web/src/App.tsx", ".uat-evidence/005/shot-01.png"],
            ".uat-evidence/005", exists=lambda p: False)
        self.assertEqual(len(warnings), 2)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 .claude/skills/j-finish/scripts/test_j_finish.py`
Expected: FAIL — `AttributeError: module 'j_finish' has no attribute '_warn_uat_evidence'`

- [ ] **Step 3: Write minimal implementation**

3-a. `j_finish.py` の import 群の直後（`try: import yaml` ブロックの下）に追記:

```python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uat_attach import AttachError, attach_evidence  # noqa: E402
```

3-b. `_warn_missing_uat_evidence` を丸ごと次で置き換える:

```python
def _changed_paths(head_range):
    """push 範囲で変わったパス。git が失敗したら空 (チェックを黙って諦める)。"""
    try:
        return subprocess.run(
            ["git", "diff", "--name-only", head_range],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines()
    except (subprocess.CalledProcessError, OSError):
        return []

def _warn_uat_evidence(changed, evidence_dir, exists=os.path.isfile):
    """UAT 証跡まわりを警告する (never blocks)。返り値は出した警告の一覧。

    joifup tasks/295 で証跡は commit せず PR に添付する形になった。旧実装は
    「diff に .uat-evidence/ が無ければ警告」で、意味がちょうど反転していた。
    見るべきものは 2 つに変わる:

      1. UI を変えたのに `pnpm uat` を回した形跡 (results.jsonl) が手元に無い
         — 証跡ゼロの PR が出る
      2. .uat-evidence/ が commit されている — 新しい失敗様式。gitignore が
         無い repo で起きる

    ブロックしないのは旧実装と同じ: apps/web の diff が非 UI (config だけ)
    のこともあるため。
    """
    warnings = []
    touches_ui = any(p.startswith("apps/web/") and not p.startswith("apps/web/e2e/")
                     for p in changed)
    committed = [p for p in changed if p.startswith(".uat-evidence/")]
    if committed:
        warnings.append(
            "j-finish: WARNING — .uat-evidence/ が commit されています "
            f"（例: {committed[0]}）。証跡は commit せず PR に添付します。"
            " .gitignore を確認してください")
    if touches_ui:
        if not evidence_dir:
            warnings.append(
                "j-finish: WARNING — apps/web が変わっていますが "
                "--uat-evidence-dir が指定されていません。証跡が PR に付きません")
        elif not exists(os.path.join(evidence_dir, "results.jsonl")):
            warnings.append(
                f"j-finish: WARNING — apps/web が変わっていますが {evidence_dir}"
                "/results.jsonl がありません。`pnpm uat --task <id>` を回して"
                " ください")
    for w in warnings:
        print(w, file=sys.stderr)
    return warnings
```

3-c. `main()` の引数に追加（`--no-discord` の下）:

```python
    ap.add_argument("--uat-evidence-dir",
                    help="UAT 証跡 dir（例: .uat-evidence/005）。"
                         "指定すると PR 作成後に証跡コメントを添付する")
```

3-d. 旧呼び出し

```python
    _warn_missing_uat_evidence(f"origin/{args.base}...HEAD")
```

を次で置き換える:

```python
    _warn_uat_evidence(_changed_paths(f"origin/{args.base}...HEAD"),
                       args.uat_evidence_dir)
```

3-e. 「2. PR」ブロックの直後、「3. surgical status edit」の前に証跡コメントを挟む（設計 D5 の実行順 `push → PR → 証跡コメント → status → Discord`）。既存の `# 3.` / `# 4.` コメントは `# 4.` / `# 5.` に付け替える:

```python
    # 3. UAT 証跡コメント（画像・動画を PR に添付）
    if args.uat_evidence_dir and not args.no_pr:
        task_id = os.path.basename(args.uat_evidence_dir.rstrip("/"))
        try:
            comment_url = attach_evidence(pr_url, args.uat_evidence_dir, task_id,
                                          args.dry_run)
        except AttachError as exc:
            die(f"UAT 証跡の添付に失敗: {exc}")
        if comment_url:
            print(f"UAT 証跡: {comment_url}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 .claude/skills/j-finish/scripts/test_j_finish.py`
Expected: PASS（`OK`）

Run: `python3 .claude/skills/j-finish/scripts/j_finish.py --help`
Expected: `--uat-evidence-dir` がヘルプに出る

- [ ] **Step 5: Commit**

```bash
git add .claude/skills/j-finish/scripts/j_finish.py .claude/skills/j-finish/scripts/test_j_finish.py
git commit -m "fix(j-finish): attach UAT evidence to the PR and un-invert the evidence warning"
```

---

### Task 4: skill 本文 7 箇所の書き換え

**Files:**
- Modify: `.claude/skills/j-devflow/SKILL.md`（step 10）
- Modify: `.claude/skills/j-finish/SKILL.md`（Steps 4 / What the script guarantees / Common Mistakes）
- Modify: `.claude/skills/j-pr/references/pr-body.md`（`## UAT 証跡` 節 / ルール）

**Interfaces:**
- Consumes: Task 2 の CLI（`uat_attach.py --evidence-dir --pr`）、Task 3 の `--uat-evidence-dir`
- Produces: なし

- [ ] **Step 1: `j-devflow/SKILL.md` の step 10 を差し替える**

現在の 10 行目（`10. **UAT 自動化 + \`j-finish\`**:` で始まる段落）全体を次で置き換える:

```markdown
10. **UAT 自動化 + `j-finish`**: UI 変更を含む branch は `pnpm uat --task <id>` を実行して `.uat-evidence/<id>/` に証跡を生成する（spec で確定した受け入れ基準を `apps/web/e2e/<id>.uat.spec.ts` に書いてから）。**証跡は commit しない** — `.uat-evidence/` は gitignore 済みで、画像・動画は `gh pr comment --attach` で PR に添付する（joifup tasks/295 以降）。PR 本文には pr-body recipe の `## 受け入れ基準` と `## UAT 証跡`（summary.md の PASS/FAIL 表＝テキストのみ）を載せ、画素は証跡コメント側に置く。その後 `j-finish` に `--uat-evidence-dir .uat-evidence/<id>` を渡すと、push→PR→証跡コメント→Task→In review→Discord を行う。**UAT ユーザーアクション task は file しない**（旧 heavy 分岐は廃止）。UI を含まない変更では UAT を省略し `## テスト` のみで良い。**The machine stops here.**
```

- [ ] **Step 2: `j-finish/SKILL.md` の step 3 のコマンド例に新フラグを足す**

`python3 scripts/j_finish.py --task-file ...` のコードブロックを次で置き換える:

````markdown
```bash
python3 scripts/j_finish.py --task-file <tasks/NNN-*.md> \
  --pr-title "<ja title>" --pr-body-file <body.md> \
  [--uat-evidence-dir .uat-evidence/<id>] \
  [--head <branch>] [--status "In review"] [--dry-run]
```
````

- [ ] **Step 3: `j-finish/SKILL.md` の step 4 を差し替える**

現在の `4. **UAT 証跡を PR に載せる。**` 段落全体を次で置き換える:

```markdown
4. **UAT 証跡を PR に載せる。** 承認者はコードを読まず、証跡を見て承認する。UI 変更を含む場合は `pnpm uat --task <id>` を回し、**`--uat-evidence-dir .uat-evidence/<id>` を渡す**。**証跡は commit しない** — 画像・動画は `gh pr comment --attach` で PR に添付され（joifup tasks/295 以降。`.uat-evidence/` は gitignore 済み）、PR 本文の `## UAT 証跡` には `summary.md` の PASS/FAIL 表（テキスト）と証跡コメントへのリンクだけが載る。受け入れ基準は `## 受け入れ基準` に inline 展開する。**UAT ユーザーアクション task は新規 file しない**（旧 light/heavy 分岐・md2joifup --db tasks による UAT task 発行は廃止）。UI を含まない変更では UAT を省略してよい。
```

- [ ] **Step 4: `j-finish/SKILL.md` の「What the script guarantees」の UAT 行を差し替える**

現在の `- **UAT evidence check** — warns ...` 行を次の 2 行で置き換える:

```markdown
- **UAT evidence attach** — with `--uat-evidence-dir`, posts the evidence comment (`gh pr comment --attach`, alt text = each shot's `name`) right after the PR is created, then links it from the body's `## UAT 証跡`. Requires `gh >= 2.99.0` and stops loudly below it; a partial upload fails the finish instead of silently shipping a PASS with missing evidence.
- **UAT evidence check** — warns (never blocks) if `apps/web/` changed without a local `pnpm uat` run, or if `.uat-evidence/` was committed (it must not be); runs under `--dry-run` too, since it is read-only.
```

- [ ] **Step 5: `j-finish/SKILL.md` の Common Mistakes の UAT 行を差し替える**

現在の `- UI 変更なのに \`.uat-evidence/<id>/\` を commit せず PR を出す — ...` 行を次で置き換える:

```markdown
- UI 変更なのに `pnpm uat` を回さず PR を出す — 証跡が空になる。逆に `.uat-evidence/` を **commit** するのも誤り（gitignore 対象。PR には添付する）。
```

- [ ] **Step 6: `j-pr/references/pr-body.md` の `## UAT 証跡` 節を差し替える**

positive recipe 内の

```markdown
## UAT 証跡
[.uat-evidence/<TASK>/summary.md の PASS/FAIL 表を転記。screenshot は private repo のため PR body には埋め込まず、`.uat-evidence/<TASK>/` を Files changed タブで確認する旨を明記]
```

を次で置き換える:

```markdown
## UAT 証跡
[.uat-evidence/<TASK>/summary.md の `結果:` 行と PASS/FAIL 表を転記。**画像は本文に入れない**（`## レビュー観点` 以下が押し下げられ、diff を見る前に読むべきものが読めなくなる）。画素は `gh pr comment --attach` の証跡コメント側にあり、その URL が `証跡コメント: <url>` としてこの節の末尾に自動追記される]
```

- [ ] **Step 7: `j-pr/references/pr-body.md` のルール 2 行を差し替える**

```markdown
- **UI 変更を含む PR は `## UAT 証跡` 必須**（`pnpm uat --task <id>` を実行し `.uat-evidence/<id>/summary.md` を転記）。UI を含まない変更では省略可。
```

を次の 2 行で置き換える:

```markdown
- **UI 変更を含む PR は `## UAT 証跡` 必須**（`pnpm uat --task <id>` を実行し `.uat-evidence/<id>/summary.md` の判定表を転記）。UI を含まない変更では省略可。
- **証跡は commit しない**（joifup tasks/295 以降。`.uat-evidence/` は gitignore 対象）。画像・動画は PR に添付する。ad-hoc 経路（`j-pr`）では PR 作成後に自分で叩く: `python3 ~/.claude/skills/j-finish/scripts/uat_attach.py --evidence-dir .uat-evidence/<id> --pr <PR URL>`（`gh >= 2.99.0` が必要）。`j-finish` 経路では `--uat-evidence-dir` が同じことを行う。
```

- [ ] **Step 8: 旧運用の記述が残っていないことを確認する**

Run: `grep -rn "Files changed\|証跡.*commit する\|を commit し" .claude/skills/j-devflow .claude/skills/j-finish .claude/skills/j-pr`
Expected: 「証跡を commit する」を指す行が 0 件（`commit しない` を述べる行だけがヒットする）

- [ ] **Step 9: Commit**

```bash
git add .claude/skills/j-devflow/SKILL.md .claude/skills/j-finish/SKILL.md .claude/skills/j-pr/references/pr-body.md
git commit -m "docs(skills): align UAT evidence instructions with PR attachments"
```
