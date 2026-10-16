# Vegas Studio

![Vegas Studio — ideas in chat, production under control](docs/assets/banner.svg)

**[Complete Instagram / Facebook / YouTube setup (scopes, redirects, uploads, deletion, thumbnails)](docs/COMPLETE-SOCIAL-SETUP.md)**

[Start here](docs/USER-GUIDE.md) · [Self-host](docs/SELF-HOSTING.md) · [Current status](docs/STATUS.md) · [Security](SECURITY.md)

Your social production team inside ChatGPT.

**Primary workstation: ChatGPT web (Work). No desktop app or local computer executor is required.** Read [web setup](docs/CHATGPT-WEB.md) for connection steps and verification.

**Plan in ChatGPT. Execute on your own VPS. Monitor and review in the dashboard.** An open-source, independently self-hosted social production system for original research, scripts, scene images, Google Flow clips and reviewed publishing. Not affiliated with OpenAI, Google or Meta.

## Start in three steps

1. **Install your own workspace.** Give this repo to a ChatGPT Work agent connected to your VPS or AWS. Follow the setup prompt below.
2. **Sign in and connect.** Open the private setup link, set your owner password, connect the plugin and sign into your own accounts.
3. **Review before release.** Choose a concept, approve actual storyboards and credits, then review the exact final post.

Your installation includes branded login, Show/Hide password, forgotten-password guidance, direct private recovery links and a setup guide at `/help`. [Read the complete user guide →](docs/USER-GUIDE.md)

**Release status:** a tested self-hosting candidate, not a guarantee of fully unattended production. Provider registration, personal login and real generation/publishing acceptance remain owner-specific.

## The product

ChatGPT is your main workstation. Its private plugin connects to your own installation. You discuss strategy and scenes in chat; ChatGPT uses native images and the VPS's Flow browser/execution engine. The dashboard is your control panel: host resources, observed Flow balances, connected identities, actual specialist activity, named video projects and publishing schedules. Images, scene clips and final exports stay under each production. Light and dark themes work on desktop and mobile. Account onboarding and storyboard/release review are built in. Manual generation forms are excluded from normal navigation.

Read [the accepted ChatGPT-first architecture](docs/CHATGPT-FIRST.md) and [the complete new-user journey](docs/NEW-USER-JOURNEY.md), including plugin structure, permissions, VPS administration boundaries, optional Drive storage and the unattended-work implementation gates.

**0.8.0 control panel candidate:** light/dark layouts, named media projects, truthful specialist activity and calendar views pass isolated desktop/mobile browser checks. Durable storyboard-feedback requests and review-focused navigation are implemented. Paid Flow rendering, fresh AWS onboarding, real publishing and event-driven ChatGPT continuation are not yet accepted end to end. [Current evidence](docs/STATUS.md) distinguishes source, menus, submitted jobs and usable outputs.

## Give this repository to your ChatGPT

If AWS Core is connected to your own AWS account, send:

> Set up https://github.com/AdityaAgarwal75/vegas-social-os on my own independent AWS VPS. Read BOOTSTRAP.md and docs/CHATGPT-FIRST.md. Prepare the deployment and costs for approval, install a pinned revision, verify HTTPS/private browser, and prepare my own ChatGPT plugin. I will use the dashboard to sign into Google accounts and review storyboards/clips. Keep credentials private; do not spend Flow credits or publish yet. Explain tested versus pending automation.

Your agent uses the [AWS setup recipe](docs/AWS-ONBOARDING.md), scoped AWS tools and SSM. It derives a stable HTTPS address and returns the dashboard plus private onboarding link after checks. AWS Core connection alone does not prove all required permissions are available. Account login/2FA, provider approval, billable-resource authorization and plugin installation consent remain personal steps. There is no maintainer VPS or shared account pool in this path.

## Meta developer MCP assisted onboarding (recommended)

Vegas Social OS provides a read-only `meta_mcp_setup` tool and a **Workspace settings → Meta developer setup** panel. New users are guided to connect the official Meta Social Technologies MCP at `https://mcp.facebook.com/devtools` in their own ChatGPT/IDE client. That integration helps the agent inspect app roles and App Review grants, detect OAuth callback mismatches, check compliance, and manage explicitly approved webhooks. See **[Meta MCP setup and exact capabilities](docs/META-MCP-ONBOARDING.md)**. Users without beta access can follow the manual Meta Developer setup path.

Meta MCP's developer-app **Manage** access does NOT grant Instagram/Facebook Page OAuth privileges or approval to delete Reels. The app-creation and use-case tools advertised in Meta's documentation are **coming soon** and cannot be required or claimed as operational until the connected Meta MCP actually exposes them.

## Complete community social onboarding: 2026 verified steps

Follow the **[step-by-step social setup runbook](docs/COMPLETE-SOCIAL-SETUP.md)** before connecting platforms. It includes a capability/permissions matrix, separate Meta Instagram Login versus Facebook Login for Business, the distinction between the Facebook **App Secret and Configuration ID**, **Valid OAuth Redirect URIs** setup, exact per-installation callbacks, owner-only OAuth consent, Page-to-Instagram identity verification, YouTube MP4 and thumbnail behavior, the approved provider-confirmed Instagram media deletion sequence, and the errors actually encountered during founder testing.

**Verified 16 October 2026:** owner-authenticated Instagram publishing, a YouTube private upload with thumbnail, and an explicit approval-gated **Meta-confirmed deletion of one test Instagram Reel** using a matching authorized Facebook Page. This proves a particular owner grant and media ID worked—not blanket permission for other users or a universal App Review approval. Facebook Page publication still requires its separate posting permission and live acceptance; YouTube deletion and post-publication Instagram cover edits are not implemented.

Multi-page Facebook consent can import more than one Page under the same connection label. Every Page must be checked by **Page ID and linked Instagram ID**. A linked Page is not automatically an Instagram Login publishing connection for that Instagram profile. Never post or delete just because an account appears after a bulk Meta consent.

## Google accounts and social connections

The dashboard opens a private screen mirror of Chrome on **your VPS**. Your agent creates profiles; you sign into them one by one and open Flow. Sessions persist on that server. No Google API key or pasted cookie is required for Flow. Connecting Flow does not grant YouTube upload access.

YouTube, Instagram professional accounts and Facebook Pages use official OAuth consent after the owner's developer app is configured. [Permissions and eligibility](docs/PLATFORM-PERMISSIONS.md) and [connection setup](docs/CONNECTION-EXPERIENCE.md) explain registration, exact callbacks and scopes. This repository contains no universal approved OAuth app, so independent social setup cannot yet be promised as “only click Allow.” Optional Drive can archive assets through a verified writable ChatGPT connector or separately authorized server OAuth.

## Review and automation

ChatGPT saves two ideas per production, scripts, scene direction and actual transferred native images. Choose an idea and review the storyboard in the dashboard. Approve attached images under the agreed credit ceiling or request changes; feedback persists for the agent and revisions preserve the original. Watch the exact clips and final export, then review the prepared release.

**Morning preparation and approve-to-render are the target workflow, not a running background feature yet.** The existing scheduler creates briefs and executes exact approved scheduled posts. The selected design uses [OpenAI MCP Events](https://developers.openai.com/plugins/build/mcp-events) to notify a supported ChatGPT Work workflow of due briefs and decisions. The server implements signed subscriptions and a durable event outbox; actual host continuation remains unverified. Neither a connected badge nor a queued request proves ChatGPT is generating. See the [event contract and acceptance gates](docs/CHATGPT-FIRST.md#event-bridge-implemented-protocol-host-acceptance-pending). Until then, resume the connected ChatGPT agent to consume due briefs/review requests.

## Existing VPS installation

Supported target: Ubuntu 24.04 / Debian 12+ x86_64, persistent disk, public IPv4, sudo and HTTPS ports 80/443. An agent can run these for you:

```bash
git clone https://github.com/AdityaAgarwal75/vegas-social-os.git
cd vegas-social-os
sudo bash scripts/bootstrap-ubuntu.sh
```

Use `--domain social.example.com` for your own DNS, or the installer derives an sslip.io hostname. On a host with dependencies already installed use `scripts/install-vps.sh`. Read [self-hosting](docs/SELF-HOSTING.md) before changing an existing server. One isolated service user, loopback port, state directory and Caddy virtual host keep other apps separate.

Generate a private ten-minute, one-use pairing link with:

```bash
sudo bash /opt/vegas-social-os/scripts/new-setup-link.sh
```

Owner browser sessions last eight hours. For easier repeated sign-ins, the owner
may visit https://YOUR-DOMAIN/password in their already-paired browser
to set a private scrypt-protected password, or use
python -m vso owner-password in a private interactive terminal.
Subsequent visits use https://YOUR-DOMAIN/login. The password never replaces OAuth/PKCE consent for
ChatGPT. Never post pairing links or passwords publicly.

Forgot your password? An authorized infrastructure agent can generate a private link with `sudo bash /opt/vegas-social-os/scripts/new-setup-link.sh --reset-password`; open it once to set a new password directly in your browser. See [recovery and OAuth troubleshooting](docs/SELF-HOSTING.md#forgotten-owner-password--agent-assisted-browser-recovery).

## Vegas Creative Engine

See [the complete content capability, attribution and verification matrix](docs/CREATIVE-ENGINE.md).
New first-party tools handle hooks, caption and writing QA, carousels,
Stories, engagement triage, profile/competitor scoring, transcript repurposing
and a source-aware two-concept creative brief lifecycle. 13 explicit
video/story production pipelines specify gates before media spend or release.
OpenMontage can be cloned separately as optional AGPL-preserved external source
and discovered read-only; its renderers/providers are NOT auto-installed.
This project does not scrape private platform data or claim unattended
ChatGPT native image generation.

## Cinematic Template Library and Higgsfield craft (0.9)

Open **Template Library** in the dashboard. Browse 16 original Vegas recipes across product, fashion, creator and cinematic work, preview a subject study, adjust lens/lighting/motion, and save a direction to a new or existing named project. Related recipes share one of four clearly labeled illustrative previews; these are not rendered motion samples or Higgsfield private templates. Ask ChatGPT: **“Use my saved template selections for this project.”**

The dashboard and plugin share `template_catalog`, `template_compile` and `template_select`. Compiled prompts preserve continuity and enter the existing two-concept/native-image/Flow approval path. Selecting a template starts no paid generation, publishing or background ChatGPT run.

Pinned MIT [Higgsfield skills](https://github.com/higgsfield-ai/skills) and companion references are bundled with attribution and exposed through `skill_reference`. `higgsfield_status` checks optional setup; `higgsfield_discover` can read an explicitly configured owner CLI's live models/workflows/presets. Flow remains the default video execution path. **Automatic paid Higgsfield rendering is not implemented**; use an explicitly authorized operator handoff until its auth, cost, idempotency and media-recovery contract passes acceptance. [Integration, setup and limits →](docs/HIGGSFIELD-INTEGRATION.md)

## Per-owner ChatGPT plugin

After verifying the owner's HTTPS endpoint, the setup agent packages it:

```bash
python scripts/package_plugin.py --url https://YOUR-DOMAIN/mcp --output /tmp/vegas-social-os-plugin.zip
```

The ZIP includes the master workflow, Flow craft and setup/review references. Install through a supported ChatGPT plugin/custom MCP workflow and complete OAuth consent; test `guide`, `doctor` and `account_list`. Packaging does not install/authorize the host connection. Each brother/client generates a package for their own endpoint. [Plugin/setup instructions](BOOTSTRAP.md) explain host prerequisites and unavailable capabilities honestly.

## What is verified

| Capability | Evidence / boundary |
| --- | --- |
| VPS + HTTPS + private SQLite | Live founder deployment; independent AWS provisioning still pending |
| Google profiles/private mirror | Existing five accounts verified; disposable fresh browser startup tested; new-owner login is personal |
| Flow models/settings | Account-specific menu/settings probes; advanced operations and paid render acceptance pending |
| Native ChatGPT keyframes | Requires actual host image tool and transferable bytes; prompts alone are not images |
| Storyboard revisions | Durable idempotent feedback, immutable originals, fresh approvals on new plans |
| Social publishing | Owner-verified Instagram publishing and Meta-confirmed test Reel deletion; single-channel YouTube private upload and thumbnail tested. Independent accounts and Facebook Page publishing need their own consent/trials |
| Daily briefs/approved schedules | VPS queues briefs and schedules exact approved posts while running |
| ChatGPT event continuation | Protocol and signed delivery implemented; actual Web host continuation not accepted |
| Full VPS admin in same plugin | Isolated root-owned Unix broker implemented; owner approval/enrollment required |

Private state/media/profiles live in `/var/lib/vegas-social-os`, code in `/opt/vegas-social-os`, service `vegas-social-os.service`, default loopback port 8899. Back up complete private state/key securely; never commit it. VPS/credits/network costs are separate from this free project. Respect authentication challenges, quotas, provider review and researched dependency licenses.

Read [architecture](docs/ARCHITECTURE.md), [Flow execution contract](docs/FLOW-EXECUTION-CONTRACT.md), [contributing](CONTRIBUTING.md) and [security](SECURITY.md). MIT licensed.

Current engineering repairs, web connection acceptance and owner administration: [operations 0.7](docs/OPERATIONS-0.7.md), [dated audit](docs/audits/2026-10-14-engineering.md).

## Workspace design

The 0.12 workspace uses an original warm-grey, white and sage visual system inspired by the owner's dashboard reference. A labelled navigation rail separates production, publishing and operations. Images, scene clips and final exports have distinct project sections and a grouped media library. Posts & releases exposes the exact composer, review, frozen schedule, cancellation and recovery actions supported by the backend. Public landing, sign-in, recovery, consent, settings and owner administration share light/dark tokens and self-hosted DM Sans.

Read [the frontend map, validation and rollback guide](docs/FRONTEND-DESIGN.md). Existing MIT Horizon reference sources remain attributed in `third_party/horizon-ui`; the current UI no longer loads the legacy Horizon stylesheet. Font licensing remains in `web/fonts/OFL.txt`.
