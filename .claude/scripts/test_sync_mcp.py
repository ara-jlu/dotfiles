import json
import pathlib
import tempfile
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

    def test_accepts_an_embedded_var_reference_after_a_secret_flag_in_args(self):
        manifest = {"mcpServers": {"context7": {"args": ["@upstash/context7-mcp", "--api-key", "key-${CONTEXT7_API_KEY}"]}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), [])

    def test_flags_a_plaintext_authorization_header(self):
        manifest = {"mcpServers": {"remote": {"headers": {"Authorization": "Bearer fc-real"}}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest),
                         ["remote: headers.Authorization"])

    def test_accepts_an_embedded_var_reference_in_an_authorization_header(self):
        manifest = {"mcpServers": {"remote": {"headers": {"Authorization": "Bearer ${TOKEN}"}}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), [])

    def test_reports_every_offending_location(self):
        manifest = {"mcpServers": {
            "a": {"env": {"A_TOKEN": "raw"}},
            "b": {"env": {"B_SECRET": "raw"}},
        }}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest),
                         ["a: env.A_TOKEN", "b: env.B_SECRET"])


class TestSecretFlagSpellings(unittest.TestCase):
    """完全一致の列挙では取りこぼす、実在するフラグの綴り。"""

    def test_flags_a_plaintext_value_after_each_real_world_secret_flag(self):
        for flag in ("--bearer-token", "--auth-token", "--access-token",
                     "--client-secret", "--credential", "--api-token", "--apiKey"):
            with self.subTest(flag=flag):
                manifest = {"mcpServers": {"remote": {"args": ["pkg", flag, "sk-SYNTHETIC-VALUE-000"]}}}
                self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), ["remote: args[2]"])

    def test_accepts_a_var_reference_after_a_widened_secret_flag(self):
        manifest = {"mcpServers": {"remote": {"args": ["pkg", "--bearer-token", "${REMOTE_TOKEN}"]}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), [])

    def test_ignores_a_flag_that_has_nothing_to_do_with_secrets(self):
        manifest = {"mcpServers": {"chrome": {"args": ["chrome-devtools-mcp@latest", "--autoConnect", "true"]}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), [])


class TestEqualJoinedSecretFlags(unittest.TestCase):
    """--flag=value の形。値が別要素にならないので、要素の中身を見ないと素通りする。"""

    def test_flags_a_plaintext_value_joined_with_an_equals_sign(self):
        manifest = {"mcpServers": {"context7": {"args": ["@upstash/context7-mcp", "--api-key=ctx7sk-SYNTHETIC-000"]}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), ["context7: args[1]"])

    def test_accepts_a_var_reference_joined_with_an_equals_sign(self):
        manifest = {"mcpServers": {"context7": {"args": ["@upstash/context7-mcp", "--api-key=${CONTEXT7_API_KEY}"]}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), [])

    def test_ignores_a_non_secret_flag_joined_with_an_equals_sign(self):
        manifest = {"mcpServers": {"a": {"args": ["pkg", "--mode=stdio"]}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), [])


class TestScanUrl(unittest.TestCase):
    """http / sse トランスポートの url。env や headers と違って構造を持たない。"""

    def test_flags_a_plaintext_key_in_a_query_parameter(self):
        manifest = {"mcpServers": {"remote": {"type": "http", "url": "https://host/mcp?apiKey=sk-SYNTHETIC-VALUE-000"}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), ["remote: url.apiKey"])

    def test_accepts_a_var_reference_in_a_query_parameter(self):
        manifest = {"mcpServers": {"remote": {"type": "http", "url": "https://host/mcp?apiKey=${REMOTE_API_KEY}"}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), [])

    def test_ignores_a_query_parameter_that_is_not_secret_named(self):
        manifest = {"mcpServers": {"remote": {"type": "http", "url": "https://host/mcp?version=2"}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), [])

    def test_flags_a_password_in_the_userinfo(self):
        manifest = {"mcpServers": {"remote": {"type": "sse", "url": "https://user:SYNTHETICPASSWORD@host/mcp"}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), ["remote: url.userinfo"])

    def test_ignores_a_url_without_credentials(self):
        manifest = {"mcpServers": {"notion": {"type": "http", "url": "https://mcp.notion.com/mcp"}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), [])


class TestDecoyVarReferences(unittest.TestCase):
    """${VAR} を1つ置いただけで平文を通す囮。語ではなく形（長さと文字種）で判断する。"""

    def test_keeps_accepting_a_var_reference_with_a_short_literal_prefix(self):
        manifest = {"mcpServers": {"remote": {"headers": {"Authorization": "Bearer ${TOKEN}"}}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest), [])

    def test_flags_key_shaped_residue_next_to_a_decoy_var_reference(self):
        manifest = {"mcpServers": {"remote": {"env": {"REMOTE_API_KEY": "${DECOY}sk-live-51H8xKqRtPvNmWzYbGcDfJeLa9"}}}}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest),
                         ["remote: env.REMOTE_API_KEY"])

    def test_flags_a_decoy_in_args_and_in_a_url_too(self):
        manifest = {"mcpServers": {
            "a": {"args": ["pkg", "--api-key", "${DECOY}sk-live-51H8xKqRtPvNmWzYbGcDfJeLa9"]},
            "b": {"url": "https://host/mcp?apiKey=${DECOY}sk-live-51H8xKqRtPvNmWzYbGcDfJeLa9"},
        }}
        self.assertEqual(sync_mcp.scan_plaintext_secrets(manifest),
                         ["a: args[2]", "b: url.apiKey"])

    def test_treats_ordinary_words_and_punctuation_as_not_key_shaped(self):
        for residue in ("Bearer ", "key-", ":", "token ", "Authorization"):
            with self.subTest(residue=residue):
                self.assertFalse(sync_mcp.looks_like_key_material(residue + "${TOKEN}"))

    def test_treats_a_long_unbroken_run_as_key_shaped(self):
        self.assertTrue(sync_mcp.looks_like_key_material("${DECOY}eyJhbGciOiJIUzI1NiJ9"))


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
                         "gsc", "chrome-devtools", "n8n-mcp"):
            self.assertIn(existing, names)

    def test_every_server_normalizes_to_a_known_transport(self):
        for name, defn in self.manifest["mcpServers"].items():
            with self.subTest(server=name):
                self.assertIn(sync_mcp.normalize_server(defn)["type"], {"stdio", "http", "sse"})

    def test_the_research_servers_take_their_keys_from_env_refs(self):
        needed = sync_mcp.required_env_vars(self.manifest)
        self.assertIn("exa", needed.get("EXA_API_KEY", set()))
        self.assertIn("firecrawl", needed.get("FIRECRAWL_API_KEY", set()))


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


if __name__ == "__main__":
    unittest.main()
