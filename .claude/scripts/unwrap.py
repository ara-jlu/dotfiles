#!/usr/bin/env python3
"""日本語の md 本文のハード折り返しを結合する。

段落の途中で改行されている行を結合し、frontmatter・コードフェンス・HTML ブロック・コンテナディレクティブ (`:::`) の行・表・見出し・引用・意図的なハードブレイク・日本語を含まない段落は触らない。
**文末 (`。` `！` `？`) での改行は折り返しではないので結合しない。**

**規約と変換規則の正典は notes/document/008-no-hard-wrap-japanese-design.md**（dotfiles）である。何を結合し何を触らないか、書き戻す前に何を確かめるかは、すべてそこで決めている。規則を変えるときは設計を先に直す。

使い方:

    # dry-run。対象ディレクトリを1つ以上渡す。書き換えは一切しない
    python3 unwrap.py <対象ディレクトリ> [<対象ディレクトリ> ...]

    # 適用。dry-run で FAILED が 0 件であることを確かめてから
    python3 unwrap.py <対象ディレクトリ> [...] --apply

対象ディレクトリの下の *.md を再帰的に見る（例: `<repo>/notes <repo>/tasks <repo>/.claude`）。除外（node_modules・.git・worktrees 等）は**対象ディレクトリからの相対パスの要素名**で判定する。だから worktree の中を対象にしても全件が除外されることはなく、対象の内側に worktrees/ があればその中は除外される。
対象がディレクトリとして存在しなければ、その旨を出して exit 2 する。

検証の第5条件 (AST 比較) には `markdown-it-py` が要る。**任意の依存**であり、無ければその条件だけを飛ばして警告を出す。入れるには `pip3 install --user markdown-it-py`。

**他の repo に当てる前に必ずテストを走らせる**（`cd .claude/scripts && python3 -m unittest test_unwrap -v`）。道具が壊れていないことを先に確かめてから実データに当てる。適用したあとは measure_wraps.py で折り返しの残量を測り、直り切らなかった分を数で見る。
"""
import re

# **テスト専用ではなく検証専用の、任意の依存である。** `markdown-it-py` があれば verify の第5条件 (独立したパーサによる AST 比較) が働き、無ければその条件だけを飛ばす。
# **`unwrap.py` 本体は依存ゼロのまま保つ。** 変換そのものは markdown_it を一切使わない。使うのは「変換が壊していないか」を第三者の目で確かめる側だけである。
# 無いときに黙って飛ばしてはならない。この道具は「黙って成功に見える」形を何度も潰してきた。main が警告を出し、verify も検査を行ったかどうかを呼び出し側に返す。
try:
    from markdown_it import MarkdownIt as _MarkdownIt
except ImportError:  # pragma: no cover - パーサの有無は環境で決まる
    _MarkdownIt = None

HAS_AST_PARSER = _MarkdownIt is not None
AST_MISSING_NOTE = ("markdown-it-py が無いため AST 比較 (検証の第5条件) を行っていない。"
                    "`pip3 install --user markdown-it-py` で入れること。")

# フェンスのマーカー行。開くか閉じるかに関わらず、マーカーだけを見た形。
# 1 群が行頭のインデント、2 群がマーカー (``` 以上または ~~~ 以上)、3 群がそのあとの情報文字列。
FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")
# CommonMark のタブ幅。インデントは**桁**で数える規則なので、タブは次の 4 の倍数の桁まで進む。
TAB_WIDTH = 4


def indent_width(indent):
    """行頭の空白を CommonMark の**桁**で数える。タブは次の 4 の倍数の桁まで進む。

    `len()` で数えてはならない。その根拠は notes/document/008-no-hard-wrap-japanese-design.md の `## 変換の規則` が正典。
    """
    width = 0
    for ch in indent:
        width = width + TAB_WIDTH - width % TAB_WIDTH if ch == "\t" else width + 1
    return width


def fence_open(line):
    """行がフェンスを開くなら (マーカーの文字, 長さ, インデント幅) を返す。

    開かないなら None。**バッククォートのフェンスの情報文字列にはバッククォートを書けない**ので、`` ```a` の書き方 `` のような行はフェンスではなく段落である。これを見ないとただの段落行がフェンスを開き、以降のフェンスの内と外が入れ替わる。チルダのフェンスにはこの制限が無い (情報文字列にバッククォートを書いてよい)。

    インデント幅を返すのは、閉じマーカーのインデントを**開きからの相対**で見るためである (fence_closes を見よ)。
    """
    m = FENCE.match(line)
    if not m:
        return None
    marker = m.group(2)
    if marker[0] == "`" and "`" in m.group(3):
        return None
    return marker[0], len(marker), indent_width(m.group(1))

def fence_closes(line, char, length, indent):
    """行が (char, length, indent) で開いたフェンスを閉じるか。

    markdown でフェンスを閉じられるのは、**開いたときと同じ文字で、同じ長さ以上**のマーカーだけである。それより短いマーカーや別の文字のマーカーは中身 (コンテンツ) であって、閉じない。また**閉じマーカーの行には情報文字列を書けない**ので、マーカーのあとに空白以外が続く行も閉じない。

    **閉じマーカーのインデントは開きマーカーから 3 桁までである。** それより深くインデントされた行は中身であって、閉じない。絶対の桁数で「3 桁まで」と書いてはならない。リスト項目の中のフェンスは 4 桁以上インデントされて開くことがあり、その閉じマーカーも同じ深さにあるからである。見るのは **開きからの相対**である。

    ここを見ずに実装したときに何が壊れたかは notes/document/008-no-hard-wrap-japanese-design.md の `## 変換の規則` が正典。
    """
    m = FENCE.match(line)
    if not m:
        return False
    marker = m.group(2)
    return (marker[0] == char and len(marker) >= length
            and not m.group(3).strip()
            and indent_width(m.group(1)) <= indent + 3)

# HTML ブロックの開始行。扱うのは 3 種類である: CommonMark の 1 種目 (`<pre>` `<script>` `<style>` `<textarea>`)、2 種目の HTML コメント (`<!--`)、そして行頭が HTML のタグに見える行 (6 種目・7 種目を広く取ったもの)。
# HTML ブロックを触らない根拠は notes/document/008-no-hard-wrap-japanese-design.md の `## 変換の規則`、判定を広く取ることの代償は同じ文書の `## 直り切らないものを見えるようにする` が正典。
# インデントを 3 桁までに限るのは CommonMark の規則に合わせたものである。4 桁以上はインデントされたコードブロックであり、そちらは INDENTED_CODE が別に触らない側へ倒している。
HTML_COMMENT_OPEN = re.compile(r"^ {0,3}<!--")
# **どこまでを「タグに見える」とするか。** 行頭 (インデント 3 桁まで) が `<` または `</` で始まり、続いて ASCII の英字・英数字とハイフンのタグ名があり、そのあとが空白・`>`・`/>`・行末のいずれかである行をタグと見なす。
# 判定を CommonMark より広く取る根拠と、タグ名の形に当たらない行の例は notes/document/008-no-hard-wrap-japanese-design.md の `## 変換の規則` が正典。
HTML_TAG_OPEN = re.compile(r"^ {0,3}</?[A-Za-z][A-Za-z0-9-]*(\s|/?>|$)")
# **CommonMark の HTML ブロックの 1 種目**。`<pre>` `<script>` `<style>` `<textarea>` で始まるブロックだけは、**空行では終わらず閉じタグまで**が範囲である。他の種別と同じ「空行まで」で扱うと、空行をまたいだ続きが本文として結合される。`<pre>` は空白が意味を持つので、結合すれば描画が変わる。
# 件数に関わらず塞ぐ根拠は notes/document/008-no-hard-wrap-japanese-design.md の `## 変換の規則` が正典。
# 終了条件が 4 つの閉じタグのどれでもよいのは CommonMark の規定どおりである (開いたタグ名と一致している必要はない)。大文字小文字は区別しない。
HTML_RAW_OPEN = re.compile(r"^ {0,3}<(pre|script|style|textarea)(\s|>|$)",
                           re.IGNORECASE)
HTML_RAW_CLOSE = re.compile(r"</(pre|script|style|textarea)>", re.IGNORECASE)


def html_block_open(line):
    """行が HTML ブロックを開くなら種別 ("comment" か "raw" か "tag") を返す。開かないなら None。

    **行の途中にある `<!--` は開かない。** インラインのコメントは HTML ブロックではなく段落の一部だからである。
    **フェンスの中の `<!--` や `<div>` も開かない。** これは呼び出し側の順序で担保する。フェンスの判定を先に行い、フェンスの中は中身として読み飛ばす。

    **`raw` の判定は `tag` より先に置く。** `<pre>` は HTML_TAG_OPEN にも当たるので、順序を逆にすると 1 種目が空行で終わる扱いに戻ってしまう。
    """
    if HTML_COMMENT_OPEN.match(line):
        return "comment"
    if HTML_RAW_OPEN.match(line):
        return "raw"
    if HTML_TAG_OPEN.match(line):
        return "tag"
    return None


def html_block_closes(line, kind):
    """行で HTML ブロックが終わるか。終わる行そのものもブロックの一部として扱う (出力はそのまま)。

    コメントは `-->` を含む行までである。閉じが無ければファイルの終わりまで中身として扱う (フェンスと同じ扱い)。**1 種目 (`<pre>` `<script>` `<style>` `<textarea>`) は閉じタグを含む行まで**であり、空行では終わらない。タグで始まるそれ以外のブロックは空行までである (CommonMark の 6 種目・7 種目と同じ)。
    """
    if kind == "comment":
        return "-->" in line
    if kind == "raw":
        return bool(HTML_RAW_CLOSE.search(line))
    return not line.strip()


HEADING = re.compile(r"^\s*#{1,6}\s")
QUOTE = re.compile(r"^\s*>")
TABLE = re.compile(r"^\s*\|")
RULE = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
# **コンテナディレクティブ** (`:::column` / `::::columns` / 閉じの `:::`)。行頭 (インデントは 3 桁まで) がコロン 3 個以上で始まる行は**本文の行ではない**ので、単独で触らない行として扱う。
# 開きと閉じを対応させない理由と、実データの状況は notes/document/008-no-hard-wrap-japanese-design.md の `## 変換の規則` が正典。
DIRECTIVE = re.compile(r"^ {0,3}:{3,}")
LIST = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")
INDENTED_CODE = re.compile(r"^( {4,}|\t)")
CJK = re.compile(r"[぀-ヿ一-鿿]")
# 結合点の判定に使う「日本語」。かな・漢字に加えて、全角の句読点・括弧・記号 (。、「」（） 等) を含む。CJK より広いのは、結合点には本文の文字だけでなく約物も来るためである。
JA = re.compile(r"[　-〿぀-ヿ㐀-䶿一-鿿＀-￯]")
# 意図的なハードブレイク (行末が半角空白2つ、または `\`)。**判定は rstrip の前の行に当てるので、CRLF の `\r` を許して読む。**
# `\r` を見ないと `本文  \r` に一致せず、CRLF の入力では保護が**黙って外れる**。ハードブレイクを含む段落が結合され、`_squeeze` も markdown-it も `\r` を吸収するので**検証の 5 条件すべてが通る**。
# 実データに CRLF は 0 件だが、扱いは `<pre>` と同じ基準である —— **黙って通る同種の欠陥は件数に関わらず塞ぐ**。
HARD_BREAK = re.compile(r"(  |\\)\r?$")
# 文末。行末から閉じ記号 (強調・コードスパン・閉じ括弧・引用符) を剥がしたうえで、`。` `！` `？` のいずれかで終わっているか。`…します。**` や `…する）。` のような形も文末として扱うためである。`：` や `:` は含めない。
# 次に続く内容の導入なので、そこでの改行は折り返しである。
SENTENCE_END = re.compile("[。！？][*_`）」』】〕)\"']*$")
INDENT = re.compile(r"^\s*")
# 全角の句読点。この直後には、右が何であっても空白を入れない。
JA_PUNCT = "。、"
# 全角の開き括弧。この直前には、左が何であっても空白を入れない。
JA_OPEN = "（「『【〔"

def is_block_start(line):
    """段落の続きになりえない行か。

    HTML ブロックの開始行もここに含める。段落の続きに見える位置に `<!--` や `<div>` が来ても、そこで段落を切って触らない側に倒す。コンテナディレクティブ (`:::`) の行も同じで、日本語の段落の直後に閉じの `:::` が来ても巻き込まない。
    """
    return bool(FENCE.match(line) or HEADING.match(line) or QUOTE.match(line)
                or TABLE.match(line) or RULE.match(line) or LIST.match(line)
                or DIRECTIVE.match(line) or html_block_open(line))

# 結合点の「普通の文字」。ASCII の英数字と JA (かな・漢字・全角の約物) に加えて、設計が定めた記号を足している。**どれでもない文字が結合点の左右に現れたら、それは本文の結合ではないかもしれない。**
# 判定は JA より広い。JA は結合点に空白を入れるかどうかを決める規則なので、そちらを広げると出力が変わる。こちらは**何を人間に見せるか**を決めるだけなので、別に持つ。
# どの記号を「普通の文字」に足し、何を足さないかの根拠は notes/document/008-no-hard-wrap-japanese-design.md の `### 検証を通ったあとに人間へ見せるもの` が正典。
ORDINARY = re.compile(r"[A-Za-z0-9/.\u00a7\u00b0\u00d7\u2010-\u205e"
                      r"\u2190-\u21ff\u2460-\u24ff]")
# **インラインの markdown 記法の文字。** 強調 (`**`)・コードスパン (`` ` ``)・リンク (`[]()`)・画像 (`!`)・取り消し線 (`~~`) は、**普通の本文の途中に普通に現れる**。判定の前にこれらを結合点から剥がす。
# 何を剥がし、何を剥がさないかの根拠は notes/document/008-no-hard-wrap-japanese-design.md の `### 検証を通ったあとに人間へ見せるもの` が正典。
INLINE_MARKUP = "`*_[]()\"'~!"
# 一覧に出す見本の長さの上限。長い行がそのまま出ると読めなくなる。
JOIN_SAMPLE_MAX = 24


def _is_ordinary(ch):
    """結合点の片側の文字が、日本語でも英数字でもある「普通の文字」か。"""
    return bool(ORDINARY.match(ch) or JA.match(ch))


def _odd_join_key(left_text, right_text):
    """結合点が「未知の形」なら、一覧でまとめるための鍵を返す。普通の結合なら None。

    **見るのは結合点の左右 1 文字ずつである** (インラインの markdown 記法を剥がしたあとの)。どちらかが日本語でも英数字でもなければ、本文どうしの結合ではない疑いがある。`-->`・`:::`・`$$` のようなブロックのマーカーも、`const a = 1;` のようなコードも、必ずここに当たる。

    鍵には**おかしいほうの側の語**を採る。右 (新しく足された行の先頭) を先に見るのは、ブロックの閉じマーカーが本文に巻き込まれるときは必ず右側に現れるからである (`-->`・`:::`)。左が原因のときだけ左の語を採る (コードの行末の `;` など)。両側を鍵にすると、相手側の本文が毎回違うので同じ形がまとまらず、一覧が件数分の行になって読まれなくなる。
    """
    left = left_text.rstrip(INLINE_MARKUP)[-1:]
    right = right_text.lstrip(INLINE_MARKUP)[:1]
    if not left_text or not right_text:
        return None
    if not _is_ordinary(right):
        token = re.match(r"\S+", right_text).group(0)
    elif not _is_ordinary(left):
        token = re.search(r"\S+$", left_text).group(0)
    else:
        return None
    return token[:JOIN_SAMPLE_MAX]


def join_parts(parts, joins=None):
    """行の並びを1行に結合する。

    `joins` にリストを渡すと、**未知の形の結合点**の鍵をそこへ足す (`_odd_join_key` を見よ)。何をなぜ人間に見せるかは notes/document/008-no-hard-wrap-japanese-design.md の `### 検証を通ったあとに人間へ見せるもの` が正典。

    結合点に空白を入れるかどうかの規則と、その決め方の根拠は notes/document/008-no-hard-wrap-japanese-design.md の `## 変換の規則` が正典。
    """
    out = parts[0]
    for part in parts[1:]:
        left = out[-1:] if out else ""
        right = part[:1]
        if joins is not None:
            key = _odd_join_key(out, part)
            if key is not None:
                joins.append(key)
        if not left or not right:
            # どちらかが空なら結合点そのものが無いので、空白を入れない (マーカーだけの行など)。この分岐が無くても `"" in JA_PUNCT` が真になるため結果は同じだが、`in` の性質に意図を負わせないために明示しておく。素朴に空白を入れると行末が半角空白2つになり、意図しないハードブレイクが生まれる。
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

def _fold(raw_lines, joins=None):
    """1つの段落 (またはリスト項目の本文) を結合して行の並びに返す。

    触らない場合は原文の行をそのまま返す。触らないのは、日本語を含まない段落と、意図的なハードブレイクを含む段落である (設計の「触らないもの」)。

    **文末での改行は折り返しではないので結合しない。** 前の行が `。` `！` `？` で終わっていれば (末尾に `**` や `）` のような閉じ記号が付いていてもよい)、そこで結合を止め、次の行から新しい結合の単位を始める。このタスクが問題にしているのは語や句の途中で割れることであり、文末は意味のある位置だから害が無い。段落そのものは分割しない (空行は入れない)。
    """
    if not CJK.search("\n".join(raw_lines)):
        return list(raw_lines)
    if any(HARD_BREAK.search(line) for line in raw_lines):
        return list(raw_lines)
    groups = []
    group = []
    for line in raw_lines:
        group.append(line)
        if SENTENCE_END.search(line.rstrip()):
            groups.append(group)
            group = []
    if group:
        groups.append(group)
    folded = []
    for i, group in enumerate(groups):
        text = join_parts([line.strip() for line in group], joins)
        if i:
            # 2つ目以降の単位は原文のインデントを保つ。落とすとリストの中の継続行が桁 0 に出てリストがそこで切れる。1つ目は呼び出し側が prefix (リストのマーカーまたは行頭のインデント) を戻す。
            text = INDENT.match(group[0]).group(0) + text
        folded.append(text)
    return folded

def unwrap_text(text, joins=None):
    """md の全文を受け、段落の途中の改行を結合した全文を返す。

    `joins` にリストを渡すと、未知の形の結合点の鍵をそこへ足す (`_odd_join_key` を見よ)。
    """
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

        opened = fence_open(line)
        if opened:
            # 開いたマーカーの文字と長さを覚え、それを閉じられる行だけで抜ける。閉じられないままファイルが終わる場合は、最後まで中身として扱う。
            out.append(line)
            i += 1
            char, length, indent = opened
            while i < len(lines):
                out.append(lines[i])
                closed = fence_closes(lines[i], char, length, indent)
                i += 1
                if closed:
                    break
            continue

        # **フェンスの判定より後に置く。** フェンスの中の `<!--` や `<div>` は HTML ブロックではなく、フェンスの中身だからである。上の分岐がフェンスを丸ごと読み飛ばすので、ここに来る時点でフェンスの外であることが保証される。
        kind = html_block_open(line)
        if kind:
            # 開始行そのものも閉じの判定にかける。`<!-- 一行のコメント -->` は 1 行で閉じるからである (フェンスは開きマーカーの行が自分を閉じることはないので、この点だけ扱いが違う)。
            while i < len(lines):
                out.append(lines[i])
                closed = html_block_closes(lines[i], kind)
                i += 1
                if closed:
                    break
            continue

        if (not line.strip() or HEADING.match(line) or QUOTE.match(line)
                or TABLE.match(line) or RULE.match(line)
                or DIRECTIVE.match(line) or INDENTED_CODE.match(line)):
            out.append(line)
            i += 1
            continue

        # 段落、またはリスト項目。リスト項目ならマーカーまでを、ただの段落なら行頭のインデントを prefix として外し、本文だけを畳んであとから prefix を戻す。段落のインデントを戻さないと、リスト項目の中の継続段落が桁 0 に出てリストがそこで切れる。verify はリスト項目の数も段落テキストも変わらないため、これを検出できない。だから結合の側で必ずインデントを保つ。
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
        folded = _fold(raw, joins)
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

# 英数字でも CJK (かな・漢字) でもある文字。これを **1 つも含まない非空行**が「マーカーだけの行」である。
ALNUM_OR_CJK = re.compile(r"[A-Za-z0-9぀-ヿ一-鿿]")


def _marker_lines(text):
    """英数字も CJK も含まない非空行を、現れる順に (前後の空白を落として) 並べて返す。"""
    return [line.strip() for line in text.split("\n")
            if line.strip() and not ALNUM_OR_CJK.search(line)]


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

# **ブロックの中身をそのまま比べる種別。** 下の `ast_blocks` は、この種別のトークンだけ中身を正規化せずに持つ。
AST_EXACT_TYPES = frozenset({"fence", "code_block", "html_block"})


def ast_blocks(text):
    """独立したパーサ (markdown-it-py) で text を解析し、ブロックの列を返す。

    返すのは `(ネストの深さ, トークンの種別, 中身)` の並びである。

    独立したパーサを使う理由と、何を正規化し何をしないかは notes/document/008-no-hard-wrap-japanese-design.md の `### 5つ目: 独立したパーサによる AST 比較` が正典。

    パーサが無い環境では `None` を返す。呼び出し側が「検査を飛ばした」ことを利用者に見せる。
    """
    if _MarkdownIt is None:
        return None
    tokens = _MarkdownIt("commonmark").parse(text)
    blocks = []
    depth = 0
    for token in tokens:
        if token.nesting == -1:
            depth -= 1
        content = ""
        if token.nesting == 0:
            content = (token.content if token.type in AST_EXACT_TYPES
                       else _squeeze(token.content))
        blocks.append((depth, token.type, content))
        if token.nesting == 1:
            depth += 1
    return blocks


def _describe_ast_difference(before_blocks, after_blocks):
    """最初に食い違ったブロックを、人が読める 1 行にして返す。"""
    for i, (b, a) in enumerate(zip(before_blocks, after_blocks)):
        if b != a:
            return (f"{i + 1} 番目のブロックが "
                    f"{b[1]} (深さ {b[0]}) から {a[1]} (深さ {a[0]}) に変わった"
                    if (b[0], b[1]) != (a[0], a[1])
                    else f"{i + 1} 番目のブロック ({b[1]}) の中身が変わった")
    return (f"ブロックの数が {len(before_blocks)} から "
            f"{len(after_blocks)} に変わった")


def ast_problems(before, after):
    """AST 比較 (検証の第5条件) の結果を返す。パーサが無ければ空のリスト。"""
    before_blocks = ast_blocks(before)
    if before_blocks is None:
        return []
    after_blocks = ast_blocks(after)
    if before_blocks == after_blocks:
        return []
    return ["独立したパーサで見たブロックの列が変わった: "
            + _describe_ast_difference(before_blocks, after_blocks)]


def verify(before, after):
    """変換の前後を比べ、書き戻して安全でない理由を並べて返す。空のリストなら安全である。

    条件とその根拠は notes/document/008-no-hard-wrap-japanese-design.md の `## 検証` が正典。
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
    b, a = _marker_lines(before), _marker_lines(after)
    if b != a:
        problems.append(
            "マーカーだけの行 (英数字も CJK も含まない非空行) の並びが変わった: "
            f"{len(b)} 行から {len(a)} 行")
    problems.extend(ast_problems(before, after))
    return problems

# 除外するディレクトリ**名**。パスの接頭辞ではなく、対象ディレクトリからの相対パスの要素名と突き合わせる。
# measure_wraps.py と同じ一覧にしておく (test_unwrap が一致を固定している)。
# 要素名で判定する根拠と、両者の一覧を揃える根拠は notes/document/008-no-hard-wrap-japanese-design.md の `## 適用の範囲と順序` が正典。
SKIP_PARTS = frozenset({"node_modules", ".git", "worktrees", ".worktrees",
                        ".superpowers",
                        "fixtures", "dist", "build", "target", ".next",
                        "coverage"})

def is_skipped(path, base):
    """path (base の下のファイル) が除外対象のディレクトリの中にあるか。"""
    return not SKIP_PARTS.isdisjoint(path.relative_to(base).parts[:-1])

def unwrap_file(path, apply=False, joins=None):
    """1ファイルを変換する。戻り値は ("changed"|"unchanged"|"failed", 詳細)。

    `joins` にリストを渡すと、未知の形の結合点の鍵をそこへ足す。**書き戻したかどうかに関わらず足す** —— dry-run でこそ見たい情報だからである。検証に落ちたファイルの分は足さない (そのファイルは変換されないため)。
    """
    try:
        before = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        # 他の repo には壊れたファイルや読めないファイルがある。1件で全体を落とすと残りが処理されないので、そのファイルを失敗として報告して続ける。
        return "failed", f"読めない ({e.__class__.__name__})"
    found = []
    after = unwrap_text(before, found)
    if before == after:
        return "unchanged", ""
    problems = verify(before, after)
    if problems:
        return "failed", "; ".join(problems)
    if joins is not None:
        joins.extend(found)
    if apply:
        try:
            path.write_text(after, encoding="utf-8")
        except OSError as e:
            return "failed", f"書けない ({e.__class__.__name__})"
    return "changed", ""

# 未知の結合点の一覧に出す行数の上限。これを超えた分は件数だけを出す。
ODD_JOINS_SHOWN = 20


def report_odd_joins(counts, examples, out=print):
    """未知の結合点の一覧を出す。`counts` は 鍵 -> 件数、`examples` は 鍵 -> 見本のパス。

    まとめ方・並べ方・出す数とその根拠は notes/document/008-no-hard-wrap-japanese-design.md の `### 検証を通ったあとに人間へ見せるもの` が正典。
    """
    if not counts:
        return
    out("")
    out(f"未知の結合点 (左右のどちらかが日本語でも英数字でもない): "
        f"{sum(counts.values())} 件 / {len(counts)} 形")
    out("**検証は通っている。** 見たことのない形が出ていないかを目で確かめること。")
    for key, n in counts.most_common(ODD_JOINS_SHOWN):
        out(f"  {n:5d}  {key!r} との結合   例: {examples[key]}")
    rest = len(counts) - ODD_JOINS_SHOWN
    if rest > 0:
        out(f"  (ほかに {rest} 形)")


def main(argv):
    import collections
    import pathlib
    apply = "--apply" in argv
    roots = [a for a in argv if not a.startswith("--")]
    if not roots:
        # 渡し忘れたときに「変換した: 0 / 変更なし: 0 / 失敗: 0」を出して exit 0 すると、何もしていないのに成功に見える。
        print("使い方: python3 unwrap.py <対象ディレクトリ> [...] [--apply]")
        return 2
    bases = [pathlib.Path(root) for root in roots]
    missing = [str(b) for b in bases if not b.is_dir()]
    if missing:
        # 打ち間違いが最も起きやすい形である。黙って 0 件を報告して exit 0 すると、何も走っていないのに成功に見える。
        for name in missing:
            print(f"対象がディレクトリとして存在しない: {name}")
        return 2
    changed = unchanged = failed = 0
    odd_counts = collections.Counter()
    odd_examples = {}
    for base in bases:
        for path in sorted(base.rglob("*.md")):
            # 除外は対象ディレクトリからの相対パスの**要素名**で判定する。
            # 対象が worktree の中にあっても中身は除外されず、対象の内側に worktrees/ があればその中は除外される。
            if is_skipped(path, base):
                continue
            joins = []
            state, detail = unwrap_file(path, apply, joins)
            for key in joins:
                odd_counts[key] += 1
                odd_examples.setdefault(key, path)
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
    if not HAS_AST_PARSER:
        # 黙って飛ばさない。検証が 1 つ欠けたまま「成功」に見えるのが、この道具で最も危ない形である。
        print(f"警告: {AST_MISSING_NOTE}")
    report_odd_joins(odd_counts, odd_examples)
    return 1 if failed else 0

if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv[1:]))
