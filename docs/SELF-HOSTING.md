# VPS-first self-hosting guide (0.6.1 alpha)

The accepted interface is [ChatGPT-first](CHATGPT-FIRST.md): sign in and review in the dashboard, do creative production through the owner plugin. Follow the [new-user journey](NEW-USER-JOURNEY.md). Unattended host events and same-plugin privileged administration are designed but not yet implemented.

## Model: independent instance per person

Your brother, client or community user should have their **own VPS and data directory**. A single installation is **one trusted operator**, not a shared multi-tenant SaaS. Do not give clients access to another operator's session database, Google cookies, encryption key, or plugin token. No hardcoded maintainer account, VPS IP, key or channel is required by the distributable installer.

Google Flow is automated through a graphical browser on the installation owner's host; this is different from Google YouTube OAuth. The user signs in directly and completes all authentication challenges. Authenticated browser sessions persist on the **same host** at /var/lib/vegas-social-os/profiles. Browser ports remain localhost; only account-scoped WebSocket access is permitted through the authenticated dashboard.

## Host prerequisites and automated setup

Recommended: Ubuntu 24.04, Debian 12+ x86_64, at least 2 CPU and 4–8 GiB RAM for one browser, enough disk for generated clips, open inbound ports 80/443, HTTPS hostname and sudo. **Hardware sizing is a starting point, not a verified performance guarantee.** Accounts are not the same as concurrent browsers.

1. Get the code: git clone https://github.com/AdityaAgarwal75/vegas-social-os.git
2. Inside the checkout run: sudo bash scripts/bootstrap-ubuntu.sh
3. On an eligible x86_64 Debian/Ubuntu host the bootstrap installs system packages, Node.js 22 when needed, Chrome when needed, and the HTTPS Caddy service. If you supply --domain social.example.com, configure that DNS A record to your server first. Without a domain it tries to derive a free sslip.io hostname from the public IPv4.
4. Existing shared VPS? Run sudo bash scripts/install-vps.sh --domain social.example.com to reuse installed dependencies without changing unrelated package versions. It adds only its own systemd service, app directory, data directory and a separately marked Caddy virtual host.
5. Request a short-lived onboarding URL with sudo bash /opt/vegas-social-os/scripts/new-setup-link.sh. **Never place this URL in a public issue, CI log, screenshots or group chat.** Open it within 10 minutes. Requests after expiry need a fresh link.
6. Enter profile, add a Flow account, sign in using the private browser, create/open a Flow project, then run the non-credit inspection. For YouTube, Instagram and Facebook use the owner's official developer apps and approvals; this project does not ship shared OAuth credentials.
7. Connect the HTTPS /mcp endpoint to a supported ChatGPT/Codex agent through the agent's plugin installation/consent flow, then test harmless guide and doctor calls. The installer does not silently install a ChatGPT plugin.

## Security design

- Separate Linux service account: vegas-social; application bound to 127.0.0.1:8899; Caddy serves HTTPS.
- State: SQLite, scoped permissions 0700 in /var/lib/vegas-social-os. Fernet key is local in vault.key; no Supabase or managed database required.
- Secrets: Never commit or print vault keys, OAuth client secrets, user passwords, session cookies, or provider access tokens. Store provider app secrets in the root-owned /etc/vegas-social-os.env, with mode 0600. Prefer the encrypted dashboard Connections form for Google/Instagram/Facebook developer registrations; legacy environment variables are optional. Callback URLs and scopes are shown for this installation, and app approval/consent remain operator-specific.
- Browser: per-account Chrome profile, graphical Xvfb/noVNC, no provider password harvesting, no CAPTCHA bypass, no quota rotation. Do not add a no-sandbox Chrome flag. Sandbox behavior must be tested on the target host.
- Isolation: deploy a **separate instance/VPS** for each owner. This project does not implement multi-tenant access controls, shared team roles, managed client billing or an account marketplace.
- Backups: encrypt and back up /var/lib/vegas-social-os, including the key, database, media and profiles; test restores. Losing vault.key makes encrypted credentials unrecoverable. Restrict backups and use your own retention policy.
- Updates: pull a reviewed tagged release, keep a backup, rerun installer, restart service, then verify /health and a non-credit browser inspection. Updates must not overwrite the private data directory.

## Operating boundaries

Publishing to YouTube/Instagram is a separately approved action. Instagram Reels may publish publicly, so only publish an exact reviewed destination/video. Generation jobs are idempotent; unknown provider outcomes require reconciliation, not blind resubmission. The default credit cap for any new plan is 0 until explicitly changed by the owner.

Google Flow UI automation may break after provider updates or access checks. No guarantee of unlimited free credits, automated Google consent, or guaranteed publishing eligibility. Google Drive archives are optional and must be authorized separately. ChatGPT-native images can be used only when the host exposes actual output bytes for transfer; text descriptions alone are insufficient.

## Troubleshooting

- Check service: sudo systemctl status vegas-social-os.service
- Inspect safe logs: sudo journalctl -u vegas-social-os.service -n 100 --no-pager
- Local health: curl http://127.0.0.1:8899/health
- HTTPS health: curl https://YOUR-HOSTNAME/health
- Browser not starting: verify Chrome executable, Xvfb, private display/ports, and sandbox support. Keep browser/CDP ports private; do not turn off Chrome sandbox as a quick workaround.
- No dashboard authentication: generate a fresh one-use setup URL on the host.
- Google sign-in denied: follow provider prompts; browser launch is not proof of account connection. Never transfer everyday Google cookies from someone else's profile.
- For image transfer, plugins or official publishing: check app scopes, consent and host tool availability rather than treating a passing /health check as success.

## Developers and test status

Local unit suite: python -m unittest discover -s tests -v
Node helper suite: node --test tests/flow.test.mjs
Shell checks: bash -n scripts/install-vps.sh scripts/bootstrap-ubuntu.sh scripts/new-setup-link.sh

These tests do not log into Google, publish a video or spend Flow credits. The founder's VPS separately passed a live non-credit Chrome launch and a signed-out Flow inspection. Consult docs/STATUS.md for verification scope and outstanding blockers.

The public source may be used under the MIT license. The founder's private VPS accounts are never part of a community install.

For a fresh AWS install, use [AWS agent onboarding](AWS-ONBOARDING.md). For provider scopes/media support, use [platform permissions](PLATFORM-PERMISSIONS.md). The daily scheduler publishes exact approved scheduled releases while running; a real connected host agent consumes creative briefs.

## Model and strategy controls

Use Content manager to save audience, voice, objective and pillars, then request a reviewed weekly plan from your connected host agent. The VPS retains the request and calendar; it does not start ChatGPT itself. Scene prompts can be stored in calendar entries, with unsourced ideas labeled creative hypotheses.

Flow Studio lists model-dependent duration/resolution controls and fresh account-specific model-menu evidence. The normal installer includes the complete pinned Flow engine; native browser sessions and existing-service imports use the same API adapter. Standalone clips, end frames and ingredient uploads no longer depend on founder-only configuration. Every new owner must sign in personally. Paid rendering, actual input attachment and advanced operations remain acceptance tests; see FLOW-EXECUTION-CONTRACT.md.

Dependency source is installed separately at /opt/vegas-social-os-flow-engine and private native queue/output/token state stays under each account profile. Do not overwrite a conflicting engine contract or launch another driver on the same profile.

### OAuth Authorize reports Origin rejected

Older releases combined Referrer-Policy: no-referrer with exact-Origin CSRF checks.
Browsers can submit normal HTML authorization forms with Origin: null under that policy.
Social OS and its generated Caddy route now use Referrer-Policy: origin, which sends
only the hostname origin, not OAuth paths, codes, or private setup tickets. This
does not weaken CSRF protection: foreign/null Origins still receive HTTP 403.

For existing installs, rerun the installer with the same domain and port. The
installer repairs only its marked Caddy route and saves a backup. When using
--no-caddy or your own reverse proxy, configure a single Referrer-Policy: origin
response header for Social OS. Do not append another no-referrer policy.
Verify GET /authorize has that header and browser consent succeeds.
