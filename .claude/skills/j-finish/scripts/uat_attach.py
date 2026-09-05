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
# 証跡ファイル名に許さない文字。詳細は validate_shots() の中のコメント。
_UNSAFE_FILE = re.compile(r"[\x00#/\\]")


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


def _encodable(text):
    """utf-8 に encode できるか。単独サロゲートを入口で弾くために使う。"""
    try:
        str(text).encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


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
    パスの妥当性は validate_shots() が先に見ている前提。
    """
    args = []
    for s in shots:
        path = f"{evidence_dir.rstrip('/')}/{s.get('file')}"
        name = str(s.get("name") or "")
        args += ["--attach", f"{path}#{name}" if name else path]
    return args


def validate_shots(evidence_dir, shots, realpath=os.path.realpath,
                   islink=os.path.islink):
    """証跡行の `file` が evidence_dir の中に収まっていることを確かめる。

    ここは **GitHub へアップロードする前の最後の関門**である。添付は一度
    上げると取り消せない (コメントを消してもアセットは残る) ので、`file` に
    `../../.ssh/id_rsa` のような値が入った results.jsonl や、証跡 dir に
    紛れ込んだ symlink を、そのまま `gh --attach` に渡してはならない。

    joifup 側の slug() は ASCII の basename しか作らないが、その不変条件を
    守っているのは別リポジトリの生成側であって、こちらではない。壊れた
    results.jsonl・手で編集された行・spec が書いた任意の file 値がここに
    届きうる以上、渡す側で確かめる。

    違反は AttachError で止める — 黙って読み飛ばすと、証跡が欠けたまま
    PASS の PR が出る。
    """
    # evidence_dir 自身も `<dir>/<file>#<alt>` の一部として gh に渡るので、
    # `#` や NUL が入っていれば gh が切り出すパスは検査した物とずれる。
    if "#" in evidence_dir or "\x00" in evidence_dir or not _encodable(evidence_dir):
        raise AttachError(
            f"証跡 dir に `#`・NUL・utf-8 にできない文字は使えません"
            f" ({evidence_dir!r})")
    root = realpath(evidence_dir)
    for s in shots:
        file = s.get("file")
        if not file or not str(file).strip():
            raise AttachError(
                f"証跡行に file がありません: {s.get('name', '(名前なし)')}")
        file = str(file)
        # `file` は生成側 (joifup の slug()) が作る ASCII の basename しか
        # 正しくない。素の basename だけを通すことで、絶対パス・`..`・
        # サブディレクトリ・NUL をまとめて閉じる。
        #   - `#` は gh の `<file>#<alt>` 区切り。含まれていると gh が
        #     解釈するパスは検査した文字列の *前半* になり、検査した物と
        #     渡した物がずれる。
        #   - NUL は subprocess が ValueError で落ちる。OSError ではない
        #     ので _run の except を素通りし、push/PR 済みの復旧案内が出ない。
        if _UNSAFE_FILE.search(file) or file in (".", ".."):
            raise AttachError(
                f"証跡の file が basename ではありません ({file!r})。"
                " 区切り文字・`#`・NUL を含む名前は添付しません")
        # 単独サロゲートは json.loads を通るが utf-8 に encode できない。
        # 素通しすると dry-run の print と temp への書き出しがそれぞれ別の
        # 場所で UnicodeEncodeError を投げる。値の入口で 1 度だけ弾く。
        name = str(s.get("name") or "")
        for label, value in (("file", file), ("name", name)):
            if not _encodable(value):
                raise AttachError(
                    f"証跡行の {label} を utf-8 にできません ({value!r})")
        # `name` は alt text として `<path>#<name>` の右側に入る。`#` を
        # 含むと gh がどちらの `#` で切るかに依存するので、こちらも拒否する。
        if "#" in name:
            raise AttachError(
                f"証跡の name に `#` は使えません ({name!r})。"
                " gh の `<file>#<alt text>` 区切りと衝突します")
        path = f"{evidence_dir.rstrip('/')}/{file}"
        if islink(path):
            raise AttachError(
                f"証跡が symlink です ({file})。リンク先を辿って想定外の"
                " ファイルを上げないため拒否します")
        resolved = realpath(path)
        if resolved != root and not resolved.startswith(root + os.sep):
            raise AttachError(
                f"証跡 {file} が証跡 dir ({evidence_dir}) の外を指しています"
                f" ({resolved})。添付は取り消せないため拒否します")


def body_with_evidence_link(body, url):
    """PR 本文の `## UAT 証跡` 節の末尾に証跡コメントへのリンクを足す。

    節が無ければ None を返す (本文の別の場所に押し込むと、読み手が探す場所と
    ずれる)。GitHub のアンカーはコメント単位なので、証跡表の行ごとにリンクを
    張ることはできない — リンクは 1 本 (設計 D3)。

    既に `証跡コメント:` の行があれば **置き換える**。gh pr edit が失敗した
    後の復旧手順はこのスクリプトの再実行なので、追記にすると本文にリンクが
    2 本並ぶ。
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
    section = [ln for ln in lines[start:end]
               if not ln.strip().startswith("証跡コメント:")]
    tail = len(section)
    while tail > 1 and not section[tail - 1].strip():
        tail -= 1
    return "\n".join(lines[:start] + section[:tail]
                     + ["", f"証跡コメント: {url}", ""] + lines[end:])


class AttachError(Exception):
    """添付が成立しなかった。握り潰さず呼び出し側を止めるための例外。

    `comment_url` が入っているものは「証跡コメントは投稿済みだが、その後で
    失敗した」という意味。添付は取り消せないので、呼び出し側は復旧案内で
    「もう一度添付しろ」と言ってはならない (二重にアップロードされる)。
    """

    def __init__(self, message, comment_url=None):
        super().__init__(message)
        self.comment_url = comment_url


def _run(cmd):
    """`gh` を実行し stdout を返す。非 0 は AttachError にする。

    gh は部分失敗のとき「成功したぶんでコメントを作り、非 0 で終了する」ので、
    終了コードを握り潰すと証跡が欠けたまま PASS に見える (設計のエラー
    ハンドリング節)。stderr をそのまま載せて止める。

    起動そのものの失敗も AttachError にする — gh が入っていない (OSError) と、
    引数に NUL が混じっている (ValueError) の 2 つ。素のまま抜けると呼び出し側
    (j_finish) の except AttachError を素通りして traceback で落ち、push と
    PR 作成が済んだ状態の復旧案内が出ない。
    """
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
    except (OSError, ValueError) as exc:
        raise AttachError(f"{cmd[0]} を実行できません: {exc}") from exc
    if res.returncode != 0:
        raise AttachError(
            f"{' '.join(cmd)} が exit {res.returncode} で失敗\n{res.stderr.strip()}")
    return res.stdout.strip()


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _write_temp(text):
    """本文を temp file に書き、そのパスを返す。書けなければ消してから上げる。

    `with tempfile.NamedTemporaryFile(delete=False)` の中で書くと、write が
    落ちたときブロックを抜けた先の try/finally に届かず temp が残る。加えて
    UnicodeEncodeError (results.jsonl に単独サロゲートがあると起きる) は
    ValueError であって AttachError ではないので、そのまま抜けると呼び出し側
    (j_finish) の except AttachError を素通りし、push/PR 済みの復旧案内が
    出ないまま traceback で落ちる。両方ここで閉じる。

    temp の **生成** も try の中に入れる。TMPDIR が read-only なら生成の時点で
    PermissionError が出るが、これも AttachError でなければ同じ穴になる。
    """
    fh = None
    path = None
    try:
        fh = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                         encoding="utf-8")
        path = fh.name
        fh.write(text)
        # close() も try の中。TextIOWrapper の write はバッファに積むだけで、
        # 実際の write(2) は flush = close のときに走る。ENOSPC のような
        # 一番ありそうな失敗はここでしか出ない。
        fh.close()
    except (ValueError, OSError) as exc:
        if fh is not None:
            try:
                fh.close()
            except OSError:
                pass
        if path is not None:
            try:
                os.unlink(path)
            except OSError:
                # 消せなくても、元の失敗のほうを伝えるのが先。
                pass
        raise AttachError(f"証跡コメント本文を書き出せません: {exc}") from exc
    return path


def _unlink_quietly(path):
    """finally からの後始末。unlink の失敗で伝播中の例外を上書きしない。"""
    try:
        os.unlink(path)
    except OSError:
        pass


def attach_evidence(pr, evidence_dir, task, dry_run=False, runner=None, reader=None,
                    required=False):
    """UAT 証跡を PR にコメントとして添付し、そのコメント URL を返す。

    証跡が 1 つも無ければ何もせず None を返す — UI を変えない PR は証跡が
    無いのが正常だから。runner / reader は差し替え可能 (テスト用)。

    `required=True` のときは、証跡が無いこと自体を AttachError にする。
    呼び出し側が証跡 dir を **明示的に指定した** 場合 (j_finish の
    --uat-evidence-dir) は「証跡がある」と主張しているので、stale な id や
    typo で 0 件だったときに黙って進むと、PASS と書かれた本文と添付ゼロの
    PR のまま status が In review に飛び Discord まで鳴る。
    """
    run = runner or _run
    read = reader or _read

    version = parse_gh_version(run(["gh", "--version"]))
    if version is None or version < MIN_GH_VERSION:
        floor = ".".join(str(n) for n in MIN_GH_VERSION)
        raise AttachError(
            f"gh {floor} 以上が必要です (--attach の初出)。検出: {version}。"
            " `brew upgrade gh` などで更新してください")

    results_path = os.path.join(evidence_dir, "results.jsonl")
    try:
        text = read(results_path)
    except FileNotFoundError:
        if required:
            raise AttachError(
                f"{results_path} がありません。証跡 dir を明示的に指定して"
                " いるので、証跡ゼロのまま先へ進みません。`pnpm uat --task"
                " <id>` を回したか、id が合っているか確かめてください")
        print(f"uat-attach: {evidence_dir}/results.jsonl が無いので添付をスキップ",
              file=sys.stderr)
        return None
    except OSError as exc:
        # ファイルが無い (正常なスキップ) 以外の読み取りエラーは握り潰さない。
        # PermissionError や IsADirectoryError まで無いことにすると、
        # 証跡が実際にはあるのに「無い扱い」で PASS を報告してしまう。
        raise AttachError(f"{results_path} の読み取りに失敗: {exc}") from exc

    rows, skipped = parse_results(text)
    if skipped:
        print(f"uat-attach: results.jsonl の壊れた行を {skipped} 行スキップしました"
              " — 証跡が不完全な可能性があります", file=sys.stderr)
    shots = shot_rows(rows)
    if not shots:
        if required:
            raise AttachError(
                f"{results_path} に証跡行 (kind=\"shot\") が 1 件もありません。"
                " 証跡 dir を明示的に指定しているので、証跡ゼロのまま先へ"
                " 進みません")
        print("uat-attach: 証跡が 0 件のため添付しません", file=sys.stderr)
        return None
    if len(shots) > MAX_ATTACH:
        raise AttachError(
            f"証跡が {len(shots)} 件あり gh の上限 {MAX_ATTACH} を超えています。"
            " 分割ではなく shot() を減らしてください")
    validate_shots(evidence_dir, shots)

    body = render_comment(task, shots)
    args = attach_args(evidence_dir, shots)
    if dry_run:
        print(f"[dry-run] gh pr comment {pr} --body-file <tmp> {' '.join(args)}")
        return None

    pr_body = run(["gh", "pr", "view", pr, "--json", "body", "--jq", ".body"])

    body_file = _write_temp(body)
    try:
        url = run(["gh", "pr", "comment", pr, "--body-file", body_file] + args)
    finally:
        _unlink_quietly(body_file)
    url = url.splitlines()[-1].strip() if url else ""
    if not url:
        # gh が exit 0 なのに URL を返さなかった。ここで進むと本文に
        # 「証跡コメント: 」だけの死んだラベルを書き込み、呼び出し側には
        # falsy が返って「証跡なし」と同じ扱いになる — 失敗が成功に見える。
        raise AttachError(
            "gh pr comment が成功しましたが証跡コメントの URL を返しません"
            "でした。添付が本当に付いたか PR を確認してください")

    linked = body_with_evidence_link(pr_body, url)
    if linked is None:
        print("uat-attach: PR 本文に `## UAT 証跡` 節が無いためリンクを追記しません",
              file=sys.stderr)
    else:
        # temp への書き出しもこの try の中に入れる。ここから先の失敗は
        # すべて「コメントは投稿済み」の世界の話であり、外に出すと
        # 「証跡はまだ添付されていません」という嘘の復旧案内が出て、人が
        # もう一度アップロードしてしまう (添付は取り消せない)。
        edit_file = None
        try:
            edit_file = _write_temp(linked)
            run(["gh", "pr", "edit", pr, "--body-file", edit_file])
        except AttachError as exc:
            # コメント自体は投稿済み。証跡は PR に既にあるので、ここで握り
            # 潰して None を返すと「添付できた」のか「全滅した」のか呼び
            # 出し側が区別できなくなる。失敗として上げつつ、投稿済みの
            # コメント URL をメッセージに含め、人が手でリンクを足せるよう
            # にする。
            raise AttachError(
                f"証跡コメントの投稿には成功しました ({url}) が、PR 本文への"
                f"リンク追記に失敗しました: {exc}。証跡は既に PR にあるので"
                " 再アップロードは不要です", comment_url=url) from exc
        finally:
            if edit_file:
                _unlink_quietly(edit_file)
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
        # CLI は --evidence-dir が必須なので、叩いた時点で「証跡がある」と
        # 主張している。0 件で exit 0 すると、添付ゼロのまま成功に見える。
        url = attach_evidence(args.pr, args.evidence_dir, task, args.dry_run,
                              required=True)
    except AttachError as exc:
        sys.exit(f"uat-attach: {exc}")
    if url:
        print(url)


if __name__ == "__main__":
    main()
