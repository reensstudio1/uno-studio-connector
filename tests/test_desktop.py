"""Configuration preservation and safe failure checks; no live settings touched."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

INSTALL = Path(__file__).resolve().parents[1] / 'install_desktop.py'

class DesktopInstall(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='uno-desktop-test-')
        self.home = Path(self.tmp.name)
        self.config = self.home / 'Library/Application Support/Claude/claude_desktop_config.json'
        self.config.parent.mkdir(parents=True)
    def tearDown(self):
        self.tmp.cleanup()
    def run_install(self, version='v1.1.0'):
        return subprocess.run([sys.executable, str(INSTALL), '--release', version], env=dict(os.environ, HOME=str(self.home)), capture_output=True, text=True)
    def test_preserve_backup_idempotence(self):
        before={'mcpServers':{'davinci-resolve':{'command':'/test/python','args':['server.py'],'env':{'KEEP':'yes'}}},'preferences':{'theme':'dark'}}
        raw=json.dumps(before).encode()
        self.config.write_bytes(raw)
        self.assertEqual(self.run_install().returncode,0)
        after=json.loads(self.config.read_text())
        self.assertEqual(after['preferences'], before['preferences'])
        self.assertEqual(after['mcpServers']['davinci-resolve'],before['mcpServers']['davinci-resolve'])
        backups=list((self.home/'.uno-studio-connector/backups').glob('*/claude_desktop_config.json'))
        self.assertEqual(len(backups),1)
        self.assertEqual(backups[0].read_bytes(),raw)
        installed=self.config.read_bytes()
        self.assertEqual(self.run_install().returncode,0)
        self.assertEqual(installed,self.config.read_bytes())
        self.assertTrue(Path(after['mcpServers']['uno-studio']['command']).is_file())
        self.assertTrue(Path(after['mcpServers']['uno-studio']['args'][0]).is_file())
    def test_new_user(self):
        self.assertEqual(self.run_install().returncode,0)
        self.assertEqual(list(json.loads(self.config.read_text())['mcpServers']),['uno-studio'])
    def test_corrupt_config_is_not_overwritten(self):
        for raw in [b'{bad',b'[]',b'{"mcpServers": []}']:
            self.config.write_bytes(raw)
            self.assertNotEqual(self.run_install().returncode,0)
            self.assertEqual(self.config.read_bytes(),raw)
    def test_unrelated_name_collision(self):
        raw=b'{"mcpServers":{"uno-studio":{"command":"unrelated"}}}'
        self.config.write_bytes(raw)
        self.assertNotEqual(self.run_install().returncode,0)
        self.assertEqual(self.config.read_bytes(),raw)
    def test_keep_explicit_root_and_preferences_on_update(self):
        entry={'command':'/old/python','args':['/old/uno_connector.py'],'env':{'UNO_STUDIO_ROOT':'/chosen/root'},'disabled':True}
        self.config.write_text(json.dumps({'mcpServers':{'uno-studio':entry}}))
        self.assertEqual(self.run_install().returncode,0)
        after=json.loads(self.config.read_text())['mcpServers']['uno-studio']
        self.assertEqual(after['env'],entry['env'])
        self.assertTrue(after['disabled'])
    def test_version_traversal_rejected(self):
        self.assertNotEqual(self.run_install('../../bad').returncode,0)
        self.assertFalse(self.config.exists())

if __name__=='__main__':unittest.main()
