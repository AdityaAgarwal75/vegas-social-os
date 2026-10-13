import os
import time
import urllib.parse
import uuid

from . import net


class Accounts:
    def __init__(self, store, base):
        self.store, self.base = store, base.rstrip("/")

    def start(self, provider, label):
        if provider not in ("youtube", "instagram", "flow"):
            raise ValueError("Supported providers: youtube, instagram, flow")
        if not isinstance(label, str) or not 1 <= len(label) <= 80:
            raise ValueError("Account label must be 1–80 characters")
        if provider != "flow":
            prefix = "GOOGLE" if provider == "youtube" else "INSTAGRAM"
            if not os.getenv(prefix + "_CLIENT_ID") or not os.getenv(prefix + "_CLIENT_SECRET"):
                raise ValueError(f"Configure {prefix}_CLIENT_ID and {prefix}_CLIENT_SECRET on this installation first")
        ticket = self.store.ticket("connect", {"provider": provider, "label": label})
        return {"url": self.base + "/connect?ticket=" + ticket, "expires_in": 600,
                "instructions": "Open this private one-use link in your browser. Never paste passwords into chat."}

    def authorize(self, ticket):
        data = self.store.consume(ticket, "connect")
        provider = data["provider"]
        if provider == "flow":
            ident = uuid.uuid4().hex
            body = {"id": ident, "provider": "flow", "label": data["label"],
                    "status": "login_required", "credits": None}
            self.store.put("account", ident, body)
            return {"flow": body}
        state = self.store.ticket("oauth-state", data)
        callback = self.base + "/callback/" + provider
        if provider == "youtube":
            params = {"client_id": os.environ["GOOGLE_CLIENT_ID"], "redirect_uri": callback,
                      "response_type": "code", "state": state, "access_type": "offline",
                      "prompt": "consent select_account", "include_granted_scopes": "true",
                      "scope": "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"}
            return {"redirect": "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)}
        params = {"client_id": os.environ["INSTAGRAM_CLIENT_ID"], "redirect_uri": callback,
                  "response_type": "code", "state": state,
                  "scope": "instagram_business_basic,instagram_business_content_publish"}
        return {"redirect": "https://www.instagram.com/oauth/authorize?" + urllib.parse.urlencode(params)}

    def callback(self, provider, state, code):
        data = self.store.consume(state, "oauth-state")
        if data["provider"] != provider:
            raise ValueError("OAuth provider mismatch")
        if not code or len(code) > 8192:
            raise ValueError("Authorization failed or cancelled")
        ident = uuid.uuid4().hex
        callback = self.base + "/callback/" + provider
        prefix = "GOOGLE" if provider == "youtube" else "INSTAGRAM"
        form = {"client_id": os.environ[prefix + "_CLIENT_ID"],
                "client_secret": os.environ[prefix + "_CLIENT_SECRET"], "code": code,
                "redirect_uri": callback, "grant_type": "authorization_code"}
        endpoint = "https://oauth2.googleapis.com/token" if provider == "youtube" else "https://api.instagram.com/oauth/access_token"
        tokens, _ = net.request(endpoint, method="POST", form=form)
        if provider == "youtube":
            info, _ = net.request("https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true", token=tokens["access_token"])
            channels = info.get("items", [])
            if len(channels) != 1:
                raise ValueError("Choose a Google/Brand account that exposes exactly one YouTube channel, then reconnect")
            remote_id, name = channels[0]["id"], channels[0]["snippet"]["title"]
        else:
            # Upgrade the short-lived professional-account token on the server.
            url = "https://graph.instagram.com/access_token?" + urllib.parse.urlencode({
                "grant_type": "ig_exchange_token", "client_secret": os.environ["INSTAGRAM_CLIENT_SECRET"],
                "access_token": tokens["access_token"]})
            upgraded, _ = net.request(url)
            tokens.update(upgraded)
            version = graph_version()
            info, _ = net.request(f"https://graph.instagram.com/{version}/me?fields=user_id,username", token=tokens["access_token"])
            remote_id, name = str(info["user_id"]), info["username"]
        tokens["expires_at"] = time.time() + int(tokens.get("expires_in", 3600))
        self.store.secret(ident, tokens)
        account = {"id": ident, "provider": provider, "label": data["label"],
                   "remote_id": remote_id, "name": name, "status": "connected"}
        self.store.put("account", ident, account)
        self.store.log("account.connect", ident)
        return account

    def token(self, ident):
        account = self.store.get("account", ident)
        tokens = self.store.secret(ident)
        if tokens.get("expires_at", 0) < time.time() + 120:
            if account["provider"] == "youtube":
                if not tokens.get("refresh_token"):
                    raise ValueError("Refresh token missing; reconnect with consent")
                fresh, _ = net.request("https://oauth2.googleapis.com/token", method="POST", form={
                    "grant_type": "refresh_token", "refresh_token": tokens["refresh_token"],
                    "client_id": os.environ["GOOGLE_CLIENT_ID"], "client_secret": os.environ["GOOGLE_CLIENT_SECRET"]})
            else:
                fresh, _ = net.request("https://graph.instagram.com/refresh_access_token?" + urllib.parse.urlencode({
                    "grant_type": "ig_refresh_token", "access_token": tokens["access_token"]}))
            tokens.update(fresh)
            tokens["expires_at"] = time.time() + int(fresh.get("expires_in", 3600))
            self.store.secret(ident, tokens)
        return tokens["access_token"]

    def info(self, ident):
        account = self.store.get("account", ident)
        token = self.token(ident)
        if account["provider"] == "youtube":
            return net.request("https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true", token=token)[0]
        return net.request(f"https://graph.instagram.com/{graph_version()}/{account['remote_id']}?fields=user_id,username,media_count,followers_count", token=token)[0]


def graph_version():
    import re
    version = os.getenv("META_GRAPH_VERSION", "")
    if not re.fullmatch(r"v\d+\.\d+", version):
        raise ValueError("Set META_GRAPH_VERSION to a currently supported version from Meta's documentation")
    return version
