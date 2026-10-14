"""Browser consent Origin policy and backward-compatible Caddy policy repair."""
import http.cookiejar
import importlib.util
import json
import re
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from vso.engine import Engine
from vso.server import HTTPServer, pkce
from vso.store import Store

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None

class OAuthOriginTests(unittest.TestCase):
    def test_caddy_repair(self):
        path = Path(__file__).resolve().parents[1] / "scripts/repair-caddy-referrer.py"
        spec = importlib.util.spec_from_file_location("oauth_caddy", path)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        other = "# BEGIN VSO other.example\nother.example {\n  header Referrer-Policy no-referrer\n}\n# END VSO other.example\n"
        for body in ("header Referrer-Policy no-referrer",
                     "header {\n Referrer-Policy no-referrer\n}"):
            old = other + "# BEGIN VSO this.example\nthis.example {\n " + body + "\n}\n# END VSO this.example\n"
            new = m.repair(old, "this.example")
            self.assertIn(other, new)
            self.assertIn("Referrer-Policy origin", new)
            self.assertEqual(m.repair(new, "this.example"), new)
        self.assertEqual(m.repair(other, "this.example"), other)

    def test_authorize_html_origin_and_consent_csrf(self):
        with tempfile.TemporaryDirectory() as d:
            store = Store(d)
            engine = Engine(store)
            server = HTTPServer(("127.0.0.1", 0), engine)
            engine.base = "http://127.0.0.1:" + str(server.server_port)
            engine.accounts.base = engine.base
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            jar = http.cookiejar.CookieJar()
            browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
            no_redirect = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirect)
            base = engine.base
            try:
                with browser.open(base + "/pair?ticket=" + store.ticket("pair", {})):
                    pass
                payload = {"client_name": "Browser consent regression",
                           "redirect_uris": ["https://example.org/callback"]}
                req = urllib.request.Request(base + "/register", json.dumps(payload).encode(),
                                             {"Content-Type": "application/json"})
                with browser.open(req) as response:
                    client = json.load(response)
                params = {"client_id": client["client_id"], "redirect_uri": payload["redirect_uris"][0],
                          "response_type": "code", "scope": "social:read social:write",
                          "code_challenge": pkce("v"*43), "code_challenge_method": "S256",
                          "resource": base + "/mcp", "state": "test"}
                with browser.open(base + "/authorize?" + urllib.parse.urlencode(params)) as response:
                    self.assertEqual(response.headers.get("Referrer-Policy"), "origin")
                    page = response.read().decode()
                ticket = re.search(r'name="ticket" value="([^"]+)"', page).group(1)
                def submit(origin):
                    return urllib.request.Request(
                        base + "/consent", urllib.parse.urlencode({"ticket": ticket}).encode(),
                        {"Content-Type": "application/x-www-form-urlencoded", "Origin": origin})
                for foreign in ("null", "https://evil.example"):
                    with self.assertRaises(urllib.error.HTTPError) as e:
                        no_redirect.open(submit(foreign))
                    self.assertEqual(e.exception.code, 403)
                with self.assertRaises(urllib.error.HTTPError) as e:
                    no_redirect.open(submit(base))
                self.assertEqual(e.exception.code, 303)
                self.assertTrue(e.exception.headers["Location"].startswith("https://example.org/callback?code="))
                with self.assertRaises(urllib.error.HTTPError) as e:
                    no_redirect.open(submit(base))
                self.assertEqual(e.exception.code, 409)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)
