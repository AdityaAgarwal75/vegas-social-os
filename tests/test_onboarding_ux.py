"""Owner-facing pages remain useful before setup, after failure and after logout."""
import http.cookiejar
import json
from pathlib import Path
from vso import __version__
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from vso.engine import Engine
from vso.server import HTTPServer
from vso.store import Store
from vso.owner_auth import password_set

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args): return None

class OnboardingUXTests(unittest.TestCase):
    def test_release_versions_match(self):
        root=Path(__file__).resolve().parents[1]
        for file in ('plugin.json','agent-manifest.json'):
            self.assertEqual(json.loads((root/file).read_text())['version'], __version__)
        self.assertIn('version = "'+__version__+'"', (root/'pyproject.toml').read_text())

    def test_facebook_login_business_configuration_input_is_visible(self):
        root = Path(__file__).resolve().parents[1]
        js = (root/'web/app.js').read_text()
        self.assertIn("'config_id','Facebook Login for Business Configuration ID','text'",js)
        self.assertIn("Facebook Login for Business → Configurations",js)
        self.assertIn("f.onsubmit=async e=>",js)
        from vso.engine import Engine
        from vso.store import Store
        with tempfile.TemporaryDirectory() as directory:
            engine = Engine(Store(directory),"https://example.com")
            result = engine.accounts.config.save('facebook',{
                'client_id':'1234567890123456',
                'client_secret':'private-test-only-secret',
                'graph_version':'v25.0',
                'config_id':'1650387526437553',
            })
            self.assertEqual(result['config_id'],'1650387526437553')
            self.assertNotIn('private-test-only-secret',str(result))

    def test_public_help_locked_routes_and_failed_signin(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Store(directory); engine = Engine(store)
            server = HTTPServer(('127.0.0.1', 0), engine)
            base = engine.base = 'http://127.0.0.1:' + str(server.server_port)
            engine.accounts.base = base
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            browser = urllib.request.build_opener(NoRedirect, urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
            try:
                for route in ('/', '/dashboard', '/onboarding'):
                    with self.assertRaises(urllib.error.HTTPError) as response: browser.open(base + route)
                    self.assertEqual(response.exception.code, 303)
                    self.assertEqual(response.exception.headers['Location'], '/login')
                with self.assertRaises(urllib.error.HTTPError) as response: browser.open(base+'/api/control')
                self.assertEqual(response.exception.code,401)
                for route in ('/login', '/help', '/forgot-password'):
                    with browser.open(base + route) as response:
                        page = response.read().decode()
                        self.assertIn('lang="en"', page)
                        self.assertIn('/logo.svg', page)
                        self.assertIn('Skip to content', page)
                        self.assertNotIn('undefined', page)
                with browser.open(base + '/help') as response: self.assertIn(base + '/mcp', response.read().decode())
                for route, mime in (('/logo.svg','image/svg+xml'),('/auth.css','text/css'),('/auth.js','javascript'),('/control.css','text/css'),('/theme.js','javascript')):
                    with browser.open(base + route) as response: self.assertIn(mime, response.headers['Content-Type'])
                password_set(store, 'a valid private test password')
                request = urllib.request.Request(base+'/login', urllib.parse.urlencode({'password':'wrong','next':'/authorize?state=retained'}).encode(), {'Origin':base,'Content-Type':'application/x-www-form-urlencoded'})
                with self.assertRaises(urllib.error.HTTPError) as response: browser.open(request)
                self.assertEqual(response.exception.code, 401)
                body=response.exception.read().decode()
                self.assertIn('name="password"', body)
                self.assertIn('/forgot-password', body)
                self.assertIn('/authorize?state=retained', body)
                self.assertNotIn('value="wrong"', body)
                with browser.open(base+'/forgot-password') as response:
                    self.assertIn('--reset-password', response.read().decode())
                for _ in range(7):
                    with self.assertRaises(urllib.error.HTTPError) as response: browser.open(request)
                self.assertEqual(response.exception.code, 429)
                self.assertIn('text/html', response.exception.headers['Content-Type'])
                self.assertEqual(response.exception.headers['Retry-After'], '900')
                self.assertIn('Recover password', response.exception.read().decode())
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=3)
