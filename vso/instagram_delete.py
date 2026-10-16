"""Guarded, account-bound Instagram published-media deletion.

Instagram Login's documented API does not guarantee a published-media DELETE endpoint.
Never claim removal from a local state transition. Only a positive provider confirmation
can establish deletion; any rejection requires manual deletion in Instagram.
"""
import json
import re
import time

from . import net

_ID = re.compile(r"^[0-9]{10,30}$")
_MAX_REQUEST = 200


def _source(engine, account_id, media_id):
    if not isinstance(account_id, str) or not account_id:
        raise ValueError("Choose an exact connected Instagram account ID")
    if not isinstance(media_id, str) or not _ID.fullmatch(media_id):
        raise ValueError("An exact numeric Instagram media ID is required")
    account = engine.store.get("account", account_id)
    if account.get("provider") != "instagram" or account.get("status") != "connected":
        raise ValueError("Deletion is restricted to a connected Instagram professional account")
    matches = [
        p for p in engine.store.all("publication")
        if p.get("provider") == "instagram"
        and p.get("account_id") == account_id
        and str(p.get("remote_id") or "") == media_id
        and p.get("status") == "published"
    ]
    if len(matches) != 1:
        raise ValueError("Media must match one published post recorded for this exact Instagram account")
    return account, matches[0]


def prepare(engine, account_id, media_id, request_id):
    """Freeze the exact connected account and previously published media for human review."""
    if not isinstance(request_id, str) or not 1 <= len(request_id) <= _MAX_REQUEST:
        raise ValueError("A stable deletion request ID is required")
    account, publication = _source(engine, account_id, media_id)
    ident = engine.store.digest("instagram-delete:" + request_id)[:32]
    frozen = {
        "id": ident,
        "kind": "instagram-media-delete",
        "provider": "instagram",
        "account_id": account_id,
        "account_remote_id": str(account["remote_id"]),
        "username": account.get("name", ""),
        "media_id": media_id,
        "publication_id": publication["id"],
        "caption_excerpt": str(publication.get("caption") or "")[:180],
        "status": "review",
    }
    with engine.store.db() as db:
        row = db.execute(
            "SELECT body FROM records WHERE kind='media-deletion' AND id=?", (ident,)
        ).fetchone()
        if row:
            old = json.loads(row[0])
            if any(old.get(k) != v for k, v in frozen.items() if k != "status"):
                raise ValueError("Request ID already belongs to a different deletion")
            return old
        frozen["created_at"] = time.time()
        engine.store.write(db, "media-deletion", ident, frozen)
    engine.store.log("instagram.delete.prepare", ident)
    return frozen


def approve(engine, deletion_id, account_id, media_id):
    """Approval must repeat BOTH frozen identifiers to prevent account confusion."""
    # Do not open the Store's nested IMMEDIATE transaction while one is active.
    _source(engine, account_id, media_id)
    with engine.store.db() as db:
        record = engine._load(db, "media-deletion", deletion_id)
        if record["status"] != "review":
            raise ValueError("Only an unapproved deletion request can be approved")
        if record["account_id"] != account_id or record["media_id"] != media_id:
            raise ValueError("Approval must match exact Instagram account AND media ID")
        record.update(status="approved", approved_at=time.time())
        engine.store.write(db, "media-deletion", deletion_id, record)
    engine.store.log("instagram.delete.approve", deletion_id)
    return record


def execute(engine, deletion_id):
    """One attempt on one owned media ID; no retry after uncertain provider response.

    The current Instagram Login API has no verified published-media DELETE grant.
    Fail closed until explicitly supported by an operator-verified adapter.
    """
    record = engine.store.get("media-deletion", deletion_id)
    if record["status"] != "approved":
        raise ValueError("Exact published-media deletion requires separate owner approval")
    _source(engine, record["account_id"], record["media_id"])
    a = engine.store.get("account", record["account_id"])
    if str(a.get("remote_id")) != record["account_remote_id"]:
        raise ValueError("Instagram account identity changed; reconnect and prepare a new request")

    # No official Instagram Login DELETE published media contract has been
    # established for this integration. Deliberately avoid a speculative
    # DELETE /{media-id} or escalation to a different connected account.
    record.update(
        status="manual_required",
        reason="Published Instagram media deletion is not verified for Instagram Login. "
               "Delete this exact Reel from the Instagram app, then reconcile manually. "
               "Adding Meta permissions or AWS access cannot bypass API support.",
        checked_at=time.time(),
    )
    engine.store.put("media-deletion", deletion_id, record)
    engine.store.log("instagram.delete.manual_required", deletion_id)
    return record


def status(engine, deletion_id):
    return engine.store.get("media-deletion", deletion_id)
