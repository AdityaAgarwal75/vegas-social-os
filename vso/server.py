import base64
import hashlib
import html
import json
import secrets
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import tools


def pkce(verifier):
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()


def valid_redirect(url):
    p = urllib.parse.urlsplit(url)
    return not p.username and not p.password and not p.fragment and (
        (p.scheme == "https" and bool(p.hostname)) or
        (p.scheme == "http" and p.hostname in ("127.0.0.1", "localhost", "::1")))


class HTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, engine):
        self.engine = engine
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "VegasSocialOS/0.1"

    @property
    def engine(self): return self.server.engine
    @property
    def store(self): return self.engine.store
    @property
    def base(self): return self.engine.base

    def log_message(self, format, *args):
        # Never log request query strings, authorization codes, tickets or tokens.
        import sys
        sys.stderr.write(f"{self.command} {urllib.parse.urlsplit(self.path).path}\n")

    def send(self, data, status=200, content_type="application/json", headers=None):
        body = json.dumps(data).encode() if content_type == "application/json" else data.encode() if isinstance(data, str) else data
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        for k, v in (headers or {}).items(): self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD": self.wfile.write(body)

    def page(self, title, body, status=200):
        self.send(f'<!doctype html><html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><link rel="stylesheet" href="/style.css"><title>{html.escape(title)}</title><main class="login"><p class="eyebrow">VEGAS / SOCIAL OS</p><h1>{html.escape(title)}</h1>{body}</main></html>', status, "text/html")

    def redirect(self, url, headers=None):
        self.send("", 303, "text/plain", {"Location": url, **(headers or {})})

    def parse(self):
        parts = urllib.parse.urlsplit(self.path)
        return parts.path, {k: v[0] for k, v in urllib.parse.parse_qs(parts.query).items()}

    def body(self):
        length = int(self.headers.get("Content-Length", "0"))
        if not 0 < length <= 90_000_000: raise ValueError("Missing or oversized request body")
        data = self.rfile.read(length)
        if "application/x-www-form-urlencoded" in self.headers.get("Content-Type", ""):
            return {k: v[0] for k, v in urllib.parse.parse_qs(data.decode()).items()}
        return json.loads(data)

    def session(self):
        from http.cookies import SimpleCookie
        c = SimpleCookie()
        try: c.load(self.headers.get("Cookie", ""))
        except Exception: return None
        if "vso_session" not in c: return None
        try:
            session = self.store.get("session", self.store.digest(c["vso_session"].value))
            return session if session["expires"] > time.time() else None
        except ValueError: return None

    def authorized(self):
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            try:
                record = self.store.get("access", self.store.digest(auth[7:]))
                return record["expires"] > time.time() and record["resource"] == self.base + "/mcp"
            except ValueError: return False
        return self.session() is not None

    def origin_ok(self):
        origin = self.headers.get("Origin")
        return not origin or origin == self.base

    def guard(self):
        if not self.origin_ok():
            self.send({"error": "Origin rejected"}, 403); return False
        if not self.authorized():
            self.send({"error": "Authentication required"}, 401, headers={
                "WWW-Authenticate": 'Bearer resource_metadata="' + self.base + '/.well-known/oauth-protected-resource/mcp"'})
            return False
        return True

    def do_GET(self):
        try: self.get()
        except ValueError as e: self.page("Action unavailable", "<p>" + html.escape(str(e)) + "</p>", 400)
        except Exception: self.page("Action unavailable", "<p>Operation failed. Check installation settings; credentials are never displayed.</p>", 400)

    def do_HEAD(self):
        path, _ = self.parse()
        if path in ("/media", "/health") or path.startswith("/asset/"):
            self.do_GET()
        else:
            self.send("", 405, "text/plain")

    def get(self):
        path, q = self.parse()
        if path == "/health": return self.send({"ok": True, "version": "0.1.0"})
        if path in ("/", "/dashboard", "/app.js", "/style.css"):
            file = {"/": "index.html", "/dashboard": "index.html", "/app.js": "app.js", "/style.css": "style.css"}[path]
            mime = "application/javascript" if file.endswith(".js") else "text/css" if file.endswith(".css") else "text/html"
            return self.send((Path(__file__).parent.parent / "web" / file).read_bytes(), content_type=mime)
        if path == "/pair":
            self.store.consume(q.get("ticket", ""), "pair")
            token = secrets.token_urlsafe(32)
            self.store.put("session", self.store.digest(token), {"expires": time.time() + 8 * 3600})
            secure = "; Secure" if self.base.startswith("https://") else ""
            return self.redirect("/dashboard", {"Set-Cookie": "vso_session=" + token + "; HttpOnly; SameSite=Lax; Path=/; Max-Age=28800" + secure})
        if path == "/connect":
            result = self.engine.accounts.authorize(q.get("ticket", ""))
            if "redirect" in result: return self.redirect(result["redirect"])
            a = result["flow"]
            return self.page("Connect Google Flow", "<p>This account has its own browser profile on your worker computer.</p><p>Return to ChatGPT and ask it to open the dedicated Flow login window. You enter your password and 2FA directly into Google.</p><p>Account label: " + html.escape(a["label"]) + "</p><p>No session is exported from your everyday browser.</p>")
        if path.startswith("/callback/"):
            a = self.engine.accounts.callback(path.rsplit("/", 1)[1], q.get("state", ""), q.get("code", ""))
            return self.page("Account connected", "<p>" + html.escape(a["name"]) + " is connected to this installation. Return to ChatGPT to continue.</p>")
        if path in ("/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/mcp"):
            return self.send({"resource": self.base + "/mcp", "authorization_servers": [self.base], "scopes_supported": ["social:manage"]})
        if path == "/.well-known/oauth-authorization-server":
            return self.send({"issuer": self.base, "authorization_endpoint": self.base + "/authorize",
                              "token_endpoint": self.base + "/token", "registration_endpoint": self.base + "/register",
                              "response_types_supported": ["code"], "grant_types_supported": ["authorization_code", "refresh_token"],
                              "token_endpoint_auth_methods_supported": ["none"], "code_challenge_methods_supported": ["S256"],
                              "scopes_supported": ["social:manage"]})
        if path == "/authorize":
            if not self.session(): return self.page("Open your setup link first", "<p>Run <code>python -m vso setup</code> on the installation computer. Open the private setup link in this browser, then retry connecting the plugin.</p>", 401)
            client = self.store.get("oauth-client", q.get("client_id", ""))
            if q.get("redirect_uri") not in client["redirect_uris"] or q.get("response_type") != "code" or q.get("code_challenge_method") != "S256" or len(q.get("code_challenge", "")) != 43 or q.get("resource") != self.base + "/mcp":
                raise ValueError("Invalid OAuth client, PKCE challenge or resource")
            if q.get("scope", "social:manage") != "social:manage": raise ValueError("Unsupported scope")
            ticket = self.store.ticket("consent", q)
            return self.page("Authorize this plugin", "<p>This client can manage the accounts and productions in this installation. It does not receive provider passwords or tokens.</p><p>Client: " + html.escape(client["name"]) + "</p><p>Return address: " + html.escape(q["redirect_uri"]) + '</p><form action="/consent" method="post"><input type="hidden" name="ticket" value="' + ticket + '"><button type="submit">Authorize Vegas Social OS</button></form>')
        if path == "/api/state":
            if not self.guard(): return
            return self.send({"doctor": self.engine.doctor(), **self.engine.snapshot()})
        if path == "/media":
            record = self.store.get("media-link", self.store.digest(q.get("ticket", "")))
            if record["expires"] < time.time(): raise ValueError("Media link expired")
            return self.media(record["asset_id"])
        if path.startswith("/asset/"):
            if not self.guard(): return
            return self.media(path.rsplit("/", 1)[1])
        if path == "/mcp":
            if not self.guard(): return
            return self.send({"error": "SSE subscriptions not offered; use POST"}, 405, headers={"Allow": "POST"})
        self.send({"error": "Not found"}, 404)

    def media(self, ident):
        asset = self.store.get("asset", ident)
        file = self.engine.asset_path(ident)
        size = file.stat().st_size
        start, end = 0, size - 1
        range_header = self.headers.get("Range")
        status, headers = 200, {"Accept-Ranges": "bytes"}
        if range_header:
            import re
            m = re.fullmatch(r"bytes=(\d+)-(\d*)", range_header)
            if not m: return self.send("", 416, "text/plain", {"Content-Range": f"bytes */{size}"})
            start, end = int(m[1]), min(int(m[2]) if m[2] else size - 1, size - 1)
            if start > end: return self.send("", 416, "text/plain", {"Content-Range": f"bytes */{size}"})
            status = 206
            headers["Content-Range"] = f"bytes {start}-{end}/{size}"
        with file.open("rb") as f:
            f.seek(start)
            self.send(f.read(end - start + 1), status, asset["media_type"], headers)

    def do_POST(self):
        try: self.post()
        except ValueError as e: self.send({"error": str(e)}, 400)
        except Exception: self.send({"error": "Operation failed; check installation settings"}, 400)

    def post(self):
        path, q = self.parse()
        if not self.origin_ok(): return self.send({"error": "Origin rejected"}, 403)
        body = self.body()
        if path == "/register":
            redirects = body.get("redirect_uris", [])
            if not isinstance(redirects, list) or not 1 <= len(redirects) <= 10 or any(not isinstance(x, str) or not valid_redirect(x) for x in redirects):
                raise ValueError("Use exact HTTPS or loopback redirect URIs")
            if len(self.store.all("oauth-client")) >= 100: raise ValueError("Client registration limit reached")
            ident = secrets.token_urlsafe(24)
            self.store.put("oauth-client", ident, {"redirect_uris": redirects, "name": str(body.get("client_name", "MCP client"))[:100]})
            return self.send({"client_id": ident, "redirect_uris": redirects, "token_endpoint_auth_method": "none",
                              "grant_types": ["authorization_code", "refresh_token"], "response_types": ["code"]}, 201)
        if path == "/consent":
            if not self.session(): raise ValueError("Sign into this installation before consent")
            data = self.store.consume(body.get("ticket", ""), "consent")
            code = self.store.ticket("mcp-code", data, ttl=120)
            sep = "&" if "?" in data["redirect_uri"] else "?"
            return self.redirect(data["redirect_uri"] + sep + urllib.parse.urlencode({"code": code, "state": data.get("state", "")}))
        if path == "/token":
            grant = body.get("grant_type")
            if grant == "authorization_code":
                data = self.store.consume(body.get("code", ""), "mcp-code")
                if data["client_id"] != body.get("client_id") or data["redirect_uri"] != body.get("redirect_uri") or pkce(body.get("code_verifier", "")) != data["code_challenge"]:
                    raise ValueError("Invalid authorization code or PKCE verifier")
            elif grant == "refresh_token":
                data = self.store.consume(body.get("refresh_token", ""), "mcp-refresh")
                if data["client_id"] != body.get("client_id"): raise ValueError("Client mismatch")
            else: raise ValueError("Unsupported grant type")
            if body.get("resource", self.base + "/mcp") != self.base + "/mcp": raise ValueError("Resource mismatch")
            access = secrets.token_urlsafe(32)
            self.store.put("access", self.store.digest(access), {"expires": time.time() + 3600, "resource": self.base + "/mcp", "client_id": data["client_id"]})
            refresh = self.store.ticket("mcp-refresh", {"client_id": data["client_id"]}, ttl=30 * 86400)
            return self.send({"access_token": access, "token_type": "Bearer", "expires_in": 3600, "refresh_token": refresh, "scope": "social:manage"})
        if path in ("/mcp", "/api/tool"):
            if not self.guard(): return
            if path == "/api/tool":
                return self.send(tools.call(self.engine, body.get("name"), body.get("arguments", {})))
            result = tools.rpc(self.engine, body)
            return self.send(result) if result is not None else self.send("", 202, "text/plain")
        self.send({"error": "Not found"}, 404)
