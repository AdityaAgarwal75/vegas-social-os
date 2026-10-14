import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path

from .accounts import Accounts, graph_version
from . import net


class Engine:
    def __init__(self, store, base="http://127.0.0.1:8787"):
        self.store, self.base = store, base.rstrip("/")
        self.accounts = Accounts(store, base)

    def doctor(self):
        from . import flow_runtime
        return {"version": "0.7.0-alpha", "image_provider": "chatgpt-native-only",
                "state_backend": "supabase" if self.store.__class__.__name__ == "SupabaseStore" else "sqlite",
                "agent_first": True, "remote_browser": os.getenv("VSO_REMOTE_BROWSER") == "1",
                "native_images": "Host capability; unavailable hosts must pause, never substitute",
                "node": bool(shutil.which("node")), "ffmpeg": bool(shutil.which("ffmpeg")),
                "chrome_configured": bool(os.getenv("VSO_CHROME")),
                "flow_engine_installed": flow_runtime.installed(),
                "youtube_oauth_configured": self.accounts.config.public("google")["configured"],
                "facebook_oauth_configured": self.accounts.config.public("facebook")["configured"],
                "instagram_oauth_configured": self.accounts.config.public("instagram")["configured"],
                "supabase_sync_configured": all(os.getenv(x) for x in ("SUPABASE_URL", "SUPABASE_PUBLISHABLE_KEY", "SUPABASE_USER_JWT")),
                "live_integrations_verified": False}

    def channel_save(self, name, niche, language="English", account_ids=None):
        if not name.strip() or not niche.strip():
            raise ValueError("Channel name and niche are required")
        account_ids = account_ids or []
        for ident in account_ids:
            account = self.store.get("account", ident)
            if account["provider"] not in ("youtube", "instagram", "facebook"):
                raise ValueError("Only YouTube/Instagram/Facebook accounts are publishing destinations; Flow is generation and Drive is storage")
        ident = uuid.uuid4().hex
        body = {"id": ident, "name": name, "niche": niche, "language": language, "account_ids": account_ids}
        self.store.put("channel", ident, body)
        return body

    def plan_save(self, channel_id, concepts, request_id):
        channel = self.store.get("channel", channel_id)
        if len(concepts) != 2:
            raise ValueError("Provide exactly two distinct concepts")
        for c in concepts:
            if not all(isinstance(c.get(k), str) and c[k].strip() for k in ("title", "hook", "script")):
                raise ValueError("Each concept needs title, hook and script")
            if not isinstance(c.get("scenes"), list) or not 1 <= len(c["scenes"]) <= 12:
                raise ValueError("Each concept needs 1–12 scenes")
            for s in c["scenes"]:
                if not all(isinstance(s.get(k), str) and s[k].strip() for k in ("image_prompt", "video_prompt")):
                    raise ValueError("Each scene needs image_prompt and video_prompt")
        ident = self.store.digest("plan:" + channel_id + ":" + request_id)[:32]
        from .production import scenes
        concepts=scenes(concepts,ident)
        body = {"id": ident, "channel_id": channel_id, "channel_name": channel["name"],
                "concepts": concepts, "selected": None, "status": "concept_review", "images": {},
                "video": None, "budget": 0, "reserved": 0, "created_at": time.time()}
        with self.store.db() as db:
            row = db.execute("SELECT body FROM records WHERE kind='plan' AND id=?", (ident,)).fetchone()
            if row:
                old = json.loads(row[0])
                if old["concepts"] != concepts:
                    raise ValueError("Request ID already belongs to a different plan")
                return old
            self.store.write(db, "plan", ident, body)
        return body

    def concept_select(self, plan_id, concept, max_credits):
        if type(concept) is not int or concept not in (0, 1) or type(max_credits) is not int or not 0 <= max_credits <= 10000:
            raise ValueError("Concept must be 0 or 1; max_credits must be an integer from 0 to 10000")
        with self.store.db() as db:
            p = self._load(db, "plan", plan_id)
            if p["status"] not in ("concept_review", "images_pending"):
                raise ValueError("Production has progressed; create a new plan instead of changing approved content")
            if p["selected"] != concept:
                p["images"] = {}
            p.update(selected=concept, budget=max_credits, status="images_pending")
            self.store.write(db, "plan", plan_id, p)
        self.store.log("concept.select", plan_id)
        return p

    def image_tasks(self, plan_id):
        p = self.store.get("plan", plan_id)
        if p["selected"] is None:
            raise ValueError("Select a concept first")
        return {"provider": "chatgpt-native-only", "plan_id": plan_id,
                "instructions": "Call your host's native image generation tool separately for each scene. Import the actual outputs; do not claim images exist from prompts alone. Pause if no native image tool is available.",
                "tasks": [{"scene": i, "prompt": s["image_prompt"], "asset_id": p["images"].get(str(i))}
                          for i, s in enumerate(p["concepts"][p["selected"]]["scenes"])]}

    def asset_import(self, data_base64, media_type):
        if media_type not in ("image/png", "image/jpeg", "image/webp", "video/mp4"):
            raise ValueError("Supported media: PNG, JPEG, WebP, MP4")
        if len(data_base64) > 90_000_000:
            raise ValueError("Asset exceeds 64 MiB limit")
        try:
            data = base64.b64decode(data_base64, validate=True)
        except Exception:
            raise ValueError("Invalid base64 asset") from None
        if not data or len(data) > 64 * 1024 * 1024:
            raise ValueError("Asset is empty or exceeds 64 MiB limit")
        signatures = {"image/png": data.startswith(b"\x89PNG\r\n\x1a\n"),
                      "image/jpeg": data.startswith(b"\xff\xd8\xff"),
                      "image/webp": data.startswith(b"RIFF") and data[8:12] == b"WEBP",
                      "video/mp4": len(data) > 12 and data[4:8] == b"ftyp"}
        if not signatures[media_type]:
            raise ValueError("Asset bytes do not match declared media type")
        ident = hashlib.sha256(data).hexdigest()
        suffix = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "video/mp4": ".mp4"}[media_type]
        file = self.store.root / "media" / (ident + suffix)
        file.write_bytes(data)
        asset = {"id": ident, "file": file.name, "media_type": media_type, "size": len(data)}
        self.store.put("asset", ident, asset)
        return asset

    def asset_path(self, ident):
        asset = self.store.get("asset", ident)
        path = (self.store.root / "media" / asset["file"]).resolve()
        if path.parent != self.store.root / "media" or not path.is_file():
            raise ValueError("Asset unavailable")
        from .media import sha256_file
        if sha256_file(path) != ident:
            raise ValueError("Asset checksum mismatch")
        return path

    def image_attach(self, plan_id, scene, asset_id):
        a = self.store.get("asset", asset_id)
        self.asset_path(asset_id)
        if not a["media_type"].startswith("image/"):
            raise ValueError("A scene keyframe must be an image")
        with self.store.db() as db:
            p = self._load(db, "plan", plan_id)
            if p["status"] != "images_pending" or type(scene) is not int or not 0 <= scene < len(p["concepts"][p["selected"]]["scenes"]):
                raise ValueError("Invalid scene or production no longer accepts keyframes")
            p["images"][str(scene)] = asset_id
            self.store.write(db, "plan", plan_id, p)
        return p

    def images_approve(self, plan_id):
        with self.store.db() as db:
            p = self._load(db, "plan", plan_id)
            if p["status"] != "images_pending" or len(p["images"]) != len(p["concepts"][p["selected"]]["scenes"]):
                raise ValueError("Attach and review every scene image first")
            p["status"] = "ready"
            self.store.write(db, "plan", plan_id, p)
        self.store.log("images.approve", plan_id)
        return p

    def flow(self, operation, account_id, **kwargs):
        account = self.store.get("account", account_id)
        if account["provider"] != "flow":
            raise ValueError("Select a Flow account")
        from . import flow_runtime
        if account.get("service_alias") or (flow_runtime.configured() and operation != 'login'):
            from . import flow_service
            if operation == "login": return flow_service.login(self, account_id)
            if operation == "inspect": return flow_service.inspect(self, account_id)
            if operation == 'submit':
                from .video_service import submit
                return submit(self,account_id,kwargs['prompt'],kwargs['options'],kwargs['first_frame_id'],submission_id=kwargs['request_id'])
            if operation == 'poll':
                from .video_service import poll
                return poll(self,account_id,kwargs['job'])
            raise ValueError('Unsupported local Flow operation')
        if operation in ('submit','poll'):
            raise ValueError('Complete Flow engine is required; legacy experimental generation is disabled')
        worker = Path(__file__).resolve().parent.parent / "worker" / "flow.mjs"
        command = ["node", str(worker)]
        payload = {"operation": operation, "account_id": account_id, "data_dir": str(self.store.root), **kwargs}
        try:
            result = subprocess.run(command, input=json.dumps(payload), text=True, capture_output=True, timeout=50)
            body = json.loads(result.stdout)
        except Exception:
            raise ValueError("Flow worker interrupted; inspect the existing job before resubmitting") from None
        if not body.get("ok"):
            raise ValueError(body.get("error", "Flow worker failed"))
        if operation == 'login' and flow_runtime.configured(): flow_runtime.ensure(self,account_id)
        return body["result"]

    def flow_login(self, account_id):
        result = self.flow("login", account_id)
        if os.getenv("VSO_REMOTE_BROWSER") == "1":
            ticket = self.store.ticket("flow-browser", {"account_id": account_id}, ttl=600)
            return {**result, "login_url": self.base + "/flow/login?ticket=" + ticket,
                    "instructions": "Open the private link and sign into Google in this isolated browser. Enter passwords/2FA only there. Return here after opening a Flow project."}
        return {**result, "instructions": "Sign in yourself in the dedicated browser on the worker computer. Then call flow_inspect. Passwords and 2FA stay in Google's window."}

    def flow_inspect(self, account_id):
        result = self.flow("inspect", account_id)
        a = self.store.get("account", account_id)
        a["status"] = "workspace_ready" if result.get("workspace_ready") else "verification_required" if result.get("blocked") else "login_required"
        a["credits"] = result.get("credits")
        self.store.put("account", account_id, a)
        return result

    def video_request(self, plan_id, scene, account_id, max_credits, request_id, options=None):
        if type(max_credits) is not int or max_credits < 1 or type(scene) is not int:
            raise ValueError("Positive integer max_credits and integer scene are required")
        account=self.store.get('account',account_id)
        from .flow_runtime import installed
        if not account.get('service_alias') and not installed():
            raise ValueError('Install the complete Flow engine before reserving a production job')
        from .video_service import settings
        if not isinstance(options,dict): raise ValueError('Choose model, duration, resolution and aspect before generating')
        options=settings(options.get('model'),options.get('duration'),options.get('resolution'),options.get('aspect_ratio'),max_credits)
        from .flow_models import validate_observed
        validate_observed(self,account_id,options)
        ident = self.store.digest("video:" + request_id)[:32]
        with self.store.db() as db:
            row = db.execute("SELECT body FROM records WHERE kind='job' AND id=?", (ident,)).fetchone()
            if row:
                job = json.loads(row[0])
                if any(job[k] != v for k, v in {"plan_id": plan_id, "scene": scene, "account_id": account_id, "max_credits": max_credits, **({"options":options} if options else {})}.items()):
                    raise ValueError("Request ID already belongs to a different generation")
                return self.public_job(job)
            p = self._load(db, "plan", plan_id)
            a = self._load(db, "account", account_id)
            if p.get('revision_requested'):
                raise ValueError('Storyboard revision requested; review a new plan before new rendering')
            if a["provider"] != "flow" or a["status"] != "workspace_ready":
                raise ValueError("Inspect a signed-in Flow workspace before generation")
            if p["status"] not in ("ready", "generating") or not 0 <= scene < len(p["concepts"][p["selected"]]["scenes"]):
                raise ValueError("Approve keyframes and select a valid scene first")
            for row in db.execute("SELECT body FROM records WHERE kind='job'"):
                other = json.loads(row[0])
                if other["status"] in ("submitting", "processing", "unknown") or (other["plan_id"] == plan_id and other["scene"] == scene):
                    raise ValueError("Account is busy or scene already has a job; poll/reconcile it")
            for row in db.execute("SELECT body FROM records WHERE kind IN ('image-job','video-job')"):
                if json.loads(row[0])['status'] in ('submitting','processing','unknown'):
                    raise ValueError('Finish or reconcile active browser work before production')
            if p["reserved"] + max_credits > p["budget"]:
                raise ValueError("Production credit budget exceeded")
            from .production import enforce
            enforce(db,self._load(db,"channel",p["channel_id"]),account_id,max_credits)
            p["reserved"] += max_credits
            p["status"] = "generating"
            job = {"id": ident, "plan_id": plan_id, "scene": scene, "account_id": account_id,
                   "max_credits": max_credits, "options": options, "scene_id":p["concepts"][p["selected"]]["scenes"][scene].get("scene_id"), "input_sha256":self.store.digest(json.dumps({"prompt":p["concepts"][p["selected"]]["scenes"][scene]["video_prompt"],"image":p["images"][str(scene)],"options":options,"account_id":account_id},sort_keys=True)), "status": "submitting", "created_at": time.time()}
            self.store.write(db, "plan", plan_id, p)
            self.store.write(db, "job", ident, job)
        self.store.log("video.request", ident)
        try:
            prompt = p["concepts"][p["selected"]]["scenes"][scene]["video_prompt"]
            result = self.flow("submit", account_id, prompt=prompt, max_credits=max_credits,
                               first_frame=str(self.asset_path(p["images"][str(scene)])), first_frame_id=p["images"][str(scene)], options=options, request_id=ident)
            job.update(status="processing", worker=result)
        except ValueError as e:
            job.update(status="unknown", error=str(e))
        self.store.put("job", ident, job)
        return self.public_job(job)

    def video_poll(self, job_id):
        job = self.store.get("job", job_id)
        if job["status"] == "completed":
            return self.public_job(job)
        if job["status"] != "processing" or not job.get("worker"):
            raise ValueError("Submission outcome unknown; inspect Flow before any new request")
        result = self.flow("poll", job["account_id"], job=job["worker"])
        if result.get("completed"):
            if result.get('asset_id'): asset=self.store.get('asset',result['asset_id'])
            else:
                data = Path(result["file"]).read_bytes()
                asset = self.asset_import(base64.b64encode(data).decode(), "video/mp4")
            job.update(status="completed", asset_id=asset["id"])
            self.store.put("job", job_id, job)
        if result.get('status') in ('stopped','failed'):
            job.update(status=result['status'],error=result.get('error'));self.store.put('job',job_id,job)
        return {**self.public_job(job), "progress": result.get("status")}

    def video_assemble(self, plan_id):
        from .editing import start
        return start(self,plan_id,1080,1920,30,0,'',0.2,[],'assemble:'+plan_id)

    def video_attach(self, plan_id, asset_id):
        a = self.store.get("asset", asset_id)
        self.asset_path(asset_id)
        if a["media_type"] != "video/mp4":
            raise ValueError("Final output must be an MP4")
        with self.store.db() as db:
            p = self._load(db, "plan", plan_id)
            if p["status"] not in ("ready", "generating", "video_review"):
                raise ValueError("Approve images before attaching a final video")
            p.update(video=asset_id, status="video_review")
            self.store.write(db, "plan", plan_id, p)
        return p

    def publish_prepare(self, plan_id, account_id, title, caption, visibility="private"):
        p = self.store.get("plan", plan_id)
        a = self.store.get("account", account_id)
        if a["provider"]=="facebook":raise ValueError("Use post_prepare with this approved final asset; legacy production publishing does not support Facebook")
        channel = self.store.get("channel", p["channel_id"])
        if p["status"] != "video_review" or not p["video"]:
            raise ValueError("Attach a completed video for final review first")
        if account_id not in channel["account_ids"]:
            raise ValueError("Destination is not assigned to this channel")
        if a["provider"] not in ("youtube", "instagram", "facebook") or a["status"] != "connected":
            raise ValueError("Connect a supported publishing account")
        if a["provider"] == "instagram" and visibility != "public":
            raise ValueError("Instagram Reels publish publicly; set visibility=public explicitly")
        if visibility not in ("private", "unlisted", "public") or not 1 <= len(title) <= 100 or len(caption) > (2200 if a["provider"] == "instagram" else 5000):
            raise ValueError("Invalid visibility, title or caption length")
        body = {"plan_id": plan_id, "account_id": account_id, "asset_id": p["video"], "provider": a["provider"],
                "title": title, "caption": caption, "visibility": visibility}
        ident = self.store.digest(json.dumps(body, sort_keys=True))[:32]
        try:
            return self.store.get("publication", ident)
        except ValueError:
            pass
        body.update(id=ident, status="review", remote_id=None)
        self.store.put("publication", ident, body)
        return body

    def publish_approve(self, publication_id):
        with self.store.db() as db:
            p = self._load(db, "publication", publication_id)
            if p["status"] != "review":
                raise ValueError("Only a pending exact publication can be approved")
            p["status"] = "approved"
            self.store.write(db, "publication", publication_id, p)
        self.store.log("publish.approve", publication_id)
        return p

    def publish_execute(self, publication_id):
        with self.store.db() as db:
            p = self._load(db, "publication", publication_id)
            if p["status"] in ("published", "processing", "uploading", "unknown"):
                return p
            if p["status"] != "approved":
                raise ValueError("Approve the exact destination, video and text before publishing")
            p["status"] = "uploading"
            self.store.write(db, "publication", publication_id, p)
        try:
            token = self.accounts.token(p["account_id"])
            a = self.store.get("account", p["account_id"])
            file = self.asset_path(p["asset_id"])
            if p["provider"] == "youtube":
                metadata = {"snippet": {"title": p["title"], "description": p["caption"]},
                            "status": {"privacyStatus": p["visibility"]}}
                _, headers = net.request("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
                                         method="POST", token=token, payload=metadata,
                                         headers={"X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(file.stat().st_size)})
                url = headers.get("Location") or headers.get("location")
                if not url:
                    raise ValueError("YouTube upload session missing")
                # Persist the resumable URL encrypted, never send it to the agent.
                self.store.secret("upload:" + publication_id, {"url": url})
                result, _ = net.request(url, method="PUT", token=token, raw=file.read_bytes(), headers={"Content-Type": "video/mp4"})
                p.update(status="published", remote_id=result["id"], url="https://www.youtube.com/watch?v=" + result["id"])
            else:
                if not self.base.startswith("https://"):
                    raise ValueError("Instagram needs a publicly reachable HTTPS media URL; configure VSO_PUBLIC_URL")
                media_ticket = self.store.ticket("media", {"asset_id": p["asset_id"]}, ttl=3600)
                # Media tokens are reusable for range/repeated fetches during processing.
                self.store.put("media-link", self.store.digest(media_ticket), {"asset_id": p["asset_id"], "expires": time.time() + 3600})
                result, _ = net.request(f"https://graph.instagram.com/{self.accounts.config.version('instagram')}/{a['remote_id']}/media", method="POST", token=token,
                                        form={"media_type": "REELS", "video_url": self.base + "/media?ticket=" + media_ticket, "caption": p["caption"]})
                p.update(status="processing", container_id=result["id"])
        except Exception:
            p.update(status="unknown", error="Publishing interrupted or rejected; inspect provider before retrying")
        self.store.put("publication", publication_id, p)
        self.store.log("publish.execute", publication_id)
        return p

    def publish_poll(self, publication_id):
        p = self.store.get("publication", publication_id)
        if p["status"] == "published":
            return p
        if p["provider"] != "instagram" or p["status"] != "processing":
            raise ValueError("This publication needs manual reconciliation")
        token = self.accounts.token(p["account_id"])
        info, _ = net.request(f"https://graph.instagram.com/{self.accounts.config.version('instagram')}/{p['container_id']}?fields=status_code", token=token)
        if info.get("status_code") == "FINISHED":
            # Claim the write before network I/O; competing polls cannot publish twice.
            with self.store.db() as db:
                current = self._load(db, "publication", publication_id)
                if current["status"] != "processing":
                    return current
                p["status"] = "uploading"
                self.store.write(db, "publication", publication_id, p)
            a = self.store.get("account", p["account_id"])
            try:
                result, _ = net.request(f"https://graph.instagram.com/{self.accounts.config.version('instagram')}/{a['remote_id']}/media_publish", method="POST", token=token,
                                        form={"creation_id": p["container_id"]})
                p.update(status="published", remote_id=result["id"])
            except Exception:
                p.update(status="unknown", error="Publish outcome unknown; reconcile before retry")
            self.store.put("publication", publication_id, p)
        return {**p, "provider_status": info.get("status_code")}

    def snapshot(self):
        result = {kind: self.store.all(kind) for kind in ("channel", "account", "plan", "asset", "job", "publication", "image-job", "video-job", "strategy", "content-request", "review-request")}
        result["job"] = [self.public_job(j) for j in result["job"]]
        result["video-job"]=[self.public_job(j) for j in result["video-job"]]
        from . import flow_runtime
        result['flow_engine_installed'] = flow_runtime.installed()
        return result

    @staticmethod
    def public_job(job):
        return {k: v for k, v in job.items() if k != "worker"}

    @staticmethod
    def _load(db, kind, ident):
        row = db.execute("SELECT body FROM records WHERE kind=? AND id=?", (kind, ident)).fetchone()
        if not row:
            raise ValueError(f"{kind} not found")
        return json.loads(row[0])
