"""Checks the repeatable self-hosted VPS distribution without changing the host."""
from pathlib import Path
import subprocess
import unittest
from vso.bootstrap import plan

ROOT = Path(__file__).resolve().parents[1]


class VPSBootstrapTests(unittest.TestCase):
    def test_install_shell_files_are_syntax_valid(self):
        for filename in ("install-vps.sh", "bootstrap-ubuntu.sh", "new-setup-link.sh", "install-flow-engine.sh"):
            with self.subTest(filename=filename):
                script = ROOT / "scripts" / filename
                self.assertTrue(script.exists())
                subprocess.run(["bash", "-n", str(script)], check=True)

    def test_vps_first_does_not_need_supabase_or_render(self):
        flags = {
            "source_read": True,
            "vps_manage": True,
            "persistent_volume": True,
            "https_route": True,
            "process_exec": True,
        }
        result = plan(flags)
        self.assertEqual(result["status"], "ready_for_agent_setup")
        self.assertEqual(result["mode"], "vps")
        self.assertEqual(result["architecture"]["state"], "SQLite")
        self.assertTrue(result["architecture"]["user_managed_vps_required"])
        self.assertNotIn("supabase_manage", {x["capability"] for x in result["blockers"]})

    def test_vps_installer_keeps_services_and_state_isolated(self):
        source = (ROOT / "scripts" / "install-vps.sh").read_text()
        self.assertIn("User=vegas-social", source)
        self.assertIn("VSO_STATE_BACKEND=sqlite", source)
        self.assertIn("ExecStart=", source)
        self.assertIn("127.0.0.1", source)
        self.assertIn("Caddy", source)
        self.assertIn("Source", source.title())  # independent checkout path
        self.assertNotIn("--no-sandbox", source)
        self.assertNotIn("SUPABASE_SERVER_KEY=", source)
        self.assertIn("chmod -R a+rX", source)

    def test_secrets_and_data_not_bundled_for_community(self):
        import json
        manifest = json.loads((ROOT / "agent-manifest.json").read_text())
        self.assertEqual(manifest["database"]["provider"], "SQLite")
        self.assertFalse(manifest["community"]["multi_tenant_saas"])
        self.assertFalse(manifest["community"]["maintainer_credentials_included"])
        self.assertFalse(manifest["community"]["flow_generation_live_verified"])


if __name__ == "__main__":
    unittest.main()
