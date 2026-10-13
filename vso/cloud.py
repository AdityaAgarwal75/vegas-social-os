"""Legacy optional metadata backup; agent-first state uses SupabaseStore."""
import os
import re
import urllib.parse
import uuid

from . import net


def sync(engine):
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    parts = urllib.parse.urlsplit(base)
    if parts.scheme != "https" or not re.fullmatch(r"[a-z0-9]+\.supabase\.co", parts.hostname or "") or parts.path or parts.query or parts.fragment or parts.username:
        raise ValueError("Use your project's exact https://<ref>.supabase.co origin")
    jwt = os.environ.get("SUPABASE_USER_JWT")
    key = os.environ.get("SUPABASE_PUBLISHABLE_KEY")
    if not jwt or not key: raise ValueError("Configure a user JWT and publishable key server-side")
    kwargs = {"token": jwt, "headers": {"apikey": key}, "allowed_hosts": {parts.hostname}}
    # Verify the JWT with the provider, never trust client-decodable metadata.
    user, _ = net.request(base + "/auth/v1/user", **kwargs)
    owner = str(uuid.UUID(user["id"]))
    try: installation = engine.store.get("installation", "self")["id"]
    except ValueError:
        installation = str(uuid.uuid4()); engine.store.put("installation", "self", {"id": installation})
    snapshot = engine.snapshot()
    # Worker records may hold generated Google media URLs; backup only essential status.
    snapshot["job"] = [{k: v for k, v in j.items() if k not in ("worker", "error")} for j in snapshot["job"]]
    snapshot["asset"] = [{k: v for k, v in a.items() if k != "file"} for a in snapshot["asset"]]
    net.request(base + "/rest/v1/vso_snapshots?on_conflict=owner_id,installation_id", method="POST",
                payload={"owner_id": owner, "installation_id": installation, "snapshot": snapshot},
                **{**kwargs, "headers": {"apikey": key, "Prefer": "resolution=merge-duplicates,return=minimal"}})
    return {"status": "backed_up", "installation_id": installation,
            "note": "Secret-free metadata only. Media, credentials and browser sessions remain local. JWT refresh and cloud job scheduling are not implemented."}
