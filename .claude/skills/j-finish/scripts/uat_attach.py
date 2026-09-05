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
