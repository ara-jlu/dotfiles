#!/usr/bin/env python3
"""MCP サーバー定義を dotfiles のマニフェストから ~/.claude.json へ冪等に反映する。

正典は .claude/mcp-servers.json である。このスクリプトはそれを読み、claude CLI 経由で user scope に反映する。**マニフェストに平文の秘密を書いてはならない** — 秘密は必ず ${VAR} 参照にし、実値は ~/.claude/settings.json の env に置く。平文を見つけたらこのスクリプトは即停止する。リポジトリに push した秘密は履歴に残り、取り返しがつかない。

テスト: cd .claude/scripts && python3 -m unittest test_sync_mcp -v
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import urllib.parse

# 秘密を入れる箇所だと判断するキー名。env のキー名、headers のキー名、args のフラグ名、URL のクエリ名に当てる。
# AUTH は Authorization・auth-token の双方を覆う。
SECRET_NAME_RE = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTH)", re.I)

# args の要素がフラグの形をしているか。この形かつ SECRET_NAME_RE に当たる語を含むものを秘密フラグとみなす。
# 完全一致で列挙すると --bearer-token や --client-secret のような実在の綴りが素通りする。
# 秘密のゲートは取りこぼすより過検出に倒す。
FLAG_SHAPE_RE = re.compile(r"^--?[A-Za-z0-9._-]+$")

# 文字列の中に ${VAR} の参照が少なくとも1つ含まれているか。
# "Bearer ${TOKEN}" のように値の一部が ${VAR} 参照であれば安全とみなす。
# required_env_vars もこの正規表現で ${VAR} を拾うため、両者の判断基準は常に一致する。
VAR_IN_TEXT_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

# ${VAR} を取り除いた残りかすの中の、base64／hex 的な文字の途切れない連なり。
# `-` と `_` は sk-live- や sk_live_ のような接頭辞の区切りとして使われるので、連なりの区切り文字として扱う。
KEY_SHAPED_RUN_RE = re.compile(r"[A-Za-z0-9+/=]+")

# 残りかすが鍵らしいと判断する連なりの長さ。
# 16 文字は、実在の鍵のランダム部（JWT の eyJhbGciOiJIUzI1NiJ9 は 20 文字、sk-live- 系の本体は 20 文字以上）が
# ほぼ必ず超える一方、値の一部として正当に書かれる語——Bearer・key・Authorization（13 文字）・localhost・
# ホスト名やパスの各要素——が区切り文字で切られたあとに到達しない長さである。
# 過検出したときの代償は「${VAR} に直せ」と言われることだけなので、短めに倒してある。
KEY_SHAPED_MIN_RUN = 16


def looks_like_key_material(text):
    """${VAR} を全部取り除いた残りかすが鍵の形をしていれば True。

    「${VAR} を1つでも含めば安全」だけを条件にすると "${DECOY}sk-REALKEY" のような囮が素通りする。
    かといって許可する語の一覧を持つと、語が増えるたびに腐る。そこで語ではなく形——長さと文字の種類——で判断する。
    """
    residue = VAR_IN_TEXT_RE.sub("", text)
    return any(len(run) >= KEY_SHAPED_MIN_RUN for run in KEY_SHAPED_RUN_RE.findall(residue))


def value_is_safe(value):
    """秘密が置かれうる場所の値が安全か。${VAR} 参照を含み、かつ残りかすが鍵の形をしていないこと。"""
    return (isinstance(value, str)
            and bool(VAR_IN_TEXT_RE.search(value))
            and not looks_like_key_material(value))


def is_secret_flag(arg):
    """args の要素が「次の要素が秘密になるフラグ」か。"""
    return (isinstance(arg, str)
            and bool(FLAG_SHAPE_RE.match(arg))
            and bool(SECRET_NAME_RE.search(arg)))


def scan_url(url):
    """URL の中の秘密らしい箇所を、場所を表す接尾辞の一覧で返す。

    http / sse トランスポートの url は env や headers と違って構造を持たないので、クエリ文字列と
    userinfo（https://user:pass@host の部分）を個別に見る。設計時に exa / firecrawl のリモート
    HTTP 版を検討しているので、この形は今後いちばん現れやすい。
    """
    if not isinstance(url, str):
        return []
    found = []
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        # 解析できない url は中身を確かめられない。確かめられないものは安全と言えないので報告する。
        return ["url"]
    if parsed.password is not None and not value_is_safe(parsed.password):
        found.append("url.userinfo")
    for key, value in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True):
        if SECRET_NAME_RE.search(key) and not value_is_safe(value):
            found.append(f"url.{key}")
    return found


def scan_plaintext_secrets(manifest):
    """平文の秘密が置かれている箇所を "<server>: <location>" の一覧で返す。"""
    found = []
    for name, defn in sorted(manifest.get("mcpServers", {}).items()):
        for section in ("env", "headers"):
            for key, value in sorted(defn.get(section, {}).items()):
                if not SECRET_NAME_RE.search(key):
                    continue
                if value_is_safe(value):
                    continue
                found.append(f"{name}: {section}.{key}")

        args = defn.get("args", [])
        for i, arg in enumerate(args):
            # --api-key=sk-... のように = で繋いだ形。値が別要素にならないので、その場で中身を見る。
            if isinstance(arg, str) and "=" in arg:
                flag, _, value = arg.partition("=")
                if is_secret_flag(flag) and not value_is_safe(value):
                    found.append(f"{name}: args[{i}]")
                    continue
            # --api-key sk-... のように空白で分けた形。直前の要素がフラグなら、この要素が値。
            if i > 0 and is_secret_flag(args[i - 1]) and not value_is_safe(arg):
                found.append(f"{name}: args[{i}]")

        for location in scan_url(defn.get("url")):
            found.append(f"{name}: {location}")
    return found


def required_env_vars(manifest):
    """定義が参照している ${VAR} を、変数名 -> それを必要とするサーバー名の集合 で返す。"""
    needed = {}

    def walk(value, server):
        if isinstance(value, str):
            for var in VAR_IN_TEXT_RE.findall(value):
                needed.setdefault(var, set()).add(server)
        elif isinstance(value, dict):
            for item in value.values():
                walk(item, server)
        elif isinstance(value, list):
            for item in value:
                walk(item, server)

    for name, defn in manifest.get("mcpServers", {}).items():
        walk(defn, name)
    return needed


def normalize_server(defn):
    """比較用に定義を正規化する。

    claude mcp add-json が保存した定義には "type" や空の "env" が補われる一方、マニフェストではそれらを省いて書く。正規化しないと毎回「更新あり」と判定され、冪等にならない。
    """
    out = dict(defn)
    if "type" not in out:
        out["type"] = "stdio" if "command" in out else "http"
    for key in ("env", "args", "headers"):
        if key in out and not out[key]:
            del out[key]
    return out


def diff_servers(manifest, current):
    """マニフェストの各サーバーを add / update / unchanged に分類する。

    マニフェストに無いサーバーはどのリストにも入らない（削除の同期はしない）。
    """
    result = {"add": [], "update": [], "unchanged": []}
    for name, defn in sorted(manifest.get("mcpServers", {}).items()):
        if name not in current:
            result["add"].append(name)
        elif normalize_server(defn) == normalize_server(current[name]):
            result["unchanged"].append(name)
        else:
            result["update"].append(name)
    return result


MANIFEST_PATH = pathlib.Path(__file__).resolve().parent.parent / "mcp-servers.json"
CLAUDE_CONFIG_PATH = pathlib.Path.home() / ".claude.json"
SETTINGS_PATH = pathlib.Path.home() / ".claude" / "settings.json"


def load_manifest(path):
    """マニフェストを読む。読めなければ即停止する。"""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"エラー: マニフェストが見つかりません: {path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"エラー: マニフェストが不正な JSON です: {path}: {exc}")


def read_current_servers(path):
    """~/.claude.json から現在の MCP 定義を読む。読めなければ空として扱う。"""
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("mcpServers", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def available_env_names(settings_path):
    """${VAR} の解決元になりうる名前の集合。settings.json の env と、現在のシェル環境。"""
    names = set(os.environ)
    try:
        names |= set(json.loads(settings_path.read_text(encoding="utf-8")).get("env", {}))
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return names


def missing_local_command(defn):
    """command が絶対パスで、その実行ファイルが無ければ True。

    ローカルアプリの実行ファイルに依存するサーバーを、インストールされていないマシンで skip するために使う。相対コマンド（npx 等）は PATH 解決に任せるので対象外。
    """
    command = defn.get("command", "")
    return command.startswith("/") and not os.access(command, os.X_OK)


# claude CLI 1 回あたりの待ち時間の上限（秒）。
# add-json はローカルの JSON を書き換えるだけなので通常は 1 秒未満で終わる。
# 60 秒は npm レジストリの解決などで遅い環境でも十分な余裕を取りつつ、応答しなくなった CLI が
# setup.sh 全体を無期限に止めるのを防ぐ長さである。`||` のガードは返ってこないプロセスには効かない。
CLAUDE_TIMEOUT_SECONDS = 60


def run_claude(args):
    """claude CLI を実行する。応答が無ければ、他の失敗と同じ形で返す。"""
    command = ["claude", *args]
    try:
        return subprocess.run(command, capture_output=True, text=True,
                              timeout=CLAUDE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(
            command, 1, "",
            f"claude が {CLAUDE_TIMEOUT_SECONDS} 秒以内に応答しませんでした")


def add_json(name, defn):
    return run_claude(["mcp", "add-json", name, json.dumps(defn), "--scope", "user"])


def apply_server(name, defn, previous_defn):
    """1 サーバーを user scope に投入する。成功すれば True。

    まず add-json をそのまま試し、既存の定義があって失敗したときだけ remove してから retry する。
    retry の add も失敗したら、remove する前の定義（previous_defn）に戻す。
    戻すのは既存サーバーの update が失敗した場合だけで、新規追加（previous_defn が None）の場合は戻す対象が無い。復元にまで失敗したら、それだけは必ず出力する——設定が消えたままになる唯一のケースなので、黙らせてはならない。
    """
    done = add_json(name, defn)
    if done.returncode != 0 and previous_defn is not None:
        # remove して retry するのは名前の衝突を解くためなので、既存の定義があるときだけ意味がある。
        # 新規追加は衝突しようがなく、消す対象も無い。
        run_claude(["mcp", "remove", name, "--scope", "user"])
        done = add_json(name, defn)
    if done.returncode != 0:
        message = done.stderr.strip() or done.stdout.strip()
        if previous_defn is None:
            print(f"  ✗ {name}: {message}")
        else:
            restore = add_json(name, previous_defn)
            if restore.returncode == 0:
                print(f"  ✗ {name}: {message}（元の定義に戻しました）")
            else:
                restore_message = restore.stderr.strip() or restore.stdout.strip()
                print(f"  ✗ {name}: {message}"
                      f"（元の定義への復元にも失敗しました。手動で確認してください: {restore_message}）")
        return False
    return True


def main():
    manifest = load_manifest(MANIFEST_PATH)

    leaks = scan_plaintext_secrets(manifest)
    if leaks:
        print("エラー: マニフェストに平文の秘密があります。${VAR} 参照に直してください。")
        for leak in leaks:
            print(f"  - {leak}")
        return 1

    if shutil.which("claude") is None:
        print("⚠ claude CLI が見つかりません。MCP の同期をスキップします。")
        return 0

    current = read_current_servers(CLAUDE_CONFIG_PATH)
    diff = diff_servers(manifest, current)

    skipped = [n for n in diff["add"] + diff["update"]
               if missing_local_command(manifest["mcpServers"][n])]
    for name in skipped:
        print(f"⚠ {name}: 実行ファイルが見つからないので skip します"
              f"（{manifest['mcpServers'][name]['command']}）")

    targets = [n for n in diff["add"] + diff["update"] if n not in skipped]
    if not targets:
        print(f"MCP 設定に変更はありません（{len(diff['unchanged'])} サーバー）。")
    else:
        if diff["add"]:
            print(f"追加: {', '.join(n for n in diff['add'] if n not in skipped) or 'なし'}")
        if diff["update"]:
            print(f"更新: {', '.join(n for n in diff['update'] if n not in skipped) or 'なし'}")

    # env の充足検査は投入より前に出す。
    # 投入したあとに警告しても、そのときにはもう ${VAR} 参照で上書きされている。
    # 実際に n8n-mcp は、動いていた平文のキーが未定義の ${N8N_API_KEY} に置き換わったあとで初めて警告が出た。
    known = available_env_names(SETTINGS_PATH)
    for var, servers in sorted(required_env_vars(manifest).items()):
        if var not in known:
            print(f"⚠ {var} が未設定です（{', '.join(sorted(servers))} が必要としています）。"
                  f"~/.claude/settings.json の env に追加してください。")

    failed = [name for name in targets
              if not apply_server(name, manifest["mcpServers"][name], current.get(name))]

    if failed:
        print(f"エラー: {len(failed)} サーバーの投入に失敗しました: {', '.join(failed)}")
        return 1

    if targets:
        print(f"✓ MCP 設定を同期しました（{len(targets)} サーバー）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
