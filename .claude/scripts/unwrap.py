#!/usr/bin/env python3
"""日本語の md 本文のハード折り返しを結合する。

段落の途中で改行されている行を結合し、frontmatter・コードフェンス・表・
見出し・引用・意図的なハードブレイク・日本語を含まない段落は触らない。

**規約と変換規則の正典は notes/document/008-no-hard-wrap-japanese-design.md**
（dotfiles）である。結合点の空白・触らないものの一覧・検証の3条件は、
すべてそこで決めている。規則を変えるときは設計を先に直す。

使い方:

    # dry-run。対象ディレクトリを1つ以上渡す。書き換えは一切しない
    python3 unwrap.py <対象ディレクトリ> [<対象ディレクトリ> ...]

    # 適用。dry-run で FAILED が 0 件であることを確かめてから
    python3 unwrap.py <対象ディレクトリ> [...] --apply

対象ディレクトリの下の *.md を再帰的に見る（例: `<repo>/notes <repo>/tasks
<repo>/.claude`）。除外パス（node_modules・.git・worktrees 等）は**対象
ディレクトリからの相対**で判定するので、worktree の中を対象にしても全件が
除外されることはない。

**他の repo に当てる前に必ずテストを走らせる**（`cd .claude/scripts &&
python3 -m unittest test_unwrap -v`）。道具が壊れていないことを先に確かめて
から実データに当てる。適用したあとは measure_wraps.py で折り返しの残量を
測り、直り切らなかった分を数で見る。
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
# 結合点の判定に使う「日本語」。かな・漢字に加えて、全角の句読点・括弧・
# 記号 (。、「」（） 等) を含む。CJK より広いのは、結合点には本文の文字
# だけでなく約物も来るためである。
JA = re.compile(r"[　-〿぀-ヿ㐀-䶿一-鿿＀-￯]")
HARD_BREAK = re.compile(r"(  |\\)$")
INDENT = re.compile(r"^\s*")
# 全角の句読点。この直後には、右が何であっても空白を入れない。
JA_PUNCT = "。、"
# 全角の開き括弧。この直前には、左が何であっても空白を入れない。
JA_OPEN = "（「『【〔"

def is_block_start(line):
    """段落の続きになりえない行か。"""
    return bool(FENCE.match(line) or HEADING.match(line) or QUOTE.match(line)
                or TABLE.match(line) or RULE.match(line) or LIST.match(line))

def join_parts(parts):
    """行の並びを1行に結合する。

    結合点の前後がともに日本語 (かな・漢字・全角の句読点や記号) なら空白
    なしで繋ぎ、それ以外は半角空白1つを入れる (設計の「結合点の空白」)。
    ただし全角の約物には例外を置く。左が全角の句読点 (。、) なら右が何で
    あっても、右が全角の開き括弧 (（「『【〔) なら左が何であっても、空白を
    入れない。日本語では句読点の直後にも開き括弧の直前にも空白を置かない
    ためである。例外は必ず両側に置く。片側だけにすると鏡の側が開く。前者が
    無いと `解決される。` + `` `brew upgrade tmux` `` に空白が入り、後者が
    無いと `` `.claude` `` + `（対象は…` に空白が入る。

    判定は「片側が ASCII 英数か」ではなく「両側が日本語か」で行う。前者
    だと、結合点に記号どうしが来たときに空白が落ちるためである。たとえば
    `使う:` と `` `brainstorming` `` は : も ` も ASCII 英数でないので
    空白なしで繋がれ、原文にあった区切りが消えてしまう。空白が要らないの
    は日本語どうしの間だけなのだから、判定もそのまま日本語で書く。
    """
    out = parts[0]
    for part in parts[1:]:
        left = out[-1:] if out else ""
        right = part[:1]
        if not left or not right:
            # どちらかが空なら結合点そのものが無い。空文字は in 判定でどの
            # 文字列にも含まれるので、明示的に先に落としておかないと
            # `left in JA_PUNCT` が偽の真になる (マーカーだけの行など)。
            out = out + part
        elif left in JA_PUNCT:
            out = out + part
        elif right in JA_OPEN:
            out = out + part
        elif JA.match(left) and JA.match(right):
            out = out + part
        else:
            out = out + " " + part
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

        # 段落、またはリスト項目。リスト項目ならマーカーまでを、ただの段落
        # なら行頭のインデントを prefix として外し、本文だけを畳んであとから
        # prefix を戻す。段落のインデントを戻さないと、リスト項目の中の継続
        # 段落が桁 0 に出てリストがそこで切れる。verify はリスト項目の数も
        # 段落テキストも変わらないため、これを検出できない。だから結合の側
        # で必ずインデントを保つ。
        m = LIST.match(line) or INDENT.match(line)
        prefix = line[:m.end()]
        raw = [line[m.end():]]
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

def _squeeze(text):
    """空白と改行をすべて落とす。文字の欠落・重複・順序変更だけを見るため。"""
    return re.sub(r"\s+", "", text)

def _count(text, pattern):
    return sum(1 for line in text.split("\n") if pattern.match(line))

PIPE_SEP = re.compile(r"^\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+$")

STRUCTURE = (("見出し", HEADING), ("コードフェンス", FENCE),
             ("リスト項目", LIST), ("表の行", TABLE),
             ("表の区切り行", PIPE_SEP))

def _paragraph_indents(text):
    """段落の先頭行 (空行の次の非空行) の行頭インデント幅を順に並べて返す。"""
    indents = []
    previous_blank = True
    for line in text.split("\n"):
        blank = not line.strip()
        if not blank and previous_blank:
            indents.append(len(line) - len(line.lstrip()))
        previous_blank = blank
    return indents

def verify(before, after):
    """変換の前後を比べ、書き戻して安全でない理由を並べて返す。

    空のリストなら安全である。設計の「検証」の3条件を実装している:
    段落テキストが文字単位で一致すること、構造の数が変わらないこと、
    段落の頭のインデントの並びが変わらないこと。

    3つ目は、インデントを落としてリストを切る壊し方が1つ目も2つ目も
    素通りするから要る。リスト項目の数は変わらず、段落テキストの比較は
    空白を無視するので、どちらも気づかない。
    """
    problems = []
    if _squeeze(before) != _squeeze(after):
        problems.append("段落テキストが一致しない (文字の欠落・重複・順序変更)")
    for name, pattern in STRUCTURE:
        b, a = _count(before, pattern), _count(after, pattern)
        if b != a:
            problems.append(f"{name} の数が {b} から {a} に変わった")
    b, a = _paragraph_indents(before), _paragraph_indents(after)
    if b != a:
        problems.append("段落の頭のインデントの並びが変わった")
    return problems

SKIP = ("/node_modules/", "/.git/", "/.claude/worktrees/", "/.superpowers/",
        "/fixtures/", "/dist/", "/build/", "/target/", "/.next/",
        "/coverage/")

def unwrap_file(path, apply=False):
    """1ファイルを変換する。戻り値は ("changed"|"unchanged"|"failed", 詳細)。"""
    try:
        before = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        # 他の repo には壊れたファイルや読めないファイルがある。1件で全体を
        # 落とすと残りが処理されないので、そのファイルを失敗として報告して続ける。
        return "failed", f"読めない ({e.__class__.__name__})"
    after = unwrap_text(before)
    if before == after:
        return "unchanged", ""
    problems = verify(before, after)
    if problems:
        return "failed", "; ".join(problems)
    if apply:
        try:
            path.write_text(after, encoding="utf-8")
        except OSError as e:
            return "failed", f"書けない ({e.__class__.__name__})"
    return "changed", ""

def main(argv):
    import pathlib
    apply = "--apply" in argv
    roots = [a for a in argv if not a.startswith("--")]
    if not roots:
        # 渡し忘れたときに「変換した: 0 / 変更なし: 0 / 失敗: 0」を出して
        # exit 0 すると、何もしていないのに成功に見える。
        print("使い方: python3 unwrap.py <対象ディレクトリ> [...] [--apply]")
        return 2
    changed = unchanged = failed = 0
    for root in roots:
        base = pathlib.Path(root)
        for path in sorted(base.rglob("*.md")):
            # root より内側だけを見て判定する。root 自身が .claude/worktrees/
            # の下にあるときに全件が除外されてしまうのを避けるため。
            rel = "/" + str(path.relative_to(base))
            if any(s in rel for s in SKIP):
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
