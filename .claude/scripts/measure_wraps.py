#!/usr/bin/env python3
"""md のハード折り返しの量を測る。unwrap.py の適用前後の比較に使う。

「折り返された行」= 段落の途中で改行されている行。判定は「次の行が同じ
段落の続き（空行でなく、見出し・リスト・表・フェンスの開始でもない）」。
**文末（`。` `！` `？`）で終わる行は折り返しとして数えない。** 文末での改行
は桁数の折り返しではなく「1文1行」という書き方であり、unwrap.py もそこでは
結合しない。数え方を合わせないと、直さないと決めたものが残量に出続ける。
frontmatter とコードフェンスの中は除外する。引用（`>`）の中も数えないので、
引用に残った折り返しはこの数に出ない。

使い方:

    python3 measure_wraps.py <対象ディレクトリ> [<対象ディレクトリ> ...]

対象を渡し忘れたとき、および対象がディレクトリとして存在しないときは、その旨
を出して exit 2 する（unwrap.py と同じ扱い）。

対象ごとに「折り返し行 / 段落行 = 割合（うち日本語 N）」を1行で出す。
unwrap.py が「変更なし」と答えることと、そのファイルに折り返しが残って
いないことは別である。**適用のあとはこれで残量を測って報告する。**

折り返しの定義と、直り切らないもの（4スペース以上のインデント行・引用の
中）の扱いの正典は notes/document/008-no-hard-wrap-japanese-design.md。
"""
import re
import sys
from pathlib import Path

# フェンスのマーカー行。unwrap.py と同じ定義にしておく (一致は
# test_unwrap の test_the_fence_handling_matches_unwrap が固定している)。
# 片方だけがフェンスの内と外を取り違えると、変換しないと決めた場所の
# 折り返しが残量に出続ける。
# markdown でフェンスを閉じられるのは**開いたときと同じ文字で、同じ長さ
# 以上**のマーカーだけであり、**閉じマーカーの行には情報文字列を書けず、
# インデントは開きマーカーから 3 桁までである**。また**バッククォートの
# フェンスの情報文字列にはバッククォートを書けない** (含む行は段落である)。
FENCE = re.compile(r"^(\s*)(`{3,}|~{3,})(.*)$")


def fence_open(line):
    """行がフェンスを開くなら (マーカーの文字, 長さ, インデント幅) を返す。"""
    m = FENCE.match(line)
    if not m:
        return None
    marker = m.group(2)
    if marker[0] == "`" and "`" in m.group(3):
        return None
    return marker[0], len(marker), len(m.group(1))


def fence_closes(line, char, length, indent):
    """行が (char, length, indent) で開いたフェンスを閉じるか。

    インデントは**開きからの相対**で見る。絶対の桁数で見ると、リスト項目の
    中で 4 桁以上インデントされて開いたフェンスが閉じられなくなる。
    """
    m = FENCE.match(line)
    if not m:
        return False
    marker = m.group(2)
    return (marker[0] == char and len(marker) >= length
            and not m.group(3).strip()
            and len(m.group(1)) <= indent + 3)

BLOCK_START = re.compile(r"^\s*(#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\||---\s*$|===)")
# 文末。unwrap.py と同じ定義にしておく (一致は test_unwrap が固定している)。
# 片方だけが文末を折り返しと見なすと、結合しないと決めた改行が残量に出て、
# 直し切れない数がいつまでも残る。
SENTENCE_END = re.compile("[。！？][*_`）」』】〕)\"']*$")
# 除外するディレクトリ**名**。パスの接頭辞ではなく、対象ディレクトリからの
# 相対パスの要素名と突き合わせる (理由は unwrap.py の SKIP_PARTS を見よ)。
# unwrap.py と同じ一覧にしておく。片方だけが数えると、変換しないと決めた
# ディレクトリの折り返しが残量に出て、直し切れない数がいつまでも残る。
# 一致は test_unwrap の test_the_skip_list_matches_unwrap が固定している。
SKIP_PARTS = frozenset({"node_modules", ".git", "worktrees", ".worktrees",
                        ".superpowers",
                        "fixtures", "dist", "build", "target", ".next",
                        "coverage"})


def is_skipped(path, base):
    """path (base の下のファイル) が除外対象のディレクトリの中にあるか。"""
    return not SKIP_PARTS.isdisjoint(path.relative_to(base).parts[:-1])
CJK = re.compile(r"[぀-ヿ一-鿿]")


def classify(path):
    try:
        lines = path.read_text(encoding="utf-8").split("\n")
    except (UnicodeDecodeError, OSError):
        return 0, 0, 0
    i = 0
    if lines and lines[0].strip() == "---":
        i = 1
        while i < len(lines) and lines[i].strip() != "---":
            i += 1
        i += 1
    fence = None
    body = cont = cont_ja = 0
    for j in range(i, len(lines)):
        line = lines[j]
        if fence is not None:
            # フェンスの中。閉じられるのは開いたときと同じ文字で同じ長さ
            # 以上のマーカーだけで、それ以外の行は中身である。閉じられない
            # ままファイルが終われば最後まで中身として扱う。
            if fence_closes(line, *fence):
                fence = None
            continue
        opened = fence_open(line)
        if opened:
            fence = opened
            continue
        if not line.strip() or BLOCK_START.match(line):
            continue
        body += 1
        nxt = lines[j + 1] if j + 1 < len(lines) else ""
        if SENTENCE_END.search(line.rstrip()):
            # 文末で終わる行は、次が段落の続きでも折り返しではない。
            continue
        if nxt.strip() and not FENCE.match(nxt) and not BLOCK_START.match(nxt):
            cont += 1
            if CJK.search(line):
                cont_ja += 1
    return body, cont, cont_ja


def main(argv):
    # unwrap.py と同じ扱いにする。渡し忘れや打ち間違いで黙って 0 件を出して
    # exit 0 すると、何も測っていないのに「残量なし」に見える。
    roots = [a for a in argv if not a.startswith("--")]
    if not roots:
        print("使い方: python3 measure_wraps.py <対象ディレクトリ> [...]")
        return 2
    bases = [Path(root) for root in roots]
    missing = [str(b) for b in bases if not b.is_dir()]
    if missing:
        for name in missing:
            print(f"対象がディレクトリとして存在しない: {name}")
        return 2
    for r in bases:
        tb = tc = tj = files = 0
        for p in r.rglob("*.md"):
            if is_skipped(p, r):
                continue
            b, c, j = classify(p)
            if b:
                files += 1
            tb += b
            tc += c
            tj += j
        if tb:
            print(f"{r.name:20s} {files:5d} files  "
                  f"{tc:6d}/{tb:6d} = {tc / tb:3.0%} 折り返し  "
                  f"(うち日本語 {tj})")
        else:
            print(f"{r.name:20s} {files:5d} files  対象なし")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
