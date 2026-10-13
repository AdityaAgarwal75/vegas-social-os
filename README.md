# Vegas Social OS — community self-hosted alpha

**An independent AI social production workspace.** Use your own VPS, Google Flow account(s), and authorized YouTube/Instagram/Facebook apps. ChatGPT or Codex can plan original video concepts, generate native images when supported, review clips, and prepare approved publishing actions. This project is **not affiliated with OpenAI, Google, or Meta**.

**Status (October 2026): 0.5.0 alpha.** The dashboard, local state, private remote-browser login, MCP tools, approval guards and offline tests exist. The founder's Ubuntu VPS deployment has passed HTTPS health and remote-browser startup tests. The existing-service image adapter has controlled live trials pending; the independent video worker and live social publishing remain unverified. See [status](docs/STATUS.md).

## A complete independent control room

Your own **Overview, Content studio, Google Flow Studio, Connections, Media library, Publishing and Automation** live in a rebuilt control centre. Click a provider button to redirect to official sign-in and consent. Developer app settings are kept in advanced operator setup; the setup agent configures them once, rather than asking every account owner to paste secrets. See [connection design](docs/CONNECTION-EXPERIENCE.md) for the independent-host and shared-registration options.

**Starting without a VPS?** Give this URL to a capable ChatGPT/Codex agent connected to your AWS account. Follow [AWS agent onboarding](docs/AWS-ONBOARDING.md) and the pinned [CloudFormation template](deploy/aws/instance.json). The agent can provision through its actual available permissions and return a private dashboard link after checks; billable resource consent, platform consent and app approval are still individual steps. We do not provision everyone on a maintainer server.

See [provider permissions](docs/PLATFORM-PERMISSIONS.md). YouTube MP4s/thumbnails, Instagram professional photos/Reels/carousels and Facebook Page posts/photos/videos have implemented adapters, with live account trials still pending. Additional social platforms are not represented as working. Scheduled approved releases run on the VPS; native creative work requires a real connected agent/host trigger.

## Install on an independent VPS (recommended)

Each person installs their **own instance**. Your accounts and browser profiles stay on your VPS, not the maintainer's server. Supabase, Render, Google Drive and any centrally hosted service are **not required**.

For **Ubuntu 24.04 / Debian 12+ x86_64**, with a public IPv4, DNS/HTTPS access (ports 80/443) and sudo rights:

~~~bash
git clone https://github.com/AdityaAgarwal75/vegas-social-os.git
cd vegas-social-os
sudo bash scripts/bootstrap-ubuntu.sh
~~~

The installer attempts to install missing system dependencies, then chooses a free sslip.io hostname based on your public IPv4, configures a standalone SQLite state store, systemd service and Caddy HTTPS reverse proxy. Use your own domain when you have one:

~~~bash
sudo bash scripts/bootstrap-ubuntu.sh --domain social.example.com
~~~

Already have Python 3.11+, Node 22+, Chrome/Chromium, FFmpeg, Xvfb, x11vnc, websockify, noVNC and Caddy? Skip dependency installation:

~~~bash
sudo bash scripts/install-vps.sh --domain social.example.com
~~~

The installer **does not create accounts, silently log in to Google, bypass Google restrictions, or guarantee free cloud hosting**. Your VPS/provider and optional AI services may charge. Neither project source nor generated clips are sent to the maintainer. Using another person's shared VPS/account pool is not supported by this single-operator edition.

## Finish onboarding

1. On the VPS, request an expiring private link via the admin helper: **sudo bash /opt/vegas-social-os/scripts/new-setup-link.sh**. The first setup URL works for ten minutes and only once. A connected ChatGPT/Codex agent may run this for you; do not post it publicly.
2. Open the link in your browser and complete the dashboard profile (name, brand, channel goals, timezone).
3. Open **Google Flow Studio → Add Google account**, follow the private browser link and sign in directly with Google. Complete consent and 2FA yourself, then open a Flow project.
4. Your setup agent configures the Google/Instagram/Facebook developer applications once in **Workspace settings → Advanced operator setup**. Then click **Connect YouTube / Instagram / Facebook** in **Connections**, sign in on the official provider page and Allow access. Verify the workspace through **flow_inspect**, before scheduling or spending credits. YouTube and Instagram require separate official developer-app OAuth configurations and approvals where applicable.
5. Optionally connect your private MCP endpoint at **https://YOUR-DOMAIN/mcp** to a compatible ChatGPT/Codex host through its **consent/installation** flow. A package is not automatically installed into every user account.
6. Prepare two creative concepts, select one, approve exact native images, explicitly cap Flow credits, verify generated videos, and approve any YouTube or Instagram release separately.

A Google Flow login does not grant YouTube/Instagram publishing access. Flow UI selectors can change. **Never automate CAPTCHA/2FA, evade quotas, or assume Google/Meta API review is automatic.** This project is for authorized accounts and explicit publishing approval.

## What works, what remains experimental

| Capability | Status |
| --- | --- |
| Dedicated Ubuntu VPS + HTTPS + SQLite deployment | Live health tested on founder's VPS |
| Separate service user, state/media directory and private Flow browser sessions | Browser launch and signed-out workspace inspection tested |
| Original content planning, prompt/image approvals, idempotency and budget caps | Offline unit tests passed |
| Google Flow production controls | Experimental; live generation not yet validated in this installation |
| YouTube upload/thumbnail + Instagram photos/Reels/carousels + Facebook Page posts/photos/videos | Implemented adapters, offline request tests passed; live end-to-end testing pending |
| Rebuilt control centre, consent buttons, Google Flow Studio and media/review controls | Real isolated Chrome QA passed at 360/768/1440; 11 routes |
| AWS independent-instance bootstrap | CloudFormation schema validated; new-account provisioning trial pending |
| Native ChatGPT image transfer | Host-dependent; do not assume generated files are automatically available |
| ChatGPT plugin creation/consent | Supported as packaged remote MCP; installation is host-controlled |
| Scheduled releases and daily creative briefs | VPS scheduler publishes exact approved releases; creative briefs require a host agent trigger |
| Multi-user shared SaaS, DMs, comments and all-platform scheduling | Not implemented |

**One install per operator, not one server for all clients.** If you run a managed agency, put each client on an independently secured instance with their own approval and credentials. No one receives maintainer accounts or cookies.

## Operations

- Web app: HTTPS domain configured at install.
- Runtime: **vegas-social-os.service**, bound only to **127.0.0.1:8899** by default, behind Caddy.
- Private data: **/var/lib/vegas-social-os** (including SQLite, encryption key, profiles, media); backup this folder securely. Never commit it.
- Code: **/opt/vegas-social-os**; use version-controlled updates and run tests before installing an update.
- Restart: **sudo systemctl restart vegas-social-os.service**.
- Diagnostics: **sudo systemctl status vegas-social-os.service** and **sudo journalctl -u vegas-social-os.service**; redact URLs containing setup tickets before sharing logs.
- VPS running cost is separate from this free/open-source project; the service is offline whenever your VPS is stopped.

Read [VPS installation and security details](docs/SELF-HOSTING.md), [agent setup](BOOTSTRAP.md), [architecture](docs/ARCHITECTURE.md), and [current limitations](docs/STATUS.md).

MIT licensed. Contributions and security reports are welcome through [CONTRIBUTING](CONTRIBUTING.md) and [SECURITY](SECURITY.md).
