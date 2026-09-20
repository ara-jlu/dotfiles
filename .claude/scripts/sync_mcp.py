#!/usr/bin/env python3
"""MCP サーバー定義を dotfiles のマニフェストから ~/.claude.json へ冪等に反映する。

正典は .claude/mcp-servers.json である。このスクリプトはそれを読み、claude CLI 経由で
user scope に反映する。**マニフェストに平文の秘密を書いてはならない** — 秘密は必ず
${VAR} 参照にし、実値は ~/.claude/settings.json の env に置く。平文を見つけたら
このスクリプトは即停止する。リポジトリに push した秘密は履歴に残り、取り返しがつかない。

テスト: cd .claude/scripts && python3 -m unittest test_sync_mcp -v
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

# 秘密を入れる箇所だと判断するキー名。env のキー名と headers のキー名に当てる。
SECRET_NAME_RE = re.compile(r"(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|AUTHORIZATION)", re.I)

# args の中で、次の要素が秘密になるフラグ。
SECRET_FLAG_RE = re.compile(r"^--?(api[-_]?key|token|secret|password)$", re.I)

# 文字列の中に ${VAR} の参照が少なくとも1つ含まれているか。
# "Bearer ${TOKEN}" のように値の一部が ${VAR} 参照であれば安全とみなす。
# required_env_vars もこの正規表現で ${VAR} を拾うため、両者の判断基準は常に一致する。
VAR_IN_TEXT_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def scan_plaintext_secrets(manifest):
    """平文の秘密が置かれている箇所を "<server>: <location>" の一覧で返す。"""
    found = []
    for name, defn in sorted(manifest.get("mcpServers", {}).items()):
        for section in ("env", "headers"):
            for key, value in sorted(defn.get(section, {}).items()):
                if not SECRET_NAME_RE.search(key):
                    continue
                if isinstance(value, str) and VAR_IN_TEXT_RE.search(value):
                    continue
                found.append(f"{name}: {section}.{key}")

        args = defn.get("args", [])
        for i, arg in enumerate(args):
            if i == 0 or not isinstance(args[i - 1], str):
                continue
            if not SECRET_FLAG_RE.match(args[i - 1]):
                continue
            if isinstance(arg, str) and VAR_IN_TEXT_RE.search(arg):
                continue
            found.append(f"{name}: args[{i}]")
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

    claude mcp add-json が保存した定義には "type" や空の "env" が補われる一方、
    マニフェストではそれらを省いて書く。正規化しないと毎回「更新あり」と判定され、冪等にならない。
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

    pencil のようにローカルアプリに依存するサーバーを、インストールされていないマシンで
    skip するために使う。相対コマンド（npx 等）は PATH 解決に任せるので対象外。
    """
    command = defn.get("command", "")
    return command.startswith("/") and not os.access(command, os.X_OK)


def add_json(name, defn):
    return subprocess.run(
        ["claude", "mcp", "add-json", name, json.dumps(defn), "--scope", "user"],
        capture_output=True, text=True)


def apply_server(name, defn):
    """1 サーバーを user scope に投入する。成功すれば True。

    まず add-json をそのまま試し、失敗したときだけ remove してから retry する。
    先に remove してしまうと、add に失敗したときに動いていたサーバーを失う。
    """
    done = add_json(name, defn)
    if done.returncode != 0:
        subprocess.run(["claude", "mcp", "remove", name, "--scope", "user"],
                       capture_output=True, text=True)
        done = add_json(name, defn)
    if done.returncode != 0:
        print(f"  ✗ {name}: {done.stderr.strip() or done.stdout.strip()}")
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

    diff = diff_servers(manifest, read_current_servers(CLAUDE_CONFIG_PATH))

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

    failed = [name for name in targets if not apply_server(name, manifest["mcpServers"][name])]

    known = available_env_names(SETTINGS_PATH)
    for var, servers in sorted(required_env_vars(manifest).items()):
        if var not in known:
            print(f"⚠ {var} が未設定です（{', '.join(sorted(servers))} が必要としています）。"
                  f"~/.claude/settings.json の env に追加してください。")

    if failed:
        print(f"エラー: {len(failed)} サーバーの投入に失敗しました: {', '.join(failed)}")
        return 1

    if targets:
        print(f"✓ MCP 設定を同期しました（{len(targets)} サーバー）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
