---
title: 一次情報の二重化をやめる 実装計画
tag: [plan]
Project: devops
Task: 007-stop-duplicating-rationale
created_at: 2026-09-18
updated_at: 2026-09-18
---

# 一次情報の二重化をやめる 実装計画

**Goal:** 設計判断の根拠をコードから notes へ寄せる指針を `~/.claude/rules/` に置き、dotfiles の Python 5ファイルでその指針を実際に適用する。

**Architecture:** 指針は2層に分ける。原則は `CLAUDE.md` に2〜3行（常時ロード）、判定の表は `.claude/rules/comment-rationale.md` に `paths` スコープ付き（コードを触ったときだけロード）。`setup.sh` に `rules` のシンボリックリンクを足して、ユーザースコープの rules として joifup / fde にも届かせる。そのうえで dotfiles 自身の Python を掃除して指針を実証する。

**Tech Stack:** Python 3（標準ライブラリのみ）、bash、Claude Code の rules 機能（`paths` frontmatter）。

## Global Constraints

- **判定の表**（全タスクの掃除作業がこれに従う）:

  | 書こうとしている内容 | 置き場所 |
  | --- | --- |
  | コードから復元できない why | **コメント。ここが唯一の一次情報** |
  | いつ・誰が・なぜ変えたか | git |
  | タスクIDの鎖 | git・notes |
  | 他ファイルの動作の再説明 | そのファイル |
  | 設計判断の根拠（条件の列挙・トレードオフ・却下した案） | 設計書。コードには**1行のポインタだけ** |

- **ポインタは正典の場所を指すだけにする。中身を要約しない。** 数・条件の列挙・項目名を写さない。これを破ると、指し先を書いた同じ文が最初に陳腐化する（`unwrap.py` の「検証の4条件」が実例）。
- **消す前に、その内容が設計書に本当にあるかを確かめる。無ければ消さない。** コメントにしか無い why を消すことが、この作業で唯一の回復困難な損害である。判断がつかないものは残し、タスクの報告に「残した理由」を書く。
- **コードを1行も変えない。** 変えてよいのはコメントと docstring だけ。各タスクが AST 比較で機械的に確かめる。
- **日本語の本文は桁数で折り返さない**（`notes/document/008-no-hard-wrap-japanese-design.md`）。文末（`。`）での改行はそのままでよい。
- **コミットメッセージは英語**、Semantic Commit 形式、1 commit = 1 logical change。
- 設計の正典は `notes/document/007-stop-duplicating-rationale-design.md`。迷ったらこれを読む。

## 検査スクリプトの用意（全タスク共通・コミットしない）

掃除タスク（Task 3〜6）は、コードを触っていないことを機械で確かめる。`tasks/009` の前例に従い、**一度きりの作業用なのでコミットしない**。次の絶対パスに置く: `/private/tmp/claude-501/-Users-ara-Joifup-dotfiles/73d70231-b8b1-4c2b-86fa-fdb5ad3e0f54/scratchpad/check_code_unchanged.py`

各タスクの実装者は、最初に次のファイルを scratchpad に作る（既にあれば作り直さなくてよい）。

`/private/tmp/claude-501/-Users-ara-Joifup-dotfiles/73d70231-b8b1-4c2b-86fa-fdb5ad3e0f54/scratchpad/check_code_unchanged.py`:

```python
#!/usr/bin/env python3
"""コメントと docstring 以外が変わっていないことを確かめる。

使い方: check_code_unchanged.py <base-ref> <file.py> [<file.py> ...]

docstring を取り除いた AST を base と作業ツリーで突き合わせる。一致すれば
「コメントと docstring しか触っていない」ことの機械的な担保になる。
"""
import ast
import subprocess
import sys

def strip_docstrings(tree):
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        body = node.body
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            node.body = body[1:] or [ast.Pass()]
    return tree

def normalized(src):
    return ast.dump(strip_docstrings(ast.parse(src)))

def main(argv):
    base, paths = argv[0], argv[1:]
    failed = 0
    for path in paths:
        old = subprocess.run(["git", "show", f"{base}:{path}"],
                             capture_output=True, text=True, check=True).stdout
        new = open(path, encoding="utf-8").read()
        if normalized(old) == normalized(new):
            print(f"OK    {path}")
        else:
            print(f"FAIL  {path}  コメント以外が変わっている")
            failed += 1
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

**この道具が両方向で効くことは確認済み**（無変更で `OK`、`TAB_WIDTH = 4` を `8` に変えると `FAIL`）。

---

### Task 1: 指針を置く

`rules` ファイルの新規作成・`CLAUDE.md` への原則追加・`setup.sh` のリンク追加は一体である。リンクが無ければ rules は dotfiles の中でしか効かず、指針として成立しない。だから1タスクにする。

**Files:**
- Create: `.claude/rules/comment-rationale.md`
- Modify: `.claude/CLAUDE.md`（`## 記録先（Joifup）` 節の末尾）
- Modify: `setup.sh`（`skills` のリンクの直後、87行目のあと）

**Interfaces:**
- Produces: `.claude/rules/comment-rationale.md` — Task 3〜6 の掃除作業が従う判定の表の正典。`~/.claude/rules/` 経由でユーザースコープの rule として載る。

- [ ] **Step 1: `.claude/rules/comment-rationale.md` を作る**

```markdown
---
paths:
  - "**/*.{ts,tsx,js,jsx,mjs,cjs}"
  - "**/*.{py,rs,go,sh}"
---

# コメントに何を書き、何を書かないか

`CLAUDE.md` § 記録先 の「一次情報は1箇所にしか置かない」の細則。**コードのコメントと docstring を書く / 直すときに適用する。**

以下は `tasks/006` の調査（コメント比率の実測と、コメントの中身の分類）と `tasks/007` の適用から確定したものである。推測ではない。

## 書こうとしている内容ごとの置き場所

| 内容 | 置き場所 |
| --- | --- |
| コードから復元できない why（同一タブでは `focus` が発火しない、等） | **コメント。ここが唯一の一次情報** |
| いつ・誰が・なぜ変えたか（「元々は今は無い◯◯ボタン用に書かれた」） | git |
| タスクIDの鎖（`task-136` → `157` → `178`） | git・notes |
| 他ファイルの動作の再説明（「`AppSidebar` は◯◯でしか refetch しない」） | そのファイル |
| 設計判断の根拠（条件の列挙・トレードオフ・却下した案） | 設計書。コードには**1行のポインタだけ** |

## ポインタの書き方

**正典の場所を1行で指すだけにする。そこにある内容を要約しない。** 要約した瞬間に二重化が始まり、その要約が最初に陳腐化する。

実例: `unwrap.py` は「正典は `008` の設計書である。**検証の4条件**は、すべてそこで決めている」と書いていた。設計書の条件は5つである。指し先を書いた同じ文の中で数を写したために、1ヶ月で嘘になった。**数・条件の列挙・項目名は写さない。**

## 既存コードを触るとき

- **触った関数のコメントだけを見る。** ファイル全体の掃除はしない。
- **消す前に、その内容が設計書に本当にあるかを確かめる。無ければ消さずに設計書へ移す。** コメントにしか無い why を消すことが、この作業で唯一の回復困難な損害である。

## 禁止形にはしない

「コメントを書くな」という固定ルールは採らない。コメントを内部的に無効化する実験では、タスクによって効果の符号が反転する（コード翻訳 +67%、補完 −22%、**修正 −90%**）。エージェントが日常的に行うのは修正であり、そこで削除が最も害になる。**減らすべきは量ではなく、嘘になりうる面の数である。**

同じ理由で、リンターによる機械判定も作らない。「コードから復元できない why か」は意味の判断であり、機械化できない。
```

- [ ] **Step 2: `CLAUDE.md` § 記録先 に原則を足す**

`## 記録先（Joifup）` 節の最後の箇条書き（`- 概念対応: superpowers の spec = 仕様書 …` の行）の直後に、次の1項目を足す。

```markdown
- **一次情報は1箇所にしか置かない。** 設計判断の根拠は notes 側にあり、コードには**そこへのポインタと、コードから復元できない why だけ**を書く。写しは必ず陳腐化し、陳腐化したコメントは欠落よりも大きく性能を損なう。細則は `.claude/rules/comment-rationale.md`（内容ごとの置き場所・ポインタの書き方・既存コードを触るときの扱い）。`paths` スコープでコードを読むときに自動で載る。
```

- [ ] **Step 3: `setup.sh` に `rules` のリンクを足す**

`skills` のリンク（`ln -sf "$DOTFILES_DIR/.claude/skills" "$HOME/.claude/skills"`）の直後の空行のあとに、次を挿入する。`CLAUDE.md` のリンクより前に置く。

```bash
# rules ディレクトリのシンボリックリンク
# ユーザースコープの rules は全プロジェクトに効く。paths スコープを使う rule は
# プロジェクト側に貼ると外部 import 扱いになって読まれないので、ここでしか置けない
backup_if_exists "$HOME/.claude/rules"
ln -sf "$DOTFILES_DIR/.claude/rules" "$HOME/.claude/rules"

```

- [ ] **Step 4: `setup.sh` を実行せずに検査する**

**`setup.sh` をこの worktree から実行してはならない。** `$DOTFILES_DIR` をスクリプト自身の位置から決めるため、worktree から走らせると nvim・tmux・zsh・`~/.claude/skills`・`~/.claude/CLAUDE.md` を含む**すべてのリンクが worktree を指すように張り替わり**、既存のリンクは `backup_if_exists` によって退避される。ユーザーの環境が壊れる。

構文と挿入内容だけを検査する。

Run:
```bash
bash -n setup.sh && echo "SYNTAX OK"
grep -n -A 2 'HOME/.claude/rules' setup.sh
```

Expected: `SYNTAX OK` が出る。`backup_if_exists "$HOME/.claude/rules"` と `ln -sf "$DOTFILES_DIR/.claude/rules" "$HOME/.claude/rules"` の2行が、この順で並んでいる。

- [ ] **Step 5: rule ファイルが Claude Code に読める形であることを確かめる**

**`$HOME` を書き換えてはならない。** リンクを実際に張るのは `setup.sh` の仕事であり、人間がマージを承認したあとに走らせる。ここで張ると、承認前に指針が全セッションで有効になる。worktree の外を書き換えることにもなる。

frontmatter が有効な YAML で、`paths` が期待どおりであることだけを検査する。

Run:
```bash
python3 -c "
import yaml
src = open('.claude/rules/comment-rationale.md', encoding='utf-8').read()
assert src.startswith('---\n'), 'frontmatter が無い'
paths = yaml.safe_load(src.split('---\n')[1])['paths']
assert any('py' in p for p in paths), paths
assert any('ts' in p for p in paths), paths
print('OK', paths)
"
```

Expected: `OK ['**/*.{ts,tsx,js,jsx,mjs,cjs}', '**/*.{py,rs,go,sh}']`

**リンクを張るのは人間の仕事である。** マージ後に `bash setup.sh` を主チェックアウトから走らせると、`~/.claude/rules` が張られて `comment-rationale.md` と `skill-language.md` の両方が有効になる。この申し送りを PR 本文に書く。

- [ ] **Step 6: コミット**

```bash
git add .claude/rules/comment-rationale.md .claude/CLAUDE.md setup.sh
git commit -m "feat(harness): put the single-source-of-truth rule in user-scope rules"
```

---

### Task 2: 記述言語の規約を自作スクリプトへ広げる

`tasks/009` からの申し送り。`.py` を規約の対象に入れる。**新しいルールファイルは作らない** —— 既存の `skill-language.md` を広げる。

**Files:**
- Modify: `.claude/rules/skill-language.md`（frontmatter の `paths`、冒頭の対象の記述）
- Modify: `.claude/CLAUDE.md:47`（`- **自作スキルの SKILL.md: 日本語**…` の行）

**Interfaces:**
- Consumes: なし（Task 1 とは独立）
- Produces: `.py` を対象に含む記述言語の規約。Task 5・Task 6 の日本語化がこれに従う。

- [ ] **Step 1: `skill-language.md` の `paths` を広げる**

frontmatter を次に置き換える。

```yaml
---
paths:
  - ".claude/skills/**/*.md"
  - ".claude/skills/**/*.py"
  - ".claude/scripts/**/*.py"
---
```

- [ ] **Step 2: `skill-language.md` の冒頭の対象の記述を広げる**

現在の1文目:

```markdown
`CLAUDE.md` § 言語 の「自作スキルの SKILL.md: 日本語」の細則。**自作スキル（`.claude/skills/j-*` と `md2joifup`）を新規作成・改訂するときに適用する。** superpowers / ECC のスキルは無改変で使うので対象外（それらはこのリポジトリの `.claude/skills/` 配下に無い）。
```

を、次に置き換える。

```markdown
`CLAUDE.md` § 言語 の「自作スキルの SKILL.md と自作スクリプト: 日本語」の細則。**自作スキル（`.claude/skills/j-*` と `md2joifup`）の SKILL.md と、自作スクリプト（`.claude/scripts/` と `.claude/skills/*/scripts/` の `.py`）を新規作成・改訂するときに適用する。** superpowers / ECC のスキルは無改変で使うので対象外（それらはこのリポジトリの `.claude/skills/` 配下に無い）。

**スクリプトでは docstring とコメントが対象である。** 識別子・コマンド・パス・フラグ・環境変数・型名・例外のメッセージ・エラー文字列は英語のまま残す（下の「英語のまま残すもの」の一覧と同じ扱い）。
```

- [ ] **Step 3: `CLAUDE.md:47` の該当行を広げる**

行頭の `- **自作スキルの SKILL.md: 日本語**（`.claude/skills/j-*` と `md2joifup`。本文・` の部分を、次のように書き換える。**行の残り（英語のまま残すものの一覧以降）は変えない。**

変更前の先頭:
```
- **自作スキルの SKILL.md: 日本語**（`.claude/skills/j-*` と `md2joifup`。本文・`##`/`###` 見出し・`description`・`argument-hint`）。
```

変更後の先頭:
```
- **自作スキルの SKILL.md と自作スクリプト: 日本語**（`.claude/skills/j-*` と `md2joifup` の SKILL.md は本文・`##`/`###` 見出し・`description`・`argument-hint`。`.claude/scripts/` と `.claude/skills/*/scripts/` の `.py` は docstring とコメント）。
```

同じ行の末尾にある `` `paths` スコープで `.claude/skills/**/*.md` を読むときに自動で載る `` を、`` `paths` スコープで対象のファイルを読むときに自動で載る `` に変える。

- [ ] **Step 4: 規約の参照先が一致していることを確かめる**

Run:
```bash
grep -n "自作スキルの SKILL.md と自作スクリプト" .claude/CLAUDE.md .claude/rules/skill-language.md
```

Expected: 2ファイルとも1件ずつヒットする（`CLAUDE.md` の該当行と、`skill-language.md` の1文目）。

- [ ] **Step 5: frontmatter が壊れていないことを確かめる**

Run:
```bash
python3 -c "
import sys
src = open('.claude/rules/skill-language.md', encoding='utf-8').read()
assert src.startswith('---\n'), 'frontmatter が無い'
fm = src.split('---\n')[1]
import yaml
paths = yaml.safe_load(fm)['paths']
assert '.claude/scripts/**/*.py' in paths, paths
print('OK', paths)
"
```

Expected: `OK ['.claude/skills/**/*.md', '.claude/skills/**/*.py', '.claude/scripts/**/*.py']`

- [ ] **Step 6: コミット**

```bash
git add .claude/rules/skill-language.md .claude/CLAUDE.md
git commit -m "docs(harness): extend the Japanese-prose rule to our own scripts"
```

---

### Task 3: `unwrap.py` の二重化を除く

このファイルが本タスクの出発点である。設計書との重複が最大で、既に陳腐化している。

**Files:**
- Modify: `.claude/scripts/unwrap.py`
- Reference: `notes/document/008-no-hard-wrap-japanese-design.md`（正典。読むだけ）
- Test: `.claude/scripts/test_unwrap.py`（既存。変更しない）

**Interfaces:**
- Consumes: Task 1 の判定の表（Global Constraints に転記済み）

- [ ] **Step 1: 既知の重複を設計書と突き合わせる**

次の5箇所は `notes/document/008-no-hard-wrap-japanese-design.md` に同じ根拠がある。**消す前に、対応する節を実際に開いて内容が本当にあることを確かめる。**

| `unwrap.py` | 設計書の対応節 |
| --- | --- |
| `:444` 付近 `verify()` の docstring、検証5条件の列挙 | `## 検証` の 1〜5 |
| `:452` 付近 「5つ目がその残りを塞ぐ」＋自己参照の説明 | `### 5つ目: 独立したパーサによる AST 比較` 第1段落 |
| `:394` 付近 `ast_blocks()` の「1文字でも違えば欠陥」 | `### 5つ目` の正規化の項 |
| `:48` 付近 `indent_width()` のタブ展開の根拠 | `## 変換の規則` |
| `:215` 付近 `joins` を人間に見せる理由 | `### 検証を通ったあとに人間へ見せるもの` |

Run:
```bash
grep -n "^##\|^###" notes/document/008-no-hard-wrap-japanese-design.md
```

Expected: `## 検証` / `### 5つ目: 独立したパーサによる AST 比較` / `### 検証を通ったあとに人間へ見せるもの` / `## 変換の規則` がすべて存在する。

- [ ] **Step 2: モジュール docstring の陳腐化した写しを直す**

7行目の現在の文:

```
**規約と変換規則の正典は notes/document/008-no-hard-wrap-japanese-design.md**（dotfiles）である。結合点の空白・触らないものの一覧・検証の4条件は、すべてそこで決めている。規則を変えるときは設計を先に直す。
```

「検証の4条件」は設計書の5条件と食い違っている。**数を直すのではなく、列挙そのものを落とす。** 次に置き換える。

```
**規約と変換規則の正典は notes/document/008-no-hard-wrap-japanese-design.md**（dotfiles）である。何を結合し何を触らないか、書き戻す前に何を確かめるかは、すべてそこで決めている。規則を変えるときは設計を先に直す。
```

- [ ] **Step 3: 残る4箇所を1行のポインタに畳む**

Step 1 の表の残り4箇所について、設計書にある根拠の説明を落とし、正典の節を指す1行だけを残す。**条件の数・条件の列挙・節の中身の要約を書かない。**

例（`verify()` の docstring）:

```python
def verify(...):
    """変換が壊していないことを確かめる。空のリストなら安全である。

    条件とその根拠は notes/document/008-no-hard-wrap-japanese-design.md の `## 検証` が正典。
    """
```

**コードから復元できない why は残す。** 例として次は残す（設計書に無い、あるいはコードの形そのものに関する事実である）:

- `:26` の「`unwrap.py` 本体は依存ゼロのまま保つ」——このファイルの設計上の制約であり、読む人が最初に知るべきこと
- `:149` の `\r` を見ないと CRLF で保護が黙って外れる件——実装の具体的な落とし穴
- `:575` の「黙って飛ばさない」——その行の直下のコードの意図

判断がつかないものは**残す**。落とした行数ではなく、嘘になりうる面が減ったかで見る。

- [ ] **Step 4: コードを1行も変えていないことを確かめる**

Run:
```bash
python3 /private/tmp/claude-501/-Users-ara-Joifup-dotfiles/73d70231-b8b1-4c2b-86fa-fdb5ad3e0f54/scratchpad/check_code_unchanged.py HEAD .claude/scripts/unwrap.py
```

Expected: `OK    .claude/scripts/unwrap.py`

FAIL が出たらコードを触っている。戻して、コメントだけを直す。

- [ ] **Step 5: テストが green であることを確かめる**

Run:
```bash
cd .claude/scripts && python3 -m unittest test_unwrap -v 2>&1 | tail -5
```

Expected: 最終行が `OK`。**件数は固定しない** —— テストは増えるので、数を書けばそれ自体が陳腐化する（この計画は当初「139」と書いていたが、実際は 154 だった）。

- [ ] **Step 6: 陳腐化した写しが消えたことを確かめる**

Run:
```bash
grep -n "検証の4条件\|4 条件" .claude/scripts/unwrap.py
```

Expected: ヒット 0 件（`grep` の exit code は 1）。

- [ ] **Step 7: コミット**

```bash
git add .claude/scripts/unwrap.py
git commit -m "docs(scripts): collapse unwrap rationale into a pointer to its design"
```

---

### Task 4: `measure_wraps.py` の二重化を除く

**Files:**
- Modify: `.claude/scripts/measure_wraps.py`
- Reference: `notes/document/008-no-hard-wrap-japanese-design.md`
- Test: `.claude/scripts/test_unwrap.py`（`measure_wraps` も import している。変更しない）

- [ ] **Step 1: 重複を設計書と突き合わせる**

このファイルはモジュール docstring の最後に既にポインタを持っている。

```
折り返しの定義と、直り切らないもの（4スペース以上のインデント行・引用の中）の扱いの正典は notes/document/008-no-hard-wrap-japanese-design.md。
```

そのうえで docstring の前半で、折り返しの定義・文末の扱い・除外するものを設計書から写している。設計書の `## 規約` と `## 直り切らないものを見えるようにする` を開いて、写しであることを確かめる。

`FENCE` と `TAB_WIDTH` の上のコメントは、CommonMark のフェンスの規則を再説明している。これは `unwrap.py` にも同じ説明があり、**他ファイルの動作の再説明**にも当たる。

- [ ] **Step 2: docstring を畳む**

前半の定義の写しを落とし、この道具が何を出すかと使い方だけを残す。ポインタは末尾の1行を先頭付近へ移し、**内容の要約を付けない**。

**残すもの:** 使い方のコマンド、出力の形（「折り返し行 / 段落行 = 割合（うち日本語 N）」）、引数なし・存在しないディレクトリで `exit 2` する挙動。これらはコードから読み取るより docstring で読むほうが速く、設計書には無い。

**落とすもの:** 折り返しの定義、文末で数えない理由、除外するものの列挙。すべて設計書にある。

- [ ] **Step 3: `FENCE` / `TAB_WIDTH` のコメントを畳む**

CommonMark の規則の再説明を落とし、**`unwrap.py` と同じ定義に保つ必要があること**だけを残す（これはこのファイル固有の制約であり、設計書にも `unwrap.py` にも無い）。テストが一致を固定していることは残す —— 読む人が定義を勝手に変えないための情報である。

```python
# unwrap.py と同じ定義に保つ。一致は test_unwrap の test_the_fence_handling_matches_unwrap が固定している。
# 片方だけがフェンスの内と外を取り違えると、変換しないと決めた場所の折り返しが残量に出続ける。
FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
# unwrap.py と同じ定義に保つ（同上）。
TAB_WIDTH = 4
```

- [ ] **Step 4: コードを1行も変えていないことを確かめる**

Run:
```bash
python3 /private/tmp/claude-501/-Users-ara-Joifup-dotfiles/73d70231-b8b1-4c2b-86fa-fdb5ad3e0f54/scratchpad/check_code_unchanged.py HEAD .claude/scripts/measure_wraps.py
```

Expected: `OK    .claude/scripts/measure_wraps.py`

- [ ] **Step 5: テストが green であることを確かめる**

Run:
```bash
cd .claude/scripts && python3 -m unittest test_unwrap -v 2>&1 | tail -5
```

Expected: 最終行が `OK`。**件数は固定しない** —— テストは増えるので、数を書けばそれ自体が陳腐化する（この計画は当初「139」と書いていたが、実際は 154 だった）。

- [ ] **Step 6: 道具が動くことを確かめる**

Run:
```bash
python3 .claude/scripts/measure_wraps.py notes
```

Expected: `notes` の下の md について「折り返し行 / 段落行 = 割合」の行が出る。exit code 0。

- [ ] **Step 7: コミット**

```bash
git add .claude/scripts/measure_wraps.py
git commit -m "docs(scripts): drop the wrap definition copied into measure_wraps"
```

---

### Task 5: `j_finish.py` と `uat_attach.py` を掃除し日本語にそろえる

2ファイルは同じスキルの配線であり、同じ性質の重複（joifup の `notes/document/295-*` の写し）を持つ。モジュール docstring が英語なのも共通。まとめて扱う。

**Files:**
- Modify: `.claude/skills/j-finish/scripts/j_finish.py`
- Modify: `.claude/skills/j-finish/scripts/uat_attach.py`
- Reference: `/Users/ara/Joifup/joifup/notes/document/295-uat-e2e-split-evidence-to-pr-attachments.md`（正典。読むだけ）
- Test: `.claude/skills/j-finish/scripts/test_j_finish.py`、`.claude/skills/j-finish/scripts/test_uat_attach.py`（既存。変更しない）

**Interfaces:**
- Consumes: Task 2 の記述言語の規約（`.py` の docstring とコメントは日本語）

- [ ] **Step 1: `uat_attach.py` の契約の列挙を正典と突き合わせる**

モジュール docstring の箇条書き5項目が、joifup の設計書にあることを確かめる。

Run:
```bash
grep -n "50\|alt text\|ASCII slug\|書き換わる\|裸 URL\|プレイヤー" /Users/ara/Joifup/joifup/notes/document/295-uat-e2e-split-evidence-to-pr-attachments.md
```

Expected: 「最大 50 ファイル」「アップロード先 URL に自動で書き換わる」「alt text」「ASCII slug」に当たる記述がヒットする。

**ただし `MIN_GH_VERSION = (2, 99, 0)` の `2.99.0` は設計書に無い。** 設計書は「下限バージョンは実装時に `gh` のリリースノートで特定する（2.100.0 で存在することは確認済み）」と書いている。**2.99.0 は実装時に確定した、コードにしか無い一次情報である。消さずに、定数の上に短く残す。**

- [ ] **Step 2: `uat_attach.py` の docstring を畳む**

契約の列挙5項目を落とし、正典を指す1行に置き換える。**項目の数も内容も書かない。**

```python
#!/usr/bin/env python3
"""UAT 証跡を PR に添付する — `gh pr comment --attach` の配線。

添付の運用と、この配線が守るべき契約の正典は joifup の
`notes/document/295-uat-e2e-split-evidence-to-pr-attachments.md` である。

標準ライブラリのみに依存する（j_finish.py と違い PyYAML を要求しない）。
"""
```

**`results.jsonl` から読む理由**（`name` に `|` が入ると表はずれるが JSONL はずれない）は設計書に無い実装上の判断なので、読む側の関数のところに残す。

- [ ] **Step 3: `MIN_GH_VERSION` にコードにしか無い事実を残す**

```python
# 2.99.0 は `--attach` の初出。設計書は「実装時にリリースノートで特定する」と
# 書いており、この数字はここにしか無い。
MIN_GH_VERSION = (2, 99, 0)
```

- [ ] **Step 4: `j_finish.py` の docstring を日本語にし、手順の再説明を落とす**

現在の英語の docstring は、5つの手順を列挙している。この順序と内容は `j-finish/SKILL.md` にある（同じリポジトリの、人が読む面）。**手順の列挙を落とし、SKILL.md を指す。**

```python
#!/usr/bin/env python3
"""j-finish — 完了したブランチを承認ゲートの手前の状態まで仕上げる出力アダプタ。

手順とその順序、各手順が何を行うかの正典は `.claude/skills/j-finish/SKILL.md`。

**絶対に Done にせず、絶対にマージしない。** status→Done と
`chore(joifup): approve TASK-xxx` とマージは、人間の承認セッションが持つ。

--dry-run はネットワークと副作用のある手順（git / gh / curl）だけを止め、
実行するはずのコマンドを出す。ローカルのファイル操作（status の書き換え）と
2つの読み取り専用の手順（UAT 証跡の事前確認、証跡添付の `gh --version` 確認と
`results.jsonl` の読み取りと各証跡パスの包含確認）は両方のモードで走る ——
何も変えないうえ、その答えこそが dry-run を読む価値だからである。
"""
```

- [ ] **Step 5: 残りの英語コメントを日本語にする**

Run:
```bash
grep -nE '^\s*#\s*[A-Za-z]' .claude/skills/j-finish/scripts/j_finish.py .claude/skills/j-finish/scripts/uat_attach.py
```

ヒットした行のうち、英語の散文になっているものを日本語にする。**識別子・コマンド・フラグ・型名・エラー文字列はそのまま。** `# noqa: E402` のようなツール向けの指示も英語のまま残す。

- [ ] **Step 6: コードを1行も変えていないことを確かめる**

Run:
```bash
python3 /private/tmp/claude-501/-Users-ara-Joifup-dotfiles/73d70231-b8b1-4c2b-86fa-fdb5ad3e0f54/scratchpad/check_code_unchanged.py HEAD .claude/skills/j-finish/scripts/j_finish.py .claude/skills/j-finish/scripts/uat_attach.py
```

Expected: 2行とも `OK`。

- [ ] **Step 7: テストが green であることを確かめる**

Run:
```bash
python3 .claude/skills/j-finish/scripts/test_j_finish.py 2>&1 | tail -3
python3 .claude/skills/j-finish/scripts/test_uat_attach.py 2>&1 | tail -3
```

Expected: どちらも最終行が `OK`。

- [ ] **Step 8: コミット**

```bash
git add .claude/skills/j-finish/scripts/j_finish.py .claude/skills/j-finish/scripts/uat_attach.py
git commit -m "docs(j-finish): point at the design instead of restating the attach contract"
```

---

### Task 6: `md2joifup.py` を日本語にし、SKILL.md の写しを落とす

**Files:**
- Modify: `.claude/skills/md2joifup/scripts/md2joifup.py`
- Reference: `.claude/skills/md2joifup/SKILL.md`（正典。読むだけ）

**Interfaces:**
- Consumes: Task 2 の記述言語の規約

- [ ] **Step 1: docstring と SKILL.md の重複を確かめる**

モジュール docstring は、このツールが何をするかを箇条書きで列挙している。同じ内容が `SKILL.md` の `## 何をするか` にある。

Run:
```bash
grep -n "^- " .claude/skills/md2joifup/SKILL.md | sed -n '1,30p'
```

Expected: 「H1 を抽出し、frontmatter の `title` に反映する」「superpowers の agentic-worker の scaffolding を取り除く」「house-style の frontmatter」「Project は常に解決される」「ファイル名 `<NNN>-<slug>.md`」「自動採番の `ID` だけを daemon に委ねる」が `SKILL.md` にあることを確かめる。**docstring の箇条書きと一対一で対応している。**

- [ ] **Step 2: docstring を日本語にし、列挙を落とす**

```python
#!/usr/bin/env python3
"""md2joifup — markdown ファイルを Joifup の Notes-DB row（frontmatter + 本文）
として、その場で永続化する。source は superpowers の成果物（plan / spec）でも
手書きの note（doc / log / research）でもよい。

何をするか、引数の意味、Task と Project の解決順の正典は
`.claude/skills/md2joifup/SKILL.md` である。

frontmatter・tag・リレーションの規約は**ハードコードしない** —— 実行時に
Joifup の schema を読む。
"""
```

**最後の1文は残す。** これはこのファイルの実装上の制約であり、`SKILL.md` にも書かれているが、**コードを直す人が最初に知るべき禁止事項**である。判断がつかないものは残す側に倒す。

- [ ] **Step 3: 残りの英語コメントを日本語にする**

Run:
```bash
grep -nE '^\s*#\s*[A-Za-z]|"""[A-Za-z]' .claude/skills/md2joifup/scripts/md2joifup.py
```

ヒットした行のうち、英語の散文を日本語にする。**識別子・コマンド・フラグ・型名・エラー文字列・`argparse` の `help` 文字列はそのまま**（`help` は実行時の出力であり、コメントではない）。

- [ ] **Step 4: コードを1行も変えていないことを確かめる**

Run:
```bash
python3 /private/tmp/claude-501/-Users-ara-Joifup-dotfiles/73d70231-b8b1-4c2b-86fa-fdb5ad3e0f54/scratchpad/check_code_unchanged.py HEAD .claude/skills/md2joifup/scripts/md2joifup.py
```

Expected: `OK    .claude/skills/md2joifup/scripts/md2joifup.py`

- [ ] **Step 5: 道具が動くことを確かめる**

Run:
```bash
python3 .claude/skills/md2joifup/scripts/md2joifup.py --help 2>&1 | head -5
```

Expected: usage が出る。exit code 0。

- [ ] **Step 6: 英語の散文が残っていないことを確かめる**

Run:
```bash
grep -nE '^\s*#\s*[A-Z][a-z]+ [a-z]+' .claude/skills/md2joifup/scripts/md2joifup.py
```

Expected: ヒット 0 件。ヒットしたものは、識別子やコマンドでなければ日本語にする。

- [ ] **Step 7: コミット**

```bash
git add .claude/skills/md2joifup/scripts/md2joifup.py
git commit -m "docs(md2joifup): translate to Japanese and point at the skill doc"
```

---

## 完了時の検査（全タスクのあと）

- [ ] **すべての Python がコンパイルできる**

Run:
```bash
python3 -m compileall -q .claude/scripts .claude/skills/j-finish/scripts .claude/skills/md2joifup/scripts && echo "COMPILE OK"
```

Expected: `COMPILE OK`

- [ ] **全テストが green**

Run:
```bash
cd .claude/scripts && python3 -m unittest test_unwrap -v 2>&1 | tail -3
python3 .claude/skills/j-finish/scripts/test_j_finish.py 2>&1 | tail -3
python3 .claude/skills/j-finish/scripts/test_uat_attach.py 2>&1 | tail -3
```

Expected: 3つとも `OK`。

- [ ] **コードが1行も変わっていない**

Run:
```bash
python3 /private/tmp/claude-501/-Users-ara-Joifup-dotfiles/73d70231-b8b1-4c2b-86fa-fdb5ad3e0f54/scratchpad/check_code_unchanged.py <base-sha> \
  .claude/scripts/unwrap.py .claude/scripts/measure_wraps.py \
  .claude/skills/j-finish/scripts/j_finish.py \
  .claude/skills/j-finish/scripts/uat_attach.py \
  .claude/skills/md2joifup/scripts/md2joifup.py
```

`<base-sha>` はこのブランチの起点（`git merge-base main HEAD`）。

Expected: 5行とも `OK`。

- [ ] **コメント比率が下がったことを数で示す**

Run:
```bash
git diff --stat <base-sha> -- '*.py'
```

削除行数を PR 本文に載せる。**数字は目標ではない**（量ではなく嘘になりうる面の数を減らすのが目的）が、変化の規模を読む人に示す。

- [ ] **UAT は行わない。** UI を変更しないため。PR 本文には `## テスト` のみを載せる。

## 申し送り（マージ後に人間が起票する）

worktree から他リポジトリへ書かないため、本タスクでは起票しない。

- **joifup（コメント 38,178行 / 35.1%）** — 上位から当てる。`apps/web/src/lib/events.ts`（372%）・`rich-editor/joifup-node-stop-event.ts`（303%）・`use-pin-status.ts`（266%）は、`notes/document/178-sidebar-event-source-id-design.md` との重複が `tasks/006` で確認済み。**コメントは英語で統一されているので日本語化しない。**
- **fde（コメント 2,008行 / 24.9%）** — 同じ指針を当てる。
- どちらも**指針を各リポジトリに写さない**。`~/.claude/rules/comment-rationale.md` が正典であり、写した瞬間にこのタスクが直した問題を再生産する。
