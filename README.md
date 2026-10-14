# Vegas Social OS — your social production team inside ChatGPT

**Primary workstation: ChatGPT web (Work). No desktop app or local computer executor is required.** Read [web setup](docs/CHATGPT-WEB.md) for connection steps and verification.

**Plan in ChatGPT. Execute on your own VPS. Sign in and review in the dashboard.** An open-source, independently self-hosted social production system for original research, scripts, scene images, Google Flow clips and reviewed publishing. Not affiliated with OpenAI, Google or Meta.

## The product

ChatGPT is your main workstation. Its private plugin connects to your own installation. You discuss strategy and scenes in chat; ChatGPT uses native images and the VPS's Flow browser/execution engine. The dashboard is only for account onboarding, storyboard decisions, watching clips/final videos and reviewing releases. Manual generation forms are excluded from normal navigation.

Read [the accepted ChatGPT-first architecture](docs/CHATGPT-FIRST.md) and [the complete new-user journey](docs/NEW-USER-JOURNEY.md), including plugin structure, permissions, VPS administration boundaries, optional Drive storage and the unattended-work implementation gates.

**0.7.0 engineering candidate:** founder VPS browser/settings checks and offline tests exist. Durable storyboard-feedback requests and review-focused navigation are implemented. Paid Flow rendering, fresh AWS onboarding, real publishing and event-driven ChatGPT continuation are not yet accepted end to end. [Current evidence](docs/STATUS.md) distinguishes source, menus, submitted jobs and usable outputs.

## Give this repository to your ChatGPT

If AWS Core is connected to your own AWS account, send:

> Set up https://github.com/AdityaAgarwal75/vegas-social-os on my own independent AWS VPS. Read BOOTSTRAP.md and docs/CHATGPT-FIRST.md. Prepare the deployment and costs for approval, install a pinned revision, verify HTTPS/private browser, and prepare my own ChatGPT plugin. I will use the dashboard to sign into Google accounts and review storyboards/clips. Keep credentials private; do not spend Flow credits or publish yet. Explain tested versus pending automation.

Your agent uses the [AWS setup recipe](docs/AWS-ONBOARDING.md), scoped AWS tools and SSM. It derives a stable HTTPS address and returns the dashboard plus private onboarding link after checks. AWS Core connection alone does not prove all required permissions are available. Account login/2FA, provider approval, billable-resource authorization and plugin installation consent remain personal steps. There is no maintainer VPS or shared account pool in this path.

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

Current owner browser sessions last eight hours; issue a fresh link after expiry. Convenient persistent owner sign-in is planned. Never post pairing links publicly.

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
| Social publishing | Implemented adapters/offline guards; real provider consent and release trials pending |
| Daily briefs/approved schedules | VPS queues briefs and schedules exact approved posts while running |
| ChatGPT event continuation | Protocol and signed delivery implemented; actual Web host continuation not accepted |
| Full VPS admin in same plugin | Isolated root-owned Unix broker implemented; owner approval/enrollment required |

Private state/media/profiles live in `/var/lib/vegas-social-os`, code in `/opt/vegas-social-os`, service `vegas-social-os.service`, default loopback port 8899. Back up complete private state/key securely; never commit it. VPS/credits/network costs are separate from this free project. Respect authentication challenges, quotas, provider review and researched dependency licenses.

Read [architecture](docs/ARCHITECTURE.md), [Flow execution contract](docs/FLOW-EXECUTION-CONTRACT.md), [contributing](CONTRIBUTING.md) and [security](SECURITY.md). MIT licensed.

Current engineering repairs, web connection acceptance and owner administration: [operations 0.7](docs/OPERATIONS-0.7.md), [dated audit](docs/audits/2026-10-14-engineering.md).
