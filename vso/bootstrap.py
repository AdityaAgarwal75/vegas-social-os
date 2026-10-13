"""Agent-owned setup planning and truthful verification receipts.

This planner never invents cloud access or asks an end user to run commands.
The setup agent executes actions through the user's connected tools.
"""
from urllib.parse import urlsplit

CAPABILITIES = (
    "source_read", "repository_write", "supabase_manage", "persistent_runtime",
    "persistent_volume", "https_route", "secret_write", "process_exec",
    "plugin_create", "plugin_install", "native_images", "native_asset_transfer",
    "provider_app_manage", "host_scheduler", "managed_app_host", "drive_write", "vps_manage",
)


def plan(capabilities):
    if not isinstance(capabilities, dict) or set(capabilities) - set(CAPABILITIES):
        raise ValueError("Unknown capability; inspect agent-manifest.json")
    if any(type(v) is not bool for v in capabilities.values()):
        raise ValueError("Capability flags must be verified booleans")
    c = {k: capabilities.get(k, False) for k in CAPABILITIES}
    mode = "vps" if c["vps_manage"] else "managed_cloud"
    if mode == "vps":
        # One owner/installation; an existing VPS runs browser + state locally.
        required = ["source_read", "vps_manage", "persistent_volume", "https_route", "process_exec"]
    else:
        required = ["source_read", "supabase_manage", "persistent_volume",
                    "https_route", "secret_write", "process_exec", "plugin_create", "provider_app_manage"]
    blockers = [{"capability": k, "action": "Connect a tool/service providing " + k,
                 "user_work": "Service authorization only; agents perform technical setup"}
                for k in required if not c[k]]
    if mode == "managed_cloud" and not c["managed_app_host"]:
        blockers.append({"capability": "managed_app_host",
                         "action": "Connect persistent managed browser app hosting or switch to a VPS",
                         "user_work": "Authorize deployment; paid resources need explicit approval"})
    creative_blockers = [k for k in ("native_images", "native_asset_transfer") if not c[k]]
    integration_blockers = [k for k in ("plugin_create", "provider_app_manage") if not c[k]]
    browser_runtime = ("user-owned VPS with Chrome and SQLite" if mode == "vps"
                       else "managed cloud app with private volume and Supabase")
    return {
        "status": "ready_for_agent_setup" if not blockers else "connections_needed",
        "mode": mode,
        "integration_stage_blockers": integration_blockers,
        "capabilities": c,
        "architecture": {"source": "GitHub", "state": "SQLite" if mode == "vps" else "Supabase",
                         "browser_runtime": browser_runtime,
                         "images": "ChatGPT native only", "media_archive": "Google Drive when authorized",
                         "interaction": "ChatGPT + onboarding dashboard",
                         "local_pc_required": False, "user_managed_vps_required": mode == "vps"},
        "blockers": blockers,
        "creative_stage_blockers": creative_blockers,
        "agent_actions": [
            "Read BOOTSTRAP.md and discover actual tool schemas",
            "Use an isolated checkout; create a private source mirror only if repository creation is available and useful",
            "Prefer scripts/install-vps.sh or scripts/bootstrap-ubuntu.sh when VPS access exists",
            "Select a dedicated Supabase project ONLY for optional managed-cloud mode",
            "For VPS mode, verify SQLite private storage and no cloud keys; optional cloud mode verifies its RPC",
            "Provision an isolated VPS service or managed cloud app with HTTPS and private remote browser",
            "Inject project keys directly into the runtime secret store; never into chat or GitHub",
            "Run VPS installer for VPS mode; use agent_bootstrap.py only for managed-cloud mode",
            "Package one remote master plugin; create it with the host's plugin tool",
            "Present onboarding URL and plugin install/consent action",
            "Verify a harmless call after plugin connection; record verification receipt",
        ],
        "user_actions": ["Authorize missing services", "Approve any paid resources",
                         "Open onboarding link and enter profile/channel details", "Sign into accounts and finish provider consent/2FA",
                         "Accept plugin installation when the host requires it", "Approve concepts, images and releases"],
        "limits": {
            "github_supabase_only": "Insufficient for persistent Chrome sessions; an existing VPS works",
            "plugin_install": "Host consent may remain even when plugin creation is available",
            "drive": "Existing ChatGPT Drive access must be verified for writes; it does not transfer backend tokens",
            "provider_apps": "Agent manages registration when tools permit; review/consent cannot be bypassed",
            "native_asset_transfer": "Automated only when the host exposes generated bytes; otherwise image-stage blocker, independent of dashboard readiness",
            "daily_runs": "Requires an actual host-supported scheduler; queue records do not wake ChatGPT",
        },
    }


def verify_receipt(receipt):
    required = {"dashboard_url", "mcp_url", "source_commit", "health_verified", "supabase_verified",
                "runtime_persistent", "browser_verified", "plugin_created", "plugin_connected"}
    if not isinstance(receipt, dict) or set(receipt) != required:
        raise ValueError("Provide all required verification receipt fields, with no extras")
    for key in required - {"dashboard_url", "mcp_url", "source_commit"}:
        if type(receipt[key]) is not bool: raise ValueError("Verification flags must be booleans")
    origin = None
    for key in ("dashboard_url", "mcp_url"):
        p = urlsplit(receipt[key])
        if p.scheme != "https" or not p.hostname or p.username or p.password or p.fragment or p.query:
            raise ValueError("Receipt URLs must be clean HTTPS links")
        current = (p.scheme, p.netloc)
        if origin and current != origin: raise ValueError("Dashboard and MCP must belong to the same installation")
        origin = current
    if urlsplit(receipt["mcp_url"]).path != "/mcp": raise ValueError("MCP path must be /mcp")
    import re
    if not re.fullmatch(r"[a-f0-9]{40}", receipt["source_commit"]): raise ValueError("Use the actual source commit SHA")
    checks = [receipt[k] for k in required - {"dashboard_url", "mcp_url", "source_commit"}]
    return {"status": "onboarding_ready" if all(checks) else "setup_incomplete", "checks": receipt,
            "note": "Receipt records the agent's evidence. It does not independently verify third-party connectivity."}
