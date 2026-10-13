import base64
import concurrent.futures
import json
import os
from pathlib import Path
import tempfile
import unittest
import urllib.parse
from unittest.mock import patch

from vso import flow_service
from vso.engine import Engine
from vso.store import Store

class LocalFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        self.config=self.root/'services.json'; self.token=self.root/'token';self.token.write_text('private-control-token')
        self.config.write_text(json.dumps({'owner':{'port':8831,'token_file':str(self.token),'label':'Owner account','desktop_ws_port':6080}}))
        self.env=patch.dict(os.environ,{'VSO_FLOW_SERVICES':str(self.config)});self.env.start()
        self.e=Engine(Store(self.root/'data'),'https://owner.example')
        with patch('vso.flow_service.request',return_value={'flow':{'signedIn':True,'inProject':True,'credits_remaining':50}}):
            self.account=flow_service.sync(self.e)[0]
    def tearDown(self):self.env.stop();self.tmp.cleanup()
    def submit(self):return flow_service.image_request(self.e,self.account['id'],'A red paper boat','Nano Banana 2','1:1',0,'same-request')
    def test_import_has_no_token_path_or_secret_and_is_idempotent(self):
        with patch('vso.flow_service.request',return_value={'flow':{'signedIn':True,'inProject':True}}):
            again=flow_service.sync(self.e)[0]
        self.assertEqual(again['id'],self.account['id'])
        output=json.dumps(self.e.snapshot());self.assertNotIn(str(self.token),output);self.assertNotIn('private-control-token',output)
        self.assertEqual(len(self.e.store.all('account')),1)
    def test_concurrent_submission_runs_once_and_free_budget_is_preserved(self):
        def backend(config,method,payload):
            if method=='status':return {'jobs':[]}
            self.assertEqual(payload['scenes'][0]['max_credits'],0)
            self.assertEqual(payload['scenes'][0]['retries'],0)
            self.assertEqual(payload['scenes'][0]['variants'],1)
            return {'jobs':[{'id':'backend-one'}]}
        with patch('vso.flow_service.request',side_effect=backend) as request:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:jobs=list(pool.map(lambda _:self.submit(),range(2)))
        self.assertEqual(jobs[0]['id'],jobs[1]['id']);self.assertEqual(sum(c.args[1]=='generate' for c in request.call_args_list),1)
    def test_uncertain_submission_is_retained_without_retry(self):
        with patch('vso.flow_service.request',side_effect=[{'jobs':[]},ValueError('Interrupted')]) as request:
            self.assertEqual(self.submit()['status'],'unknown');self.assertEqual(self.submit()['status'],'unknown')
            self.assertEqual(request.call_count,2)
        with self.assertRaisesRegex(ValueError,'unresolved'):
            flow_service.image_request(self.e,self.account['id'],'Different','Nano Banana 2','1:1',0,'different')
    def test_exact_download_is_imported_and_never_regenerated(self):
        with patch('vso.flow_service.request',side_effect=[{'jobs':[]},{'jobs':[{'id':'backend-one'}]}]):job=self.submit()
        png=b'\x89PNG\r\n\x1a\nactual-download'
        with patch('vso.flow_service.request',side_effect=[{'jobs':[{'id':'unrelated','status':'done','files':['/wrong.png']},{'id':'backend-one','status':'done','files':['/exact.png'],'credits':0}]},png]) as request:
            done=flow_service.image_poll(self.e,job['id']);again=flow_service.image_poll(self.e,job['id'])
        self.assertEqual(done,again);self.assertEqual(done['quoted_credits'],0);self.assertEqual(request.call_args_list[1].kwargs['query'],{'path':'/exact.png'})
        asset=self.e.store.get('asset',done['asset_ids'][0]);self.assertEqual(asset['origin'],'flow');self.assertEqual(asset['size'],len(png))
    def test_operator_configuration_rejects_writable_file(self):
        self.config.chmod(0o666)
        with self.assertRaises(ValueError):flow_service.services()

class OAuthRoutingTests(unittest.TestCase):
    def test_exact_operator_callback_and_wrong_provider_fail_closed(self):
        with tempfile.TemporaryDirectory() as root,patch.dict(os.environ,{'VSO_YOUTUBE_REDIRECT_URI':'https://owner.example/api/social/callback/youtube'}):
            e=Engine(Store(root),'https://private.owner.example')
            e.accounts.config.save('google',{'client_id':'app','client_secret':'secret'})
            ticket=urllib.parse.parse_qs(urllib.parse.urlsplit(e.accounts.start('youtube','My channel')['url']).query)['ticket'][0]
            url=e.accounts.authorize(ticket)['redirect'];q=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            self.assertEqual(q['redirect_uri'],['https://owner.example/api/social/callback/youtube']);self.assertTrue(q['state'][0].startswith('vso_youtube_'))
            with self.assertRaisesRegex(ValueError,'mismatch'):e.accounts.callback('instagram',q['state'][0],'code')
            with patch('vso.accounts.net.request',side_effect=[({'access_token':'private','refresh_token':'private-refresh'},{}),({'items':[{'id':'owner-channel','snippet':{'title':'Mine'}}]}, {})]) as request:
                result=e.accounts.callback('youtube',q['state'][0],'code')
            self.assertEqual(request.call_args_list[0].kwargs['form']['redirect_uri'],q['redirect_uri'][0]);self.assertEqual(result['remote_id'],'owner-channel')
            self.assertNotIn('private-refresh',json.dumps(result))
