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
