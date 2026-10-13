# Agent guidance — Vegas Social OS community

Read README.md, BOOTSTRAP.md, agent-manifest.json, docs/SELF-HOSTING.md and docs/STATUS.md before changing or deploying anything.

- **One owner per install.** No shared service-role keys, login cookies, Flow accounts or API tokens in the repo. Clients/brothers must use independently isolated VPS installations.
- **Prefer existing VPS + SQLite** when users want zero *additional* hosting bills. Use a dedicated Linux user, loopback port, /var/lib/vegas-social-os and one Caddy vhost. Cloud/Render/Supabase deployment is optional, not required.
- User owns account consent, Google login/2FA, OAuth developer-app approval, ChatGPT plugin installation consent, and explicit publishing/credit authorization.
- Agents with VPS controls can execute all system setup. If no such tool is connected, the end user can install via the documented bootstrap script.
- Never copy or harvest browser cookies from maintainer/other apps. Start distinct browser profiles; do not disable the Chrome sandbox or bypass provider restrictions.
- Run Python + Node tests and bash -n on install scripts; verify /health plus real non-credit browser readiness. CI passes are not live Google Flow verification.
- Native ChatGPT images only. Generated image bytes must be genuinely transferable to the runtime before claiming automatic keyframe handoff.
- Flow UI controls are experimental. Unknown submissions are not retried blindly. Publisher records/approvals remain separate.
- Keep original code/license and respect researched dependencies' licenses. Never commit private data, generated assets, token files or secrets.
- Report observed vs not yet tested features and cost assumptions in docs/STATUS.md after changing behavior.
