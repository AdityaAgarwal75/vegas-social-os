"""Read-only, owner-scoped Instagram Reel metrics through a verified Facebook Page.

No browser scraping, credential exposure, guessed view totals, or implicit posting.
"""
import re
import urllib.parse

from . import net

_ID = re.compile(r"^[0-9]{10,30}$")
_FIELDS = "id,caption,media_type,media_product_type,permalink,timestamp,like_count,comments_count,thumbnail_url"
_DETAIL_METRICS = ("reach", "saved", "shares", "total_interactions",
                   "ig_reels_avg_watch_time", "ig_reels_video_view_total_time")


def _context(engine, account_id):
    account = engine.store.get("account", account_id)
    if account.get("provider") != "instagram" or account.get("status") != "connected":
        raise ValueError("Choose a connected Instagram professional account")
    ig_id = str(account.get("remote_id") or "")
    if not _ID.fullmatch(ig_id):
        raise ValueError("Instagram account identity is not verified")
    pages = [
        p for p in engine.store.all("account")
        if p.get("provider") == "facebook"
        and p.get("status") == "connected"
        and str(p.get("linked_instagram_id") or "") == ig_id
        and {"instagram_basic", "instagram_manage_insights", "pages_read_engagement",
             "pages_show_list"}.issubset(set(p.get("permissions") or []))
        and (not p.get("linked_instagram_username")
             or p["linked_instagram_username"].casefold() == str(account.get("name", "")).casefold())
    ]
    if len(pages) != 1:
        raise ValueError("Connect exactly one Facebook Page linked to this Instagram account with instagram_manage_insights permission")
    page = pages[0]
    token = engine.accounts.token(page["id"])
    root = "https://graph.facebook.com/" + engine.accounts.config.version("facebook")
    # The cached Page association cannot authorize access by itself.
    identity, _ = net.request(root + "/" + page["remote_id"]
                              + "?fields=instagram_business_account{id,username}", token=token)
    linked = identity.get("instagram_business_account") or {}
    if str(linked.get("id")) != ig_id or (
        linked.get("username") and linked["username"].casefold() != str(account.get("name", "")).casefold()
    ):
        raise ValueError("Live Facebook Page-to-Instagram identity verification failed")
    return account, root, token


def _pages(root, token, ig_id, fields, limit):
    """Only follow opaque cursors on a constructed fixed-host URL."""
    items, seen_ids, seen_cursors = [], set(), set()
    after = None
    while len(items) < limit:
        params = {"fields": fields, "limit": min(100, limit - len(items))}
        if after:
            params["after"] = after
        result, _ = net.request(root + "/" + ig_id + "/media?"
                                + urllib.parse.urlencode(params), token=token)
        for media in result.get("data", []):
            if not isinstance(media, dict):
                continue
            media_id = str(media.get("id") or "")
            if _ID.fullmatch(media_id) and media_id not in seen_ids:
                items.append(media)
                seen_ids.add(media_id)
                if len(items) == limit:
                    break
        cursors = result.get("paging", {}).get("cursors", {})
        next_cursor = cursors.get("after") if result.get("paging", {}).get("next") else None
        if not next_cursor:
            return items, True
        if not isinstance(next_cursor, str) or len(next_cursor) > 512 or next_cursor in seen_cursors:
            raise ValueError("Instagram pagination cursor was invalid or repeated")
        seen_cursors.add(next_cursor)
        after = next_cursor
    # Reaching the requested limit may omit older posts; don't claim a full ranking.
    return items, False


def _metric(root, token, media_id, metric):
    result, _ = net.request(root + "/" + media_id + "/insights?"
                            + urllib.parse.urlencode({"metric": metric}), token=token)
    for item in result.get("data", []):
        if item.get("name") != metric:
            continue
        total = (item.get("total_value") or {}).get("value")
        if total is None:
            values = item.get("values") or []
            total = values[-1].get("value") if values else None
        if isinstance(total, (int, float)) and not isinstance(total, bool) and total >= 0:
            return total
    return None


def _reel(media):
    return str(media.get("media_product_type") or "").upper() == "REELS"


def _public(media):
    return {
        "id": str(media["id"]),
        "caption": str(media.get("caption") or "")[:500],
        "permalink": str(media.get("permalink") or ""),
        "timestamp": media.get("timestamp"),
        "media_type": media.get("media_type"),
        "media_product_type": media.get("media_product_type"),
        "thumbnail_url": media.get("thumbnail_url"),
        "likes": media.get("like_count"),
        "comments": media.get("comments_count"),
    }


def _views(root, token, media):
    record = _public(media)
    try:
        record["views"] = _metric(root, token, record["id"], "views")
    except ValueError:
        record["views"] = None
    record["views_available"] = record["views"] is not None
    return record


def media_list(engine, account_id, limit=100):
    """Rank an account's observed Reels by actual views, without fabricated zeros."""
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("Choose 1 to 100 media items")
    account, root, token = _context(engine, account_id)
    media, complete = _pages(root, token, account["remote_id"], _FIELDS, limit)
    reels = [_views(root, token, m) for m in media if _reel(m)]
    reels.sort(key=lambda r: (r["views"] is None, -(r["views"] or 0)))
    ranked = bool(reels) and complete and all(r["views_available"] for r in reels)
    return {
        "account_id": account_id, "username": account.get("name"),
        "scanned_media": len(media), "reels_found": len(reels),
        "ranking_complete": ranked,
        "note": ("All listed Reels returned views and the media list was complete."
                 if ranked else "Top Reel cannot be certified: some views were unavailable or media pagination was incomplete."),
        "top_reel": reels[0] if ranked else None, "reels": reels,
    }


def media_insights(engine, account_id, media_id):
    """Detailed views/engagement for one Reel verified to belong to the given account."""
    if not isinstance(media_id, str) or not _ID.fullmatch(media_id):
        raise ValueError("Choose an exact numeric Instagram media ID")
    account, root, token = _context(engine, account_id)
    # Meta's media read uses this exact Instagram owner, not an arbitrary media ID.
    media, _ = _pages(root, token, account["remote_id"], _FIELDS, 500)
    match = next((m for m in media if str(m.get("id")) == media_id), None)
    if not match or not _reel(match):
        raise ValueError("This Reel was not found among the account's latest 500 media items")
    record = _views(root, token, match)
    record["insights"] = {}
    record["unavailable_metrics"] = []
    for metric in _DETAIL_METRICS:
        try:
            value = _metric(root, token, media_id, metric)
        except ValueError:
            value = None
        if value is None:
            record["unavailable_metrics"].append(metric)
        else:
            record["insights"][metric] = value
    record["note"] = "Unavailable metrics are unknown, not zero; Instagram may limit historic watch-time and retention data."
    return record
