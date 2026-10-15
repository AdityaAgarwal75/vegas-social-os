"""A server-issued recovery link resets a password without granting API access."""
import http.cookiejar
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from vso.engine import Engine
from vso.server import HTTPServer
from vso.store import Store
from vso.owner_auth import password_set, password_check

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args): return None

class OwnerRecoveryTests(unittest.TestCase):
    def test_reset_link_does_not_clear_password_or_grant_dashboard_access(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory)
            old, new = 'old private test password', 'new private test password'
            password_set(store, old)
            store.put('session', 'old-session', {'expires': 9999999999})
            ticket = store.ticket('owner-reset', {}, ttl=600)
            unused = store.ticket('owner-reset', {}, ttl=600)
            self.assertTrue(password_check(store, old, 'local'))
            engine = Engine(store)
            server = HTTPServer(('127.0.0.1', 0), engine)
            base = engine.base = 'http://127.0.0.1:' + str(server.server_port)
            engine.accounts.base = base
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), NoRedirect)
            try:
                with self.assertRaises(urllib.error.HTTPError) as response:
                    browser.open(base + '/password')
                self.assertEqual(response.exception.code, 401)
                with self.assertRaises(urllib.error.HTTPError) as response:
                    browser.open(base + '/owner-recovery?ticket=' + ticket)
                self.assertEqual(response.exception.code, 303)
                self.assertEqual(response.exception.headers['Location'], '/password')
                with self.assertRaises(urllib.error.HTTPError) as response:
                    browser.open(base + '/owner-recovery?ticket=' + ticket)
                self.assertEqual(response.exception.code, 410)
                with browser.open(base + '/password') as response:
                    self.assertNotIn('name="current"', response.read().decode())
                with self.assertRaises(urllib.error.HTTPError) as response:
                    browser.open(base + '/api/state')
                self.assertEqual(response.exception.code, 401)
                def reset(password, confirmation):
                    return urllib.request.Request(base + '/password', urllib.parse.urlencode(
                        {'password': password, 'confirmation': confirmation}).encode(),
                        {'Content-Type': 'application/x-www-form-urlencoded', 'Origin': base})
                with self.assertRaises(urllib.error.HTTPError) as response:
                    browser.open(reset(new, 'mismatch'))
                self.assertEqual(response.exception.code, 400)
                with self.assertRaises(urllib.error.HTTPError) as response:
                    browser.open(reset(new, new))
                self.assertEqual(response.exception.code, 303)
                self.assertEqual(response.exception.headers['Location'], '/login')
                self.assertTrue(password_check(store, new, 'local'))
                self.assertFalse(password_check(store, old, 'local'))
                self.assertEqual(store.all('session'), [])
                self.assertEqual(store.all('password-reset-session'), [])
                with self.assertRaises(ValueError): store.consume(unused, 'owner-reset')
                with self.assertRaises(urllib.error.HTTPError) as response:
                    browser.open(reset(old, old))
                self.assertEqual(response.exception.code, 401)
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=3)
