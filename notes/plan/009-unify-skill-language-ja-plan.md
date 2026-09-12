---
title: 自作スキルの記述言語を日本語に統一する 実装計画
tag: [plan]
Project: devops
Task: 009-unify-skill-language-ja
created_at: 2026-09-12
updated_at: 2026-09-12
---

# 自作スキルの記述言語を日本語に統一する 実装計画

**Goal:** 現役の自作スキル 9 個の SKILL.md を、節構成を一切変えずに日本語へ翻訳し、記述言語の規約を CLAUDE.md に置く。

**Architecture:** 先に「訳しただけであること」を機械で検査する使い捨てスクリプトを作り（Task 1）、以降は 1 スキル 1 タスク 1 コミットで翻訳し、各タスクの検収をそのスクリプトで行う。文体は最小のスキル（`j-task`）で確定し、最も密な `j-devflow` を最後に回す。検査スクリプトはリポジトリにコミットしない。

**Tech Stack:** Markdown（SKILL.md）、Python 3（標準ライブラリのみ。検査スクリプト用）、git。

## Global Constraints

これは全タスクに暗黙に適用される。各タスクの要件はこの節を含む。

- **作業ディレクトリ（worktree）:** `/Users/ara/Joifup/dotfiles/.claude/worktrees/feature-009-unify-skill-language-ja`。以降これを `<WT>` と書く。すべてのパスは `<WT>` 相対。主チェックアウト（`/Users/ara/Joifup/dotfiles/` 直下で `.claude/worktrees/` を含まないパス）を絶対に触らない。
- **検査の基準リビジョン:** `42c70b5`（`git merge-base HEAD origin/main`）。旧版は必ず `git show 42c70b5:<path>` で取る。
- **scratchpad:** `/private/tmp/claude-501/-Users-ara-Joifup-dotfiles/43bb6817-dbaa-47b6-9eb9-3e2dca8cbe99/scratchpad`。以降これを `<SP>` と書く。検査スクリプトはここに置き、**コミットしない**。
- **コミットメッセージは英語**（Semantic Commit・Atomic）。PR 本文は日本語。
- **節構成・順序・項目数を変えない。** 訳すだけ。言い回しの改善、節の統廃合、内容の追加・削除を行わない。原文に不備を見つけても直さず、タスクの報告に書く。
- **日本語にするもの:** 散文、`##` と `###` 見出し、frontmatter の `description`、frontmatter の `argument-hint` の値。
- **英語のまま残すもの:** `name`、frontmatter のキー名、コマンド・パス・フラグ・環境変数、他スキル名と `agentType`（`superpowers:brainstorming` / `ecc:docs-lookup`）、Joifup の status 値（`Not started` / `In progress` / `In review` / `Done` / `Cancelled`）とタグ名（`plan` / `document` / `log` / `research` / `memo`）、コミットメッセージ例、コードフェンスの中身、原語で使われている技術識別子（`frontmatter` / `diff` / `worktree` / `subagent` 等）。
- **見出しの語彙表**（全スキル共通。訳を発明しない）:

  | 英語 | 日本語 |
  |---|---|
  | Overview | 概要 |
  | When to Use | 使う場面 |
  | Flow | 流れ |
  | Steps | 手順 |
  | Usage | 使い方 |
  | Runbook | 手順書 |
  | Modes: two independent axes | モード — 独立した二軸 |
  | Guards (all mode combinations) | ガード（全モード共通） |
  | What it does | 何をするか |
  | What the script guarantees | スクリプトが保証すること |
  | ECC knowledge | ECC の活用 |
  | Document content spec | ドキュメントの内容規定 |
  | Log content spec | ログの内容規定 |
  | Research content spec | 調査ノートの内容規定 |
  | Body | 本文 |
  | Identifier | 識別子 |
  | Common Mistakes | よくある失敗 |

- **文体:** 規定文は「〜する」「〜してはならない」。丁寧語にしない。`**…**` 強調は保持する。`never` / `MUST` / `ABSOLUTELY` は否定形と強調を保って訳す（`**never** set Done` → `**絶対に** Done にしない`）。主語の `you` は落とす。**ハード折り返しをしない**（桁数で改行せず、1 段落 1 行）。
- **`description` の型:** 日本語の文で「〜するときに使う」。ユーザーが実際に打つ日本語の起動語を含める。固有語（`Joifup` / `PR` / `UAT` / `Discord` / `superpowers`）は英語のまま。
- **不変条件（全翻訳タスクの検収条件）:** Task 1 のスクリプトが 6 項目すべて PASS すること。落ちたら訳を直す。条件を緩めるのは原文側に明白な不備がある場合のみで、理由をコミットメッセージに書く。

---

## File Structure

| ファイル | 役割 | 担当タスク |
|---|---|---|
| `<SP>/check_invariants.py` | 旧版と新版の構造不変 6 条件を検査する使い捨てスクリプト（**コミットしない**） | Task 1 |
| `<SP>/test_check_invariants.py` | 上記のテスト（**コミットしない**） | Task 1 |
| `.claude/skills/j-task/SKILL.md` | 翻訳（文体の基準を確定する） | Task 2 |
| `.claude/skills/j-pr/SKILL.md` | 翻訳 | Task 3 |
| `.claude/skills/j-doc/SKILL.md` | 翻訳 | Task 4 |
| `.claude/skills/j-research/SKILL.md` | 翻訳 | Task 5 |
| `.claude/skills/j-log/SKILL.md` | 翻訳 | Task 6 |
| `.claude/skills/md2joifup/SKILL.md` | 翻訳 | Task 7 |
| `.claude/skills/j-finish/SKILL.md` | 翻訳 | Task 8 |
| `.claude/skills/j-recap/SKILL.md` | 見出しと `description` のみ（本文は既に日本語） | Task 9 |
| `.claude/skills/j-devflow/SKILL.md` | 翻訳（最大・最も密。最後） | Task 10 |
| `.claude/CLAUDE.md` | § 言語 に記述言語の規約を追記 | Task 11 |

---

### Task 1: 構造不変チェッカー（使い捨て）

**Files:**
- Create: `<SP>/check_invariants.py`
- Test: `<SP>/test_check_invariants.py`

**Interfaces:**
- Consumes: なし。
- Produces: CLI `python3 <SP>/check_invariants.py <path...> [--base 42c70b5]`。各パスについて 6 条件を検査し、`PASS: <path>` または `FAIL: <path>` と落ちた条件の詳細を stdout に出す。1 つでも落ちたら exit code 1、全部通れば 0。Task 2〜10 はこの CLI をそのまま叩く。
- Produces: モジュール関数 `check_file(base_text: str, new_text: str) -> list[str]` — 違反メッセージのリストを返す（空リスト＝合格）。テストはこれを直接呼ぶ。

**検査する 6 条件**（`base_text` = 旧版、`new_text` = 新版）:

1. `##` / `###` 見出しの個数と階層の並びが一致。かつ各対について、新見出しが「語彙表の訳」か「旧見出しとバイト一致」のいずれかであること。どちらでもない対は違反として両方を並べて報告する。
2. 節ごとの箇条書き項目数が一致。節は直前の見出しで区切り、行頭マーカー（`- ` / `* ` / `1. ` 形式。先行空白は許す）で始まる行を数える。ネストした階層も数に含める。
3. コードフェンスの中身がバイト一致。出現順に比較する。
4. frontmatter のキー集合が一致し、値が変わったキーが `description` と `argument-hint` のみであること。
5. インラインコード `` `…` `` の多重集合が一致（語順の入れ替えは許す）。
6. `**…**` 強調の出現数が一致。

**実装の要点:**
- 条件 2・5・6 はコードフェンスの**外側**だけを見る。フェンスの開閉は CommonMark と同じ規則で判定する — 開きフェンスのバッククォート連長を記録し、**同じ文字で連長が開き以上**の行で閉じる。`j-doc` には 4 連バッククォートの中に ` ```joifup ` が入る箇所があるので、3 連固定の実装では壊れる。
- 見出しの抽出もフェンスの外側のみ。`j-recap` の出力例フェンス内に `## 2026-07-26 の作業` / `### joifup` があり、これを見出しと数えてはならない。
- frontmatter は先頭の `---` 〜 `---`。キー名は行頭 `^([A-Za-z-]+):` で取る。YAML パーサは使わない（標準ライブラリに無い）。
- 語彙表はスクリプト内の dict にハードコードする（使い捨てなので外部ファイルにしない）。

- [ ] **Step 1: 失敗するテストを書く**

`<SP>/test_check_invariants.py`:

```python
import unittest
from check_invariants import check_file

CLEAN_BASE = """---
name: demo
description: Use when demoing.
argument-hint: "[id (optional)]"
---

# demo

## Overview

A **demo** skill that uses `--flag`.

## Flow

1. First step with `path/to/x`.
2. Second step.

```bash
python3 scripts/demo.py --flag
```

## Common Mistakes

- Doing it wrong.
"""

CLEAN_NEW = """---
name: demo
description: デモするときに使う。
argument-hint: "[id（任意）]"
---

# demo

## 概要

`--flag` を使う**デモ**スキル。

## 流れ

1. `path/to/x` を使う最初の手順。
2. 次の手順。

```bash
python3 scripts/demo.py --flag
```

## よくある失敗

- 誤った使い方をする。
"""

class TestCheckFile(unittest.TestCase):
    def test_faithful_translation_passes(self):
        self.assertEqual(check_file(CLEAN_BASE, CLEAN_NEW), [])

    def test_unchanged_file_passes(self):
        self.assertEqual(check_file(CLEAN_BASE, CLEAN_BASE), [])

    def test_heading_dropped_fails(self):
        broken = CLEAN_NEW.replace("## よくある失敗\n\n- 誤った使い方をする。\n", "")
        self.assertTrue(any("heading" in v for v in check_file(CLEAN_BASE, broken)))

    def test_heading_off_vocabulary_fails(self):
        broken = CLEAN_NEW.replace("## 概要", "## はじめに")
        self.assertTrue(any("vocabulary" in v for v in check_file(CLEAN_BASE, broken)))

    def test_bullet_added_fails(self):
        broken = CLEAN_NEW.replace("- 誤った使い方をする。", "- 誤った使い方をする。\n- 余計な項目。")
        self.assertTrue(any("bullet" in v for v in check_file(CLEAN_BASE, broken)))

    def test_code_fence_edited_fails(self):
        broken = CLEAN_NEW.replace("--flag\n```", "--flag --extra\n```")
        self.assertTrue(any("fence" in v for v in check_file(CLEAN_BASE, broken)))

    def test_frontmatter_key_changed_fails(self):
        broken = CLEAN_NEW.replace("name: demo", "name2: demo")
        self.assertTrue(any("frontmatter" in v for v in check_file(CLEAN_BASE, broken)))

    def test_frontmatter_unexpected_value_change_fails(self):
        broken = CLEAN_NEW.replace("name: demo", "name: デモ")
        self.assertTrue(any("frontmatter" in v for v in check_file(CLEAN_BASE, broken)))

    def test_inline_code_dropped_fails(self):
        broken = CLEAN_NEW.replace("`--flag` を使う", "フラグを使う")
        self.assertTrue(any("inline code" in v for v in check_file(CLEAN_BASE, broken)))

    def test_bold_dropped_fails(self):
        broken = CLEAN_NEW.replace("**デモ**", "デモ")
        self.assertTrue(any("bold" in v for v in check_file(CLEAN_BASE, broken)))

    def test_heading_inside_fence_is_not_counted(self):
        base = CLEAN_BASE.replace("python3 scripts/demo.py --flag", "## not a heading")
        new = CLEAN_NEW.replace("python3 scripts/demo.py --flag", "## not a heading")
        self.assertEqual(check_file(base, new), [])

    def test_nested_four_backtick_fence(self):
        base = CLEAN_BASE + "\n````\n```joifup\ntype: ref\n```\n````\n"
        new = CLEAN_NEW + "\n````\n```joifup\ntype: ref\n```\n````\n"
        self.assertEqual(check_file(base, new), [])

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが落ちることを確認**

Run: `cd <SP> && python3 test_check_invariants.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'check_invariants'`

- [ ] **Step 3: チェッカーを実装**

`<SP>/check_invariants.py`。骨組みは次のとおり（フェンス判定・節分割・6 条件の比較）。

```python
#!/usr/bin/env python3
"""009 用の使い捨て検査: SKILL.md の翻訳が構造を変えていないかを確かめる。"""
import argparse
import collections
import re
import subprocess
import sys

VOCAB = {
    "Overview": "概要",
    "When to Use": "使う場面",
    "Flow": "流れ",
    "Steps": "手順",
    "Usage": "使い方",
    "Runbook": "手順書",
    "Modes: two independent axes": "モード — 独立した二軸",
    "Guards (all mode combinations)": "ガード（全モード共通）",
    "What it does": "何をするか",
    "What the script guarantees": "スクリプトが保証すること",
    "ECC knowledge": "ECC の活用",
    "Document content spec": "ドキュメントの内容規定",
    "Log content spec": "ログの内容規定",
    "Research content spec": "調査ノートの内容規定",
    "Body": "本文",
    "Identifier": "識別子",
    "Common Mistakes": "よくある失敗",
}

FENCE_RE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
HEADING_RE = re.compile(r"^(#{2,3}) +(.*?)\s*$")
BULLET_RE = re.compile(r"^\s*(?:[-*] |\d+\. )")
INLINE_RE = re.compile(r"`([^`\n]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")

def split_fences(text):
    """(prose_lines, fence_blocks) を返す。fence_blocks は中身の文字列のリスト。"""
    prose, blocks = [], []
    fence_char, fence_len, buf = None, 0, None
    for line in text.split("\n"):
        m = FENCE_RE.match(line)
        if fence_char is None:
            if m and m.group(2)[0] in "`~":
                fence_char, fence_len = m.group(2)[0], len(m.group(2))
                buf = []
                continue
            prose.append(line)
        else:
            if (m and m.group(2)[0] == fence_char
                    and len(m.group(2)) >= fence_len and not m.group(3).strip()):
                blocks.append("\n".join(buf))
                fence_char, fence_len, buf = None, 0, None
                continue
            buf.append(line)
    if buf is not None:
        blocks.append("\n".join(buf))
    return prose, blocks

def frontmatter(text):
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    out = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z][A-Za-z0-9_-]*):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out

def headings_and_sections(prose):
    """[(level, title)] と、節ごとの箇条書き数 [int] を返す。"""
    heads, counts = [], []
    current = 0
    for line in prose:
        m = HEADING_RE.match(line)
        if m:
            if heads:
                counts.append(current)
            heads.append((len(m.group(1)), m.group(2)))
            current = 0
        elif BULLET_RE.match(line):
            current += 1
    if heads:
        counts.append(current)
    return heads, counts

def check_file(base_text, new_text):
    violations = []
    b_prose, b_blocks = split_fences(base_text)
    n_prose, n_blocks = split_fences(new_text)

    # 1. 見出し
    b_heads, b_counts = headings_and_sections(b_prose)
    n_heads, n_counts = headings_and_sections(n_prose)
    if [h[0] for h in b_heads] != [h[0] for h in n_heads]:
        violations.append(
            f"heading structure changed: {len(b_heads)} -> {len(n_heads)} "
            f"levels {[h[0] for h in b_heads]} -> {[h[0] for h in n_heads]}")
    else:
        for (bl, bt), (nl, nt) in zip(b_heads, n_heads):
            if nt == bt or VOCAB.get(bt) == nt:
                continue
            violations.append(
                f"heading off vocabulary: {bt!r} -> {nt!r}")

    # 2. 箇条書き
    if b_counts != n_counts:
        violations.append(f"bullet counts per section changed: {b_counts} -> {n_counts}")

    # 3. コードフェンス
    if b_blocks != n_blocks:
        if len(b_blocks) != len(n_blocks):
            violations.append(f"code fence count changed: {len(b_blocks)} -> {len(n_blocks)}")
        else:
            for i, (bb, nb) in enumerate(zip(b_blocks, n_blocks)):
                if bb != nb:
                    violations.append(f"code fence #{i + 1} content changed")

    # 4. frontmatter
    bf, nf = frontmatter(base_text), frontmatter(new_text)
    if set(bf) != set(nf):
        violations.append(
            f"frontmatter keys changed: {sorted(set(bf) ^ set(nf))}")
    else:
        allowed = {"description", "argument-hint"}
        for k in bf:
            if bf[k] != nf[k] and k not in allowed:
                violations.append(f"frontmatter value changed outside {sorted(allowed)}: {k}")

    # 5. インラインコード
    b_inline = collections.Counter(INLINE_RE.findall("\n".join(b_prose)))
    n_inline = collections.Counter(INLINE_RE.findall("\n".join(n_prose)))
    if b_inline != n_inline:
        lost = sorted((b_inline - n_inline).elements())
        added = sorted((n_inline - b_inline).elements())
        violations.append(f"inline code multiset changed: lost={lost} added={added}")

    # 6. 強調
    b_bold = len(BOLD_RE.findall("\n".join(b_prose)))
    n_bold = len(BOLD_RE.findall("\n".join(n_prose)))
    if b_bold != n_bold:
        violations.append(f"bold count changed: {b_bold} -> {n_bold}")

    return violations

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--base", default="42c70b5")
    args = ap.parse_args()
    failed = False
    for path in args.paths:
        base_text = subprocess.run(
            ["git", "show", f"{args.base}:{path}"],
            capture_output=True, text=True, check=True).stdout
        with open(path, encoding="utf-8") as fh:
            new_text = fh.read()
        violations = check_file(base_text, new_text)
        if violations:
            failed = True
            print(f"FAIL: {path}")
            for v in violations:
                print(f"  - {v}")
        else:
            print(f"PASS: {path}")
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: テストが通ることを確認**

Run: `cd <SP> && python3 test_check_invariants.py`
Expected: PASS — `Ran 12 tests ... OK`

- [ ] **Step 5: 未変更の実ファイル 9 個が全部 PASS することを確認**

Run:
```bash
cd <WT> && python3 <SP>/check_invariants.py \
  .claude/skills/j-task/SKILL.md .claude/skills/j-pr/SKILL.md \
  .claude/skills/j-doc/SKILL.md .claude/skills/j-research/SKILL.md \
  .claude/skills/j-log/SKILL.md .claude/skills/md2joifup/SKILL.md \
  .claude/skills/j-finish/SKILL.md .claude/skills/j-recap/SKILL.md \
  .claude/skills/j-devflow/SKILL.md
```
Expected: 9 行すべて `PASS:`、exit code 0。（まだ 1 文字も訳していないので、ここで FAIL が出るならチェッカー側のバグ。とくに `j-doc` の 4 連バッククォートと `j-recap` の出力例フェンスを疑う。）

- [ ] **Step 6: コミットしない**

このタスクは `<SP>` 配下のみを作る。`cd <WT> && git status --porcelain` が**空**であることを確認して終える。リポジトリに検査スクリプトを入れてはならない。

---

### Task 2: j-task を翻訳（文体の基準を確定）

**Files:**
- Modify: `.claude/skills/j-task/SKILL.md`（全 50 行）

**Interfaces:**
- Consumes: Task 1 の `check_invariants.py`。
- Produces: **以降のタスクが従う文体の実例。** 訳語の判断（とくに `Overview` 配下の散文、`Common Mistakes` の箇条書きの言い切り方、`description` の書き方）はこのファイルに合わせる。

- [ ] **Step 1: 旧版を読む**

Run: `cd <WT> && cat .claude/skills/j-task/SKILL.md`

節構成は `## Overview` / `## When to Use` / `## Flow` / `## Body` / `## Identifier` / `## Common Mistakes` の 6 節。

- [ ] **Step 2: 翻訳して書き込む**

Global Constraints の語彙表・文体・英語で残すものに従って全文を置き換える。`description` は次の形にする（日本語の起動語を含め、`Joifup` は英語のまま）:

```yaml
description: タスクやアイデアを Joifup に backlog として起票する、あるいは開発の入口として記録するときに使う。「あとで詳細を詰めるので今は記録だけしたい」「j-devflow を始める前の起票」に該当する場合。
```

`## Identifier` 節の `ID: TASK-N` と filename id の区別、`## Body` 節の「既存タスクの粒度に合わせない。**このルールが勝つ**」という強調は、**強さを落とさずに**訳す。

- [ ] **Step 3: 不変条件を検査**

Run: `cd <WT> && python3 <SP>/check_invariants.py .claude/skills/j-task/SKILL.md`
Expected: `PASS: .claude/skills/j-task/SKILL.md`、exit code 0

FAIL が出たら訳を直す。条件を緩めない。

- [ ] **Step 4: ハード折り返しが無いことを確認**

Run: `cd <WT> && awk 'length($0) > 0 && /^[^|#`-]/ && length($0) < 40 {print FILENAME":"FNR": "$0}' .claude/skills/j-task/SKILL.md`
Expected: 散文が途中で切れた短い行が出ないこと（表・見出し・コード・箇条書きは除外している）。出た行は、前の行と結合すべき折り返しでないかを目で確かめる。

- [ ] **Step 5: コミット**

```bash
cd <WT>
git add .claude/skills/j-task/SKILL.md
git commit -m "docs(j-task): write the skill in Japanese"
```

---

### Task 3: j-pr を翻訳

**Files:**
- Modify: `.claude/skills/j-pr/SKILL.md`（全 36 行）

**Interfaces:**
- Consumes: Task 2 が確定した文体、Task 1 のチェッカー。
- Produces: なし。

- [ ] **Step 1: Task 2 の訳文を読んで文体を合わせる**

Run: `cd <WT> && cat .claude/skills/j-task/SKILL.md && cat .claude/skills/j-pr/SKILL.md`

節構成は `## Overview` / `## When to Use` / `## Flow` / `## Common Mistakes` の 4 節。`argument-hint: "[base-branch (default: main)]"` は `"[base-branch（既定: main）]"` にする。

- [ ] **Step 2: 翻訳して書き込む**

`references/pr-body.md` への参照、`gh pr create …` のコマンド、`uat_attach.py` のパスは**英語のまま**。`## Common Mistakes` の「PR 本文は日本語、コミットは英語（独立）」は訳しても意味が反転しないよう注意する。

- [ ] **Step 3: 不変条件を検査**

Run: `cd <WT> && python3 <SP>/check_invariants.py .claude/skills/j-pr/SKILL.md`
Expected: `PASS`、exit code 0

- [ ] **Step 4: コミット**

```bash
cd <WT>
git add .claude/skills/j-pr/SKILL.md
git commit -m "docs(j-pr): write the skill in Japanese"
```

---

### Task 4: j-doc を翻訳

**Files:**
- Modify: `.claude/skills/j-doc/SKILL.md`（全 52 行）

**Interfaces:**
- Consumes: Task 2 の文体、Task 1 のチェッカー。
- Produces: なし。

- [ ] **Step 1: 旧版と Task 2 の訳文を読む**

Run: `cd <WT> && cat .claude/skills/j-task/SKILL.md && cat .claude/skills/j-doc/SKILL.md`

節構成は `## Overview` / `## Flow` / `## Document content spec` / `## ECC knowledge` / `## Common Mistakes` の 5 節。`## Document content spec` → `## ドキュメントの内容規定`。`argument-hint: "[note-ids... and/or task-id (optional)]"` → `"[note-id...／task-id（任意）]"`。

- [ ] **Step 2: 翻訳して書き込む**

`## Document content spec` 内の `### 概要` / `### 参照元` は**既に日本語**なので触らない（これは SKILL.md の見出しではなく、生成物の見出しの指定である）。4 連バッククォートで囲まれた `joifup` フェンスは**1 バイトも変えない**。

- [ ] **Step 3: 不変条件を検査**

Run: `cd <WT> && python3 <SP>/check_invariants.py .claude/skills/j-doc/SKILL.md`
Expected: `PASS`、exit code 0

- [ ] **Step 4: コミット**

```bash
cd <WT>
git add .claude/skills/j-doc/SKILL.md
git commit -m "docs(j-doc): write the skill in Japanese"
```

---

### Task 5: j-research を翻訳

**Files:**
- Modify: `.claude/skills/j-research/SKILL.md`（全 49 行）

**Interfaces:**
- Consumes: Task 2 の文体、Task 1 のチェッカー。
- Produces: なし。

- [ ] **Step 1: 旧版と Task 2 の訳文を読む**

Run: `cd <WT> && cat .claude/skills/j-task/SKILL.md && cat .claude/skills/j-research/SKILL.md`

節構成は `## Overview` / `## Flow` / `## Research content spec` / `## ECC knowledge` / `## Common Mistakes` の 5 節。`## Research content spec` → `## 調査ノートの内容規定`。`argument-hint: "[task-id (optional)]"` → `"[task-id（任意）]"`。

- [ ] **Step 2: 翻訳して書き込む**

`## Research content spec` 内の `### 背景・目的` / `### 調査結果` / `### 比較表` / `### 結論・推奨` / `### 残課題` は**既に日本語**なので触らない。`ecc:docs-lookup` / `WebSearch` / `Context7` は英語のまま。`## ECC knowledge` の「accuracy over recall」の主張は、強調を保って訳す。

- [ ] **Step 3: 不変条件を検査**

Run: `cd <WT> && python3 <SP>/check_invariants.py .claude/skills/j-research/SKILL.md`
Expected: `PASS`、exit code 0

- [ ] **Step 4: コミット**

```bash
cd <WT>
git add .claude/skills/j-research/SKILL.md
git commit -m "docs(j-research): write the skill in Japanese"
```

---

### Task 6: j-log を翻訳

**Files:**
- Modify: `.claude/skills/j-log/SKILL.md`（全 50 行）

**Interfaces:**
- Consumes: Task 2 の文体、Task 1 のチェッカー。
- Produces: なし。

- [ ] **Step 1: 旧版と Task 2 の訳文を読む**

Run: `cd <WT> && cat .claude/skills/j-task/SKILL.md && cat .claude/skills/j-log/SKILL.md`

節構成は `## Overview` / `## Flow` / `## Log content spec` / `## ECC knowledge` / `## Common Mistakes` の 5 節。`## Log content spec` → `## ログの内容規定`。`argument-hint: "[task-id (optional)]"` → `"[task-id（任意）]"`。

- [ ] **Step 2: 翻訳して書き込む**

`## Log content spec` の `## 概要` への言及、`### 1.` / `### 2.` の形式指定、`<task/topic> 作業ログ [YYYY-MM-DD]` のタイトル書式は**生成物の仕様**なので形を変えない。「**Record, do not summarize.**」＝「**要約せず記録する。**」のように、強調と命令の強さを保つ。

- [ ] **Step 3: 不変条件を検査**

Run: `cd <WT> && python3 <SP>/check_invariants.py .claude/skills/j-log/SKILL.md`
Expected: `PASS`、exit code 0

- [ ] **Step 4: コミット**

```bash
cd <WT>
git add .claude/skills/j-log/SKILL.md
git commit -m "docs(j-log): write the skill in Japanese"
```

---

### Task 7: md2joifup を翻訳

**Files:**
- Modify: `.claude/skills/md2joifup/SKILL.md`（全 54 行）

**Interfaces:**
- Consumes: Task 2 の文体、Task 1 のチェッカー。
- Produces: なし。

- [ ] **Step 1: 旧版と Task 2 の訳文を読む**

Run: `cd <WT> && cat .claude/skills/j-task/SKILL.md && cat .claude/skills/md2joifup/SKILL.md`

節構成は `## Overview` / `## When to Use` / `## Usage` / `## What it does` / `## Common Mistakes` の 5 節。`## Usage` → `## 使い方`、`## What it does` → `## 何をするか`。frontmatter に `user-invocable` / `argument-hint` は無い（`name` と `description` のみ）。

- [ ] **Step 2: 翻訳して書き込む**

`## Usage` 節はフラグの説明が中心である。**フラグ名・値の例・コマンド行は 1 文字も変えない**。説明文だけを訳す。とくに次を強さを保って訳す:
- `--task` の「**md2joifup validates** that …」＝「**md2joifup が検証する** …」
- filename id と daemon `ID: TASK-N` が別体系で一致しないこと
- `--slug` の「**pass an English slug for non-ASCII titles**」

- [ ] **Step 3: 不変条件を検査**

Run: `cd <WT> && python3 <SP>/check_invariants.py .claude/skills/md2joifup/SKILL.md`
Expected: `PASS`、exit code 0

- [ ] **Step 4: コミット**

```bash
cd <WT>
git add .claude/skills/md2joifup/SKILL.md
git commit -m "docs(md2joifup): write the skill in Japanese"
```

---

### Task 8: j-finish を翻訳

**Files:**
- Modify: `.claude/skills/j-finish/SKILL.md`（全 53 行）

**Interfaces:**
- Consumes: Task 2 の文体、Task 1 のチェッカー。
- Produces: なし。

- [ ] **Step 1: 旧版と Task 2 の訳文を読む**

Run: `cd <WT> && cat .claude/skills/j-task/SKILL.md && cat .claude/skills/j-finish/SKILL.md`

節構成は `## Overview` / `## When to Use` / `## Steps` / `## What the script guarantees` / `## Common Mistakes` の 5 節。`## Steps` → `## 手順`、`## What the script guarantees` → `## スクリプトが保証すること`。

- [ ] **Step 2: 翻訳して書き込む**

**このファイルは既に 6 行が日本語**（手順 4 の UAT 証跡の段落と、`## Common Mistakes` の末尾 2 項目）。**その日本語部分は 1 文字も変えない。** 英語部分だけを訳す。

次は強さを落とさずに訳す:
- `**The human owns the approval commit.**` / `j-finish never sets Done and never merges.`
- `## What the script guarantees` の `**Surgical status edit**` と、`It refuses Done/Cancelled.`
- `## Common Mistakes` の「承認コミットは**英語**、PR 本文は**日本語**」

`👀 レビュー依頼` / `DISCORD_COLOR` / `CLAUDE_SESSION_ID` / `gh >= 2.99.0` はそのまま。

- [ ] **Step 3: 不変条件を検査**

Run: `cd <WT> && python3 <SP>/check_invariants.py .claude/skills/j-finish/SKILL.md`
Expected: `PASS`、exit code 0

- [ ] **Step 4: スクリプトを触っていないことを確認**

Run: `cd <WT> && git status --porcelain .claude/skills/j-finish/scripts`
Expected: 空（スクリプトは 009 の対象外。`tasks/007` の領域）

- [ ] **Step 5: コミット**

```bash
cd <WT>
git add .claude/skills/j-finish/SKILL.md
git commit -m "docs(j-finish): write the skill in Japanese"
```

---

### Task 9: j-recap の見出しと description を日本語に

**Files:**
- Modify: `.claude/skills/j-recap/SKILL.md`（全 73 行。本文は既に日本語）

**Interfaces:**
- Consumes: Task 1 のチェッカー。
- Produces: なし。

- [ ] **Step 1: 旧版を読む**

Run: `cd <WT> && cat .claude/skills/j-recap/SKILL.md`

英語で残っているのは `## Overview` / `## Flow` / `## Common Mistakes` の 3 見出しと、`description` の英語部分だけである。`## 出力フォーマット` / `## 出力例` は既に日本語。

- [ ] **Step 2: 3 つの見出しと description を直す**

`## Overview` → `## 概要`、`## Flow` → `## 流れ`、`## Common Mistakes` → `## よくある失敗`。

`description` は英語の `Use when …` 構文を日本語にする。**既にある日本語の起動語（「今日やったことまとめて」「作業まとめ」「振り返り」「日報」）は消さない。** `Joifup` 等の固有語は英語のまま。

**本文には一切手を入れない。** 出力例フェンス内の `## 2026-07-26 の作業` / `### joifup` / `### dotfiles` は出力の見本であり、見出しではない。

- [ ] **Step 3: 不変条件を検査**

Run: `cd <WT> && python3 <SP>/check_invariants.py .claude/skills/j-recap/SKILL.md`
Expected: `PASS`、exit code 0

- [ ] **Step 4: 本文が変わっていないことを確認**

Run: `cd <WT> && git diff --stat .claude/skills/j-recap/SKILL.md`
Expected: 変更行数が **8 行以下**（見出し 3 行 × 2（削除＋追加）＋ `description` 1 行 × 2）。これを超えるなら本文に触っている。

- [ ] **Step 5: コミット**

```bash
cd <WT>
git add .claude/skills/j-recap/SKILL.md
git commit -m "docs(j-recap): translate the remaining English headings and description"
```

---

### Task 10: j-devflow を翻訳

**Files:**
- Modify: `.claude/skills/j-devflow/SKILL.md`（全 110 行・16,163 B。最大・最も密）

**Interfaces:**
- Consumes: Task 2〜9 で固まった文体と語彙、Task 1 のチェッカー。
- Produces: なし。

**このタスクが最も危険である。** ルールが密で、訳で強さが落ちると実際に事故が起きる（worktree 隔離の指示、GATE の規定、`-auto` / `-light` のエスカレーション条件）。訳す前に、他 8 ファイルの訳文で語彙を確認してから始める。

- [ ] **Step 1: 旧版と確定済みの訳文を読む**

Run: `cd <WT> && cat .claude/skills/j-task/SKILL.md && cat .claude/skills/j-finish/SKILL.md && cat .claude/skills/j-devflow/SKILL.md`

節構成は `## Overview` / `## When to Use` / `## Modes: two independent axes`（配下に `### GATE 1: …` と `### Phase B: …`）/ `## Runbook` / `## Guards (all mode combinations)` / `## Common Mistakes` の 6 節 + `###` 2 つ。

- [ ] **Step 2: 翻訳して書き込む**

見出し: `## Modes: two independent axes` → `## モード — 独立した二軸`、`## Runbook` → `## 手順書`、`## Guards (all mode combinations)` → `## ガード（全モード共通）`。`###` 2 つはモード名・フラグ名を英語で残し `(default)` だけ `（既定）` にする（例: `### GATE 1: attended（既定） vs \`-auto\``）。

**既に日本語の箇所**（`## Runbook` の手順 10「UAT 自動化 + j-finish」の段落）は 1 文字も変えない。

次は**強さを落とさずに**訳す。訳が弱まると事故が起きる箇所である:
- `**HUMAN GATE 1: design approval — no code until approved**`
- `**Nothing auto-merges**` / `Merge lives only here.` / `structurally impossible for the machine`
- Worktree-pinning contract の (a)〜(d)。とくに `**STOP and report BLOCKED**`、`never edit or run cargo/pnpm in the fallback dir`、`**forbid literal primary paths**`
- `-auto` / `-light` のエスカレーション条件（`**pause and ask the dispatcher**`、`do NOT auto-approve`）
- `Critical/Important are blocking` と fix ループの出口条件
- `**Why \`-light\` is safe (008 followup evidence)**` の「n=2 なので directional として扱う」という限定

ブランチ命名（`feature-001-slug`、**not** `feature/001-slug`）、`WT="$(git rev-parse --show-toplevel)"`、`cargo … --manifest-path`、`pnpm uat --task <id>`、タスク番号の参照（`tasks/154, 155, 156`、`joifup tasks/295`）は**そのまま**。

- [ ] **Step 3: 不変条件を検査**

Run: `cd <WT> && python3 <SP>/check_invariants.py .claude/skills/j-devflow/SKILL.md`
Expected: `PASS`、exit code 0

- [ ] **Step 4: 規定の強さが残っているか自己確認**

Run: `cd <WT> && grep -c '絶対\|してはならない\|しない\|必ず\|STOP\|BLOCKED' .claude/skills/j-devflow/SKILL.md`
Expected: 1 以上。そのうえで Step 2 に挙げた箇所を 1 つずつ目で確かめ、「禁止」が「推奨」に弱まっていないことを確認する。弱まっていたら直す。

- [ ] **Step 5: コミット**

```bash
cd <WT>
git add .claude/skills/j-devflow/SKILL.md
git commit -m "docs(j-devflow): write the skill in Japanese"
```

---

### Task 11: CLAUDE.md § 言語 に規約を追記

**Files:**
- Modify: `.claude/CLAUDE.md`（§ 言語）

**Interfaces:**
- Consumes: Task 2〜10 で確定した「日本語にするもの / 英語で残すもの」の境界。
- Produces: なし（最終タスク）。

- [ ] **Step 1: 現在の § 言語 を読む**

Run: `cd <WT> && sed -n '/^## 言語/,/^## /p' .claude/CLAUDE.md`

現状は次の 4 項目である。

```markdown
## 言語

- **コミットメッセージ: 英語**（superpowers native・注入しない）
- **PR本文: 日本語**（diff から生成。commit 言語と独立）
- ブランチ名・コード: 英語
- 原則: **機械が扱う面 = 英語、人が読む面 = 日本語**（人が読む面 = PR本文・Discord・Joifup の doc/plan/log 本文・brainstorm 対話）
```

- [ ] **Step 2: 1 項目を追記**

既存 4 項目は**消さない**。`原則:` の行の**後ろ**に次を足す。SKILL.md は Claude が実行するので字面では機械側だが、**人が保守する面**なので保守する側の言語に合わせる、という位置づけを明示する。

```markdown
- **自作スキルの SKILL.md: 日本語**（`.claude/skills/j-*` と `md2joifup`。本文・`##` 見出し・`description`・`argument-hint`）。機械が実行し**人が保守する**面なので、保守する側の言語に合わせる。英語のまま残すのは `name`・frontmatter のキー名・コマンド／パス／フラグ・他スキル名と `agentType`・status 値とタグ名・コミットメッセージ例・コードフェンスの中身。superpowers / ECC のスキルは無改変なので対象外。
```

- [ ] **Step 3: 既存項目が消えていないことを確認**

Run: `cd <WT> && git diff .claude/CLAUDE.md`
Expected: 追加 1 行のみ（`+` が 1 行、`-` が 0 行）。既存行の削除があれば直す。

- [ ] **Step 4: コミット**

```bash
cd <WT>
git add .claude/CLAUDE.md
git commit -m "docs(claude): require Japanese for the in-house skills' SKILL.md"
```

---

### Task 12: 全体の検収

**Files:**
- 変更なし（検査のみ）

**Interfaces:**
- Consumes: Task 1 のチェッカー、Task 2〜11 の成果。
- Produces: PR 本文に載せる検査出力（`<SP>/invariants-report.txt`）。

- [ ] **Step 1: 9 ファイルをまとめて検査し、出力を保存**

Run:
```bash
cd <WT> && python3 <SP>/check_invariants.py \
  .claude/skills/j-task/SKILL.md .claude/skills/j-pr/SKILL.md \
  .claude/skills/j-doc/SKILL.md .claude/skills/j-research/SKILL.md \
  .claude/skills/j-log/SKILL.md .claude/skills/md2joifup/SKILL.md \
  .claude/skills/j-finish/SKILL.md .claude/skills/j-recap/SKILL.md \
  .claude/skills/j-devflow/SKILL.md | tee <SP>/invariants-report.txt
```
Expected: 9 行すべて `PASS:`、exit code 0

- [ ] **Step 2: 英語の散文が残っていないことを確認**

Run:
```bash
cd <WT> && for f in j-task j-pr j-doc j-research j-log md2joifup j-finish j-recap j-devflow; do
  printf '%-12s ja=%s/%s\n' "$f" \
    "$(grep -c '[ぁ-んァ-ヶ一-龠]' .claude/skills/$f/SKILL.md)" \
    "$(grep -c '' .claude/skills/$f/SKILL.md)"
done
```
Expected: 各ファイルで日本語を含む行が過半を占める。`j-devflow` は旧 1/110 だったので、ここが 1 のままなら訳が入っていない。

- [ ] **Step 3: 既存テストが green のままであることを確認**

Run:
```bash
cd <WT>/.claude/skills/j-finish/scripts && python3 test_j_finish.py && python3 test_uat_attach.py
```
Expected: `Ran 14 tests ... OK` と `Ran 51 tests ... OK`（合計 65 件）

- [ ] **Step 4: スクリプトと対象外ファイルを触っていないことを確認**

Run: `cd <WT> && git diff --stat 42c70b5 HEAD --name-only`
Expected: 現れるのは 9 個の SKILL.md と `.claude/CLAUDE.md`、および Phase A の成果物（`tasks/009-*.md`、`notes/document/009-*.md`）のみ。`*.py`、`j-pr/references/pr-body.md`、旧 Notion 系スキルが現れてはならない。

- [ ] **Step 5: 検査スクリプトがコミットされていないことを確認**

Run: `cd <WT> && git ls-files | grep -c check_invariants`
Expected: `0`

---

## Self-Review

**1. Spec coverage**

| spec の要求 | 担当 |
|---|---|
| 対象 9 ファイルの翻訳 | Task 2〜10 |
| 除外（スクリプト・pr-body.md・旧 Notion 系・他者製） | Task 8 Step 4、Task 12 Step 4 で検査 |
| 日本語にするもの / 英語で残すもの | Global Constraints、各タスク Step 2 |
| `description` の型 | Global Constraints、Task 2 Step 2 に実例 |
| 見出しの語彙表 | Global Constraints、チェッカーの `VOCAB` |
| 文体の規定 | Global Constraints、Task 2 で実例を確定 |
| 構造不変 6 条件 | Task 1（実装＋テスト）、各タスク Step 3、Task 12 Step 1 |
| 検査スクリプトをコミットしない | Task 1 Step 6、Task 12 Step 5 |
| CLAUDE.md への規約追記 | Task 11 |
| 分割と順序（j-task → … → j-devflow → CLAUDE.md） | Task 2〜11 の並び |
| 受け入れ基準 1〜4 | Task 12 Step 1〜3 |
| 受け入れ基準 5（マージ後に j-recap 実機確認） | **Phase C（人間）**。この計画の範囲外。PR 本文に明記する。 |
| 007 への申し送り | PR 本文に書く（Task 12 の報告に含める） |

**2. Placeholder scan** — TBD・TODO・「適宜」「必要に応じて」は無い。各タスクに実行コマンドと期待出力がある。Task 1 には完全なテストコードと実装コードがある。

**3. Type consistency** — チェッカーの API は `check_file(base_text, new_text) -> list[str]` で、テスト（Task 1 Step 1）と実装（Step 3）で一致。CLI は `python3 <SP>/check_invariants.py <path...> [--base 42c70b5]` で、Task 2〜12 の呼び出しと一致。違反メッセージに含まれるキーワード（`heading` / `vocabulary` / `bullet` / `fence` / `frontmatter` / `inline code` / `bold`）は、テストの `assertTrue(any(... in v ...))` と実装の文字列が一致している。
