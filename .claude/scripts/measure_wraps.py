#!/usr/bin/env python3
"""md のハード折り返しの量を測る。unwrap.py の適用前後の比較に使う。

「折り返された行」= 段落の途中で改行されている行。判定は「次の行が同じ
段落の続き（空行でなく、見出し・リスト・表・フェンスの開始でもない）」。
frontmatter とコードフェンスの中は除外する。引用（`>`）の中も数えないので、
引用に残った折り返しはこの数に出ない。

使い方:

    python3 measure_wraps.py <対象ディレクトリ> [<対象ディレクトリ> ...]

対象ごとに「折り返し行 / 段落行 = 割合（うち日本語 N）」を1行で出す。
unwrap.py が「変更なし」と答えることと、そのファイルに折り返しが残って
いないことは別である。**適用のあとはこれで残量を測って報告する。**

折り返しの定義と、直り切らないもの（4スペース以上のインデント行・引用の
中）の扱いの正典は notes/document/008-no-hard-wrap-japanese-design.md。
"""
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^\s*(```|~~~)")
BLOCK_START = re.compile(r"^\s*(#{1,6}\s|[-*+]\s|\d+[.)]\s|>|\||---\s*$|===)")
# unwrap.py と同じ一覧にしておく。片方だけが数えると、変換しないと決めた
# ディレクトリの折り返しが残量に出て、直し切れない数がいつまでも残る。
SKIP = ("/node_modules/", "/.git/", "/.claude/worktrees/", "/.superpowers/",
        "/fixtures/", "/dist/", "/build/", "/target/", "/.next/",
        "/coverage/")
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
    in_fence = False
    body = cont = cont_ja = 0
    for j in range(i, len(lines)):
        line = lines[j]
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence or not line.strip() or BLOCK_START.match(line):
            continue
        body += 1
        nxt = lines[j + 1] if j + 1 < len(lines) else ""
        if nxt.strip() and not FENCE.match(nxt) and not BLOCK_START.match(nxt):
            cont += 1
            if CJK.search(line):
                cont_ja += 1
    return body, cont, cont_ja


for root in sys.argv[1:]:
    r = Path(root)
    tb = tc = tj = files = 0
    for p in r.rglob("*.md"):
        # root より内側だけを見て判定する (root 自身が .claude/worktrees/ の
        # 下にあるときに全件が除外されるのを避けるため)
        if any(s in "/" + str(p.relative_to(r)) for s in SKIP):
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
