"""MCP サーバー定義を dotfiles のマニフェストから ~/.claude.json へ冪等に反映する。

正典は .claude/mcp-servers.json である。このスクリプトはそれを読み、claude CLI 経由で
user scope に反映する。**マニフェストに平文の秘密を書いてはならない** — 秘密は必ず
${VAR} 参照にし、実値は ~/.claude/settings.json の env に置く。平文を見つけたら
このスクリプトは即停止する。リポジトリに push した秘密は履歴に残り、取り返しがつかない。

テスト: cd .claude/scripts && python3 -m unittest test_sync_mcp -v
"""

import re

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
