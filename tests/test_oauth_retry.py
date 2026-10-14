"""No repeated setup or authorization ticket may cause confusing unhandled JSON errors."""
import http.cookiejar
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request

from vso.engine import Engine
from vso.server import HTTPServer
from vso.store import Store


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args): return None


class OAuthReplayTests(unittest.TestCase):
    def test_owner_pair_repeat_and_consent_duplicate_are_safe(self):
        with tempfile.TemporaryDirectory() as d:
            store = Store(d)
            engine = Engine(store)
            server = HTTPServer(('127.0.0.1', 0), engine)
            engine.base = 'http://127.0.0.1:' + str(server.server_port)
            engine.accounts.base = engine.base
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = engine.base
            jar = http.cookiejar.CookieJar()
            browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirect)
            anonymous = urllib.request.build_opener(NoRedirect)
            try:
                setup = base + '/pair?ticket=' + store.ticket('pair', {})
                with self.assertRaises(urllib.error.HTTPError) as e:
                    browser.open(setup)
                self.assertEqual(e.exception.code, 303)
                self.assertEqual(e.exception.headers['Location'], '/onboarding')
                with self.assertRaises(urllib.error.HTTPError) as e:
                    browser.open(setup)
                self.assertEqual(e.exception.code, 303)
                with self.assertRaises(urllib.error.HTTPError) as e:
                    anonymous.open(setup)
                self.assertEqual(e.exception.code, 410)
                self.assertIn('Setup link expired', e.exception.read().decode())
                with browser.open(base+'/oauth-consent.js') as r:
                    self.assertIn('javascript', r.headers.get('Content-Type'))
                    self.assertIn(b'disabled = true', r.read())
                ticket = store.ticket('consent', {'redirect_uri':'https://chatgpt.com/testcallback', 'state':'ok'})
                def submit():
                    return urllib.request.Request(base+'/consent',method='POST',
                        data=urllib.parse.urlencode({'ticket':ticket}).encode(),
                        headers={'Origin':base, 'Content-Type':'application/x-www-form-urlencoded'})
                with self.assertRaises(urllib.error.HTTPError) as e:
                    browser.open(submit())
                self.assertEqual(e.exception.code, 303)
                self.assertTrue(e.exception.headers['Location'].startswith('https://chatgpt.com/testcallback?code='))
                with self.assertRaises(urllib.error.HTTPError) as e:
                    browser.open(submit())
                self.assertEqual(e.exception.code, 409)
                self.assertIn('already submitted', e.exception.read().decode())
                with store.db() as db:
                    self.assertIn('mcp-code', [x[0] for x in db.execute('SELECT DISTINCT kind FROM tickets')])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=2)
