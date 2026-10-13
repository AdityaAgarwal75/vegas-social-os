"""Installation-owned provider apps. Secrets are encrypted and never returned."""
import os
import re

PROVIDERS = {
    "google": {"prefix": "GOOGLE", "callbacks": ["youtube", "drive"],
        "console": "https://console.cloud.google.com/apis/credentials",
        "permissions": ["youtube.upload", "youtube.readonly", "drive.file (optional)"],
        "steps": ["Create your Google Cloud project and enable YouTube Data API v3 (Drive API only for archives).",
                  "Configure Google Auth Platform branding, audience and test users. Create a Web application OAuth client.",
                  "Register the exact callback URLs below. Save the client ID and secret here.",
                  "Connect each Google/Brand account separately. Testing refresh tokens can expire; public uploads from unverified YouTube API projects may be restricted to private."]},
    "instagram": {"prefix": "INSTAGRAM", "callbacks": ["instagram"],
        "console": "https://developers.facebook.com/apps/",
        "permissions": ["instagram_business_basic", "instagram_business_content_publish"],
        "steps": ["Use an Instagram Business or Creator account; personal accounts cannot use this publisher.",
                  "Create your own Meta app with Instagram API setup using Instagram Login. Use the Instagram app ID and secret shown there.",
                  "Register the callback, privacy and data-deletion URLs below. Add your test account and accept its tester invitation.",
                  "For people outside app roles, obtain the required Advanced Access/App Review and any required business verification. Business verification alone does not approve permissions."]},
    "facebook": {"prefix": "FACEBOOK", "callbacks": ["facebook"],
        "console": "https://developers.facebook.com/apps/",
        "permissions": ["pages_show_list", "pages_read_engagement", "pages_manage_posts"],
        "steps": ["Connect Facebook Pages you can create content for; personal timelines are not publishing destinations.",
                  "Create your Meta app and configure Facebook Login for Business, its approved use case and redirect URI. Set a configuration ID if your app requires it.",
                  "Request only the Page permissions listed here. The connector discovers eligible Pages after consent.",
                  "App-role users can test subject to Meta's rules. Unrelated users require applicable Advanced Access/App Review. Register privacy and deletion URLs."]},
}

class Config:
    def __init__(self, store, base):
        self.store, self.base = store, base

    def get(self, provider):
        if provider not in PROVIDERS: raise ValueError("Unknown provider app")
        prefix = PROVIDERS[provider]["prefix"]
        values = {"client_id": os.getenv(prefix + "_CLIENT_ID", ""),
                  "client_secret": os.getenv(prefix + "_CLIENT_SECRET", ""),
                  "graph_version": os.getenv("META_GRAPH_VERSION", ""),
                  "config_id": os.getenv("FACEBOOK_CONFIG_ID", "")}
        try: values.update(self.store.secret("app:" + provider))
        except ValueError: pass
        return values

    def save(self, provider, values):
        if provider not in PROVIDERS or not isinstance(values, dict): raise ValueError("Unknown provider app")
        if set(values) - {"client_id", "client_secret", "graph_version", "config_id"}: raise ValueError("Unknown configuration field")
        current = self.get(provider)
        for key, value in values.items():
            if not isinstance(value, str) or len(value) > 4096: raise ValueError("Invalid configuration value")
            if value.strip(): current[key] = value.strip()
        if not current["client_id"] or not current["client_secret"]: raise ValueError("Client ID and secret are required")
        if provider != "google" and not re.fullmatch(r"v\d+\.\d+", current["graph_version"]):
            raise ValueError("Enter a currently supported Meta Graph version, e.g. vXX.0 from your app dashboard")
        self.store.secret("app:" + provider, current)
        self.store.log("app.configure", provider)
        return self.public(provider)

    def version(self, provider):
        value = self.get(provider)["graph_version"]
        if not re.fullmatch(r"v\d+\.\d+", value): raise ValueError("Configure the supported Meta Graph version in Connections")
        return value

    def public(self, provider):
        values = self.get(provider)
        spec = PROVIDERS[provider]
        ready = bool(values["client_id"] and values["client_secret"] and
                     (provider == "google" or re.fullmatch(r"v\d+\.\d+", values["graph_version"])))
        return {"provider": provider, "configured": ready, "client_id": values["client_id"],
                "secret_present": bool(values["client_secret"]), "graph_version": values["graph_version"],
                "config_id": values["config_id"], "callbacks": [self.base + "/callback/" + p for p in spec["callbacks"]],
                "privacy_url": self.base + "/privacy", "deletion_url": self.base + "/data-deletion",
                **{k: spec[k] for k in ("console", "permissions", "steps")}}

    def status(self): return [self.public(p) for p in PROVIDERS]
