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
    methods = {f.__name__: f for f in (account_start, account_list, account_disconnect, channel_list,
              plan_list, job_list, publication_list, account_info, guide, cloud_sync, schedule_daily, morning_queue,
              setup_plan, onboarding_status, profile_save, setup_receipt_save, asset_archive_drive, drive_archive_reconcile)}
    for name in ("doctor", "channel_save", "plan_save", "concept_select", "image_tasks", "asset_import", "image_attach",
                 "images_approve", "flow_login", "flow_inspect", "video_request", "video_poll", "video_assemble",
                 "video_attach", "publish_prepare", "publish_approve", "publish_execute", "publish_poll"):
        methods[name] = getattr(engine, name)
    return methods


DESCRIPTIONS = {
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
    types = {"scene": "integer", "concept": "integer", "hour": "integer", "max_credits": "integer", "concepts": "array", "account_ids": "array", "channel_ids": "array", "capabilities": "object", "receipt": "object"}
    for name, p in inspect.signature(fn).parameters.items():
        item = {"type": types.get(name, "string")}
        if name == "concepts":
            item["items"] = {"type": "object", "properties": {
                **{k: {"type": "string"} for k in ("title", "hook", "script")},
                "scenes": {"type": "array", "items": {"type": "object", "properties": {
                    "image_prompt": {"type": "string"}, "video_prompt": {"type": "string"}},
                    "required": ["image_prompt", "video_prompt"], "additionalProperties": False}}},
                "required": ["title", "hook", "script", "scenes"], "additionalProperties": False}
        if name in ("account_ids", "channel_ids"): item["items"] = {"type": "string"}
        if name in ("capabilities", "receipt"): item["additionalProperties"] = True
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
                  "capabilities": {"tools": {}}, "serverInfo": {"name": "vegas-social-os", "version": "0.2.0"},
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
