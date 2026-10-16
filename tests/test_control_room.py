import base64
import concurrent.futures
import http.cookiejar
import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request
from unittest.mock import patch

from vso import automation, publishing, research, tools
from vso.engine import Engine
from vso.server import HTTPServer
from vso.store import Store

JPEG = b'\xff\xd8\xff' + b'test photo'
PNG = b'\x89PNG\r\n\x1a\n' + b'test cover'
MP4 = b'\x00\x00\x00\x18ftypisom' + b'test video'

class ControlRoomTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.store = Store(self.tmp.name)
        self.e = Engine(self.store, 'https://own.example')
        for provider in ('youtube','instagram','facebook'):
            self.store.put('account', provider, {'id':provider,'provider':provider,'remote_id':'123','name':'My channel','status':'connected'})
        self.jpeg = self.e.asset_import(base64.b64encode(JPEG).decode(),'image/jpeg')['id']
        self.mp4 = self.e.asset_import(base64.b64encode(MP4).decode(),'video/mp4')['id']
        self.png = self.e.asset_import(base64.b64encode(PNG).decode(),'image/png')['id']
        self.e.accounts.config.save('facebook', {'client_id':'app','client_secret':'my-private-secret','graph_version':'v26.0'})
        self.e.accounts.config.save('instagram', {'client_id':'ig-app','client_secret':'ig-private-secret','graph_version':'v26.0'})
    def tearDown(self): self.tmp.cleanup()
    def prepare(self, provider='youtube', assets=None, options=None, request='stable'):
        return publishing.prepare(self.e,provider,assets if assets is not None else [self.mp4],'Title','Caption',
            'private' if provider=='youtube' else 'public',options if options is not None else {'made_for_kids':False},request)
    def test_config_is_encrypted_and_redacted(self):
        response=self.e.accounts.config.public('facebook')
        self.assertTrue(response['configured']); self.assertNotIn('my-private-secret',json.dumps(response))
        self.assertNotIn('my-private-secret',json.dumps(tools.call(self.e,'connection_setup',{})))
        self.assertNotIn(b'my-private-secret',self.store.root.joinpath('state.sqlite').read_bytes())
        self.e.accounts.config.save('facebook',{'client_id':'app','client_secret':''})
        self.assertTrue(self.e.accounts.config.public('facebook')['secret_present'])
    def test_facebook_login_is_separate_and_state_bound(self):
        r=self.e.accounts.start('facebook','Pages'); ticket=urllib.parse.parse_qs(urllib.parse.urlsplit(r['url']).query)['ticket'][0]
        url=self.e.accounts.authorize(ticket)['redirect']; q=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        self.assertEqual(q['redirect_uri'],['https://own.example/callback/facebook'])
        self.assertIn('instagram_manage_contents',q['scope'][0])
        with self.assertRaises(ValueError): self.e.accounts.callback('instagram',q['state'][0],'code')
    def test_facebook_discovers_pages_and_never_returns_tokens(self):
        r=self.e.accounts.start('facebook','Pages'); ticket=urllib.parse.parse_qs(urllib.parse.urlsplit(r['url']).query)['ticket'][0]
        q=urllib.parse.parse_qs(urllib.parse.urlsplit(self.e.accounts.authorize(ticket)['redirect']).query)
        responses=[({'access_token':'user-short'},{}),({'access_token':'user-long','expires_in':10000},{}),
            ({'data':[{'permission':p,'status':'granted'} for p in ['pages_show_list','pages_read_engagement','instagram_basic','instagram_manage_contents']]},{}),
            ({'data':[{'id':'111','name':'Page one','access_token':'page-secret','tasks':['CREATE_CONTENT'],'instagram_business_account':{'id':'17841425239410984','username':'untamedplot'}},
                      {'id':'222','name':'Read only','access_token':'other-secret','tasks':['ANALYZE']}]},{})]
        with patch('vso.accounts.net.request',side_effect=responses): result=self.e.accounts.callback('facebook',q['state'][0],'code')
        self.assertEqual(len(result['accounts']),1); self.assertNotIn('page-secret',json.dumps(result))
        self.assertEqual(result['accounts'][0]['remote_id'],'111')
        self.assertEqual(result['accounts'][0]['linked_instagram_id'],'17841425239410984')
    def test_missing_facebook_scope_does_not_connect(self):
        with patch('vso.accounts.net.request',side_effect=[({'access_token':'a'},{}),({'access_token':'b'},{}),({'data':[]},{})]):
            with self.assertRaisesRegex(ValueError,'missing'):self.e.accounts.facebook_callback({'label':'Page'},self.e.accounts.config.get('facebook'),{})
    def test_post_request_id_cannot_be_reused_for_different_copy(self):
        a=self.prepare(); b=self.prepare(); self.assertEqual(a['id'],b['id'])
        with self.assertRaises(ValueError): publishing.prepare(self.e,'youtube',[self.mp4],'Other','Caption','private',{'made_for_kids':False},'stable')
    def test_platform_constraints(self):
        with self.assertRaises(ValueError):self.prepare(options={})
        with self.assertRaises(ValueError):self.prepare('instagram',[self.png],{})
        with self.assertRaises(ValueError):self.prepare('facebook',[self.mp4,self.jpeg],{})
        with self.assertRaises(ValueError):self.prepare('facebook',[self.jpeg],{'thumbnail_id':self.jpeg})
        self.assertEqual(self.prepare('instagram',[self.jpeg],{},'photo')['status'],'review')
        self.assertEqual(self.prepare('facebook',[],{},'text')['status'],'review')
    def test_concurrent_execute_uploads_once(self):
        p=self.prepare();self.e.publish_approve(p['id'])
        with patch.object(self.e.accounts,'token',return_value='token'),patch('vso.publishing.youtube',side_effect=lambda e,p,a,t:p.update(status='published',remote_id='v')) as upload:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(lambda _:publishing.execute(self.e,p['id']),range(2)))
            self.assertEqual(upload.call_count,1)
    def test_unknown_write_never_retries(self):
        p=self.prepare();self.e.publish_approve(p['id'])
        with patch.object(self.e.accounts,'token',return_value='token'),patch('vso.publishing.youtube',side_effect=ValueError('failed')) as upload:
            a=publishing.execute(self.e,p['id']); b=publishing.execute(self.e,p['id'])
            self.assertEqual(a['status'],'unknown');self.assertEqual(b['status'],'unknown');self.assertEqual(upload.call_count,1)
    def test_cover_failure_keeps_uploaded_video(self):
        p=self.prepare(options={'made_for_kids':False,'thumbnail_id':self.png}); self.e.publish_approve(p['id'])
        with patch.object(self.e.accounts,'token',return_value='token'),patch('vso.publishing.net.request',side_effect=[({}, {'Location':'https://www.googleapis.com/upload/test'}),({'id':'video'},{}),ValueError('cover denied')]) as request:
            result=publishing.execute(self.e,p['id']);self.assertEqual(result['status'],'published');self.assertEqual(result['thumbnail_status'],'failed')
            publishing.execute(self.e,p['id']);self.assertEqual(request.call_count,3)
    def test_carousel_child_processing_precedes_parent_and_publish(self):
        p=self.prepare('instagram',[self.jpeg,self.jpeg],{});self.e.publish_approve(p['id'])
        with patch.object(self.e.accounts,'token',return_value='token'),patch('vso.publishing.net.request',side_effect=[({'id':'c1'},{}),({'id':'c2'},{}),({'status_code':'IN_PROGRESS'},{}),({'status_code':'FINISHED'},{}),({'status_code':'FINISHED'},{}),({'status_code':'FINISHED'},{}),({'id':'parent'},{}),({'status_code':'FINISHED'},{}),({'id':'published'}, {})]):
            self.assertEqual(publishing.execute(self.e,p['id'])['status'],'children_processing')
            self.assertEqual(publishing.poll(self.e,p['id'])['status'],'children_processing')
            self.assertEqual(publishing.poll(self.e,p['id'])['status'],'processing')
            self.assertEqual(publishing.poll(self.e,p['id'])['status'],'published')
    def test_exact_approved_schedule_and_cancel(self):
        from datetime import datetime, timezone
        when=datetime.fromtimestamp(time.time()+100,timezone.utc).isoformat()
        p=self.prepare(options={'made_for_kids':False,'schedule_at':when})
        with self.assertRaises(ValueError):publishing.schedule(self.e,p['id'],when)
        self.e.publish_approve(p['id'])
        with self.assertRaises(ValueError):publishing.schedule(self.e,p['id'],datetime.fromtimestamp(time.time()+200,timezone.utc).isoformat())
        publishing.schedule(self.e,p['id'],when);publishing.cancel(self.e,p['id'])
        with patch('vso.publishing.execute') as execute:automation.tick(self.e);execute.assert_not_called()
    def test_overdue_schedule_needs_new_review(self):
        p=self.prepare();self.e.publish_approve(p['id']);p=self.store.get('publication',p['id'])
        p.update(status='scheduled',scheduled_at=time.time()-4000);self.store.put('publication',p['id'],p)
        with patch('vso.publishing.execute') as execute:automation.tick(self.e);execute.assert_not_called()
        self.assertEqual(self.store.get('publication',p['id'])['status'],'missed')
    def test_research_blocks_metadata_and_dns_rebinding(self):
        for ips in [['169.254.169.254'],['127.0.0.1'],['8.8.8.8','10.0.0.1']]:
            with patch('vso.research.socket.getaddrinfo',return_value=[(2,1,6,'',(ip,443)) for ip in ips]):
                with self.assertRaises(ValueError):research.public_address('example.com')
    def test_research_respects_robots(self):
        with patch('vso.research.get',return_value=(200,{},b'User-agent: *\nDisallow: /')) as get:
            with self.assertRaisesRegex(ValueError,'robots'):research.fetch(self.e,'https://example.com/private')
            self.assertEqual(get.call_count,1)
    def test_pause_daily_briefs(self):
        channel=self.e.channel_save('Brand','Niche')
        tools.call(self.e,'schedule_daily',{'hour':0,'timezone':'UTC','channel_ids':[channel['id']]})
        automation.pause(self.e);self.assertEqual(tools.call(self.e,'morning_queue',{}),[])
    def test_youtube_resume_reuses_original_session(self):
        p=self.prepare();self.e.publish_approve(p['id']);p=self.store.get('publication',p['id'])
        p['status']='unknown';self.store.put('publication',p['id'],p)
        self.store.secret('upload:'+p['id'],{'url':'https://www.googleapis.com/upload/same-session'})
        with patch.object(self.e.accounts,'token',return_value='token'),patch('vso.publishing.net.request',side_effect=[({}, {':status':'308','Range':'bytes=0-3'}),({'id':'same-video'}, {})]) as request:
            self.assertEqual(publishing.reconcile(self.e,p['id'])['uploaded_bytes'],4)
            result=publishing.resume(self.e,p['id']);self.assertEqual(result['remote_id'],'same-video')
            self.assertEqual(request.call_args_list[0].args[0],request.call_args_list[1].args[0])
            self.assertIn('Content-Range',request.call_args_list[1].kwargs['headers'])

    def test_config_http_requires_owner_session_and_rejects_cross_origin(self):
        server=HTTPServer(('127.0.0.1',0),self.e);base='http://127.0.0.1:'+str(server.server_port)
        self.e.base=base
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        body=json.dumps({'provider':'google','values':{'client_id':'app','client_secret':'testsecret'}}).encode()
        def req(origin):return urllib.request.Request(base+'/api/config',data=body,headers={'Content-Type':'application/json','Origin':origin})
        opener=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        try:
            with self.assertRaises(urllib.error.HTTPError) as error:opener.open(req(base))
            self.assertEqual(error.exception.code,401)
            opener.open(base+'/pair?ticket='+self.store.ticket('pair',{})).close()
            with self.assertRaises(urllib.error.HTTPError) as error:opener.open(req('https://attacker.example'))
            self.assertEqual(error.exception.code,403)
            with opener.open(req(base)) as response:self.assertNotIn('testsecret',response.read().decode())
        finally:server.shutdown();server.server_close();thread.join(timeout=2)

if __name__=='__main__':unittest.main()
