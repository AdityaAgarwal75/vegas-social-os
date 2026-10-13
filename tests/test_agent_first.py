import copy
import http.cookiejar
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

from vso.bootstrap import CAPABILITIES, plan, verify_receipt
from vso.engine import Engine
from vso.server import HTTPServer
from vso.store import Store
from vso.supabase_store import SupabaseStore


class BootstrapTests(unittest.TestCase):
    def test_github_supabase_only_cannot_claim_browser_runtime(self):
        result = plan({'source_read': True, 'repository_write': True, 'supabase_manage': True})
        self.assertEqual(result['status'], 'connections_needed')
        self.assertIn('managed_app_host', {x['capability'] for x in result['blockers']})
        self.assertFalse(result['architecture']['local_pc_required'])
        self.assertFalse(result['architecture']['user_managed_vps_required'])
        self.assertTrue(all('terminal' in x['user_work'] for x in result['blockers']))

    def test_repo_creation_is_not_a_setup_prerequisite(self):
        flags = {k: True for k in CAPABILITIES}; flags['repository_write'] = False
        self.assertEqual(plan(flags)['status'], 'ready_for_agent_setup')

    def test_missing_native_images_is_not_substituted(self):
        flags = {k: True for k in CAPABILITIES}; flags['native_images'] = False
        self.assertIn('native_images', plan(flags)['creative_stage_blockers'])
        self.assertEqual(plan(flags)['status'],'ready_for_agent_setup')
        self.assertEqual(plan(flags)['architecture']['images'], 'ChatGPT native only')

    def test_capabilities_must_be_real_booleans(self):
        with self.assertRaises(ValueError): plan({'persistent_runtime': 'probably'})
        with self.assertRaises(ValueError): plan({'imaginary_cloud': True})

    def test_unverified_receipt_cannot_be_complete(self):
        receipt = {'dashboard_url':'https://example.com/dashboard','mcp_url':'https://example.com/mcp',
                   'source_commit':'a'*40,'health_verified':True,'supabase_verified':True,'runtime_persistent':True,
                   'browser_verified':False,'plugin_created':True,'plugin_connected':False}
        self.assertEqual(verify_receipt(receipt)['status'], 'setup_incomplete')
        receipt['mcp_url'] = 'https://another.example/mcp'
        with self.assertRaises(ValueError): verify_receipt(receipt)


class SupabaseStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.remote = {'revision':0, 'ciphertext':None, 'calls':0}
        remote = self.remote
        def request(instance, path, **kwargs):
            if path.startswith('/rest/v1/vso_installations'):
                return [] if remote['revision'] == 0 else [{'revision':remote['revision'],'ciphertext':remote['ciphertext']}]
            p = kwargs['payload']; remote['calls'] += 1
            if p['p_expected_revision'] != remote['revision']: raise ValueError('state_revision_conflict')
            remote['revision'] += 1; remote['ciphertext'] = p['p_ciphertext']
            return remote['revision']
        self.mock = patch.object(SupabaseStore, '_request', request)
        self.mock.start()
        self.store = SupabaseStore(self.tmp.name, 'https://testproject.supabase.co', 'test-server-key', '00000000-0000-0000-0000-000000000001')

    def tearDown(self): self.mock.stop(); self.tmp.cleanup()

    def test_encrypted_cloud_is_authoritative_across_reload(self):
        self.store.put('profile', 'owner', {'name':'Community operator'})
        self.store.secret('google', {'access_token':'private-example'})
        self.assertNotIn('Community operator', self.remote['ciphertext'])
        self.assertNotIn('private-example', self.remote['ciphertext'])
        second = SupabaseStore(self.tmp.name, 'https://testproject.supabase.co', 'test-server-key', self.store.installation_id)
        self.assertEqual(second.get('profile','owner')['name'], 'Community operator')
        self.assertEqual(second.secret('google')['access_token'], 'private-example')

    def test_read_does_not_write_new_revision(self):
        self.store.put('profile','owner',{'name':'Person'})
        revision = self.remote['revision']
        self.store.get('profile','owner')
        self.assertEqual(self.remote['revision'], revision)

    def test_network_failure_never_silently_falls_back(self):
        self.store.put('profile','owner',{'name':'Person'})
        with patch.object(self.store, '_load_cloud', side_effect=ValueError('offline')):
            with self.assertRaises(ValueError): self.store.get('profile','owner')

    def test_cas_conflict_is_not_retried(self):
        self.store.put('profile','owner',{'name':'Before'})
        calls=[]
        original=self.store._request
        def conflict(path, **kwargs):
            if path.startswith('/rest/v1/rpc'):
                calls.append(path); raise ValueError('state_revision_conflict')
            return original(path, **kwargs)
        with patch.object(self.store, '_request', side_effect=conflict):
            with self.assertRaises(ValueError): self.store.put('profile','owner',{'name':'After'})
        self.assertEqual(len(calls),1)
        self.assertEqual(self.store.get('profile','owner')['name'],'Before')


class ScopedFlowLoginTests(unittest.TestCase):
    def test_private_browser_ticket_does_not_grant_admin_or_other_account(self):
        with tempfile.TemporaryDirectory() as root:
            store=Store(root); engine=Engine(store)
            server=HTTPServer(('127.0.0.1',0),engine)
            base=f'http://127.0.0.1:{server.server_port}'
            engine.base=base
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            store.put('account','a'*32,{'id':'a'*32,'provider':'flow','status':'login_required'})
            token=store.ticket('flow-browser',{'account_id':'a'*32})
            opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            try:
                with opener.open(base+'/flow/login?ticket='+token) as response:
                    self.assertIn(b'Sign into Google Flow', response.read())
                with opener.open(base+'/flow/session') as response:
                    self.assertEqual(json.load(response)['account_id'],'a'*32)
                with self.assertRaises(urllib.error.HTTPError) as err: opener.open(base+'/api/state')
                self.assertEqual(err.exception.code,401)
                with self.assertRaises(urllib.error.HTTPError) as err: opener.open(base+'/flow/socket/'+'b'*32)
                self.assertEqual(err.exception.code,403)
                with self.assertRaises(urllib.error.HTTPError): opener.open(base+'/flow/login?ticket='+token)
            finally:
                server.shutdown();server.server_close();thread.join(timeout=2)


if __name__=='__main__': unittest.main()
