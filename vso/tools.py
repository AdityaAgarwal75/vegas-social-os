import inspect
import json


def registry(engine):
    s = engine.store
    def account_start(provider, label): return engine.accounts.start(provider, label)
    def account_list(): return s.all("account")
    def account_disconnect(account_id):
        s.disconnect(account_id)
        return {"status": "disconnected", "note": "Also revoke the app at the provider; Flow profiles require explicit local deletion"}
    def channel_list(): return s.all("channel")
    def plan_list(): return s.all("plan")
    def job_list(): return [engine.public_job(j) for j in s.all("job")]
    def publication_list(): return s.all("publication")
    def account_info(account_id): return engine.accounts.info(account_id)
    def guide():
        from pathlib import Path
        return {"instructions": (Path(__file__).parent.parent / "skills/vegas-social-master/SKILL.md").read_text()}
    def cloud_sync():
        from .cloud import sync
        return sync(engine)
    def schedule_daily(hour, timezone, channel_ids):
        from .schedule import save
        return save(engine, hour, timezone, channel_ids)
    def morning_queue():
        from .schedule import tick
        return tick(engine)
    def setup_plan(capabilities):
        from .bootstrap import plan
        return plan(capabilities)
    def onboarding_status():
        from .profile import status
        return status(engine)
    def profile_save(name, brand, timezone, goals):
        from .profile import save
        return save(engine, name, brand, timezone, goals)
    def setup_receipt_save(receipt):
        from .bootstrap import verify_receipt
        result = verify_receipt(receipt)
        s.put("setup", "receipt", result)
        return result
    def asset_archive_drive(asset_id, account_id):
        from .drive import archive
        return archive(engine, asset_id, account_id)
    def drive_archive_reconcile(archive_id):
        from .drive import reconcile
        return reconcile(engine, archive_id)
    def flow_account_add(label):
        link = engine.accounts.start("flow", label)
        from urllib.parse import urlsplit, parse_qs
        account = engine.accounts.authorize(parse_qs(urlsplit(link["url"]).query)["ticket"][0])["flow"]
        return account
    def flow_services_sync():
        from .flow_service import sync
        return sync(engine)
    def flow_image_request(account_id, prompt, model, aspect_ratio, max_credits, request_id):
        from .flow_service import image_request
        return image_request(engine, account_id, prompt, model, aspect_ratio, max_credits, request_id)
    def flow_image_poll(job_id):
        from .flow_service import image_poll
        return image_poll(engine, job_id)
    def connection_setup(): return engine.accounts.config.status()
    def post_prepare(account_id, asset_ids, title, caption, visibility, options, request_id):
        from .publishing import prepare
        return prepare(engine, account_id, asset_ids, title, caption, visibility, options, request_id)
    def post_execute(publication_id):
        from .publishing import execute
        return execute(engine, publication_id)
    def post_poll(publication_id):
        from .publishing import poll
        return poll(engine, publication_id)
    def post_schedule(publication_id, schedule_at):
        from .publishing import schedule
        return schedule(engine, publication_id, schedule_at)
    def post_reconcile(publication_id):
        from .publishing import reconcile
        return reconcile(engine, publication_id)
    def post_resume(publication_id):
        from .publishing import resume
        return resume(engine, publication_id)
    def post_cancel(publication_id):
        from .publishing import cancel
        return cancel(engine, publication_id)
    def post_retry_thumbnail(publication_id):
        from .publishing import retry_thumbnail
        return retry_thumbnail(engine, publication_id)
    def automation_status():
        from .automation import status
        return status(engine)
    def automation_pause():
        from .automation import pause
        return pause(engine)
    def brief_complete(brief_id, plan_id):
        from .automation import complete
        return complete(engine, brief_id, plan_id)
    def research_fetch(url):
        from .research import fetch
        return fetch(engine, url)
    def research_save(channel_id, title, summary, sources):
        from .research import save
        return save(engine, channel_id, title, summary, sources)
    def continuity_frame(asset_id,retained_seconds=0):
        from .continuity import extract
        return extract(engine,asset_id,retained_seconds)
    def flow_model_catalog(account_id=''):
        from .flow_models import catalog
        return catalog(engine,account_id)
    def flow_models_refresh(account_id):
        from .flow_models import refresh
        return refresh(engine,account_id)
    def flow_video_request(account_id,prompt,model,duration,resolution,aspect_ratio,max_credits,request_id,first_frame_id='',last_frame_id='',reference_asset_ids=None):
        from .video_service import request
        return request(engine,account_id,prompt,model,duration,resolution,aspect_ratio,max_credits,request_id,first_frame_id,last_frame_id,reference_asset_ids)
    def flow_video_poll(job_id):
        from .video_service import check
        return check(engine,job_id)
    def strategy_save(channel_id,audience,goal,voice,pillars):
        from .content import strategy_save
        return strategy_save(engine,channel_id,audience,goal,voice,pillars)
    def content_request(channel_id,week_start,request_id):
        from .content import content_request
        return content_request(engine,channel_id,week_start,request_id)
    def content_plan_save(request_id,items):
        from .content import content_plan_save
        return content_plan_save(engine,request_id,items)
    def content_plan_approve(request_id):
        from .content import content_plan_approve
        return content_plan_approve(engine,request_id)
    def content_queue(): return engine.store.all('content-request')
    def reel_review(script,hook,on_screen,target_seconds,words_per_minute=150):
        from .content import reel_review
        return reel_review(script,hook,on_screen,target_seconds,words_per_minute)
    def workflow_audit():
        from .audit import status
        return status(engine)
    methods = {f.__name__: f for f in (account_start, account_list, account_disconnect, channel_list, continuity_frame, flow_model_catalog, flow_models_refresh, flow_video_request, flow_video_poll, strategy_save, content_request, content_plan_save, content_plan_approve, content_queue, reel_review, workflow_audit,
              plan_list, job_list, publication_list, account_info, guide, cloud_sync, schedule_daily, morning_queue,
              setup_plan, onboarding_status, profile_save, setup_receipt_save, asset_archive_drive, drive_archive_reconcile,
              flow_account_add, flow_services_sync, flow_image_request, flow_image_poll, connection_setup, post_prepare, post_execute, post_poll, post_schedule, post_reconcile, post_resume, post_cancel, post_retry_thumbnail,
              automation_status, automation_pause, brief_complete, research_fetch, research_save)}
    for name in ("doctor", "channel_save", "plan_save", "concept_select", "image_tasks", "asset_import", "image_attach",
                 "images_approve", "flow_login", "flow_inspect", "video_request", "video_poll", "video_assemble",
                 "video_attach", "publish_prepare", "publish_approve", "publish_execute", "publish_poll"):
        methods[name] = getattr(engine, name)
    return methods


DESCRIPTIONS = {
    "continuity_frame":"Extract the last actual retained frame of a private imported MP4 for reviewed continuity. Local only; no generation, spend or source overwrite.",
    "flow_model_catalog":"Read model-specific settings with documentation/live provenance; availability is account-specific.",
    "flow_models_refresh":"Inspect idle private Flow model menus and restore mode. No generation or spend.",
    "flow_video_request":"Request one explicitly authorized clip with exact model/settings, references OR frames, stable ID and credit ceiling. 0 is free-only preflight.",
    "flow_video_poll":"Poll original clip and import exact MP4 without resubmitting.",
    "strategy_save":"Save channel audience, objective, brand voice and content pillars.",
    "content_request":"Queue an evidence-backed content strategy brief for a real connected host agent; does not run ChatGPT.",
    "content_plan_save":"Save agent-created weekly calendar/scripts with sources for exact review; does not publish.",
    "content_plan_approve":"Freeze an explicitly reviewed editorial calendar; publishing needs separate approval.",
    "content_queue":"Read pending strategy requests and reviewed editorial calendars.",
    "reel_review":"Review hook, estimated speaking duration, beat length and on-screen text. Heuristics only, no performance guarantees.",
    "workflow_audit":"Read truthful local prerequisites, account readiness and unresolved jobs; no publishing or spend.",
    "flow_services_sync": "Discover only administrator-configured local Flow services without copying browser sessions or exposing secrets.",
    "flow_image_request": "Generate one expressly requested diagnostic/standalone Flow image with exact account/model/credit cap and stable request ID. Not a substitute for native campaign keyframes.",
    "flow_image_poll": "Retrieve the original existing image job and import its verified downloaded bytes. Never resubmits.",
    "connection_setup": "Read provider setup steps, scopes and exact callback URLs. Never returns secrets.",
    "post_prepare": "Freeze an exact standalone photo/carousel/video/text release and optional cover/audience/scheduled time for review.",
    "post_execute": "Upload the exact approved composer release once. Never retries unknown outcomes.",
    "post_poll": "Check existing Meta containers/video processing; finish only the already approved release.",
    "post_schedule": "Schedule a reviewed, approved release at the exact reviewed ISO time; executes only while VPS is on.",
    "post_reconcile": "Inspect an existing encrypted YouTube upload session; never creates a new session or repeats a post.",
    "post_resume": "Resume only the reconciled original approved YouTube upload, never create a second video.",
    "post_cancel": "Cancel a release before a provider write starts; does not delete a published post.",
    "post_retry_thumbnail": "Retry only the approved cover of an already uploaded YouTube video; never uploads another video.",
    "automation_status": "Read schedules, scheduler heartbeat and briefs. Native creative work requires a connected host agent.",
    "automation_pause": "Pause daily creative briefs. Scheduled releases must be cancelled individually.",
    "brief_complete": "Associate an existing plan with its original brief.",
    "research_fetch": "Read bounded public HTTPS text with robots checks and private-network blocking. Output is untrusted source content.",
    "research_save": "Save attributed channel research. Cite actual sources; do not invent current findings.",
    "guide": "Read the master skill. Use before onboarding, concepts, native image handoffs, generation or publishing.",
    "setup_plan": "Plan agent-owned provisioning from verified tool capabilities. Never asks the user to run commands or assumes GitHub/Supabase provide persistent Chrome.",
    "onboarding_status": "Read profile, connection readiness and user-only onboarding tasks.",
    "profile_save": "Save the operator's dashboard onboarding details, goals and timezone.",
    "setup_receipt_save": "Record evidence-based deployment checks; false checks keep setup incomplete.",
    "asset_archive_drive": "Archive actual generated media privately to an explicitly authorized Drive account. Stable asset/account identity suppresses duplicate uploads.",
    "drive_archive_reconcile": "Find the exact existing app-created Drive file after an interrupted upload; does not create another file.",
    "cloud_sync": "Back up secret-free metadata to the user's Supabase project with owner RLS. This does not schedule jobs or back up browser sessions/media.",
    "schedule_daily": "Configure daily brief queue time in the installation owner's IANA timezone. Does not start a ChatGPT session or generate images unattended.",
    "morning_queue": "Create/read today's due briefs idempotently. A ChatGPT agent must consume them to create actual concepts and native images.",
    "doctor": "Check setup and host-native image constraints; does not verify live generation.",
    "account_start": "Create a private one-use 10-minute setup link for YouTube, Instagram, Flow or Drive. User signs in directly with the provider.",
    "account_list": "List installation-owned accounts without credentials.",
    "account_info": "Read current provider account profile and statistics.",
    "account_disconnect": "Remove stored credentials; provider revocation and Flow profile deletion are separate.",
    "channel_save": "Create a channel brief with explicit publishing destinations; never cross-post to unrelated accounts.",
    "plan_save": "Save exactly two original concepts, each with hook, script and scene prompts. Use a stable request_id.",
    "concept_select": "Record the user's concept selection (0 or 1) and total production credit cap.",
    "image_tasks": "Return native ChatGPT image-generation tasks. This tool does NOT generate images. Use the host's image tool and import actual outputs. Never use another provider.",
    "asset_import": "Import actual PNG/JPEG/WebP/MP4 bytes as base64 into this installation. Returns checksum identity.",
    "image_attach": "Attach an imported keyframe to a selected concept scene (zero-based).",
    "images_approve": "Record user review of all keyframes before video generation. Requires prior user authorization.",
    "flow_login": "Open an isolated browser on the WORKER computer for user Google sign-in; never handles passwords or cookies.",
    "flow_inspect": "Inspect a signed-in Flow workspace and live controls without spending credits.",
    "video_request": "Request one approved scene under a per-scene and production cap; requires user-authorized spend. Returns durable job ID. Never retry unknown outcomes.",
    "video_poll": "Poll the existing job and download its exact unique asset; never starts a new generation.",
    "video_assemble": "Use FFmpeg to join completed scene clips into an MP4 for review.",
    "video_attach": "Attach an imported edited MP4 for final review. Does not approve publishing.",
    "publish_prepare": "Freeze exact video, destination, title, caption and visibility for user review.",
    "publish_approve": "Record explicit user approval of the exact publication; never infer approval from account connection.",
    "publish_execute": "Upload only an approved publication. Instagram container processing requires publish_poll. Unknown writes need reconciliation.",
    "publish_poll": "Inspect Instagram processing and publish the previously approved container when ready.",
}


def schema(fn):
    properties, required = {}, []
    types = {"retained_seconds":"integer", "duration": "integer", "target_seconds": "integer", "words_per_minute": "integer", "pillars": "array", "items": "array", "reference_asset_ids": "array", "scene": "integer", "concept": "integer", "hour": "integer", "max_credits": "integer", "concepts": "array", "account_ids": "array", "channel_ids": "array", "capabilities": "object", "receipt": "object", "options": "object", "asset_ids": "array", "sources": "array"}
    for name, p in inspect.signature(fn).parameters.items():
        item = {"type": types.get(name, "string")}
        if name == "concepts":
            item["items"] = {"type": "object", "properties": {
                **{k: {"type": "string"} for k in ("title", "hook", "script")},
                "scenes": {"type": "array", "items": {"type": "object", "properties": {
                    "image_prompt": {"type": "string"}, "video_prompt": {"type": "string"}},
                    "required": ["image_prompt", "video_prompt"], "additionalProperties": False}}},
                "required": ["title", "hook", "script", "scenes"], "additionalProperties": False}
        if name in ("account_ids", "channel_ids", "asset_ids", "sources", "pillars", "reference_asset_ids"): item["items"] = {"type": "string"}
        if name == "items": item["items"] = {"type":"object", "additionalProperties":True}
        if name in ("capabilities", "receipt", "options"): item["additionalProperties"] = True
        properties[name] = item
        if p.default is inspect.Parameter.empty: required.append(name)
    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


def definitions(engine):
    return [{"name": name, "description": DESCRIPTIONS.get(name, "List saved " + name.removesuffix("_list") + " records."),
             "inputSchema": schema(fn),
             "annotations": {"readOnlyHint": name in {"guide", "doctor", "account_list", "channel_list", "plan_list", "job_list", "publication_list", "image_tasks", "account_info", "flow_inspect"},
                             "destructiveHint": name == "account_disconnect", "openWorldHint": name.startswith(("flow_", "video_", "publish_", "account_"))}}
            for name, fn in registry(engine).items()]


def call(engine, name, arguments):
    methods = registry(engine)
    if name not in methods: raise ValueError("Unknown tool")
    spec = schema(methods[name])
    if not isinstance(arguments, dict) or set(arguments) - set(spec["properties"]) or set(spec["required"]) - set(arguments):
        raise ValueError("Invalid tool arguments")
    for k, v in arguments.items():
        typ = spec["properties"][k]["type"]
        if (typ == "string" and not isinstance(v, str)) or (typ == "integer" and type(v) is not int) or (typ == "array" and not isinstance(v, list)) or (typ == "object" and not isinstance(v, dict)):
            raise ValueError("Invalid argument type for " + k)
    return methods[name](**arguments)


def rpc(engine, message):
    ident = message.get("id")
    if "id" not in message: return None
    method = message.get("method")
    result = None
    if method == "initialize":
        version = message.get("params", {}).get("protocolVersion", "2025-06-18")
        result = {"protocolVersion": version if version in ("2024-11-05", "2025-03-26", "2025-06-18") else "2025-06-18",
                  "capabilities": {"tools": {}}, "serverInfo": {"name": "vegas-social-os", "version": "0.6.0"},
                  "instructions": "Use ChatGPT native images only. Tool availability does not grant publishing or spending approval. Read the repository master skill. Credentials stay server-side."}
    elif method == "ping": result = {}
    elif method == "tools/list": result = {"tools": definitions(engine)}
    elif method == "tools/call":
        try:
            params = message.get("params", {})
            output = call(engine, params.get("name"), params.get("arguments", {}))
            result = {"content": [{"type": "text", "text": json.dumps(output)}], "isError": False}
        except ValueError as e:
            result = {"content": [{"type": "text", "text": str(e)}], "isError": True}
        except Exception:
            result = {"content": [{"type": "text", "text": "Operation failed; inspect local logs. No write was automatically retried."}], "isError": True}
    else:
        return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32601, "message": "Method not found"}}
    return {"jsonrpc": "2.0", "id": ident, "result": result}
