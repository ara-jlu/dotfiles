---
title: 日本語のハード折り返しをやめる 実装計画
tag: [plan]
Project: devops
Task: 008-no-hard-wrap-japanese
created_at: 2026-09-12
updated_at: 2026-09-12
---

# 日本語のハード折り返しをやめる 実装計画

**Goal:** 日本語の md 本文でハード折り返しをやめる規約を置き、dotfiles の既存分を機械的に結合する。

**Architecture:** 規約はグローバル `CLAUDE.md` の § 言語 に一文だけ足す（`~/.claude/CLAUDE.md` は dotfiles への symlink なので全リポジトリに届く）。変換は scratchpad の Python スクリプトで行い、リポジトリにはコミットしない。スクリプトは「変換」と「検証」を分け、検証が通ったファイルだけ書き戻す。

**Tech Stack:** Python 3（標準ライブラリのみ）、`unittest`

## Global Constraints

- 設計の正典は `notes/document/008-no-hard-wrap-japanese-design.md`。規則で迷ったらこれを読む。
- スクリプトとテストは `$SCRATCH` = `/private/tmp/claude-501/-Users-ara-Joifup-dotfiles/c81cbf20-6de2-4b0e-bb13-a3a5d04fff6a/scratchpad` に置く。**リポジトリにコミットしない。**
- コミットメッセージは英語。本文・コメント・docstring は日本語。
- 日本語の本文は桁数で折り返さない（このタスクが置く規約を、書くものすべてで守る）。
- 結合点の空白: 前後のどちらかが ASCII 英数なら半角空白1つ、日本語どうしなら空白なし。
- 日本語かどうかの判定は**段落単位**（行単位ではない）。

---

### Task 1: 規約を CLAUDE.md に置く

**Files:**
- Modify: `.claude/CLAUDE.md`（§ 言語 の箇条書きの末尾）

**Interfaces:**
- Consumes: なし
- Produces: なし（以降のタスクはこの規約を守って書く）

- [ ] **Step 1: § 言語 の現在の末尾を確認する**

Run: `grep -n "^## 言語" -A 12 .claude/CLAUDE.md`
Expected: `- **自作スキルの SKILL.md: 日本語**…` で終わる箇条書きが見える。

- [ ] **Step 2: 規約の一文を足す**

§ 言語 の箇条書きの末尾（`- **自作スキルの SKILL.md: 日本語**…` の項目の後）に、次の1項目を足す。

```markdown
- **日本語の本文とコメントは桁数で折り返さない**（1段落＝1行）。エディタが soft-wrap するので二重に折れ、日本語は語の間に空白が無いため語の途中で切れる。
```

- [ ] **Step 3: 文面と位置を確認する**

Run: `grep -n "桁数で折り返さない" .claude/CLAUDE.md`
Expected: § 言語 の中に1件だけ出る。

- [ ] **Step 4: Commit**

```bash
git add .claude/CLAUDE.md
git commit -m "docs(claude): stop hard-wrapping Japanese prose and comments"
```

---

### Task 2: 変換の中核を書く

**Files:**
- Create: `$SCRATCH/unwrap.py`
- Test: `$SCRATCH/test_unwrap.py`

**Interfaces:**
- Consumes: なし
- Produces: `unwrap_text(text: str) -> str` — md の全文を受け、段落の途中の改行を結合した全文を返す。末尾の改行は入力どおり保つ。

- [ ] **Step 1: 失敗するテストを書く**

`$SCRATCH/test_unwrap.py` に次を書く。

```python
import unittest

import unwrap

class TestUnwrapText(unittest.TestCase):
    def test_joins_a_wrapped_japanese_paragraph(self):
        src = "日本語の本文が桁数で\n折り返されている。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "日本語の本文が桁数で折り返されている。\n")

    def test_leaves_an_english_paragraph_alone(self):
        src = "This paragraph is wrapped\nat a column limit.\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_puts_a_space_where_either_side_is_ascii(self):
        src = "設計は Claude\nCode の上で動く。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "設計は Claude Code の上で動く。\n")

    def test_puts_a_space_at_a_japanese_to_ascii_boundary(self):
        src = "この規約は\nCLAUDE.md に置く。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "この規約は CLAUDE.md に置く。\n")

    def test_judges_japanese_by_paragraph_not_by_line(self):
        """英語の行で始まっても、段落に日本語があれば段落ごと結合する。"""
        src = "The design is simple\nだが適用範囲は広い。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "The design is simple だが適用範囲は広い。\n")

    def test_keeps_a_two_space_hard_break(self):
        src = "一行目で明示的に改行する。  \n二行目である。\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_keeps_a_backslash_hard_break(self):
        src = "一行目で明示的に改行する。\\\n二行目である。\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_leaves_a_fenced_block_alone(self):
        src = "```\nコードの中は\n折り返しても触らない。\n```\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_leaves_frontmatter_alone(self):
        src = "---\ntitle: あ\ntag: [document]\n---\n\n本文が折り\n返されている。\n"
        self.assertEqual(
            unwrap.unwrap_text(src),
            "---\ntitle: あ\ntag: [document]\n---\n\n本文が折り返されている。\n")

    def test_leaves_a_table_alone(self):
        src = "| 列 | 値 |\n|---|---|\n| あ | い |\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_leaves_a_heading_and_a_blockquote_alone(self):
        src = "## 見出し\n\n> 引用の本文が\n> 続く。\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_joins_a_wrapped_list_item(self):
        src = "- 箇条書きの本文が\n  折り返されている。\n- 次の項目。\n"
        self.assertEqual(unwrap.unwrap_text(src),
                         "- 箇条書きの本文が折り返されている。\n- 次の項目。\n")

    def test_keeps_a_nested_list_item_separate(self):
        src = "- 親の項目\n  - 子の項目\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_keeps_blank_lines_between_paragraphs(self):
        src = "最初の段落が折り\n返されている。\n\n次の段落も折り\n返されている。\n"
        self.assertEqual(
            unwrap.unwrap_text(src),
            "最初の段落が折り返されている。\n\n次の段落も折り返されている。\n")

    def test_leaves_an_indented_code_block_alone(self):
        src = "本文である。\n\n    コードの中は\n    折り返しても触らない。\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

    def test_leaves_a_paragraph_containing_a_hard_break_alone(self):
        """ハードブレイクを含む段落は、その先が折り返されていても触らない。"""
        src = "一行目で明示的に改行する。  \n二行目が桁数で\n折り返されている。\n"
        self.assertEqual(unwrap.unwrap_text(src), src)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `cd $SCRATCH && python3 -m unittest test_unwrap -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'unwrap'`

- [ ] **Step 3: 最小の実装を書く**

`$SCRATCH/unwrap.py` に次を書く。

```python
#!/usr/bin/env python3
"""日本語の md 本文のハード折り返しを結合する。

規約と規則の正典は notes/document/008-no-hard-wrap-japanese-design.md。
段落の途中で改行されている行を結合し、frontmatter・コードフェンス・表・
見出し・引用・意図的なハードブレイク・日本語を含まない段落は触らない。
"""
import re

FENCE = re.compile(r"^\s*(```|~~~)")
HEADING = re.compile(r"^\s*#{1,6}\s")
QUOTE = re.compile(r"^\s*>")
TABLE = re.compile(r"^\s*\|")
RULE = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
LIST = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")
INDENTED_CODE = re.compile(r"^( {4,}|\t)")
CJK = re.compile(r"[぀-ヿ一-鿿]")
ASCII_ALNUM = re.compile(r"[A-Za-z0-9]")
HARD_BREAK = re.compile(r"(  |\\)$")

def is_block_start(line):
    """段落の続きになりえない行か。"""
    return bool(FENCE.match(line) or HEADING.match(line) or QUOTE.match(line)
                or TABLE.match(line) or RULE.match(line) or LIST.match(line))

def join_parts(parts):
    """行の並びを1行に結合する。

    結合点の前後のどちらかが ASCII 英数なら半角空白1つを入れ、日本語
    どうしなら空白なしで繋ぐ。既存の本文の慣習に合わせた規則である
    (設計の「結合点の空白」)。
    """
    out = parts[0]
    for part in parts[1:]:
        left = out[-1:] if out else ""
        right = part[:1]
        if ASCII_ALNUM.match(left) or ASCII_ALNUM.match(right):
            out = out + " " + part
        else:
            out = out + part
    return out

def _fold(raw_lines):
    """1つの段落 (またはリスト項目の本文) を結合して行の並びに返す。

    触らない場合は原文の行をそのまま返す。触らないのは、日本語を含まない
    段落と、意図的なハードブレイクを含む段落である (設計の「触らないもの」)。
    """
    if not CJK.search("\n".join(raw_lines)):
        return list(raw_lines)
    if any(HARD_BREAK.search(line) for line in raw_lines):
        return list(raw_lines)
    return [join_parts([line.strip() for line in raw_lines])]

def unwrap_text(text):
    """md の全文を受け、段落の途中の改行を結合した全文を返す。"""
    lines = text.split("\n")
    out = []
    i = 0

    if lines and lines[0].strip() == "---":
        out.append(lines[0])
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            out.append(lines[i])
            i += 1
        if i < len(lines):
            out.append(lines[i])
            i += 1

    while i < len(lines):
        line = lines[i]

        if FENCE.match(line):
            out.append(line)
            i += 1
            while i < len(lines):
                out.append(lines[i])
                closed = FENCE.match(lines[i])
                i += 1
                if closed:
                    break
            continue

        if (not line.strip() or HEADING.match(line) or QUOTE.match(line)
                or TABLE.match(line) or RULE.match(line)
                or INDENTED_CODE.match(line)):
            out.append(line)
            i += 1
            continue

        # 段落、またはリスト項目。リストなら本文だけを畳み、マーカーは戻す
        m = LIST.match(line)
        prefix = line[:m.end()] if m else ""
        raw = [line[m.end():] if m else line]
        i += 1
        while i < len(lines):
            nxt = lines[i]
            if not nxt.strip() or is_block_start(nxt) or INDENTED_CODE.match(nxt):
                break
            raw.append(nxt)
            i += 1
        folded = _fold(raw)
        folded[0] = prefix + folded[0]
        out.extend(folded)

    return "\n".join(out)
```

- [ ] **Step 4: テストが通ることを確認する**

Run: `cd $SCRATCH && python3 -m unittest test_unwrap -v`
Expected: PASS（0 failures）

落ちるテストがあれば実装を直す。**テストの期待値を変えてはならない** — 期待値は設計から来ている。

- [ ] **Step 5: Commit（スクリプトはコミットしない）**

このタスクの成果物は `$SCRATCH` にあり、リポジトリには何も足さない。`git status` が clean であることだけ確認する。

Run: `git status --short`
Expected: 出力なし

---

### Task 3: 検証を書く

**Files:**
- Modify: `$SCRATCH/unwrap.py`
- Modify: `$SCRATCH/test_unwrap.py`

**Interfaces:**
- Consumes: `unwrap.unwrap_text(text) -> str`（Task 2）
- Produces: `unwrap.verify(before: str, after: str) -> list[str]` — 問題の説明を並べたリストを返す。空なら安全。

- [ ] **Step 1: 失敗するテストを書く**

`$SCRATCH/test_unwrap.py` の末尾（`if __name__` の前）に次のクラスを足す。

```python
class TestVerify(unittest.TestCase):
    def test_a_clean_unwrap_has_no_problems(self):
        before = "日本語の本文が桁数で\n折り返されている。\n"
        after = unwrap.unwrap_text(before)
        self.assertEqual(unwrap.verify(before, after), [])

    def test_dropped_characters_are_caught(self):
        before = "日本語の本文が桁数で\n折り返されている。\n"
        self.assertTrue(unwrap.verify(before, "日本語の本文が桁数で\n"))

    def test_reordered_characters_are_caught(self):
        before = "あいうえお\nかきくけこ\n"
        self.assertTrue(unwrap.verify(before, "かきくけこあいうえお\n"))

    def test_a_lost_heading_is_caught(self):
        before = "## 見出し\n\n本文である。\n"
        self.assertTrue(unwrap.verify(before, "見出し\n\n本文である。\n"))

    def test_a_lost_list_item_is_caught(self):
        before = "- 一つ目\n- 二つ目\n"
        self.assertTrue(unwrap.verify(before, "- 一つ目二つ目\n"))

    def test_a_lost_table_row_is_caught(self):
        before = "| 列 |\n|---|\n| あ |\n"
        self.assertTrue(unwrap.verify(before, "| 列 |\n|---|\n"))

    def test_added_join_spaces_are_not_a_problem(self):
        """結合で入る空白は差ではない (比較は空白を除いて行う)。"""
        before = "この規約は\nCLAUDE.md に置く。\n"
        after = "この規約は CLAUDE.md に置く。\n"
        self.assertEqual(unwrap.verify(before, after), [])
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `cd $SCRATCH && python3 -m unittest test_unwrap.TestVerify -v`
Expected: FAIL — `AttributeError: module 'unwrap' has no attribute 'verify'`

- [ ] **Step 3: 最小の実装を書く**

`$SCRATCH/unwrap.py` の末尾に次を足す。

```python
def _squeeze(text):
    """空白と改行をすべて落とす。文字の欠落・重複・順序変更だけを見るため。"""
    return re.sub(r"\s+", "", text)

def _count(text, pattern):
    return sum(1 for line in text.split("\n") if pattern.match(line))

STRUCTURE = (("見出し", HEADING), ("コードフェンス", FENCE),
             ("リスト項目", LIST), ("表の行", TABLE))

def verify(before, after):
    """変換の前後を比べ、書き戻して安全でない理由を並べて返す。

    空のリストなら安全である。設計の「検証」の2条件を実装している:
    段落テキストが文字単位で一致すること、構造の数が変わらないこと。
    """
    problems = []
    if _squeeze(before) != _squeeze(after):
        problems.append("段落テキストが一致しない (文字の欠落・重複・順序変更)")
    for name, pattern in STRUCTURE:
        b, a = _count(before, pattern), _count(after, pattern)
        if b != a:
            problems.append(f"{name} の数が {b} から {a} に変わった")
    return problems
```

- [ ] **Step 4: テストが通ることを確認する**

Run: `cd $SCRATCH && python3 -m unittest test_unwrap -v`
Expected: PASS（0 failures。Task 2 のテストも引き続き通っていること）

- [ ] **Step 5: Commit（スクリプトはコミットしない）**

Run: `git status --short`
Expected: 出力なし

---

### Task 4: dotfiles に適用する

**Files:**
- Modify: `$SCRATCH/unwrap.py`（CLI を足す）
- Modify: `notes/**/*.md`、`tasks/**/*.md`、`projects/*.md`、`.claude/**/*.md`（変換の結果）

**Interfaces:**
- Consumes: `unwrap.unwrap_text`、`unwrap.verify`
- Produces: なし（このタスクで完結する）

- [ ] **Step 1: CLI を足す**

`$SCRATCH/unwrap.py` の末尾に次を足す。

```python
SKIP = ("/node_modules/", "/.git/", "/.claude/worktrees/", "/fixtures/",
        "/dist/", "/build/", "/target/", "/.next/", "/coverage/")

def unwrap_file(path, apply=False):
    """1ファイルを変換する。戻り値は ("changed"|"unchanged"|"failed", 詳細)。"""
    before = path.read_text(encoding="utf-8")
    after = unwrap_text(before)
    if before == after:
        return "unchanged", ""
    problems = verify(before, after)
    if problems:
        return "failed", "; ".join(problems)
    if apply:
        path.write_text(after, encoding="utf-8")
    return "changed", ""

def main(argv):
    import pathlib
    apply = "--apply" in argv
    roots = [a for a in argv if not a.startswith("--")]
    changed = unchanged = failed = 0
    for root in roots:
        for path in sorted(pathlib.Path(root).rglob("*.md")):
            if any(s in str(path) for s in SKIP):
                continue
            state, detail = unwrap_file(path, apply)
            if state == "changed":
                changed += 1
                print(f"changed  {path}")
            elif state == "failed":
                failed += 1
                print(f"FAILED   {path}: {detail}")
            else:
                unchanged += 1
    verb = "変換した" if apply else "変換する (dry-run)"
    print(f"\n{verb}: {changed} / 変更なし: {unchanged} / 失敗: {failed}")
    return 1 if failed else 0

if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 2: dry-run で対象と失敗を見る**

Run: `cd $SCRATCH && python3 unwrap.py <WT>/notes <WT>/tasks <WT>/projects <WT>/.claude`
（`<WT>` は worktree の絶対パス）
Expected: `changed` の一覧と集計が出る。**`FAILED` が1件でもあれば、そのファイルを読んで原因を特定し、`unwrap_text` を直す。** 検証が落ちたまま先へ進まない。

- [ ] **Step 3: 適用する**

Run: `cd $SCRATCH && python3 unwrap.py <WT>/notes <WT>/tasks <WT>/projects <WT>/.claude --apply`
Expected: `失敗: 0`

- [ ] **Step 4: 差分を読む**

Run: `cd <WT> && git diff --stat`
そのうえで `git diff` を実際に読む。dotfiles の対象は日本語の折り返しが 67 行程度なので**全部読める**。次を確認する。

- 語が潰れていない（`Claude Code` が `ClaudeCode` になっていない）
- 表・コードフェンス・frontmatter が変わっていない
- 箇条書きの階層が保たれている

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "style(joifup): unwrap hard-wrapped Japanese prose in dotfiles"
```

- [ ] **Step 6: 規約と結果が一致していることを確認する**

Run: `cd $SCRATCH && python3 unwrap.py <WT>/notes <WT>/tasks <WT>/projects <WT>/.claude`
Expected: `変換する (dry-run): 0 / 失敗: 0`（もう折り返しが残っていない）
