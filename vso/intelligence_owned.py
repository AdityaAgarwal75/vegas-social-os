"""Owner-authorized Instagram Reel reference ingestion and account performance.

Uses the official linked Facebook Page Graph API to establish ownership and
resolve temporary MP4 media. Never reads browser cookies or searches other
people's private video media.
"""
import json
import re
import shutil
import statistics
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

from . import intelligence
from . import instagram_analytics as ig
from . import net
from .research import PinnedHTTPS, public_address


def performance(engine, account_id, limit=100):
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("Choose 1–100 recent media items")
    result = ig.media_list(engine, account_id, limit)
    observations = [r for r in result["reels"] if type(r.get("views")) is int]
    baseline = statistics.median(r["views"] for r in observations) if observations else None
    rank = []
    for r in observations:
        rank.append({
            "media_id": r["id"], "url": r["permalink"],
            "views": r["views"], "likes": r.get("likes"),
            "comments": r.get("comments"), "timestamp": r.get("timestamp"),
            "caption_excerpt": r["caption"][:200],
            "views_relative_to_sample_median": round(r["views"] / baseline, 2)
                if baseline and baseline > 0 else None,
        })
    return {
        "account_id": account_id, "username": result["username"],
        "sample_reels": len(result["reels"]), "median_views": baseline,
        "ranking_complete": result["ranking_complete"],
        "top_reel": rank[0] if result["ranking_complete"] and rank else None,
        "ranked": rank,
        "method": "Verified linked Facebook Page, official Meta account media + observed views. Median is of the sampled Reels, not causal performance evidence.",
        "limitations": "Small historical samples and mixed post ages can bias comparisons. Data is owner-scoped and does not discover competitors or guarantee virality."
    }


def _owned_media(engine, account_id, media_id):
    if not isinstance(media_id, str) or not re.fullmatch(r"[0-9]{10,30}", media_id):
        raise ValueError("Supply the exact numeric owned Instagram media ID")
    owner, root, token = ig._context(engine, account_id)
    items, _ = ig._pages(root, token, owner["remote_id"], ig._FIELDS, 100)
    found = next((x for x in items if str(x.get("id")) == media_id and ig._reel(x)), None)
    if found is None:
        raise ValueError("Reel was not found among the owner account's most recent 100 media items")
    record, _ = net.request(root + "/" + media_id +
                            "?fields=id,media_type,media_product_type,media_url", token=token)
    if record.get("id") != media_id or record.get("media_product_type") != "REELS":
        raise ValueError("Provider did not verify this Instagram Reel identity")
    url = record.get("media_url")
    if not isinstance(url, str) or not url:
        raise ValueError("Provider did not return an authorized media URL")
    return found, url


def _cdn_download(url, destination):
    """One no-redirect, pinned-TLS bounded download from Meta's CDN."""
    p = urlsplit(url)
    host = p.hostname or ""
    if (p.scheme != "https" or p.port not in (None, 443) or p.username or
            p.password or p.fragment or
            not (host.endswith(".cdninstagram.com") or host.endswith(".fbcdn.net"))):
        raise ValueError("Meta returned an unsupported media CDN host")
    conn = PinnedHTTPS(host, public_address(host))
    length = 0
    try:
        conn.request("GET", (p.path or "/") + ("?" + p.query if p.query else ""),
                     headers={"Accept": "video/mp4", "User-Agent": "VegasSocialOS/0.13 research"})
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError("Meta CDN media cannot be downloaded")
        if "video/" not in response.getheader("Content-Type", ""):
            raise ValueError("Meta CDN response was not a video")
        raw_len = response.getheader("Content-Length")
        if raw_len and int(raw_len) > intelligence._MAX_BYTES:
            raise ValueError("Reel exceeds 100 MiB video reference limit")
        with destination.open("xb") as output:
            while True:
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                length += len(chunk)
                if length > intelligence._MAX_BYTES:
                    raise ValueError("Reel download exceeded size limit")
                output.write(chunk)
        if length < 1024:
            raise ValueError("Reel media was empty")
    finally:
        conn.close()


def _duration(path):
    tool = shutil.which("ffprobe")
    if not tool:
        raise ValueError("FFprobe not installed")
    out = intelligence._exec([tool, "-v", "error", "-show_entries",
                 "format=duration", "-of", "json", str(path)], 20)
    if out.returncode:
        raise ValueError("Reference media could not be validated")
    try:
        seconds = float(json.loads(out.stdout)["format"]["duration"])
    except (ValueError, KeyError, TypeError):
        raise ValueError("Media duration unavailable") from None
    if not 0 < seconds <= 180:
        raise ValueError("Only Reels up to 180 seconds can be analyzed in this MVP")
    return round(seconds, 2)


def _run(engine, ident, account_id, media_id):
    folder = engine.store.root / "intelligence" / ident
    try:
        intelligence._ffmpeg()
        folder.mkdir(parents=True, exist_ok=True)
        intelligence._update(engine, ident, stage="verifying_account_and_media")
        found, media_url = _owned_media(engine, account_id, media_id)
        intelligence._update(engine, ident, stage="downloading_meta_authorized_video")
        video = folder / "source.mp4"
        _cdn_download(media_url, video)
        duration = _duration(video)
        sheet, cuts = intelligence._visual(engine, ident, folder, video)
        intelligence._update(engine, ident, status="completed",
          stage="ready_for_host_review", completed_at=time.time(),
          metadata={"platform": "instagram", "owner_account_id": account_id,
                    "media_id": media_id, "url": found.get("permalink"),
                    "duration_seconds": duration,
                    "caption_excerpt": str(found.get("caption", ""))[:300]},
          contact_sheet_asset_id=sheet, detected_cut_times=cuts,
          sampled_frame_interval_seconds=3,
          transcript_status="not_generated",
          visual_review="Technical contact sheet and estimated cuts only. Agent must actually view image and build original story. Never pretend to analyze audio or full video here.")
    except Exception as exc:
        intelligence._update(engine, ident, status="failed", stage="failed",
                             error=str(exc)[:220])
    finally:
        shutil.rmtree(folder, ignore_errors=True)
        intelligence._ACTIVE.release()


def analyze_owned(engine, account_id, media_id, request_id):
    if not isinstance(account_id, str) or not re.fullmatch(r"[a-f0-9]{32}", account_id):
        raise ValueError("Choose a connected owner Instagram account ID")
    if not isinstance(media_id, str) or not re.fullmatch(r"[0-9]{10,30}", media_id):
        raise ValueError("Choose one exact Instagram Reel ID")
    if not isinstance(request_id, str) or not 3 <= len(request_id) <= 180:
        raise ValueError("Provide a stable research request ID")
    ident = engine.store.digest("owned-reel:" + request_id)[:32]
    try:
        old = engine.store.get("intelligence-job", ident)
        if old.get("account_id") != account_id or old.get("media_id") != media_id:
            raise ValueError("Request ID belongs to a different Reel")
        return old
    except ValueError as exc:
        if "different Reel" in str(exc):
            raise
    if not intelligence._ACTIVE.acquire(blocking=False):
        raise ValueError("A reference research job is already running")
    record = {"id": ident, "account_id": account_id, "media_id": media_id,
              "status": "running", "stage": "queued",
              "created_at": time.time(), "updated_at": time.time(),
              "scope": "Official owner Meta media; analysis only, no publishing"}
    try:
        engine.store.put("intelligence-job", ident, record)
        threading.Thread(target=_run, args=(engine, ident, account_id, media_id),
                         daemon=True).start()
    except Exception:
        intelligence._ACTIVE.release()
        raise
    return record
