import hashlib
import json
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from cryptography.fernet import Fernet


class Store:
    """One installation belongs to one operator. Never share its data directory."""

    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        (self.root / "media").mkdir(exist_ok=True, mode=0o700)
        key = self.root / "vault.key"
        try:
            with key.open("xb") as f:
                os.chmod(key, 0o600)
                f.write(Fernet.generate_key())
        except FileExistsError:
            pass
        self.vault = Fernet(key.read_bytes())
        with self.db() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS records (
                kind TEXT NOT NULL, id TEXT NOT NULL, body TEXT NOT NULL,
                PRIMARY KEY(kind,id));
            CREATE TABLE IF NOT EXISTS secrets (id TEXT PRIMARY KEY, value BLOB NOT NULL);
            CREATE TABLE IF NOT EXISTS tickets (
                hash TEXT PRIMARY KEY, kind TEXT NOT NULL, body TEXT NOT NULL,
                expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS audit (
                at REAL NOT NULL, action TEXT NOT NULL, entity TEXT NOT NULL);
            """)
        os.chmod(self.root / "state.sqlite", 0o600)

    @contextmanager
    def db(self):
        db = sqlite3.connect(self.root / "state.sqlite", timeout=20)
        db.row_factory = sqlite3.Row
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def get(self, kind, ident):
        with self.db() as db:
            row = db.execute("SELECT body FROM records WHERE kind=? AND id=?", (kind, ident)).fetchone()
        if not row:
            raise ValueError(f"{kind} not found")
        return json.loads(row[0])

    def put(self, kind, ident, body):
        with self.db() as db:
            self.write(db, kind, ident, body)

    @staticmethod
    def write(db, kind, ident, body):
        db.execute("INSERT INTO records VALUES(?,?,?) ON CONFLICT(kind,id) DO UPDATE SET body=excluded.body",
                   (kind, ident, json.dumps(body)))

    def all(self, kind):
        with self.db() as db:
            return [json.loads(r[0]) for r in db.execute("SELECT body FROM records WHERE kind=? ORDER BY id", (kind,))]

    def secret(self, ident, value=None):
        with self.db() as db:
            if value is not None:
                db.execute("INSERT OR REPLACE INTO secrets VALUES(?,?)",
                           (ident, self.vault.encrypt(json.dumps(value).encode())))
                return None
            row = db.execute("SELECT value FROM secrets WHERE id=?", (ident,)).fetchone()
        if not row:
            raise ValueError("Credential missing; reconnect this account")
        return json.loads(self.vault.decrypt(row[0]))

    def ticket(self, kind, body, ttl=600):
        token = secrets.token_urlsafe(32)
        with self.db() as db:
            db.execute("DELETE FROM tickets WHERE expires<?", (time.time(),))
            db.execute("INSERT INTO tickets VALUES(?,?,?,?)",
                       (self.digest(token), kind, json.dumps(body), time.time() + ttl))
        return token

    def consume(self, token, kind):
        with self.db() as db:
            row = db.execute("SELECT body,expires FROM tickets WHERE hash=? AND kind=?",
                             (self.digest(token), kind)).fetchone()
            if not row or row[1] < time.time():
                raise ValueError("Link expired, already used, or invalid; request a new link")
            db.execute("DELETE FROM tickets WHERE hash=?", (self.digest(token),))
        return json.loads(row[0])

    @staticmethod
    def digest(value):
        return hashlib.sha256(value.encode()).hexdigest()

    def log(self, action, entity):
        with self.db() as db:
            db.execute("INSERT INTO audit VALUES(?,?,?)", (time.time(), action, entity))

    def disconnect(self, ident):
        with self.db() as db:
            db.execute("DELETE FROM records WHERE kind='account' AND id=?", (ident,))
            db.execute("DELETE FROM secrets WHERE id=?", (ident,))
        self.log("account.disconnect", ident)
