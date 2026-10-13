"""Provider requests: fixed hosts, bounded reads, no token-bearing error output."""
import json
import urllib.error
import urllib.parse
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


HOSTS = {"oauth2.googleapis.com", "www.googleapis.com", "accounts.google.com",
         "graph.instagram.com", "api.instagram.com", "graph.facebook.com"}


def request(url, *, method="GET", token=None, form=None, payload=None, raw=None, headers=None, allowed_hosts=None, allow_statuses=()):
    parts = urllib.parse.urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in (allowed_hosts or HOSTS) or parts.username or parts.password:
        raise ValueError("Provider URL is not on the HTTPS allowlist")
    h = dict(headers or {})
    if token:
        h["Authorization"] = "Bearer " + token
    data = raw
    if form is not None:
        data = urllib.parse.urlencode(form).encode()
        h["Content-Type"] = "application/x-www-form-urlencoded"
    if payload is not None:
        data = json.dumps(payload).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.build_opener(NoRedirect).open(req, timeout=60) as r:
            body = r.read(4_000_001)
            if len(body) > 4_000_000:
                raise ValueError("Provider response exceeds limit")
            return (json.loads(body) if body else {}), dict(r.headers)
    except urllib.error.HTTPError as e:
        if e.code in allow_statuses:
            body = e.read(4_000_001)
            if len(body) > 4_000_000: raise ValueError("Provider response exceeds limit")
            return (json.loads(body) if body else {}), {**dict(e.headers), ":status": str(e.code)}
        # Never echo response bodies, request URL, access tokens, or client secrets.
        raise ValueError(f"Provider rejected request (HTTP {e.code}); check permissions and account status") from None
    except (urllib.error.URLError, TimeoutError):
        raise ValueError("Provider request interrupted; reconcile before retrying a write") from None
