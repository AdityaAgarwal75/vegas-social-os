import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from vso.engine import Engine
from vso.store import Store
from vso import flow_runtime, flow_service


class ManagedFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.e = Engine(Store(self.tmp.name))
        self.ident = 'd' * 32
        self.e.store.put('account', self.ident, {'id':self.ident,'provider':'flow','status':'login_required'})

    def tearDown(self):
        self.tmp.cleanup()

    def test_native_binding_uses_complete_owner_without_import_alias(self):
        config = {'port':8888,'token_file':'/private/token'}
        with patch('vso.flow_runtime.ensure',return_value=config) as ensure:
            account, actual = flow_service.binding(self.e,self.ident)
            self.assertEqual(actual,config)
            self.assertNotIn('service_alias',account)
            ensure.assert_called_once_with(self.e,self.ident)

    def test_missing_engine_never_spawns_or_falls_back_to_generation(self):
        with patch.dict(os.environ,{'VSO_FLOW_ENGINE_ROOT':''}),patch('vso.flow_runtime.subprocess.Popen') as spawn:
            with self.assertRaisesRegex(ValueError,'Complete Flow engine missing'):
                flow_runtime.ensure(self.e,self.ident)
            with self.assertRaisesRegex(ValueError,'legacy experimental generation is disabled'):
                self.e.flow('submit',self.ident,prompt='A boat')
            spawn.assert_not_called()

    def test_doctor_and_snapshot_report_dependency_without_private_paths(self):
        root=Path(self.tmp.name)/'dependency'
        (root/'dist').mkdir(parents=True)
        (root/'dist/server.js').write_text('')
        (root/'.vso-contract').write_text('test-contract')
        with patch.dict(os.environ,{'VSO_FLOW_ENGINE_ROOT':str(root)}):
            self.assertTrue(self.e.doctor()['flow_engine_installed'])
            state=self.e.snapshot()
            self.assertTrue(state['flow_engine_installed'])
            self.assertNotIn(str(root),json.dumps(state))

    def test_missing_native_browser_never_launches_another_chrome(self):
        root=Path(self.tmp.name)/'dependency'
        (root/'dist').mkdir(parents=True)
        (root/'dist/server.js').write_text('')
        (root/'.vso-contract').write_text('test-contract')
        with patch.dict(os.environ,{'VSO_FLOW_ENGINE_ROOT':str(root)}),patch('vso.flow_runtime.subprocess.Popen') as spawn:
            with self.assertRaisesRegex(ValueError,'private Google browser first'):
                flow_runtime.ensure(self.e,self.ident)
            spawn.assert_not_called()

    def test_stale_browser_mapping_never_attaches_to_an_unrelated_process(self):
        root=Path(self.tmp.name)/'dependency';(root/'dist').mkdir(parents=True)
        (root/'dist/server.js').write_text('');(root/'.vso-contract').write_text('test-contract')
        profile=self.e.store.root/'profiles'/self.ident;profile.mkdir(parents=True)
        (profile/'browser.json').write_text(json.dumps({'port':9439,'pid':os.getpid()}))
        with patch.dict(os.environ,{'VSO_FLOW_ENGINE_ROOT':str(root)}),patch('vso.flow_runtime.urllib.request.build_opener') as http,patch('vso.flow_runtime.subprocess.Popen') as spawn:
            with self.assertRaisesRegex(ValueError,'verify this account'):
                flow_runtime.ensure(self.e,self.ident)
            http.assert_not_called();spawn.assert_not_called()

    def test_missing_dependency_rejects_production_before_job_reservation(self):
        with patch.dict(os.environ,{'VSO_FLOW_ENGINE_ROOT':''}):
            with self.assertRaisesRegex(ValueError,'before reserving'):
                self.e.video_request('not-a-plan',0,self.ident,10,'missing-engine',{'model':'Omni 1.1 Flash','duration':4,'resolution':'360p','aspect_ratio':'9:16'})
            self.assertEqual(self.e.store.all('job'),[])

    def test_managed_account_inspection_uses_same_service_contract(self):
        result={'flow':{'signedIn':True,'inProject':True,'credits_remaining':50},'jobs':[]}
        with patch.dict(os.environ,{'VSO_FLOW_ENGINE_ROOT':'/installed'}),patch('vso.flow_service.binding',return_value=(self.e.store.get('account',self.ident),{})),patch('vso.flow_service.request',return_value=result) as api:
            actual=self.e.flow_inspect(self.ident)
            self.assertTrue(actual['workspace_ready'])
            self.assertEqual(actual['credits'],50)
            api.assert_called_once_with({},'status',{'detailed':True})
