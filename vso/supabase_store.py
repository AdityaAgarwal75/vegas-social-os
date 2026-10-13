"""Supabase-authoritative state with an encrypted local transaction cache.

Database CAS prevents two runtimes from committing divergent installation state.
Unknown network outcomes are never automatically retried. The next read reloads
the database's authoritative revision.
"""
import base64
import json
import threading
import uuid
from contextlib import contextmanager
from urllib.parse import urlsplit

from .store import Store
from . import net


class SupabaseStore(Store):
    def __init__(self, root, url, server_key, installation_id):
        self._cloud_ready = False
        super().__init__(root)
        import re
        self.url = url.rstrip("/")
        p = urlsplit(self.url)
        if p.scheme != "https" or not re.fullmatch(r"[a-z0-9]+\.supabase\.co", p.hostname or "") or p.path or p.query or p.fragment or p.username:
            raise ValueError("Configure the dedicated Supabase project origin")
        if not server_key: raise ValueError("Supabase server key is required")
        self.host = p.hostname
        self.server_key = server_key
        self.installation_id = str(uuid.UUID(installation_id))
        self._cloud_lock = threading.RLock()
        self._cloud_ready = True
        with self.db(): pass  # Check schema/access immediately; no silent local fallback.

    def _request(self, path, **kwargs):
        auth = self.server_key if self.server_key.startswith("ey") else None
        return net.request(self.url + path, token=auth, headers={"apikey": self.server_key},
                           allowed_hosts={self.host}, **kwargs)[0]

    def _load_cloud(self):
        rows = self._request("/rest/v1/vso_installations?installation_id=eq." + self.installation_id + "&select=revision,ciphertext")
        if not isinstance(rows, list) or len(rows) > 1: raise ValueError("Unexpected installation state response")
        if not rows: return 0, None
        state = json.loads(self.vault.decrypt(rows[0]["ciphertext"].encode()))
        return rows[0]["revision"], state

    @staticmethod
    def _serialize(db):
        state = {}
        for table in ("records", "secrets", "tickets", "audit"):
            state[table] = [dict(row) for row in db.execute("SELECT * FROM " + table)]
        for record in state["secrets"]:
            record["value"] = base64.b64encode(record["value"]).decode()
        return state

    @staticmethod
    def _hydrate(db, state):
        # All table names/columns are fixed locally; remote content remains values.
        layouts = {"records": ("kind", "id", "body"), "secrets": ("id", "value"),
                   "tickets": ("hash", "kind", "body", "expires"), "audit": ("at", "action", "entity")}
        for table, columns in layouts.items():
            db.execute("DELETE FROM " + table)
            for row in state.get(table, []):
                values = [row[k] for k in columns]
                if table == "secrets": values[1] = base64.b64decode(values[1], validate=True)
                db.execute("INSERT INTO " + table + " VALUES(" + ",".join("?" for _ in columns) + ")", values)

    @contextmanager
    def db(self):
        if not self._cloud_ready:
            with super().db() as db: yield db
            return
        with self._cloud_lock:
            revision, cloud = self._load_cloud()
            with super().db() as db:
                if cloud is not None: self._hydrate(db, cloud)
                elif revision == 0:
                    # A new project must not accidentally inherit stale local records.
                    self._hydrate(db, {})
                before = self._serialize(db)
                yield db
                after = self._serialize(db)
                if after != before:
                    ciphertext = self.vault.encrypt(json.dumps(after, sort_keys=True).encode()).decode()
                    result = self._request("/rest/v1/rpc/vso_commit_state", method="POST", payload={
                        "p_installation_id": self.installation_id, "p_expected_revision": revision, "p_ciphertext": ciphertext})
                    if not isinstance(result, int) or result != revision + 1:
                        raise ValueError("Supabase state changed concurrently; reload and reconcile. No write was retried.")


def from_environment(root):
    import os
    mode = os.getenv("VSO_STATE_BACKEND", "sqlite")
    if mode == "sqlite": return Store(root)
    if mode != "supabase": raise ValueError("Unknown VSO_STATE_BACKEND")
    return SupabaseStore(root, os.getenv("SUPABASE_URL", ""), os.getenv("SUPABASE_SERVER_KEY", ""), os.getenv("VSO_INSTALLATION_ID", ""))
