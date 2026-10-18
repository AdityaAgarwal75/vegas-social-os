"""Bounded, opt-in video-reference research for Vegas Social OS.

Public YouTube discovery and short-video analysis; no login/cookies, posting or
Flow usage. Visual interpretation is deliberately left to the connected host.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
from urllib.parse import urlsplit


_ALLOWED = {"youtube.com", "www.youtube.com", "m.youtube.com",
            "youtu.be", "www.youtu.be", "instagram.com", "www.instagram.com"}
_ACTIVE = threading.BoundedSemaphore(1)
_SCENE_TIME = re.compile(r"pts_time:([0-9]+(?:\\.[0-9]+)?)")
_MAX_BYTES = 100 * 1024 * 1024


def validate_url(url):
    if not isinstance(url, str) or len(url) > 1024 or any(ord(c) < 33 for c in url):
        raise ValueError("Supply one public HTTPS YouTube or Instagram video URL")
    p = urlsplit(url)
    if (p.scheme != "https" or p.hostname not in _ALLOWED
            or p.port not in (None, 443) or p.username or p.password or p.fragment):
        raise ValueError("Only HTTPS YouTube and Instagram video URLs are accepted")
    path = p.path.lower()
    if p.hostname in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if not (path == "/watch" or path.startswith(("/shorts/", "/live/"))):
            raise ValueError("Use a YouTube watch, live or Shorts video link")
    elif p.hostname in {"instagram.com", "www.instagram.com"}:
        if not path.startswith(("/reel/", "/p/", "/tv/")):
            raise ValueError("Use an Instagram Reel or post link")
    elif not re.fullmatch(r"/[A-Za-z0-9_-]{6,20}", p.path):
        raise ValueError("Invalid short YouTube link")
    return url


def _exec(argv, timeout):
    try:
        return subprocess.run(argv, capture_output=True, text=True,
                              timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        raise ValueError("Source timed out; the provider may be blocking VPS access") from None


def _ytdlp():
    path = os.getenv("VSO_INTELLIGENCE_YTDLP") or shutil.which("yt-dlp")
    if not path or not Path(path).is_file():
        raise ValueError("Video research backend not installed (yt-dlp)")
    return path


def _ffmpeg():
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise ValueError("FFmpeg and ffprobe are required")


def _update(engine, ident, **changes):
    with engine.store.db() as db:
        record = engine._load(db, "intelligence-job", ident)
        record.update(changes, updated_at=time.time())
        engine.store.write(db, "intelligence-job", ident, record)


def _source(engine, ident, url):
    _ffmpeg()
    folder = engine.store.root / "intelligence" / ident
    folder.mkdir(parents=True, exist_ok=True)
    common = [_ytdlp(), "--ignore-config", "--no-playlist", "--no-warnings",
              "--socket-timeout", "12", "--retries", "1", "--no-progress"]
    probe = _exec(common + ["--dump-single-json", "--skip-download", url], 75)
    if probe.returncode:
        raise ValueError("Source metadata unavailable (login, region, rate limit or deleted video)")
    try:
        raw = json.loads(probe.stdout)
    except (ValueError, TypeError):
        raise ValueError("Source did not return valid metadata") from None
    duration = raw.get("duration")
    if not isinstance(duration, (int, float)) or not 0 < duration <= 180:
        raise ValueError("MVP accepts videos up to 180 seconds with known duration")
    _update(engine, ident, stage="downloading")
    download = _exec(common + ["--max-filesize", "100M",
                "--match-filter", "duration <= 180",
                "-f", "best[height<=720][ext=mp4]/best[height<=720]/best",
                "--merge-output-format", "mp4", "-o",
                str(folder / "source.%(ext)s"), url], 125)
    if download.returncode:
        raise ValueError("Video download denied, too large or unavailable; no bypass attempted")
    videos = [f for f in folder.glob("source.*")
              if f.suffix.lower() in (".mp4", ".webm", ".mkv", ".mov")]
    if len(videos) != 1 or videos[0].stat().st_size > _MAX_BYTES:
        raise ValueError("Downloaded video missing, ambiguous or exceeds 100 MiB")
    return folder, videos[0], {
        "title": str(raw.get("title") or "")[:200],
        "creator": str(raw.get("uploader") or "")[:130],
        "duration_seconds": round(duration, 2),
        "views": raw.get("view_count") if type(raw.get("view_count")) is int else None,
        "upload_date": raw.get("upload_date"),
        "platform": "instagram" if "instagram" in urlsplit(url).hostname else "youtube",
    }


def _visual(engine, ident, folder, video):
    _update(engine, ident, stage="extracting_frames")
    contact = folder / "contact.jpg"
    # At most sixteen samples, separated by three seconds. The sheet is
    # a sampling aid, not a claim to have understood every frame.
    process = _exec(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
        "-threads", "1", "-i", str(video), "-vf",
        "fps=1/3,scale=240:-2,tile=4x4:padding=6:margin=6:color=black",
        "-frames:v", "1", "-y", str(contact)], 90)
    if process.returncode or not contact.exists():
        raise ValueError("FFmpeg could not create the contact sheet")
    cuts = _exec(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "info",
        "-threads", "1", "-i", str(video), "-vf",
        "select=gt(scene\\,0.32),showinfo", "-an", "-f", "null", "-"], 90)
    timestamps = [round(float(m.group(1)), 2)
                  for m in _SCENE_TIME.finditer(cuts.stderr)][:60]
    # Register only the contact sheet as private media; original external
    # footage remains in an isolated research cache and is never published.
    data = contact.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    destination = engine.store.root / "media" / (sha + ".jpg")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    engine.store.put("asset", sha, {"id": sha, "file": destination.name,
                                 "media_type": "image/jpeg", "size": len(data)})
    return sha, timestamps


def _analyze(engine, ident, url):
    try:
        folder, video, summary = _source(engine, ident, url)
        sheet, cuts = _visual(engine, ident, folder, video)
        _update(engine, ident, status="completed", stage="ready_for_host_review",
                metadata=summary, contact_sheet_asset_id=sheet,
                detected_cut_times=cuts,
                sampled_frame_interval_seconds=3,
                sample_limit=16,
                transcript_status="not_generated",
                visual_review="A host model must view the private contact sheet, inspect the real clip for details, and create an original script. Scene cuts are algorithmic estimates, not a verified creative analysis.",
                completed_at=time.time())
    except Exception as exc:
        _update(engine, ident, status="failed", stage="failed",
                error=str(exc)[:220])
    finally:
        # Reference files are temporary: do not accumulate copyrighted
        # source footage or failed partial downloads on owner VPS disks.
        shutil.rmtree(engine.store.root / "intelligence" / ident,
                      ignore_errors=True)
        _ACTIVE.release()


def analyze(engine, url, request_id):
    url = validate_url(url)
    if not isinstance(request_id, str) or not 3 <= len(request_id) <= 180:
        raise ValueError("Provide a stable research request ID")
    ident = engine.store.digest("intelligence:" + request_id)[:32]
    try:
        existing = engine.store.get("intelligence-job", ident)
        if existing.get("url") != url:
            raise ValueError("Request ID already belongs to another video")
        return existing
    except ValueError as e:
        if "another video" in str(e):
            raise
    if not _ACTIVE.acquire(blocking=False):
        raise ValueError("Another video analysis is already running; retry after it finishes")
    record = {"id": ident, "url": url, "status": "running", "stage": "queued",
              "created_at": time.time(), "updated_at": time.time(),
              "scope": "Private creative research only; no publishing or generation"}
    try:
        engine.store.put("intelligence-job", ident, record)
        threading.Thread(target=_analyze, args=(engine, ident, url), daemon=True).start()
    except Exception:
        _ACTIVE.release()
        raise
    return record


def status(engine, job_id):
    if not isinstance(job_id, str) or not re.fullmatch(r"[a-f0-9]{32}", job_id):
        raise ValueError("Invalid research job ID")
    record = engine.store.get("intelligence-job", job_id)
    if record["status"] == "running" and time.time() - record["updated_at"] > 300:
        _update(engine, job_id, status="interrupted",
                error="Worker stopped or exceeded the bounded research window; no automatic retry")
        record = engine.store.get("intelligence-job", job_id)
    return record


def _discover(engine, ident, query, limit):
    try:
        _update(engine, ident, stage="searching_youtube")
        search = "ytsearch" + str(limit) + ":" + query
        p = _exec([_ytdlp(), "--ignore-config", "--no-warnings", "--no-playlist",
                   "--flat-playlist", "--dump-single-json", "--socket-timeout", "12",
                   search], 105)
        if p.returncode:
            raise ValueError("YouTube discovery unavailable or rate-limited")
        payload = json.loads(p.stdout)
        rows = []
        for e in payload.get("entries") or []:
            if not isinstance(e, dict):
                continue
            vid = str(e.get("id") or "")
            if not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
                continue
            duration = e.get("duration")
            if not isinstance(duration, (int, float)) or not 0 < duration <= 180:
                continue
            views = e.get("view_count")
            uploaded = str(e.get("upload_date") or "")
            age_days = None
            if re.fullmatch(r"[0-9]{8}", uploaded):
                from datetime import datetime, timezone
                try:
                    age_days = max(1, (datetime.now(timezone.utc).date() -
                                       datetime.strptime(uploaded, "%Y%m%d").date()).days)
                except ValueError:
                    pass
            rows.append({"url": "https://www.youtube.com/watch?v=" + vid,
                         "title": str(e.get("title") or "")[:180],
                         "creator": str(e.get("channel") or e.get("uploader") or "")[:120],
                         "duration_seconds": round(duration, 1),
                         "upload_date": uploaded or None,
                         "views": views if type(views) is int else None,
                         "views_per_day": round(views / age_days, 1)
                             if type(views) is int and age_days else None,
                         "views_verified": False,
                         "candidate_only": True})
        _update(engine, ident, status="completed", stage="candidates_ready",
                candidates=rows, completed_at=time.time(),
                evidence="Public YouTube search candidates, not confirmed viral outliers. Verify each video's actual views and creator median before ranking.")
    except Exception as exc:
        _update(engine, ident, status="failed", stage="failed", error=str(exc)[:220])
    finally:
        _ACTIVE.release()


def discover(engine, query, request_id, limit=10):
    if not isinstance(query, str) or not 3 <= len(query.strip()) <= 120 or any(ord(c) < 32 for c in query):
        raise ValueError("Supply a short niche search query")
    if type(limit) is not int or not 1 <= limit <= 20:
        raise ValueError("Request between 1 and 20 candidate videos")
    if not isinstance(request_id, str) or not 3 <= len(request_id) <= 180:
        raise ValueError("Stable research request ID required")
    ident = engine.store.digest("discovery:" + request_id)[:32]
    try:
        old = engine.store.get("intelligence-job", ident)
        if old.get("query") != query or old.get("limit") != limit:
            raise ValueError("Request ID already belongs to another discovery")
        return old
    except ValueError as e:
        if "another discovery" in str(e):
            raise
    if not _ACTIVE.acquire(blocking=False):
        raise ValueError("Another research job is running")
    rec = {"id": ident, "query": query, "limit": limit,
           "status": "running", "stage": "queued", "created_at": time.time(),
           "updated_at": time.time(), "kind": "youtube_discovery"}
    try:
        engine.store.put("intelligence-job", ident, rec)
        threading.Thread(target=_discover, args=(engine, ident, query, limit),
                         daemon=True).start()
    except Exception:
        _ACTIVE.release()
        raise
    return rec
