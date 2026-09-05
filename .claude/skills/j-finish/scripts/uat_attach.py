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
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

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
