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
    server_version = "VegasSocialOS/0.6"

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
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' blob:; frame-src 'self'; frame-ancestors " + ("'self'" if urllib.parse.urlsplit(self.path).path.startswith("/flow/") else "'none'") + "; base-uri 'none'; form-action 'self'")
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

    def flow_session(self):
        from http.cookies import SimpleCookie
        c = SimpleCookie()
        try:
            c.load(self.headers.get("Cookie", ""))
            if "vso_flow" not in c: return None
            data = self.store.get("flow-session", self.store.digest(c["vso_flow"].value))
            return data if data["expires"] > time.time() else None
        except Exception: return None

    def flow_guard(self):
        session = self.flow_session()
        if not self.origin_ok() or not session:
            self.send({"error": "Private browser login expired or unauthorized"}, 401)
            return None
        try: self.store.get("account", session["account_id"])
        except ValueError:
            self.send({"error": "Flow account disconnected"}, 401); return None
        return session

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
        if path == "/health": return self.send({"ok": True, "version": "0.6.1"})
        if path in ("/", "/onboarding", "/dashboard", "/app.js", "/style.css", "/flow-login.js"):
            file = {"/": "index.html", "/onboarding": "index.html", "/dashboard": "index.html", "/app.js": "app.js", "/style.css": "style.css", "/flow-login.js": "flow-login.js"}[path]
            mime = "application/javascript" if file.endswith(".js") else "text/css" if file.endswith(".css") else "text/html"
            return self.send((Path(__file__).parent.parent / "web" / file).read_bytes(), content_type=mime)
        if path in ("/privacy", "/data-deletion"):
            if path == "/privacy":
                text = "This independently hosted installation stores the operator's profile, channel briefs, imported media, encrypted OAuth credentials, and private Google Flow browser profiles on its own server. It sends approved media to the connected providers to generate or publish content. The project maintainer receives no account credentials. The installation owner controls access, backups and retention. Disconnect removes the saved provider token; revoke authorization in the provider's settings as well."
            else:
                text = "To remove an account, open Connections and choose Disconnect, then revoke the app in the provider's account settings. Browser profiles, media and backups require deletion by this installation's owner. Ask the owner to remove /var/lib/vegas-social-os only when decommissioning the entire installation. This page is a data-deletion instruction URL, not a signed Meta deletion webhook."
            return self.page("Privacy" if path == "/privacy" else "Data deletion", "<p>" + html.escape(text) + "</p><p>Contact this installation's owner for requests. Configure your own legal/contact details before inviting other users.</p>")
        if path == "/pair":
            self.store.consume(q.get("ticket", ""), "pair")
            token = secrets.token_urlsafe(32)
            self.store.put("session", self.store.digest(token), {"expires": time.time() + 8 * 3600})
            secure = "; Secure" if self.base.startswith("https://") else ""
            return self.redirect("/onboarding", {"Set-Cookie": "vso_session=" + token + "; HttpOnly; SameSite=Lax; Path=/; Max-Age=28800" + secure})
        if path == "/connect":
            result = self.engine.accounts.authorize(q.get("ticket", ""))
            if "redirect" in result: return self.redirect(result["redirect"])
            a = result["flow"]
            if __import__('os').getenv('VSO_REMOTE_BROWSER') == '1':
                login = self.engine.flow_login(a["id"])
                return self.redirect(login["login_url"])
            return self.page("Connect Google Flow", "<p>This account has its own browser profile on your worker computer.</p><p>Return to ChatGPT and ask it to open the dedicated Flow login window. You enter your password and 2FA directly into Google.</p><p>Account label: " + html.escape(a["label"]) + "</p><p>No session is exported from your everyday browser.</p>")
        if path == "/flow/login":
            data = self.store.consume(q.get("ticket", ""), "flow-browser")
            token = secrets.token_urlsafe(32)
            self.store.put("flow-session", self.store.digest(token), {"account_id": data["account_id"], "expires": time.time() + 1800})
            secure = "; Secure" if self.base.startswith("https://") else ""
            return self.redirect("/flow/browser", {"Set-Cookie": "vso_flow=" + token + "; HttpOnly; SameSite=Lax; Path=/flow; Max-Age=1800" + secure})
        if path == "/flow/browser":
            if not self.flow_guard(): return
            return self.send((Path(__file__).parent.parent / "web/flow-login.html").read_bytes(), content_type="text/html")
        if path == "/flow/session":
            data = self.flow_guard()
            if not data: return
            account = self.store.get('account', data['account_id'])
            return self.send({"account_id": data["account_id"], 'label': account.get('label'),
                              'existing_service': bool(account.get('service_alias')),
                              'shared_desktop': bool(account.get('shared_desktop'))})
        if path.startswith("/flow/socket/"):
            data = self.flow_guard()
            if not data: return
            if path.rsplit("/", 1)[1] != data["account_id"]: return self.send({"error": "Account scope mismatch"}, 403)
            return self.proxy_browser(data)
        if path.startswith("/novnc/"):
            import os
            root = Path(os.getenv("VSO_NOVNC_ROOT", "/usr/share/novnc")).resolve()
            file = (root / path.removeprefix("/novnc/")).resolve()
            if root not in file.parents or not file.is_file(): return self.send({"error": "Browser interface unavailable"}, 404)
            import mimetypes
            return self.send(file.read_bytes(), content_type=mimetypes.guess_type(file.name)[0] or "application/octet-stream")
        if path.startswith("/callback/"):
            self.engine.accounts.callback(path.rsplit("/", 1)[1], q.get("state", ""), q.get("code", ""))
            return self.redirect(self.base + '/dashboard#accounts')
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
            from .profile import status
            return self.send({"doctor": self.engine.doctor(), "onboarding": status(self.engine), "connections": self.engine.accounts.config.status(),
                              "automation": __import__("vso.automation", fromlist=["status"]).status(self.engine),
                              "research": self.store.all("research"), **self.engine.snapshot()})
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

    def proxy_browser(self, session):
        import socket
        import select
        import re
        from .desktop import websocket_port
        if self.headers.get("Upgrade", "").lower() != "websocket":
            return self.send({"error": "WebSocket upgrade required"}, 400)
        key = self.headers.get("Sec-WebSocket-Key", "")
        if not re.fullmatch(r"[A-Za-z0-9+/]{22}==", key): raise ValueError("Invalid WebSocket key")
        offered = [p.strip() for p in self.headers.get('Sec-WebSocket-Protocol', '').split(',') if p.strip()]
        if offered and 'binary' not in offered: raise ValueError('Unsupported browser WebSocket protocol')
        protocol = 'Sec-WebSocket-Protocol: binary\r\n' if offered else ''
        a = self.store.get("account", session["account_id"])
        if a.get("service_alias"):
            from .flow_service import websocket_port as service_port
            port = service_port(self.engine, session["account_id"])
        else: port = websocket_port(self.store.root, session["account_id"])
        upstream = socket.create_connection(("127.0.0.1", port), timeout=5)
        try:
            request = (f"GET / HTTP/1.1\r\nHost: 127.0.0.1:{port}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                       f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n{protocol}\r\n")
            upstream.sendall(request.encode())
            header = b""
            while b"\r\n\r\n" not in header and len(header) < 8192:
                block = upstream.recv(4096)
                if not block: break
                header += block
            if not header.startswith(b"HTTP/1.1 101") and not header.startswith(b"HTTP/1.0 101"):
                return self.send({"error": "Private desktop handshake failed"}, 502)
            self.wfile.flush()
            self.connection.sendall(header)
            self.close_connection = True
            upstream.settimeout(None)
            last_activity = time.time()
            while time.time() < session["expires"] and time.time() - last_activity < 300:
                readable, _, _ = select.select([self.connection, upstream], [], [], 1)
                for source in readable:
                    chunk = source.recv(65536)
                    if not chunk: return
                    (upstream if source is self.connection else self.connection).sendall(chunk)
                    last_activity = time.time()
        finally:
            upstream.close()

    def do_POST(self):
        try: self.post()
        except ValueError as e: self.send({"error": str(e)}, 400)
        except Exception: self.send({"error": "Operation failed; check installation settings"}, 400)

    def post(self):
        path, q = self.parse()
        if not self.origin_ok(): return self.send({"error": "Origin rejected"}, 403)
        body = self.body()
        if path == "/flow/verify":
            data = self.flow_guard()
            if not data: return
            return self.send(self.engine.flow_inspect(data["account_id"]))
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
        if path == "/api/config":
            # Provider secrets may be supplied only in the owner's private dashboard session.
            # They are deliberately unavailable as MCP tools or returned values.
            if not self.session() or not self.guard(): return self.send({"error": "Private dashboard session required"}, 401)
            if "application/json" not in self.headers.get("Content-Type", ""):
                return self.send({"error": "JSON required"}, 415)
            return self.send(self.engine.accounts.config.save(body.get("provider"), body.get("values")))
        if path == "/api/logout":
            if not self.guard(): return
            from http.cookies import SimpleCookie
            c = SimpleCookie(); c.load(self.headers.get("Cookie", ""))
            if "vso_session" in c:
                with self.store.db() as db:
                    db.execute("DELETE FROM records WHERE kind='session' AND id=?", (self.store.digest(c["vso_session"].value),))
            return self.send({"status": "signed_out"}, headers={"Set-Cookie": "vso_session=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"})
        if path in ("/mcp", "/api/tool"):
            if not self.guard(): return
            if path == "/api/tool":
                return self.send(tools.call(self.engine, body.get("name"), body.get("arguments", {})))
            result = tools.rpc(self.engine, body)
            return self.send(result) if result is not None else self.send("", 202, "text/plain")
        self.send({"error": "Not found"}, 404)
