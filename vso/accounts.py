import os
import time
import urllib.parse
import uuid

from . import net
from .config import Config


class Accounts:
    def __init__(self, store, base):
        self.store, self.base = store, base.rstrip("/")
        self.config = Config(store, self.base)

    def start(self, provider, label):
        if provider not in ("youtube", "instagram", "facebook", "flow", "drive"):
            raise ValueError("Supported providers: youtube, instagram, facebook, flow, drive")
        if not isinstance(label, str) or not 1 <= len(label) <= 80:
            raise ValueError("Account label must be 1–80 characters")
        if provider != "flow":
            app = "google" if provider in ("youtube", "drive") else provider
            if not self.config.public(app)["configured"]:
                raise ValueError("Configure your " + app + " developer app in Connections first")
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
        app = self.config.get("google" if provider in ("youtube", "drive") else provider)
        if provider in ("youtube", "drive"):
            scope = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly" if provider == "youtube" else "https://www.googleapis.com/auth/drive.file"
            params = {"client_id": app["client_id"], "redirect_uri": callback,
                      "response_type": "code", "state": state, "access_type": "offline",
                      "prompt": "consent select_account", "include_granted_scopes": "true", "scope": scope}
            return {"redirect": "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)}
        if provider == "facebook":
            params = {"client_id": app["client_id"], "redirect_uri": callback, "response_type": "code", "state": state}
            if app["config_id"]:
                params["config_id"] = app["config_id"]
            else:
                params["scope"] = "pages_show_list,pages_read_engagement,pages_manage_posts"
            return {"redirect": f"https://www.facebook.com/{self.config.version(provider)}/dialog/oauth?" + urllib.parse.urlencode(params)}
        params = {"client_id": app["client_id"], "redirect_uri": callback,
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
        app = self.config.get("google" if provider in ("youtube", "drive") else provider)
        form = {"client_id": app["client_id"],
                "client_secret": app["client_secret"], "code": code,
                "redirect_uri": callback, "grant_type": "authorization_code"}
        endpoint = "https://oauth2.googleapis.com/token" if provider in ("youtube", "drive") else "https://api.instagram.com/oauth/access_token"
        if provider == "facebook":
            return self.facebook_callback(data, app, form)
        tokens, _ = net.request(endpoint, method="POST", form=form)
        if provider == "youtube":
            info, _ = net.request("https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true", token=tokens["access_token"])
            channels = info.get("items", [])
            if len(channels) != 1:
                raise ValueError("Choose a Google/Brand account that exposes exactly one YouTube channel, then reconnect")
            remote_id, name = channels[0]["id"], channels[0]["snippet"]["title"]
        elif provider == "drive":
            info, _ = net.request("https://www.googleapis.com/drive/v3/about?fields=user(displayName,emailAddress,permissionId)", token=tokens["access_token"])
            user = info["user"]
            remote_id, name = user["permissionId"], user.get("displayName") or data["label"]
        else:
            # Upgrade the short-lived professional-account token on the server.
            url = "https://graph.instagram.com/access_token?" + urllib.parse.urlencode({
                "grant_type": "ig_exchange_token", "client_secret": app["client_secret"],
                "access_token": tokens["access_token"]})
            upgraded, _ = net.request(url)
            tokens.update(upgraded)
            version = self.config.version("instagram")
            info, _ = net.request(f"https://graph.instagram.com/{version}/me?fields=user_id,username", token=tokens["access_token"])
            remote_id, name = str(info["user_id"]), info["username"]
        tokens["expires_at"] = time.time() + int(tokens.get("expires_in", 3600))
        self.store.secret(ident, tokens)
        account = {"id": ident, "provider": provider, "label": data["label"],
                   "remote_id": remote_id, "name": name, "status": "connected",
                   "verified_at": time.time(), "verification": "Provider identity read succeeded; publishing not yet tested"}
        self.store.put("account", ident, account)
        self.store.log("account.connect", ident)
        return account

    def token(self, ident):
        account = self.store.get("account", ident)
        tokens = self.store.secret(ident)
        if account["provider"] == "facebook":
            if tokens.get("expires_at", 0) < time.time() + 120:
                raise ValueError("Facebook Page connection expired; reconnect from Connections")
            return tokens["access_token"]
        app = self.config.get("google" if account["provider"] in ("youtube", "drive") else "instagram")
        if tokens.get("expires_at", 0) < time.time() + 120:
            if account["provider"] in ("youtube", "drive"):
                if not tokens.get("refresh_token"):
                    raise ValueError("Refresh token missing; reconnect with consent")
                fresh, _ = net.request("https://oauth2.googleapis.com/token", method="POST", form={
                    "grant_type": "refresh_token", "refresh_token": tokens["refresh_token"],
                    "client_id": app["client_id"], "client_secret": app["client_secret"]})
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
        if account["provider"] == "drive":
            return net.request("https://www.googleapis.com/drive/v3/about?fields=user(displayName,emailAddress),storageQuota", token=token)[0]
        if account["provider"] == "facebook":
            return net.request(f"https://graph.facebook.com/{self.config.version('facebook')}/{account['remote_id']}?fields=id,name", token=token)[0]
        return net.request(f"https://graph.instagram.com/{self.config.version('instagram')}/{account['remote_id']}?fields=user_id,username,media_count,followers_count", token=token)[0]

    def facebook_callback(self, data, app, form):
        version = self.config.version("facebook")
        root = "https://graph.facebook.com/" + version
        tokens, _ = net.request(root + "/oauth/access_token?" + urllib.parse.urlencode({k: v for k, v in form.items() if k != "grant_type"}))
        upgraded, _ = net.request(root + "/oauth/access_token?" + urllib.parse.urlencode({
            "grant_type": "fb_exchange_token", "client_id": app["client_id"],
            "client_secret": app["client_secret"], "fb_exchange_token": tokens["access_token"]}))
        tokens.update(upgraded)
        permissions, _ = net.request(root + "/me/permissions", token=tokens["access_token"])
        granted = [p["permission"] for p in permissions.get("data", []) if p.get("status") == "granted"]
        required = {"pages_show_list", "pages_read_engagement", "pages_manage_posts"}
        if not required.issubset(granted): raise ValueError("Facebook consent is missing: " + ", ".join(sorted(required - set(granted))))
        pages, _ = net.request(root + "/me/accounts?fields=id,name,access_token,tasks&limit=100", token=tokens["access_token"])
        candidates = pages.get("data", [])
        # Paging URLs contain credentials: follow only the opaque cursor on a fixed origin.
        while len(candidates) < 500:
            after = pages.get("paging", {}).get("cursors", {}).get("after")
            if not pages.get("paging", {}).get("next") or not after: break
            pages, _ = net.request(root + "/me/accounts?" + urllib.parse.urlencode({
                "fields": "id,name,access_token,tasks", "limit": 100, "after": after}), token=tokens["access_token"])
            candidates.extend(pages.get("data", []))
        saved = []
        for page in candidates:
            if not page.get("access_token") or not {"CREATE_CONTENT", "MANAGE"}.intersection(page.get("tasks", [])): continue
            ident = self.store.digest("facebook:" + app["client_id"] + ":" + page["id"])[:32]
            self.store.secret(ident, {"access_token": page["access_token"],
                "expires_at": time.time() + int(tokens.get("expires_in", 60 * 86400))})
            account = {"id": ident, "provider": "facebook", "remote_id": page["id"], "name": page["name"],
                       "label": data["label"], "status": "connected", "permissions": granted,
                       "verified_at": time.time(), "verification": "Page identity, granted scopes and content task verified; publishing not yet tested"}
            self.store.put("account", ident, account)
            self.store.log("account.connect", ident)
            saved.append(account)
        if not saved: raise ValueError("No eligible Facebook Pages found. Grant Page access and the create-content task, then reconnect.")
        return {"name": str(len(saved)) + " Facebook Page(s)", "accounts": saved}


def graph_version():
    import re
    version = os.getenv("META_GRAPH_VERSION", "")
    if not re.fullmatch(r"v\d+\.\d+", version):
        raise ValueError("Set META_GRAPH_VERSION to a currently supported version from Meta's documentation")
    return version
