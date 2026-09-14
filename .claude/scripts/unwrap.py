#!/usr/bin/env python3
"""日本語の md 本文のハード折り返しを結合する。

段落の途中で改行されている行を結合し、frontmatter・コードフェンス・HTML ブロック・コンテナディレクティブ (`:::`) の行・表・見出し・引用・意図的なハードブレイク・日本語を含まない段落は触らない。
**文末 (`。` `！` `？`) での改行は折り返しではないので結合しない。**

**規約と変換規則の正典は notes/document/008-no-hard-wrap-japanese-design.md**（dotfiles）である。結合点の空白・触らないものの一覧・検証の4条件は、すべてそこで決めている。規則を変えるときは設計を先に直す。

使い方:

    # dry-run。対象ディレクトリを1つ以上渡す。書き換えは一切しない
    python3 unwrap.py <対象ディレクトリ> [<対象ディレクトリ> ...]

    # 適用。dry-run で FAILED が 0 件であることを確かめてから
    python3 unwrap.py <対象ディレクトリ> [...] --apply

対象ディレクトリの下の *.md を再帰的に見る（例: `<repo>/notes <repo>/tasks <repo>/.claude`）。除外（node_modules・.git・worktrees 等）は**対象ディレクトリからの相対パスの要素名**で判定する。だから worktree の中を対象にしても全件が除外されることはなく、対象の内側に worktrees/ があればその中は除外される。
対象がディレクトリとして存在しなければ、その旨を出して exit 2 する。

**他の repo に当てる前に必ずテストを走らせる**（`cd .claude/scripts && python3 -m unittest test_unwrap -v`）。道具が壊れていないことを先に確かめてから実データに当てる。適用したあとは measure_wraps.py で折り返しの残量を測り、直り切らなかった分を数で見る。
"""
import re

# フェンスのマーカー行。開くか閉じるかに関わらず、マーカーだけを見た形。
# 1 群が行頭のインデント、2 群がマーカー (``` 以上または ~~~ 以上)、3 群がそのあとの情報文字列。
FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")

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
    return marker[0], len(marker), len(m.group(1))

def fence_closes(line, char, length, indent):
    """行が (char, length, indent) で開いたフェンスを閉じるか。

    markdown でフェンスを閉じられるのは、**開いたときと同じ文字で、同じ長さ以上**のマーカーだけである。それより短いマーカーや別の文字のマーカーは中身 (コンテンツ) であって、閉じない。また**閉じマーカーの行には情報文字列を書けない**ので、マーカーのあとに空白以外が続く行も閉じない。

    **閉じマーカーのインデントは開きマーカーから 3 桁までである。** それより深くインデントされた行は中身であって、閉じない。絶対の桁数で「3 桁まで」と書いてはならない。リスト項目の中のフェンスは 4 桁以上インデントされて開くことがあり、その閉じマーカーも同じ深さにあるからである。見るのは **開きからの相対**である。

    以前はマーカーの文字と長さを見ず、`^\\s*(```|~~~)` に当たるどの行でも開閉を反転させていた。そのため 4 個のバッククォートで開いたフェンスの中に 3 個の行があると、そこで反転して**以降のフェンスの内と外が入れ替わり**、本来コードである ```` ```ts ```` ブロックが本文として結合された。**verify の 4 条件はどれもこの壊れ方を検出できない。** 文字は欠けず、構造の数も段落の頭のインデントも変わらず、マーカーだけの行 (第4条件) もフェンスのマーカーが全部残るので変わらないからである。
    """
    m = FENCE.match(line)
    if not m:
        return False
    marker = m.group(2)
    return (marker[0] == char and len(marker) >= length
            and not m.group(3).strip()
            and len(m.group(1)) <= indent + 3)

# HTML ブロックの開始行。扱うのは 3 種類である: CommonMark の 1 種目 (`<pre>` `<script>` `<style>` `<textarea>`)、2 種目の HTML コメント (`<!--`)、そして行頭が HTML のタグに見える行 (6 種目・7 種目を広く取ったもの)。
# markdown では、これらの行から始まる領域は **HTML ブロック**であり、中身はそのまま出力される (markdown として解釈されない)。結合すると、閉じの `-->` が箇条書きの項目にくっついたり、`<div>` の構造が壊れたりする。
# **判定を広く取っている代償は残量測定に出る。** 本文が HTML ブロックと誤認されると、そこに残った折り返しは変換されないうえ、measure_wraps.py も同じ判定で数えないので**残ったことが数にも出ない**。引用 (`>`) と同じ種類の盲点である (設計の「直り切らないものを見えるようにする」)。
# インデントを 3 桁までに限るのは CommonMark の規則に合わせたものである。4 桁以上はインデントされたコードブロックであり、そちらは INDENTED_CODE が別に触らない側へ倒している。
HTML_COMMENT_OPEN = re.compile(r"^ {0,3}<!--")
# **どこまでを「タグに見える」とするか。** 行頭 (インデント 3 桁まで) が `<` または `</` で始まり、続いて ASCII の英字・英数字とハイフンのタグ名があり、そのあとが空白・`>`・`/>`・行末のいずれかである行をタグと見なす。
# CommonMark の 6 種目 (既知のブロック要素名の一覧) より**広く**、7 種目 (行にタグだけがある形) より**緩い**。広い側に倒しているのは、結合しそこねても折り返しが残るだけだが、HTML を壊すのは戻せないためである。
# 逆に `<https://example.com>` (自動リンク) や `<型引数>` のような行はタグ名の形に当たらないので、ここには入らない。
HTML_TAG_OPEN = re.compile(r"^ {0,3}</?[A-Za-z][A-Za-z0-9-]*(\s|/?>|$)")
# **CommonMark の HTML ブロックの 1 種目**。`<pre>` `<script>` `<style>` `<textarea>` で始まるブロックだけは、**空行では終わらず閉じタグまで**が範囲である。他の種別と同じ「空行まで」で扱うと、空行をまたいだ続きが本文として結合される。`<pre>` は空白が意味を持つので、結合すれば描画が変わる。
# これはフェンスの欠陥 (開閉の範囲の取り違え) と**完全に同じ種類**なので、実データに 0 件でも塞ぐ。しかも壊れ方は verify の 4 条件をすべてすり抜ける —— 文字は欠けず、構造の数も段落の頭のインデントも変わらず、マーカーの行も全部残るからである。
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
# **フェンスのように開きと閉じを対応させることはしない。** 中身は普通の markdown の本文 (見出し・段落・フェンスを混在できる) であって、結合してよいからである。フェンスと同じ「開いたら閉じるまで中身」にすると、カラムの中の折り返しが一切直らなくなる。必要なのは「マーカーの行を本文に巻き込まない」ことだけであり、それはマーカー行を単独の触らない行にすれば足りる。開閉の対応を持たない分、閉じ忘れや入れ子の深さを取り違えて以降のファイル全体の内外が入れ替わる壊れ方も起きない。
# 対応させないので、開きの情報文字列 (`:::column`) と閉じ (`:::`) を区別する必要もない。どちらも本文でないことに変わりはない。
# 実データ (joifup の notes/tasks) では `::::columns` / `:::column` / `:::` / `::::` の 4 形がある。現時点で壊れていないのは、たまたま `:::column` の直後が見出しで段落が切れているからにすぎず、日本語の段落の直後に閉じの `:::` が来た瞬間に本文として結合される。
DIRECTIVE = re.compile(r"^ {0,3}:{3,}")
LIST = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+")
INDENTED_CODE = re.compile(r"^( {4,}|\t)")
CJK = re.compile(r"[぀-ヿ一-鿿]")
# 結合点の判定に使う「日本語」。かな・漢字に加えて、全角の句読点・括弧・記号 (。、「」（） 等) を含む。CJK より広いのは、結合点には本文の文字だけでなく約物も来るためである。
JA = re.compile(r"[　-〿぀-ヿ㐀-䶿一-鿿＀-￯]")
HARD_BREAK = re.compile(r"(  |\\)$")
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

def join_parts(parts):
    """行の並びを1行に結合する。

    結合点の前後がともに日本語 (かな・漢字・全角の句読点や記号) なら空白なしで繋ぎ、それ以外は半角空白1つを入れる (設計の「結合点の空白」)。
    ただし全角の約物には例外を置く。左が全角の句読点 (。、) なら右が何であっても、右が全角の開き括弧 (（「『【〔) なら左が何であっても、空白を入れない。日本語では句読点の直後にも開き括弧の直前にも空白を置かないためである。例外は必ず両側に置く。片側だけにすると鏡の側が開く。前者が無いと `解決される。` + `` `brew upgrade tmux` `` に空白が入り、後者が無いと `` `.claude` `` + `（対象は…` に空白が入る。

    判定は「片側が ASCII 英数か」ではなく「両側が日本語か」で行う。前者だと、結合点に記号どうしが来たときに空白が落ちるためである。たとえば `使う:` と `` `brainstorming` `` は : も ` も ASCII 英数でないので空白なしで繋がれ、原文にあった区切りが消えてしまう。空白が要らないのは日本語どうしの間だけなのだから、判定もそのまま日本語で書く。
    """
    out = parts[0]
    for part in parts[1:]:
        left = out[-1:] if out else ""
        right = part[:1]
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

def _fold(raw_lines):
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
        text = join_parts([line.strip() for line in group])
        if i:
            # 2つ目以降の単位は原文のインデントを保つ。落とすとリストの中の継続行が桁 0 に出てリストがそこで切れる。1つ目は呼び出し側が prefix (リストのマーカーまたは行頭のインデント) を戻す。
            text = INDENT.match(group[0]).group(0) + text
        folded.append(text)
    return folded

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

def verify(before, after):
    """変換の前後を比べ、書き戻して安全でない理由を並べて返す。

    空のリストなら安全である。設計の「検証」の4条件を実装している: 段落テキストが文字単位で一致すること、構造の数が変わらないこと、段落の頭のインデントの並びが変わらないこと、マーカーだけの行が同じ内容・同じ数・同じ順で独立した行として残ること。

    3つ目は、インデントを落としてリストを切る壊し方が1つ目も2つ目も素通りするから要る。リスト項目の数は変わらず、段落テキストの比較は空白を無視するので、どちらも気づかない。

    **4つ目は「ブロックの境界を本文に巻き込んだ」ことを見る。** 1〜3 は「文字列としての md」の性質しか見ておらず、**ブロックの境界がどこにあるか**を一切参照しない。ところが、この道具がこれまで出した欠陥 (フェンスの入れ子・HTML ブロック) はどちらもまさにその情報を壊すものであり、3条件をすべてすり抜けた。4つ目は `unwrap` のブロックモデルに一切依存しない純粋に語彙的な不変量なので、モデルの側の取りこぼしに巻き込まれない。英数字も CJK も含まない非空行 (`-->`・`:::`・`$$`・Setext の `===`・TOML の `+++` など) は、本文に巻き込まれた瞬間に独立した行でなくなるので、数と並びが変わる。今回の HTML コメントの欠陥は、修正前の版に対してこの条件が検出できる。誤検出は `~/Joifup` の md 1,691 ファイル・変換対象 690 ファイルに対して 0 件だった。

    **限界も明記しておく。** フェンスの欠陥 (`` ``` `` の入れ子) と HTML ブロックの 1 種目 (`<pre>`) の欠陥は、**この条件でも捕まらない**。どちらもマーカーの行そのものは独立した行として全部残り、壊れるのはマーカーに挟まれた中身のほうだからである。4つ目は 3 条件の穴を**部分的に**塞ぐものであって、ブロックの認識が正しいことの代わりにはならない。
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
    return problems

# 除外するディレクトリ**名**。パスの接頭辞ではなく、対象ディレクトリからの相対パスの要素名と突き合わせる。接頭辞で持つと、対象の渡し方によって効いたり効かなかったりする。たとえば `"/.claude/worktrees/"` を接頭辞で持ったまま対象を `<repo>/.claude` にすると、相対パスが `/worktrees/...` になって一致せず、**進行中の別ブランチの worktree を書き換える**。要素名で持てば、対象をどこに置いても、また対象の内側でも外側でも同じように効く。
# measure_wraps.py と同じ一覧にしておく (test_unwrap が一致を固定している)。
# 片方だけが数えると、変換しないと決めた場所の折り返しが残量に出て、直し切れない数がいつまでも残る。
SKIP_PARTS = frozenset({"node_modules", ".git", "worktrees", ".worktrees",
                        ".superpowers",
                        "fixtures", "dist", "build", "target", ".next",
                        "coverage"})

def is_skipped(path, base):
    """path (base の下のファイル) が除外対象のディレクトリの中にあるか。"""
    return not SKIP_PARTS.isdisjoint(path.relative_to(base).parts[:-1])

def unwrap_file(path, apply=False):
    """1ファイルを変換する。戻り値は ("changed"|"unchanged"|"failed", 詳細)。"""
    try:
        before = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as e:
        # 他の repo には壊れたファイルや読めないファイルがある。1件で全体を落とすと残りが処理されないので、そのファイルを失敗として報告して続ける。
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
    for base in bases:
        for path in sorted(base.rglob("*.md")):
            # 除外は対象ディレクトリからの相対パスの**要素名**で判定する。
            # 対象が worktree の中にあっても中身は除外されず、対象の内側に worktrees/ があればその中は除外される。
            if is_skipped(path, base):
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
