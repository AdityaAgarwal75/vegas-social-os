"""Real local HTTP/SQLite/FFmpeg tests; provider/browser calls are not made."""
import base64
import hashlib
import io
import json
import os
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from vso import auth, events, media, tools, admin_broker as broker
from vso.engine import Engine
from vso.server import HTTPServer
from vso.store import Store

PNG=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a0LsAAAAASUVORK5CYII=')

class SecurityUpgrade(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name);self.engine=Engine(self.store,'https://owner.example')
    def tearDown(self):self.tmp.cleanup()
    def grant(self,scope='social:read social:write'):
        client=auth.register(self.store,{'redirect_uris':['https://chatgpt.com/callback']},'test')
        code=self.store.ticket('mcp-code',{'client_id':client['client_id'],'redirect_uri':'https://chatgpt.com/callback','code_challenge':auth.pkce('a'*43),'scope':scope})
        body={'grant_type':'authorization_code','client_id':client['client_id'],'code':code,'redirect_uri':'https://chatgpt.com/callback','code_verifier':'a'*43,'resource':self.engine.base+'/mcp'}
        return body,auth.token(self.store,self.engine.base,body)
    def test_bad_pkce_does_not_consume_code(self):
        c=auth.register(self.store,{'redirect_uris':['https://chatgpt.com/callback']},'test')
        code=self.store.ticket('mcp-code',{'client_id':c['client_id'],'redirect_uri':'https://chatgpt.com/callback','code_challenge':auth.pkce('a'*43)})
        b={'grant_type':'authorization_code','code':code,'client_id':c['client_id'],'redirect_uri':'https://chatgpt.com/callback','code_verifier':'b'*43}
        with self.assertRaises(ValueError):auth.token(self.store,self.engine.base,b)
        b['code_verifier']='a'*43;self.assertIn('access_token',auth.token(self.store,self.engine.base,b))
    def test_refresh_replay_revocation_audience_scopes(self):
        b,t=self.grant('social:read');p=auth.validate(self.store,self.engine.base,t['access_token'])
        self.assertTrue(auth.permits(p,'social:read'));self.assertFalse(auth.permits(p,'vps:admin'));self.assertFalse(auth.permits(p,'social:write'))
        self.assertIsNone(auth.validate(self.store,'https://another.example',t['access_token']))
        rb={'grant_type':'refresh_token','client_id':b['client_id'],'refresh_token':t['refresh_token']}
        with self.assertRaises(ValueError):auth.token(self.store,self.engine.base,{**rb,'scope':'vps:admin'})
        fresh=auth.token(self.store,self.engine.base,rb)
        with self.assertRaises(ValueError):auth.token(self.store,self.engine.base,rb)
        self.assertIsNone(auth.validate(self.store,self.engine.base,fresh['access_token']))
    def test_revoke_and_registration_limits(self):
        b,t=self.grant();auth.revoke(self.store,{'client_id':b['client_id'],'token':t['refresh_token']})
        self.assertIsNone(auth.validate(self.store,self.engine.base,t['access_token']))
        for _ in range(4):auth.register(self.store,{'redirect_uris':['https://chatgpt.com/callback']},'test')
        with self.assertRaises(auth.RateLimited):auth.register(self.store,{'redirect_uris':['https://chatgpt.com/callback']},'test')
    def test_all_tools_have_authorization_and_profile_identity(self):
        for t in tools.definitions(self.engine):
            self.assertEqual(t['securitySchemes'],t['_meta']['securitySchemes'])
            self.assertEqual(t['securitySchemes'][0]['type'],'oauth2')
        a=tools.call(self.engine,'get_profile',{});self.assertEqual(a,tools.call(Engine(Store(self.tmp.name)),'get_profile',{}))
    def transfer(self,data=PNG):
        r=media.prepare(self.engine,'reference.png','image/png',len(data),hashlib.sha256(data).hexdigest(),'native-test')
        return r,r['upload_url'].split('ticket=')[1]
    def test_actual_image_bytes_resumed_and_duplicate(self):
        r,t=self.transfer();n=20;total=len(PNG)
        media.receive(self.engine,r['id'],t,io.BytesIO(PNG[:n]),n,f'bytes 0-{n-1}/{total}')
        media.receive(self.engine,r['id'],t,io.BytesIO(PNG[:n]),n,f'bytes 0-{n-1}/{total}')
        out=media.receive(self.engine,r['id'],t,io.BytesIO(PNG[n:]),total-n,f'bytes {n}-{total-1}/{total}')
        self.assertEqual(out['status'],'completed');self.assertNotIn('capability_hash',out)
        self.assertEqual(self.engine.asset_path(out['asset_id']).read_bytes(),PNG)
        self.assertEqual(media.prepare(self.engine,'reference.png','image/png',total,hashlib.sha256(PNG).hexdigest(),'native-test')['asset_id'],out['asset_id'])
    def test_interrupted_expired_invalid_media(self):
        r,t=self.transfer();total=len(PNG)
        with self.assertRaises(ValueError):media.receive(self.engine,r['id'],t,io.BytesIO(PNG[:10]),20,f'bytes 0-19/{total}')
        self.assertEqual(self.store.get('transfer',r['id'])['offset'],10)
        with self.assertRaises(PermissionError):media.receive(self.engine,r['id'],'wrong',io.BytesIO(PNG),total,f'bytes 0-{total-1}/{total}')
        # A header-shaped file must fail actual decoding rather than masquerade as a native image.
        with self.assertRaises(ValueError):media.probe(self.store.root/'vault.key','image/png')
    def test_outbox_atomicity_and_dedup(self):
        with self.assertRaises(RuntimeError):
            with self.store.db() as db:
                self.store.write(db,'plan','p',{'status':'ready','channel_id':'c'});raise RuntimeError()
        self.assertEqual(self.store.all('event'),[])
        self.store.put('plan','p',{'status':'ready','channel_id':'c'});self.store.put('plan','p',{'status':'ready','channel_id':'c'})
        self.assertEqual(len(self.store.all('event')),1)
    def test_mocked_signed_webhook_delivery_and_unsubscribe(self):
        """Mocked callback only: proves signing/state, not a ChatGPT host continuation."""
        key='whsec_'+base64.b64encode(b'a'*32).decode();params={'name':'storyboard.approved','arguments':{},'delivery':{'mode':'webhook','url':'https://host.example/events','secret':key}}
        principal={'scope':'social:read events:subscribe','client_id':'client'};received=[]
        def receiver(url,raw,headers):
            data=json.loads(raw);self.assertEqual(headers['webhook-signature'],events.signature(key,headers['webhook-id'],headers['webhook-timestamp'],raw))
            received.append(data);return 200,json.dumps({'challenge':data.get('challenge')}).encode()
        with patch('vso.events.callback',side_effect=receiver):
            sub=events.subscribe(self.engine,principal,params)
            self.store.put('plan','p',{'status':'ready','channel_id':'c'});events.tick(self.engine);events.tick(self.engine)
            self.assertEqual(len(received),2);self.assertEqual(self.store.all('event-delivery')[0]['status'],'accepted')
            events.unsubscribe(self.engine,principal,params);self.assertFalse(events.active(self.engine,self.store.get('subscription',sub['id'])))
    def test_callback_private_address_rejected(self):
        for url in ['http://host.example','https://127.0.0.1','https://user:pass@host.example','https://host.example:123']:
            with self.assertRaises((ValueError,OSError)):events.callback(url,b'{}',{})
    def test_http_pre_auth_body_limit_and_rest_scope(self):
        server=HTTPServer(('127.0.0.1',0),self.engine);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            for path,status in [('/api/tool',b'401'),('/mcp',b'413')]:
                with socket.create_connection(server.server_address,timeout=2) as conn:
                    conn.sendall(f'POST {path} HTTP/1.0\r\nContent-Length: 999999999\r\n\r\n'.encode())
                    self.assertIn(status,conn.recv(1024).split(b'\r\n')[0])
        finally:server.shutdown();server.server_close();thread.join()

class BrokerSecurity(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.state=Path(self.tmp.name)/'broker';self.patch=patch.object(broker,'STATE',self.state);self.patch.start()
    def tearDown(self):self.patch.stop();self.tmp.cleanup()
    def test_approval_bound_to_exact_arguments_and_totp_single_use(self):
        secret=base64.b32encode(b'x'*20).decode();broker.put('settings','totp',{'secret':secret,'last_counter':0})
        a=broker.request('command',{'command':'true'},'test');self.assertEqual(a['status'],'awaiting_owner')
        with self.assertRaises(ValueError):broker.execute(a['id'])
        with self.assertRaises(ValueError):broker.request('command',{'command':'false'},'test')
        broker.approve(a['id'],broker.totp(secret,int(time.time()//30)))
        b=broker.request('command',{'command':'true'},'test2')
        with self.assertRaises(ValueError):broker.approve(b['id'],broker.totp(secret,int(time.time()//30)))
    def test_new_child_start_is_not_reconciled_as_abandoned(self):
        broker.put('job','new',{'id':'new','status':'starting','created_at':time.time()})
        self.assertEqual(broker.reconcile('new')['status'],'starting')
    def test_argument_injection_and_protected_paths(self):
        for unit in ['--help.service','x;id.service','x.service\n']:
            with self.assertRaises(ValueError):broker.service(unit)
        for p in ['/etc/shadow','/var/lib/flowlogin/profiles/a/Cookies','/tmp/../etc/passwd','/tmp/.env','/var/lib/vegas-social-os/vault.key']:
            with self.assertRaises(ValueError):broker.target(p,read=True)
        with self.assertRaises(ValueError):broker.validate('packages',{'names':['x;id'],'action':'install'})
    def test_safe_open_no_symlinks_and_private_files(self):
        root=Path(self.tmp.name);f=root/'public';f.write_text('hello');f.chmod(0o644)
        link=root/'link';link.symlink_to(f)
        with self.assertRaises(OSError):broker.safe_open(link)
        private=root/'private';private.write_text('private');private.chmod(0o600)
        with self.assertRaises(ValueError):broker.perform('file_read',{'path':str(private)})
        self.assertEqual(broker.perform('file_read',{'path':str(f)})['content'],'hello')
    def test_bounded_output_and_breakglass_suppression(self):
        r=broker.run_command(['/usr/bin/printf','token=abc123'],2,track=False);self.assertNotIn('abc123',r['stdout'])
        self.assertNotIn('private-cookie',broker.redact('{"cookie": "private-cookie"}'))
        r=broker.run_command(['/usr/bin/printf','privatevalue'],2,suppress=True,track=False);self.assertNotIn('privatevalue',r['stdout'])

if __name__=='__main__':unittest.main()
