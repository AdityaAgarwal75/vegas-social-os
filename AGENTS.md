# Agent guidance — Vegas Social OS community

Read README.md, BOOTSTRAP.md, agent-manifest.json, docs/SELF-HOSTING.md, docs/CHATGPT-FIRST.md and docs/STATUS.md before changing or deploying anything.

- **One owner per install.** No shared service-role keys, login cookies, Flow accounts or API tokens in the repo. Clients/brothers must use independently isolated VPS installations.
- **Prefer existing VPS + SQLite** when users want zero *additional* hosting bills. Use a dedicated Linux user, loopback port, /var/lib/vegas-social-os and one Caddy vhost. Cloud/Render/Supabase deployment is optional, not required.
- User owns account consent, Google login/2FA, OAuth developer-app approval, ChatGPT plugin installation consent, and explicit publishing/credit authorization.
- **Meta MCP onboarding:** For developer-app setup, first invoke this installation's read-only `meta_mcp_setup` tool, then discover whether the user's ChatGPT/IDE actually provides the official `mcp__meta_mcp__devtools_*` tools. If available, start with `devtools_app_list` and operate solely on explicitly authorized app IDs. Inspect `devtools_app_review.privileges` and `requirements`, app settings including redirects, compliance, and webhooks. Reconcile observed Meta state against Vegas's exact callbacks. Never equate `Ready for testing` with live/approved scope access. Never confuse developer MCP Manage with business/Page or Instagram OAuth permission.
- Current Meta MCP supports developer-app inspection and webhook writes only. Its announced app-creation, use-case, portfolio linking actions are unavailable until **actually present** in tool discovery. Only perform those actions when supported and after owner confirmation. Never promise approval automation or copy a user's Meta MCP access token into VPS.
- All new users should be offered Meta MCP assisted setup, but the guided installation MUST allow the manual developer-console route if beta MCP connection is unavailable. See docs/META-MCP-ONBOARDING.md.

- Agents with VPS controls can execute all system setup. If no such tool is connected, the end user can install via the documented bootstrap script.
- Never copy or harvest browser cookies from maintainer/other apps. Start distinct browser profiles; do not disable the Chrome sandbox or bypass provider restrictions.
- Run Python + Node tests and bash -n on install scripts; verify /health plus real non-credit browser readiness. CI passes are not live Google Flow verification.
- Native ChatGPT images only. Generated image bytes must be genuinely transferable to the runtime before claiming automatic keyframe handoff.
- Flow UI controls are experimental. Unknown submissions are not retried blindly. Publisher records/approvals remain separate.
- Keep original code/license and respect researched dependencies' licenses. Never commit private data, generated assets, token files or secrets.
- Report observed vs not yet tested features and cost assumptions in docs/STATUS.md after changing behavior.

- ChatGPT web Work is the primary workstation. Keep extensions.com.openai.requires_local_executor=false, remote HTTPS MCP/OAuth, and no mandatory local daemon/desktop launch. Read docs/CHATGPT-WEB.md and verify web registration/tools separately from ZIP generation.

## Maintainer bug-fix completion rule

When the owner authorizes a bug fix, include the official repository update in the same task. A live-server hotfix is temporary: port the fix to current source, add relevant regression coverage, run required checks, update docs/STATUS.md and recovery instructions when behavior changes, then commit and push through authorized access. Verify the remote commit and report its link. Never report a deployed fix as an upstream fix. If pushing is blocked, preserve the tested patch and state the exact blocker; do not claim synchronization. Do not commit runtime data, setup/recovery URLs, credentials or release backups.
