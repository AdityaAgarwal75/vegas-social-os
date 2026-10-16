"""Meta DevTools MCP installation guide is truthful, nonsecret and nonblocking."""
import json
import tempfile
import unittest
from pathlib import Path

from vso import auth, tools
from vso.engine import Engine
from vso.store import Store


class MetaMcpOnboardingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.engine = Engine(Store(self.tmp.name), "https://my-independent-server.example")
        self.engine.accounts.config.save("facebook", {
            "client_id": "1234567890123456",
            "client_secret": "do-not-reveal-this-secret",
            "graph_version": "v25.0",
        })

    def test_readonly_tool_returns_owned_callback_and_no_secrets(self):
        payload = tools.call(self.engine, "meta_mcp_setup", {})
        self.assertEqual(payload["mcp_server"], "https://mcp.facebook.com/devtools")
        self.assertEqual(payload["facebook"]["app_id"], "1234567890123456")
        self.assertTrue(payload["facebook"]["secret_present"])
        self.assertTrue(payload["facebook"]["credentials_configured"])
        self.assertEqual(payload["facebook"]["oauth_callback_urls"], [
            "https://my-independent-server.example/callback/facebook",
        ])
        text = json.dumps(payload)
        self.assertNotIn("do-not-reveal-this-secret", text)
        self.assertEqual(payload["meta_mcp_connection"], "unverified_from_vps")
        self.assertIn("devtools_app_list", payload["supported_read_tools"])
        self.assertIn("devtools_webhook_manage", payload["supported_manage_tools"])
        self.assertIn("devtools_app_create", payload["upcoming_unavailable_tools"])
        self.assertEqual(auth.tool_scope("meta_mcp_setup"), "social:read")
        schemas = {x["name"]: x for x in tools.definitions(self.engine)}
        self.assertIn("meta_mcp_setup", schemas)
        self.assertEqual(schemas["meta_mcp_setup"]["inputSchema"]["required"], [])

    def test_unconfigured_facebook_is_not_marked_connected(self):
        with tempfile.TemporaryDirectory() as root:
            e = Engine(Store(root), "https://fresh-owner.example")
            report = tools.call(e, "meta_mcp_setup", {})
            self.assertFalse(report["facebook"]["credentials_configured"])
            self.assertFalse(report["facebook"]["secret_present"])
            self.assertEqual(report["facebook"]["app_id"], "")
            self.assertIn("manual", report["manual_fallback"].lower())
            self.assertNotIn("approved", report["facebook"]["oauth_grant"])

    def test_guide_and_dashboard_mention_real_endpoint_and_current_limits(self):
        root = Path(__file__).resolve().parents[1]
        doc = (root / "docs/META-MCP-ONBOARDING.md").read_text()
        script = (root / "web/app.js").read_text()
        agents = (root / "AGENTS.md").read_text()
        self.assertIn("https://mcp.facebook.com/devtools", doc)
        self.assertIn("Meta developer setup", script)
        self.assertIn("meta_mcp_setup", agents)
        self.assertIn("coming soon", doc.lower())
        self.assertIn("manual", doc.lower())


if __name__ == "__main__":
    unittest.main()
