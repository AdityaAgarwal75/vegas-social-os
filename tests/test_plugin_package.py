import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.package_plugin import package

class PluginPackageTests(unittest.TestCase):
    def test_owner_endpoint_and_craft_references_are_portable(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'plugin.zip';package('https://own.example/mcp',output)
            with zipfile.ZipFile(output) as z:
                names=set(z.namelist());prefix='vegas-social-os/'
                for p in ['skills/vegas-social-master/references/chatgpt-workstation.md','docs/CHATGPT-FIRST.md','docs/NEW-USER-JOURNEY.md','docs/FLOW-SKILL-INTEGRATION.md','third_party/flow-scripting/core/flow-orchestrator.md','third_party/flow-video-producer/references/pipeline.md','third_party/flow-scripting/LICENSE','third_party/flow-video-producer/LICENSE','BOOTSTRAP.md']:
                    self.assertIn(prefix+p,names)
                mcp=json.loads(z.read(prefix+'mcp.json'));self.assertEqual(mcp['mcpServers']['vegas-social-os']['url'],'https://own.example/mcp')
                self.assertFalse(any('/profiles/' in p or '/media/' in p or p.endswith('.env') for p in names))
    def test_credentials_or_pairing_urls_are_not_packaged(self):
        with tempfile.TemporaryDirectory() as directory:
            for url in ['https://user:secret@own.example/mcp','https://own.example/mcp?token=secret','https://own.example/pair?ticket=secret','http://own.example/mcp']:
                with self.assertRaises(ValueError):package(url,Path(directory)/'plugin.zip')
