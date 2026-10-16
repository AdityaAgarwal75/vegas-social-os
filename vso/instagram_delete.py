"""Review-gated Instagram media deletion via Facebook Login for Business.

Only an explicitly connected Facebook Page that proves a *numeric* link to the
same professional Instagram account may authorize a media deletion. No
Instagram Login token and no Page belonging to a different account may be used.
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
        raise ValueError("Media must match exactly one published post recorded for the Instagram account")
    return account, matches[0]


def _facebook_page(engine, ig_account):
    """One Facebook Page with the exact IG numeric ID and delete permission."""
    target = str(ig_account.get("remote_id", ""))
    if not _ID.fullmatch(target):
        raise ValueError("Instagram account lacks verified numeric identity")
    matches = [
        p for p in engine.store.all("account")
        if p.get("provider") == "facebook"
        and p.get("status") == "connected"
        and str(p.get("linked_instagram_id") or "") == target
        and "instagram_manage_contents" in p.get("permissions", [])
        and "instagram_basic" in p.get("permissions", [])
        and "pages_show_list" in p.get("permissions", [])
    ]
    if len(matches) != 1:
        raise ValueError("Connect exactly one authorized Facebook Page linked to this Instagram account, "
                         "with instagram_manage_contents permission")
    page = matches[0]
    if (page.get("linked_instagram_username")
            and page["linked_instagram_username"].casefold() != str(ig_account.get("name", "")).casefold()):
        raise ValueError("Facebook-linked Instagram username mismatch")
    return page


def prepare(engine, account_id, media_id, request_id):
    """Freeze exact Instagram account, Facebook Page, and prior publication for review."""
    if not isinstance(request_id, str) or not 1 <= len(request_id) <= _MAX_REQUEST:
        raise ValueError("A stable deletion request ID is required")
    account, publication = _source(engine, account_id, media_id)
    page = _facebook_page(engine, account)
    ident = engine.store.digest("instagram-delete:" + request_id)[:32]
    frozen = {
        "id": ident,
        "kind": "instagram-media-delete",
        "provider": "instagram",
        "account_id": account_id,
        "account_remote_id": str(account["remote_id"]),
        "username": account.get("name", ""),
        "facebook_account_id": page["id"],
        "facebook_page_id": str(page["remote_id"]),
        "media_id": media_id,
        "publication_id": publication["id"],
        "caption_excerpt": str(publication.get("caption") or "")[:180],
        "status": "review",
    }
    with engine.store.db() as db:
        row = db.execute("SELECT body FROM records WHERE kind='media-deletion' AND id=?", (ident,)).fetchone()
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
    """Separate explicit approval repeats BOTH frozen identifiers."""
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
    """Attempt once; uncertain outcomes are not automatically retried."""
    record = engine.store.get("media-deletion", deletion_id)
    if record.get("status") != "approved":
        raise ValueError("Exact Instagram media deletion requires separate owner approval")
    if not record.get("facebook_account_id") or not record.get("facebook_page_id"):
        raise ValueError("Old deletion requests lacking a verified Facebook Page cannot be executed")
    account, pub = _source(engine, record["account_id"], record["media_id"])
    page = _facebook_page(engine, account)
    if (str(account.get("remote_id")) != record["account_remote_id"]
            or page["id"] != record["facebook_account_id"]
            or str(page["remote_id"]) != record["facebook_page_id"]
            or pub["id"] != record["publication_id"]):
        raise ValueError("Page, Instagram account or publication identity changed; request new approval")

    with engine.store.db() as db:
        current = engine._load(db, "media-deletion", deletion_id)
        if current["status"] != "approved":
            raise ValueError("This deletion was already attempted")
        current.update(status="submitting", attempted_at=time.time())
        engine.store.write(db, "media-deletion", deletion_id, current)
    engine.store.log("instagram.delete.submitting", deletion_id)

    try:
        token = engine.accounts.token(page["id"])
        root = "https://graph.facebook.com/" + engine.accounts.config.version("facebook")
        # Re-read Page -> IG association through Graph, not only local state.
        verified, _ = net.request(root + "/" + record["facebook_page_id"]
                                  + "?fields=instagram_business_account{id,username}", token=token)
        linked = verified.get("instagram_business_account") or {}
        if str(linked.get("id")) != record["account_remote_id"]:
            raise ValueError("Meta's current Facebook Page links to a different Instagram account")
        if linked.get("username") and linked["username"].casefold() != record["username"].casefold():
            raise ValueError("Meta Instagram handle does not match the approved account")

        media, _ = net.request(root + "/" + record["media_id"]
                               + "?fields=id,username,media_product_type", token=token)
        if str(media.get("id")) != record["media_id"] or str(media.get("username", "")).casefold() != record["username"].casefold():
            raise ValueError("Meta media ownership cannot be verified for the approved Instagram account")

        response, _ = net.request(root + "/" + record["media_id"], method="DELETE", token=token)
        if response.get("success") is not True:
            raise ValueError("Meta did not affirm the deletion")
        record.update(status="deleted", deleted_at=time.time(), provider_confirmed=True)
        engine.store.put("media-deletion", deletion_id, record)
        engine.store.log("instagram.delete.confirmed", deletion_id)
        return record
    except (ValueError, KeyError, TypeError):
        # A network interruption during DELETE can be ambiguous; no replay.
        record.update(status="unknown", checked_at=time.time(),
                      reason="Meta deletion not confirmed. Inspect this exact media ID before further action; never retry automatically.")
        engine.store.put("media-deletion", deletion_id, record)
        engine.store.log("instagram.delete.unconfirmed", deletion_id)
        return record


def status(engine, deletion_id):
    return engine.store.get("media-deletion", deletion_id)
