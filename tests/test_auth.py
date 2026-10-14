import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.parse
import urllib.request

from vso.engine import Engine
from vso.server import HTTPServer, pkce, valid_redirect
from vso.store import Store


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)

    def tearDown(self): self.tmp.cleanup()

    def test_ticket_single_use(self):
        t = self.store.ticket('connect', {'provider': 'flow'})
        self.assertEqual(self.store.consume(t, 'connect')['provider'], 'flow')
        with self.assertRaises(ValueError): self.store.consume(t, 'connect')

    def test_ticket_expiry_and_wrong_purpose(self):
        t = self.store.ticket('connect', {}, ttl=-1)
        with self.assertRaises(ValueError): self.store.consume(t, 'connect')
        t = self.store.ticket('pair', {})
        with self.assertRaises(ValueError): self.store.consume(t, 'connect')

    def test_pkce_reference_vector(self):
        self.assertEqual(pkce('dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk'), 'E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM')

    def test_redirect_validation(self):
        self.assertTrue(valid_redirect('https://chatgpt.com/callback'))
        self.assertTrue(valid_redirect('http://127.0.0.1:1234/callback'))
        for url in ('http://example.com', 'javascript:alert(1)', 'https://example.com/#token', 'https://a:b@example.com'):
            self.assertFalse(valid_redirect(url))

    def test_remote_mcp_oauth_and_origin_guard(self):
        engine = Engine(self.store)
        server = HTTPServer(('127.0.0.1', 0), engine)
        engine.base = f'http://127.0.0.1:{server.server_port}'
        engine.accounts.base = engine.base
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        base = engine.base
        def post(path, data, headers=None):
            req = urllib.request.Request(base+path, data=json.dumps(data).encode(), method='POST', headers={'Content-Type':'application/json', **(headers or {})})
            with urllib.request.urlopen(req) as r: return json.load(r)
        try:
            self.assertIn('tools', post('/mcp', {'id':1, 'method':'tools/list'})['result'])
            challenge=post('/mcp',{'id':2,'method':'tools/call','params':{'name':'doctor','arguments':{}}})
            self.assertTrue(challenge['result']['isError']);self.assertIn('mcp/www_authenticate',challenge['result']['_meta'])
            client = post('/register', {'client_name':'Test MCP', 'redirect_uris':['https://example.com/callback']})
            verifier = 'a'*43
            payload = {'client_id':client['client_id'], 'redirect_uri':'https://example.com/callback', 'code_challenge':pkce(verifier)}
            code = self.store.ticket('mcp-code', payload)
            token = post('/token', {'grant_type':'authorization_code', 'code':code, 'client_id':client['client_id'],
                                   'redirect_uri':payload['redirect_uri'], 'code_verifier':verifier, 'resource':base+'/mcp'})
            rpc = post('/mcp', {'jsonrpc':'2.0','id':1,'method':'tools/list'}, {'Authorization':'Bearer '+token['access_token']})
            self.assertIn('tools', rpc['result'])
            with self.assertRaises(urllib.error.HTTPError) as err:
                post('/mcp', {'id':2,'method':'tools/list'}, {'Authorization':'Bearer '+token['access_token'], 'Origin':'https://evil.example'})
            self.assertEqual(err.exception.code, 403)
            with self.assertRaises(urllib.error.HTTPError):
                post('/token', {'grant_type':'authorization_code', 'code':code, 'client_id':client['client_id'], 'redirect_uri':payload['redirect_uri'],'code_verifier':verifier})
            refreshed = post('/token', {'grant_type':'refresh_token', 'refresh_token':token['refresh_token'], 'client_id':client['client_id']})
            self.assertNotEqual(refreshed['access_token'], token['access_token'])
            with self.assertRaises(urllib.error.HTTPError):
                post('/token', {'grant_type':'refresh_token', 'refresh_token':token['refresh_token'], 'client_id':client['client_id']})
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=2)


if __name__ == '__main__': unittest.main()
