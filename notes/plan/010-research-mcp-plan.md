---
title: リサーチ用 MCP 導入と MCP 定義の dotfiles 化 実装計画
tag: [plan]
Project: devops
Task: 010-research-mcp
created_at: 2026-09-20
updated_at: 2026-09-20
---

# リサーチ用 MCP 導入と MCP 定義の dotfiles 化 実装計画

**Goal:** MCP サーバー定義を dotfiles 内の宣言的マニフェストに正典化し、`setup.sh` から冪等に `~/.claude.json` へ反映できるようにしたうえで、リサーチ用の exa / firecrawl を追加する。

**Architecture:** `.claude/mcp-servers.json` を唯一の正典とし、`.claude/scripts/sync_mcp.py` が読み取って `claude mcp add-json --scope user` で反映する。スクリプトは純粋関数（秘密混入検査・env 抽出・差分計算）と薄い副作用層（ファイル読み取り・CLI 実行）に分ける。テストは純粋関数だけを対象にする。API キーはリポジトリに一切置かず、`~/.claude/settings.json` の `env` を `${VAR}` 参照する。

**Tech Stack:** Python 3 標準ライブラリのみ（`json` / `re` / `os` / `shutil` / `subprocess` / `pathlib` / `unittest`）、bash（`setup.sh`）、Claude Code CLI（`claude mcp`）。

## Global Constraints

- 設計の正典は `notes/document/010-research-mcp-design.md`。
- **リポジトリ内のどのファイルにも平文の API キーを書かない。** 秘密は必ず `${VAR}` 参照にする。
- 既存の `.claude/scripts/unwrap.py` / `test_unwrap.py` の流儀に合わせる: Python 3 標準ライブラリのみ、`unittest`、テストは `cd .claude/scripts && python3 -m unittest test_sync_mcp -v` で実行する。
- スクリプトが人に見せる出力は日本語。コミットメッセージは英語。
- 日本語のコメントと本文は桁数で折り返さない。
- 削除の同期は実装しない（追加と更新のみ）。

---

### Task 1: 秘密混入検査と env 変数抽出（純粋関数）

**Files:**
- Create: `.claude/scripts/sync_mcp.py`
- Test: `.claude/scripts/test_sync_mcp.py`

**Interfaces:**
- Consumes: なし（最初のタスク）
- Produces:
  - `scan_plaintext_secrets(manifest: dict) -> list[str]` — 平文の秘密が置かれている箇所を `"<server>: <location>"` 形式の文字列で返す。検出が無ければ空リスト。
  - `required_env_vars(manifest: dict) -> dict[str, set[str]]` — `${VAR}` の変数名 → それを必要とするサーバー名の集合。
  - `manifest` は `{"mcpServers": {"<name>": {<定義>}}}` 形式の dict。

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/test_sync_mcp.py` を新規作成する。

```python
import unittest

import sync_mcp

class TestScanPlaintextSecrets(unittest.TestCase):
    def test_flags_a_plaintext_value_under_a_secret_named_env_key(self):
        manifest = {"mcpServers": {"n8n-mcp": {"env": {"N8N_API_KEY": "eyJhbGciOiJIUzI1NiJ9.abc"}}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest),
                         ["n8n-mcp: env.N8N_API_KEY"])

    def test_accepts_a_var_reference_under_a_secret_named_env_key(self):
        manifest = {"mcpServers": {"n8n-mcp": {"env": {"N8N_API_KEY": "${N8N_API_KEY}"}}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), [])

    def test_ignores_an_env_key_that_is_not_secret_named(self):
        manifest = {"mcpServers": {"n8n-mcp": {"env": {"N8N_API_URL": "http://localhost:5678"}}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), [])

    def test_flags_a_plaintext_value_after_a_secret_flag_in_args(self):
        manifest = {"mcpServers": {"context7": {"args": ["@upstash/context7-mcp", "--api-key", "ctx7sk-real"]}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest),
                         ["context7: args[2]"])

    def test_accepts_a_var_reference_after_a_secret_flag_in_args(self):
        manifest = {"mcpServers": {"context7": {"args": ["@upstash/context7-mcp", "--api-key", "${CONTEXT7_API_KEY}"]}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), [])

    def test_flags_a_plaintext_authorization_header(self):
        manifest = {"mcpServers": {"remote": {"headers": {"Authorization": "Bearer fc-real"}}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest),
                         ["remote: headers.Authorization"])

    def test_reports_every_offending_location(self):
        manifest = {"mcpServers": {
            "a": {"env": {"A_TOKEN": "raw"}},
            "b": {"env": {"B_SECRET": "raw"}},
        }}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest),
                         ["a: env.A_TOKEN", "b: env.B_SECRET"])

class TestRequiredEnvVars(unittest.TestCase):
    def test_collects_a_var_from_env(self):
        manifest = {"mcpServers": {"ga": {"env": {"GA4_PROPERTY_ID": "${GA4_PROPERTY_ID}"}}}}
        self.assertEqual(sync_mcp.required_env_vars(manifest),
                         {"GA4_PROPERTY_ID": {"ga"}})

    def test_collects_a_var_from_args(self):
        manifest = {"mcpServers": {"context7": {"args": ["--api-key", "${CONTEXT7_API_KEY}"]}}}
        self.assertEqual(sync_mcp.required_env_vars(manifest),
                         {"CONTEXT7_API_KEY": {"context7"}})

    def test_groups_servers_that_need_the_same_var(self):
        manifest = {"mcpServers": {
            "a": {"env": {"SHARED_KEY": "${SHARED}"}},
            "b": {"env": {"SHARED_KEY": "${SHARED}"}},
        }}
        self.assertEqual(sync_mcp.required_env_vars(manifest),
                         {"SHARED": {"a", "b"}})

    def test_returns_empty_when_no_var_is_referenced(self):
        manifest = {"mcpServers": {"playwright": {"command": "npx", "args": ["@playwright/mcp@latest"]}}}
        self.assertEqual(sync_mcp.required_env_vars(manifest), {})

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `cd .claude/scripts && python3 -m unittest test_sync_mcp -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'sync_mcp'`

- [ ] **Step 3: 最小の実装を書く**

`.claude/scripts/sync_mcp.py` を新規作成する。

```python
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

# 値がまるごと ${VAR} の参照になっているか。
VAR_REF_RE = re.compile(r"^\$\{[A-Za-z_][A-Za-z0-9_]*\}$")

# 文字列の中に含まれる ${VAR} の参照。
VAR_IN_TEXT_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

def scan_plaintext_secrets(manifest):
    """平文の秘密が置かれている箇所を "<server>: <location>" の一覧で返す。"""
    found = []
    for name, defn in sorted(manifest.get("mcpServers", {}).items()):
        for section in ("env", "headers"):
            for key, value in sorted(defn.get(section, {}).items()):
                if not SECRET_NAME_RE.search(key):
                    continue
                if isinstance(value, str) and VAR_REF_RE.match(value):
                    continue
                found.append(f"{name}: {section}.{key}")

        args = defn.get("args", [])
        for i, arg in enumerate(args):
            if i == 0 or not isinstance(args[i - 1], str):
                continue
            if not SECRET_FLAG_RE.match(args[i - 1]):
                continue
            if isinstance(arg, str) and VAR_REF_RE.match(arg):
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
```

- [ ] **Step 4: テストが通ることを確認する**

Run: `cd .claude/scripts && python3 -m unittest test_sync_mcp -v`
Expected: PASS（11 tests）

- [ ] **Step 5: コミット**

```bash
git add .claude/scripts/sync_mcp.py .claude/scripts/test_sync_mcp.py
git commit -m "feat(scripts): detect plaintext secrets and collect env refs in the MCP manifest"
```

---

### Task 2: 差分計算（純粋関数・冪等性の本体）

**Files:**
- Modify: `.claude/scripts/sync_mcp.py`
- Test: `.claude/scripts/test_sync_mcp.py`

**Interfaces:**
- Consumes: Task 1 の `sync_mcp` モジュール。
- Produces:
  - `normalize_server(defn: dict) -> dict` — 比較用に定義を正規化する。`type` を補い、空の `env` / `args` を落とす。
  - `diff_servers(manifest: dict, current: dict) -> dict` — `{"add": [名前...], "update": [名前...], "unchanged": [名前...]}`。各リストは名前順。`current` は `~/.claude.json` の `mcpServers` に相当する dict。

正規化が必要な理由は、`claude mcp add-json` が保存した定義には `"env": {}` や `"type": "stdio"` が補われる一方、マニフェストではそれらを省いて書くためである。正規化しないと毎回「更新あり」と判定され、冪等にならない。

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/test_sync_mcp.py` の `if __name__ == "__main__":` の直前に追加する。

```python
class TestNormalizeServer(unittest.TestCase):
    def test_defaults_type_to_stdio_when_a_command_is_present(self):
        self.assertEqual(sync_mcp.normalize_server({"command": "npx"}),
                         {"type": "stdio", "command": "npx"})

    def test_defaults_type_to_http_when_a_url_is_present(self):
        self.assertEqual(sync_mcp.normalize_server({"url": "https://example.com/mcp"}),
                         {"type": "http", "url": "https://example.com/mcp"})

    def test_keeps_an_explicit_type(self):
        self.assertEqual(sync_mcp.normalize_server({"type": "sse", "url": "https://example.com/mcp"}),
                         {"type": "sse", "url": "https://example.com/mcp"})

    def test_drops_an_empty_env_and_an_empty_args(self):
        self.assertEqual(sync_mcp.normalize_server({"type": "stdio", "command": "npx", "env": {}, "args": []}),
                         {"type": "stdio", "command": "npx"})

    def test_keeps_a_non_empty_env(self):
        self.assertEqual(sync_mcp.normalize_server({"type": "stdio", "command": "npx", "env": {"A": "1"}}),
                         {"type": "stdio", "command": "npx", "env": {"A": "1"}})

    def test_does_not_mutate_the_input(self):
        defn = {"command": "npx", "env": {}}
        sync_mcp.normalize_server(defn)
        self.assertEqual(defn, {"command": "npx", "env": {}})

class TestDiffServers(unittest.TestCase):
    def test_classifies_a_missing_server_as_add(self):
        manifest = {"mcpServers": {"exa": {"command": "npx", "args": ["-y", "exa-mcp-server"]}}}
        self.assertEqual(sync_mcp.diff_servers(manifest, {}),
                         {"add": ["exa"], "update": [], "unchanged": []})

    def test_classifies_a_changed_server_as_update(self):
        manifest = {"mcpServers": {"exa": {"command": "npx", "args": ["-y", "exa-mcp-server"]}}}
        current = {"exa": {"type": "stdio", "command": "npx", "args": ["-y", "old-package"], "env": {}}}
        self.assertEqual(sync_mcp.diff_servers(manifest, current),
                         {"add": [], "update": ["exa"], "unchanged": []})

    def test_classifies_an_identical_server_as_unchanged_across_normalization(self):
        manifest = {"mcpServers": {"exa": {"command": "npx", "args": ["-y", "exa-mcp-server"]}}}
        current = {"exa": {"type": "stdio", "command": "npx", "args": ["-y", "exa-mcp-server"], "env": {}}}
        self.assertEqual(sync_mcp.diff_servers(manifest, current),
                         {"add": [], "update": [], "unchanged": ["exa"]})

    def test_ignores_a_server_that_is_only_in_current(self):
        """削除の同期はしない。マニフェストに無いサーバーは差分に現れない。"""
        manifest = {"mcpServers": {}}
        current = {"legacy": {"type": "stdio", "command": "npx"}}
        self.assertEqual(sync_mcp.diff_servers(manifest, current),
                         {"add": [], "update": [], "unchanged": []})

    def test_sorts_each_group_by_name(self):
        manifest = {"mcpServers": {"zebra": {"command": "a"}, "alpha": {"command": "b"}}}
        self.assertEqual(sync_mcp.diff_servers(manifest, {})["add"], ["alpha", "zebra"])
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `cd .claude/scripts && python3 -m unittest test_sync_mcp -v`
Expected: FAIL — `AttributeError: module 'sync_mcp' has no attribute 'normalize_server'`

- [ ] **Step 3: 最小の実装を書く**

`.claude/scripts/sync_mcp.py` の末尾に追加する。

```python
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
```

- [ ] **Step 4: テストが通ることを確認する**

Run: `cd .claude/scripts && python3 -m unittest test_sync_mcp -v`
Expected: PASS（22 tests）

- [ ] **Step 5: コミット**

```bash
git add .claude/scripts/sync_mcp.py .claude/scripts/test_sync_mcp.py
git commit -m "feat(scripts): classify MCP servers into add, update and unchanged"
```

---

### Task 3: マニフェスト `.claude/mcp-servers.json`

**Files:**
- Create: `.claude/mcp-servers.json`
- Test: `.claude/scripts/test_sync_mcp.py`（実ファイルに対する検査を追加する）

**Interfaces:**
- Consumes: Task 1 の `scan_plaintext_secrets` / `required_env_vars`、Task 2 の `normalize_server`。
- Produces: `.claude/mcp-servers.json` — 10 サーバーの正典。Task 4 の副作用層がこれを読む。

現在 `~/.claude.json` にある 8 サーバーを写し取り、exa と firecrawl を追加する。`n8n-mcp` の平文 API キーは `${N8N_API_KEY}` 参照に置き換える（**実値を書き写してはならない**）。

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/test_sync_mcp.py` の `if __name__ == "__main__":` の直前に追加する。

```python
import json
import pathlib

class TestTheShippedManifest(unittest.TestCase):
    """リポジトリに実際に置くマニフェストを対象にした検査。"""

    @classmethod
    def setUpClass(cls):
        path = pathlib.Path(__file__).resolve().parent.parent / "mcp-servers.json"
        cls.manifest = json.loads(path.read_text(encoding="utf-8"))

    def test_contains_no_plaintext_secret(self):
        self.assertEqual(sync_mcp.scan_plaintext_secrets(self.manifest), [])

    def test_declares_the_research_servers(self):
        names = set(self.manifest["mcpServers"])
        self.assertIn("exa", names)
        self.assertIn("firecrawl", names)

    def test_keeps_the_servers_that_are_already_configured(self):
        names = set(self.manifest["mcpServers"])
        for existing in ("playwright", "context7", "notion", "google-analytics",
                         "pencil", "gsc", "chrome-devtools", "n8n-mcp"):
            self.assertIn(existing, names)

    def test_every_server_normalizes_to_a_known_transport(self):
        for name, defn in self.manifest["mcpServers"].items():
            with self.subTest(server=name):
                self.assertIn(sync_mcp.normalize_server(defn)["type"], {"stdio", "http", "sse"})

    def test_the_research_servers_take_their_keys_from_env_refs(self):
        needed = sync_mcp.required_env_vars(self.manifest)
        self.assertIn("exa", needed.get("EXA_API_KEY", set()))
        self.assertIn("firecrawl", needed.get("FIRECRAWL_API_KEY", set()))
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `cd .claude/scripts && python3 -m unittest test_sync_mcp -v`
Expected: FAIL — `FileNotFoundError` で `mcp-servers.json` が無い

- [ ] **Step 3: マニフェストを書く**

`.claude/mcp-servers.json` を新規作成する。

```json
{
  "mcpServers": {
    "chrome-devtools": {
      "type": "stdio",
      "command": "npx",
      "args": ["chrome-devtools-mcp@latest", "--autoConnect"]
    },
    "context7": {
      "type": "stdio",
      "command": "npx",
      "args": ["@upstash/context7-mcp", "--api-key", "${CONTEXT7_API_KEY}"]
    },
    "exa": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "exa-mcp-server"],
      "env": {
        "EXA_API_KEY": "${EXA_API_KEY}"
      }
    },
    "firecrawl": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "firecrawl-mcp"],
      "env": {
        "FIRECRAWL_API_KEY": "${FIRECRAWL_API_KEY}"
      }
    },
    "google-analytics": {
      "type": "stdio",
      "command": "analytics-mcp",
      "args": [],
      "env": {
        "GA4_PROPERTY_ID": "${GA4_PROPERTY_ID}"
      }
    },
    "gsc": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "github:ara-jlu/mcp-server-gsc"]
    },
    "n8n-mcp": {
      "type": "stdio",
      "command": "npx",
      "args": ["n8n-mcp"],
      "env": {
        "MCP_MODE": "stdio",
        "LOG_LEVEL": "error",
        "DISABLE_CONSOLE_OUTPUT": "true",
        "WEBHOOK_SECURITY_MODE": "moderate",
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "${N8N_API_KEY}"
      }
    },
    "notion": {
      "type": "http",
      "url": "https://mcp.notion.com/mcp"
    },
    "pencil": {
      "type": "stdio",
      "command": "/Applications/Pencil.app/Contents/Resources/app.asar.unpacked/out/mcp-server-darwin-arm64",
      "args": ["--app", "desktop"]
    },
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  }
}
```

- [ ] **Step 4: テストが通ることを確認する**

Run: `cd .claude/scripts && python3 -m unittest test_sync_mcp -v`
Expected: PASS（27 tests）

- [ ] **Step 5: コミット**

```bash
git add .claude/mcp-servers.json .claude/scripts/test_sync_mcp.py
git commit -m "feat(mcp): declare the MCP server manifest with exa and firecrawl"
```

---

### Task 4: 副作用層と CLI エントリポイント

**Files:**
- Modify: `.claude/scripts/sync_mcp.py`

**Interfaces:**
- Consumes: Task 1 / 2 の純粋関数、Task 3 のマニフェスト。
- Produces: `python3 .claude/scripts/sync_mcp.py` で実行できる CLI。Task 5 の `setup.sh` がこれを呼ぶ。

この層は原則テストしない。純粋関数に処理を寄せ、ここは薄く保つことで担保する。例外は `load_manifest` で、
「マニフェストが不正な JSON なら即停止する」は設計が明示した振る舞いなのでテストで固定する。

エラー処理の強度（設計書のとおり）:

| 事象 | 扱い |
|---|---|
| マニフェストに平文の秘密 | 即停止（exit 1） |
| マニフェストが不正な JSON | 即停止（exit 1） |
| `claude` CLI が無い | 警告してスキップ（exit 0） |
| `${VAR}` が未定義 | 警告（どの変数がどのサーバーで必要かを表示）。exit 0 |
| `command` が絶対パスで実行ファイルが無い | 警告してそのサーバーのみ skip |
| `claude mcp add-json` が失敗 | 記録して続行、最後にまとめて報告し exit 1 |

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/test_sync_mcp.py` の `if __name__ == "__main__":` の直前に追加する。

```python
import tempfile

class TestLoadManifest(unittest.TestCase):
    def _write(self, text):
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        handle.write(text)
        handle.close()
        self.addCleanup(pathlib.Path(handle.name).unlink)
        return pathlib.Path(handle.name)

    def test_reads_a_valid_manifest(self):
        path = self._write('{"mcpServers": {"a": {"command": "npx"}}}')
        self.assertEqual(sync_mcp.load_manifest(path),
                         {"mcpServers": {"a": {"command": "npx"}}})

    def test_stops_on_invalid_json(self):
        path = self._write("{not json")
        with self.assertRaises(SystemExit):
            sync_mcp.load_manifest(path)

    def test_stops_when_the_manifest_is_missing(self):
        with self.assertRaises(SystemExit):
            sync_mcp.load_manifest(pathlib.Path("/nonexistent/mcp-servers.json"))
```

- [ ] **Step 2: テストが失敗することを確認する**

Run: `cd .claude/scripts && python3 -m unittest test_sync_mcp -v`
Expected: FAIL — `AttributeError: module 'sync_mcp' has no attribute 'load_manifest'`

- [ ] **Step 3: 実装を書く**

`.claude/scripts/sync_mcp.py` の冒頭の import に追加する。

```python
import json
import os
import pathlib
import shutil
import subprocess
import sys
```

そのうえでファイル末尾に追加する。

```python
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
```

- [ ] **Step 4: テストが通ることを確認する**

Run: `cd .claude/scripts && python3 -m unittest test_sync_mcp -v`
Expected: PASS（30 tests）

- [ ] **Step 5: 実際に同期を走らせる**

Run: `python3 .claude/scripts/sync_mcp.py`
Expected: `追加: exa, firecrawl` と `更新: n8n-mcp` が表示される（n8n-mcp は平文キーから `${N8N_API_KEY}` 参照へ変わるため）。
続けて `EXA_API_KEY` / `FIRECRAWL_API_KEY` / `GA4_PROPERTY_ID` / `N8N_API_KEY` が未設定である旨の警告が出て、exit 0。
残り 7 サーバーは正規化後に一致するので投入されない。

- [ ] **Step 6: 冪等性を確認する**

Run: `python3 .claude/scripts/sync_mcp.py`
Expected: `MCP 設定に変更はありません（10 サーバー）。` と表示される。もし 2 回目で「更新」と出るなら `normalize_server` が実際の保存形と合っていないので、`~/.claude.json` の保存後の形を確認して正規化を直す。

- [ ] **Step 7: コミット**

```bash
git add .claude/scripts/sync_mcp.py
git commit -m "feat(scripts): sync the MCP manifest into user scope idempotently"
```

---

### Task 5: setup.sh への統合・settings サンプル・手順の文書化

**Files:**
- Modify: `setup.sh`
- Modify: `.claude/settings.json.sample`
- Modify: `README.md`

**Interfaces:**
- Consumes: Task 4 の CLI（`python3 .claude/scripts/sync_mcp.py`）。
- Produces: なし（最終タスク）。

`setup.sh` は `set -e` で動いているので、同期の失敗が nvim や tmux の設定まで巻き込んで全体を止めないように `||` で受ける。

- [ ] **Step 1: setup.sh に同期を追加する**

`setup.sh` の「Claude Code設定のセットアップ」ブロックの末尾（`echo "✓ Claude Code設定のリンクが完了しました"` の直後）に挿入する。

```bash
# MCP サーバー設定の同期
# 正典は .claude/mcp-servers.json。秘密は ${VAR} 参照で、実値は ~/.claude/settings.json の env に置く。
echo "MCP サーバー設定を同期しています..."
python3 "$DOTFILES_DIR/.claude/scripts/sync_mcp.py" \
    || echo "⚠ MCP 設定の同期に失敗しました（他の設定は適用済みです）"
```

- [ ] **Step 2: settings.json.sample に env のプレースホルダを追加する**

`.claude/settings.json.sample` の `"env"` ブロックを次の内容に置き換える。

```json
  "env": {
    "CONTEXT7_API_KEY": "<YOUR_CONTEXT7_API_KEY>",
    "EXA_API_KEY": "<YOUR_EXA_API_KEY>",
    "FIRECRAWL_API_KEY": "<YOUR_FIRECRAWL_API_KEY>",
    "GA4_PROPERTY_ID": "<YOUR_GA4_PROPERTY_ID>",
    "N8N_API_KEY": "<YOUR_N8N_API_KEY>",
    "DISCORD_WEBHOOK_URL": "<YOUR_DISCORD_WEBHOOK_URL>",
    "DISCORD_MENTION_USER": "<YOUR_DISCORD_USER_ID>",
    "NOTION_TASK_COLLECTION_URL": "<YOUR_NOTION_TASK_COLLECTION_URL>",
    "NOTION_NOTES_COLLECTION_URL": "<YOUR_NOTION_NOTES_COLLECTION_URL>"
  },
```

- [ ] **Step 3: README.md に手順を書く**

`README.md` の「## Git Alias」節の直前に挿入する。

```markdown
## MCP サーバー

Claude Code の MCP サーバー定義は `.claude/mcp-servers.json` が正典です。`setup.sh` が
`claude mcp add-json --scope user` で `~/.claude.json` に冪等に反映します（2 回目以降は
「変更はありません」と表示されます）。

### API キーの置き場所

**キーをこのリポジトリに書かないでください。** マニフェストには `${VAR}` 参照だけを書き、
実値は `~/.claude/settings.json` の `env` に置きます（このファイルは gitignore 済みです）。
必要な変数の一覧は `.claude/settings.json.sample` にあります。平文の秘密を書いた場合、
同期スクリプトは投入せずに停止します。

### リサーチ用 MCP のキー取得

`ecc:deep-research` などの調査系スキルは exa と firecrawl を使います。どちらも無料枠が
あり、クレジットカードは不要です。

1. exa: https://exa.ai でサインアップし、API キーを発行する（サインアップ時 $20 ＋ 毎月 $10 のクレジット）
2. firecrawl: https://firecrawl.dev でサインアップし、API キーを発行する（月 1,000 クレジット）
3. `~/.claude/settings.json` の `env` に `EXA_API_KEY` と `FIRECRAWL_API_KEY` を追加する
4. `./setup.sh` を実行する（または `python3 .claude/scripts/sync_mcp.py` を直接実行する）
5. Claude Code を再起動し、`claude mcp list` で接続を確認する

### 注意

- `notion` は OAuth で認証します。定義を入れ直したあとは Claude Code 内で `/mcp` から
  再認証してください。
- `pencil` はローカルアプリの絶対パスに依存します。インストールされていないマシンでは
  警告つきで skip されます。
- マニフェストから消したサーバーは `~/.claude.json` からは消えません（削除の同期は
  行いません）。不要になったサーバーは `claude mcp remove <name> --scope user` で
  手動で消してください。
```

- [ ] **Step 4: テストとセットアップを確認する**

Run: `cd .claude/scripts && python3 -m unittest test_sync_mcp -v`
Expected: PASS（30 tests）

Run: `bash -n setup.sh`
Expected: 出力なし（構文エラーが無い）

Run: `python3 -c "import json; json.load(open('.claude/settings.json.sample'))"`
Expected: 出力なし（JSON として妥当）

- [ ] **Step 5: コミット**

```bash
git add setup.sh .claude/settings.json.sample README.md
git commit -m "feat(setup): sync MCP servers from the manifest and document the keys"
```

---

## 実装後に人間が行うこと

このブランチの実装は、キーが無くても完了する。キーに依存する受け入れ基準（設計書の 3 と 4）は
人間の確認になる。

1. exa と firecrawl の API キーを取得する。
2. `~/.claude/settings.json` の `env` に `EXA_API_KEY` / `FIRECRAWL_API_KEY` を追加する。
   欠けている `GA4_PROPERTY_ID` もここで埋める。
3. `n8n-mcp` の API キーを `settings.json` の `N8N_API_KEY` に移し、**n8n 側でローテーションする**
   （現行のキーは設計時の調査で会話ログに露出した）。
4. `python3 .claude/scripts/sync_mcp.py` を実行し、Claude Code を再起動する。
5. `claude mcp list` で exa / firecrawl が接続済みであることを確認する。
6. `ecc:deep-research` を起動し、WebSearch フォールバックではなく `web_search_exa` /
   `firecrawl_search` が実際に呼ばれることを確認する。
