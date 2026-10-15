import base64
import hashlib
import html
import json
import secrets
import socket
import threading
import re
import time
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import tools


from .auth import pkce, valid_redirect
from . import auth


class HTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, engine):
        self.engine = engine
        self.slots=threading.BoundedSemaphore(24)
        super().__init__(address, Handler)

    def process_request(self,request,client_address):
        request.settimeout(20)
        if not self.slots.acquire(blocking=False):
            try:request.sendall(b"HTTP/1.0 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
            finally:self.shutdown_request(request)
            return
        try:super().process_request(request,client_address)
        except Exception:self.slots.release();raise

    def process_request_thread(self,request,client_address):
        try:super().process_request_thread(request,client_address)
        finally:self.slots.release()

class Handler(BaseHTTPRequestHandler):
    server_version = "VegasSocialOS/0.7"

    @property
    def engine(self): return self.server.engine
    @property
    def store(self): return self.engine.store
    @property
    def base(self): return self.engine.base

    def log_message(self, format, *args):
        # Never log request query strings, authorization codes, tickets or tokens.
        import sys
        sys.stderr.write(json.dumps({"event":"http","method":self.command,"path":urllib.parse.urlsplit(self.path).path,"status":str(args[1]) if len(args)>1 else "unknown"})+"\n")

    def send(self, data, status=200, content_type="application/json", headers=None):
        body = json.dumps(data).encode() if content_type == "application/json" else data.encode() if isinstance(data, str) else data
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        # Allow origin-only Referer, not sensitive paths. no-referrer produces Origin: null
        # for normal HTML form submits, which fails the exact-Origin CSRF guard.
        self.send_header("Referrer-Policy", "origin")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' blob:; frame-src 'self'; frame-ancestors " + ("'self'" if urllib.parse.urlsplit(self.path).path.startswith("/flow/") else "'none'") + "; base-uri 'none'; form-action 'self'" + (" https://chatgpt.com/connector/oauth/" if urllib.parse.urlsplit(self.path).path in ("/authorize", "/consent") else ""))
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

    def body(self, limit=1048576):
        length = int(self.headers.get("Content-Length", "0"))
        if self.headers.get("Transfer-Encoding"): raise ValueError("Chunked RPC bodies are not supported; use media transfer")
        if length>limit:
            self.send({"error":"Request body too large; use media transfer"},413)
            raise ConnectionAbortedError("oversized body")
        if not 0 < length: raise ValueError("Missing request body")
        self.connection.settimeout(20)
        data = self.rfile.read(length)
        if len(data) != length: raise ValueError("Interrupted request body")
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

    def password_recovery(self):
        # This cookie grants password reset only, never dashboard/MCP access.
        from http.cookies import SimpleCookie
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get("Cookie", ""))
            record = self.store.get("password-reset-session", self.store.digest(cookie["vso_reset"].value))
            return record if record["expires"] > time.time() else None
        except (ValueError, KeyError):
            return None

    def principal(self):
        value=self.headers.get('Authorization','')
        if value.startswith('Bearer '): return auth.validate(self.store,self.base,value[7:])
        if self.session(): return {'principal':'owner','scope':'social:manage events:subscribe vps:admin','dashboard':True}
        return None

    def authorized(self): return self.principal() is not None

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
        return not origin or origin == self.base or (urllib.parse.urlsplit(self.path).path == '/mcp' and origin in ('https://chatgpt.com','https://chat.openai.com'))

    def guard(self, scope="social:read"):
        if not self.origin_ok():
            self.send({"error": "Origin rejected"}, 403); return False
        if not self.authorized():
            self.send({"error": "Authentication required"}, 401, headers={
                "WWW-Authenticate": auth.challenge(self.base)})
            return False
        if not auth.permits(self.principal(),scope):
            self.send({"error":"Insufficient scope"},403,headers={"WWW-Authenticate":auth.challenge(self.base,"insufficient_scope","Additional owner authorization required",scope)})
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
        if path == '/ready':
            if not self.guard():return
            with self.store.db() as db:db.execute('SELECT 1').fetchone()
            return self.send({'ready':True,'database':'sqlite','version':'0.7.0','flow_engine_installed':self.engine.doctor()['flow_engine_installed']})
        if path == "/health": return self.send({"ok": True, "version": "0.7.0"})
        if path == "/password":
            if not self.session() and not self.password_recovery():return self.page("Owner session required",
                "<p>Use an authorized owner session or private setup link first.</p>",401)
            from .owner_auth import configured
            previous=('<label>Current password<input type="password" name="current" required autocomplete="current-password"></label>' if configured(self.store) and not self.password_recovery() else '')
            return self.page("Set owner password",
                "<p>Your password stays private and is stored as a salted hash.</p>"
                '<form action="/password" method="post">'+previous+
                '<label>New password<input type="password" name="password" minlength="14" required autocomplete="new-password"></label>'
                '<label>Confirm password<input type="password" name="confirmation" minlength="14" required autocomplete="new-password"></label>'
                '<button type="submit">Save owner password</button></form>')
        if path == "/login":
            from .owner_auth import configured, validate_return
            next_url=q.get("next","/dashboard")
            try:validate_return(next_url)
            except ValueError:next_url="/dashboard"
            if self.session():return self.redirect(next_url)
            if not configured(self.store):
                return self.page("Set an owner password",
                    "<p>On your own private installation terminal, run <code>python -m vso owner-password</code> to enable browser password login. "
                    "Until configured, use the one-use local setup link. Never paste the password into ChatGPT.</p>", 401)
            import html as _html
            return self.page("Owner sign-in",
                "<p>Sign in to your own installation. ChatGPT's plugin connection still uses secure OAuth approval afterward.</p>"
                '<form action="/login" method="post">'
                '<input name="password" type="password" required minlength="14" autocomplete="current-password" aria-label="Owner password">'
                '<input type="hidden" name="next" value="' + _html.escape(next_url,quote=True) + '">'
                '<button type="submit">Sign in</button></form>')

        if path in ('/admin','/admin/enroll','/admin.js'):
            if not self.session():return self.page('Owner sign-in required','<p>Open your private owner dashboard sign-in link first.</p>',401)
            file='admin.js' if path=='/admin.js' else 'admin.html'
            return self.send((Path(__file__).parent.parent/'web'/file).read_bytes(),content_type='application/javascript' if file.endswith('.js') else 'text/html')
        if path in ("/", "/onboarding", "/dashboard", "/app.js", "/sha256.js", "/style.css", "/flow-login.js", "/oauth-consent.js"):
            file = {"/": "index.html", "/onboarding": "index.html", "/dashboard": "index.html", "/app.js": "app.js", "/sha256.js":"sha256.js", "/style.css": "style.css", "/flow-login.js": "flow-login.js", "/oauth-consent.js": "oauth-consent.js"}[path]
            mime = "application/javascript" if file.endswith(".js") else "text/css" if file.endswith(".css") else "text/html"
            return self.send((Path(__file__).parent.parent / "web" / file).read_bytes(), content_type=mime)
        if path in ("/privacy", "/data-deletion"):
            if path == "/privacy":
                text = "This independently hosted installation stores the operator's profile, channel briefs, imported media, encrypted OAuth credentials, and private Google Flow browser profiles on its own server. It sends approved media to the connected providers to generate or publish content. The project maintainer receives no account credentials. The installation owner controls access, backups and retention. Disconnect removes the saved provider token; revoke authorization in the provider's settings as well."
            else:
                text = "To remove an account, open Connections and choose Disconnect, then revoke the app in the provider's account settings. Browser profiles, media and backups require deletion by this installation's owner. Ask the owner to remove /var/lib/vegas-social-os only when decommissioning the entire installation. This page is a data-deletion instruction URL, not a signed Meta deletion webhook."
            return self.page("Privacy" if path == "/privacy" else "Data deletion", "<p>" + html.escape(text) + "</p><p>Contact this installation's owner for requests. Configure your own legal/contact details before inviting other users.</p>")
        if path == "/owner-recovery":
            try:
                self.store.consume(q.get("ticket", ""), "owner-reset")
            except ValueError:
                return self.page("Recovery link expired or already used",
                    '<p>Ask your authorized server administrator or connected infrastructure agent for a fresh password recovery link. Open it once in the browser where you will set your password.</p>', 410)
            token = secrets.token_urlsafe(32)
            self.store.put("password-reset-session", self.store.digest(token), {"expires": time.time() + 600})
            secure = "; Secure" if self.base.startswith("https://") else ""
            return self.redirect("/password", {"Set-Cookie": "vso_reset=" + token + "; HttpOnly; SameSite=Lax; Path=/password; Max-Age=600" + secure})
        if path == "/pair":
            # Pairing tickets are one-use; repeat visits from an already paired
            # browser should remain on the dashboard, not throw an invalid grant.
            try:
                self.store.consume(q.get("ticket", ""), "pair")
            except ValueError:
                if self.session(): return self.redirect("/onboarding")
                return self.page("Setup link expired or already used",
                    "<p>This owner link can only be opened once. If setup already opened your dashboard, return there. Otherwise generate a new private setup link on your own installation.</p>", 410)
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
            return self.send({"resource": self.base + "/mcp", "authorization_servers": [self.base], "scopes_supported": sorted(auth.SCOPES)})
        if path == "/.well-known/oauth-authorization-server":
            return self.send({"issuer": self.base, "authorization_endpoint": self.base + "/authorize",
                              "token_endpoint": self.base + "/token", "registration_endpoint": self.base + "/register", "revocation_endpoint": self.base + "/revoke",
                              "response_types_supported": ["code"], "grant_types_supported": ["authorization_code", "refresh_token"],
                              "token_endpoint_auth_methods_supported": ["none"], "code_challenge_methods_supported": ["S256"],
                              "scopes_supported": sorted(auth.SCOPES)})
        if path == "/authorize":
            if not self.session():
                from .owner_auth import configured
                if configured(self.store):
                    return self.redirect("/login?"+urllib.parse.urlencode({"next":self.path}))
                return self.page("Owner sign-in required", "<p>Run <code>python -m vso owner-password</code> in a private terminal to enable password sign-in, or use the private one-use setup link, then retry connecting the plugin.</p>", 401)
            client = self.store.get("oauth-client", q.get("client_id", ""))
            if q.get("redirect_uri") not in client["redirect_uris"] or q.get("response_type") != "code" or q.get("code_challenge_method") != "S256" or len(q.get("code_challenge", "")) != 43 or q.get("resource") != self.base + "/mcp":
                raise ValueError("Invalid OAuth client, PKCE challenge or resource")
            q['scope'] = auth.scopes(q.get('scope','social:read social:write'))
            ticket = self.store.ticket("consent", q)
            return self.page("Authorize this plugin", "<p>Approve only a client you trust. Requested scopes: " + html.escape(q["scope"]) + ". VPS administration has additional per-operation approval. Provider passwords and tokens are not returned.</p><p>Client: " + html.escape(client["name"]) + "</p><p>Return address: " + html.escape(q["redirect_uri"]) + '</p><form action="/consent" method="post"><input type="hidden" name="ticket" value="' + ticket + '"><button type="submit">Authorize Vegas Social OS</button></form><script defer src="/oauth-consent.js"></script>')
        if path == "/api/state":
            if not self.guard(): return
            from .profile import status
            return self.send({"doctor": self.engine.doctor(), "onboarding": status(self.engine), "connections": self.engine.accounts.config.status(),
                              "automation": __import__("vso.automation", fromlist=["status"]).status(self.engine),
                              "research": self.store.all("research"), **self.engine.snapshot()})
        if path=='/media-download':
            digest=self.store.digest(q.get('ticket',''))
            with self.store.db() as db:
                row=db.execute("SELECT body,expires FROM tickets WHERE hash=? AND kind='media-download'",(digest,)).fetchone()
            if not row or row['expires']<time.time():raise ValueError('Media preview expired')
            return self.media(json.loads(row['body'])['asset_id'])
        if path == "/media":
            record = self.store.get("media-link", self.store.digest(q.get("ticket", "")))
            if record["expires"] < time.time(): raise ValueError("Media link expired")
            return self.media(record["asset_id"])
        if path.startswith("/asset/"):
            if not self.guard(): return
            return self.media(path.rsplit("/", 1)[1])
        if path == "/mcp":
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
        self.send_response(status)
        for k,v in {"Content-Type":asset["media_type"],"Content-Length":str(end-start+1),"Cache-Control":"no-store","Referrer-Policy":"no-referrer","X-Content-Type-Options":"nosniff",**headers}.items():self.send_header(k,v)
        self.end_headers()
        if self.command=="HEAD":return
        self.connection.settimeout(30)
        with file.open("rb") as f:
            f.seek(start);remaining=end-start+1
            while remaining:
                chunk=f.read(min(1024*1024,remaining))
                if not chunk:break
                self.wfile.write(chunk);remaining-=len(chunk)

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

    def do_PUT(self):
        from . import media
        try:
            path,q=self.parse()
            if not self.origin_ok() or not path.startswith('/transfer/'):return self.send({'error':'Transfer unavailable'},403)
            if self.headers.get('Transfer-Encoding'):raise ValueError('Use bounded Content-Length chunks')
            self.connection.settimeout(30)
            result=media.receive(self.engine,path.rsplit('/',1)[1],q.get('ticket',''),self.rfile,int(self.headers.get('Content-Length','0')),self.headers.get('Content-Range'))
            return self.send(result)
        except PermissionError:return self.send({'error':'Transfer authorization required'},401)
        except ValueError as e:return self.send({'error':str(e)},400)
        except Exception:return self.send({'error':'Media transfer failed; inspect its offset before retrying'},400)

    def do_POST(self):
        try: self.post()
        except auth.RateLimited as e:self.send({"error":"temporarily_unavailable","error_description":str(e)},429,headers={"Retry-After":"60"})
        except ValueError as e:
            path,_=self.parse()
            self.send({"error":"invalid_grant" if path=="/token" else "invalid_request","error_description":str(e)},400)
        except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError,socket.timeout):pass
        except Exception:
            error_id=secrets.token_hex(6);self.store.log("http.failure",error_id)
            self.send({"error":"server_error","error_description":"Operation failed; inspect the redacted audit record","error_id":error_id},500)

    def post(self):
        path, q = self.parse()
        if not self.origin_ok(): return self.send({"error": "Origin rejected"}, 403)
        public=path in ('/register','/token','/revoke','/mcp')
        if path=='/flow/verify' and not self.flow_guard():return
        if not public and not self.authorized() and path not in ('/flow/verify','/login','/password'):
            return self.send({'error':'Authentication required'},401,headers={'WWW-Authenticate':auth.challenge(self.base)})
        limit=16384 if path in ('/register','/token','/revoke','/consent','/login','/password') else (65536 if path=='/mcp' and not self.authorized() else 1048576)
        body=self.body(limit)
        if not isinstance(body,dict):raise ValueError('Expected one JSON object')
        if path == "/password":
            if not self.session() and not self.password_recovery():return self.send({"error":"Owner session required"},401)
            from .owner_auth import configured, password_check, password_set
            if configured(self.store) and not self.password_recovery() and not password_check(self.store,body.get("current",""),self.client_address[0]):
                return self.page("Current password incorrect","<p>Verify your current password.</p>",401)
            if body.get("password")!=body.get("confirmation"):
                return self.page("Passwords differ","<p>Enter matching passwords.</p>",400)
            password_set(self.store,body.get("password",""))
            return self.redirect("/login", {"Set-Cookie": "vso_reset=; HttpOnly; SameSite=Lax; Path=/password; Max-Age=0"})
        if path == "/login":
            from .owner_auth import password_check, validate_return
            next_url=validate_return(body.get("next","/dashboard"))
            if not password_check(self.store,body.get("password",""),self.client_address[0]):
                return self.page("Incorrect owner password",
                                 '<p>Authentication failed. Return to <a href="/login">owner login</a>. Rate limits apply.</p>',401)
            token=secrets.token_urlsafe(32)
            self.store.put("session",self.store.digest(token),{"expires":time.time()+8*3600})
            secure="; Secure" if self.base.startswith("https://") else ""
            return self.redirect(next_url, {"Set-Cookie":"vso_session="+token+"; HttpOnly; SameSite=Lax; Path=/; Max-Age=28800"+secure})
        if path == "/flow/verify":
            data = self.flow_guard()
            if not data: return
            return self.send(self.engine.flow_inspect(data["account_id"]))
        if path == '/register':
            return self.send(auth.register(self.store,body,self.client_address[0]),201)
        if path == '/revoke': return self.send(auth.revoke(self.store,body))
        if path == "/consent":
            if not self.session(): raise ValueError("Sign into this installation before consent")
            try:
                data = self.store.consume(body.get("ticket", ""), "consent")
            except ValueError:
                return self.page("Authorization request already submitted",
                    "<p>This one-time approval has already been sent or expired. Return to ChatGPT and reconnect Vegas Social OS to start a fresh authorization request. If your dashboard opens, you do not need another owner setup link.</p>", 409)
            code = self.store.ticket("mcp-code", data, ttl=120)
            sep = "&" if "?" in data["redirect_uri"] else "?"
            return self.redirect(data["redirect_uri"] + sep + urllib.parse.urlencode({"code": code, "state": data.get("state", "")}))
        if path == '/token': return self.send(auth.token(self.store,self.base,body))
        if path in ('/api/admin-approve','/api/admin-enroll','/api/admin-request'):
            if not self.session() or not self.guard():return self.send({'error':'Private owner browser session required'},401)
            from .admin import call
            if path=='/api/admin-request':return self.send(call({'action':'request_status','request_id':body.get('request_id','')}))
            if path=='/api/admin-enroll':return self.send(call({'action':'enrollment','ticket':body.get('ticket',''),**({'code':body['code']} if 'code' in body else {})}))
            return self.send(call({'action':'approve','request_id':body.get('request_id',''),'code':body.get('code','')}))
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
        if path in ('/mcp','/api/tool'):
            principal=self.principal()
            if path=='/api/tool':
                if not self.authorized():return self.send({'error':'Authentication required'},401)
                name=body.get('name');required=auth.tool_scope(name)
                if not auth.permits(principal,required):return self.send({'error':'Insufficient scope'},403)
                return self.send(tools.call(self.engine,name,body.get('arguments',{})))
            method=body.get('method')
            if not isinstance(method,str) or not isinstance(body.get('params',{}),dict):return self.send({'jsonrpc':'2.0','id':body.get('id'),'error':{'code':-32600,'message':'Invalid JSON-RPC request'}},400)
            if method not in auth.DISCOVERY_METHODS and not principal:
                if method=='tools/call':return self.send(tools.auth_error(self.engine,body))
                return self.send({'error':'Authentication required'},401,headers={'WWW-Authenticate':auth.challenge(self.base)})
            if method in ('events/subscribe','events/unsubscribe') and principal and (not auth.permits(principal,'social:read') or not auth.permits(principal,'events:subscribe')):
                return self.send({'error':'Insufficient event scope'},403,headers={'WWW-Authenticate':auth.challenge(self.base,'insufficient_scope',scope='social:read events:subscribe')})
            if method=='tools/call' and principal:
                required=auth.tool_scope(body.get('params',{}).get('name'))
                if not auth.permits(principal,required):return self.send(tools.auth_error(self.engine,body,required))
            result=tools.rpc(self.engine,body,principal=principal)
            return self.send(result) if result is not None else self.send("", 202, "text/plain")
        self.send({"error": "Not found"}, 404)
