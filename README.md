# Vegas Social OS

**Open-source, self-hosted content orchestration for ChatGPT and Codex.** One master skill and MCP server organize account connections, channel briefs, two concepts, native ChatGPT images, Flow video jobs and reviewed social publishing.

**0.1.0 alpha:** original code and offline tests are included. Live Google/Meta login, Flow generation, remote ChatGPT connection and Supabase backup are **not yet verified in this new project**. This is the initial repository, not a finished one-click full social-management product. See [status](docs/STATUS.md).

## Your installation, your accounts

Each community user owns their runtime, private data directory, browser profiles, developer-app credentials and social accounts. No maintainer VPS, account or private infrastructure is embedded. GitHub stores source; the backend/browser worker still needs a running computer or server.

Images come **only from ChatGPT's native image tool**. No image APIs, Flow image tools, third-party fallback or ChatGPT-session scraping. A host without native images must pause. Some ordinary ChatGPT hosts cannot automatically transfer generated image bytes to an external plugin; the dashboard imports those real outputs. Generation and asset transfer are separate capabilities.

## Start from a checkout

Requirements: Python 3.11+, Node.js 22+, Chrome; FFmpeg for assembly.

```bash
git clone https://github.com/AdityaAgarwal75/vegas-social-os.git
cd vegas-social-os
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m vso doctor
python -m vso setup
python -m vso serve
```

Open the private setup link printed by `setup` while the server is running. It expires in 10 minutes and works once. Dashboard: `http://127.0.0.1:8787`. State defaults to `~/.local/share/vegas-social-os`, outside the checkout. On Windows choose a private `VSO_DATA_DIR` and protect it with OS access controls.

Source checkout is the supported installation, not a standalone wheel: web/worker/skill resources are repository-relative. `.env.example` documents settings but is **not automatically loaded**. Export settings through your terminal/service. Never put secrets in GitHub or chat.

## Connect one plugin

Local Codex/compatible clients: root `plugin.json`, `mcp.json` and `skills/vegas-social-master` form the portable local package. Configure absolute virtual-environment Python and checkout working directory if your client does not expand `${PLUGIN_ROOT}`. See [setup](docs/SETUP.md).

Ordinary ChatGPT: put the running server behind your own reachable HTTPS origin, configure `VSO_PUBLIC_URL`, then connect `/mcp` through a supported custom-plugin/app flow. The server provides OAuth discovery, registration, user consent, PKCE and refresh. Host plan/workspace eligibility applies. This repo supplies neither a hosted endpoint nor a public plugin-directory listing.

```bash
python scripts/package_plugin.py --url https://YOUR-ORIGIN/mcp --output /PRIVATE/PATH/vegas-social-os-plugin.zip
```

The helper packages a remote connection after your endpoint exists. Packaging is not hosting or publishing.

## Account access

| Service | User authorization | Private state |
|---|---|---|
| YouTube | Official Google OAuth + exact channel read | Encrypted access/refresh tokens |
| Instagram | Professional account via Instagram Login and user's Meta app | Encrypted access tokens |
| Flow | Separate Chrome profile; user signs in directly | Browser session stays on worker |
| MCP plugin | One-use setup, browser session, consent + PKCE | Hashed plugin access tokens |

Connections are independent: YouTube OAuth does not authorize Flow. Repeat for additional accounts; no fixed count is imposed, but resource capacity, credits and eligibility still limit use.

Users must configure their own Google/Meta developer apps and permissions. A maintained shared community OAuth app is not supplied. An installer cannot eliminate Meta review or Google verification/upload restrictions. Read [onboarding](skills/vegas-social-master/references/onboarding.md).

## Workflow

1. Save channel briefs and explicit publishing destinations.
2. Ask ChatGPT to research/save two concepts with scripts and scene prompts.
3. Choose one concept and a production credit cap.
4. Generate separate native ChatGPT keyframes, import and review them.
5. Inspect Flow, request one scene per durable job under the cap.
6. Poll existing jobs, assemble clips, review the final video.
7. Freeze/approve each exact destination, video and platform-specific copy.
8. Upload to YouTube or process/publish an Instagram Reel through official APIs.

Video jobs and publications have separate identities. Interrupted writes become `unknown` and are never automatically retried. Reservations remain held until reconciliation. The Flow worker refuses ambiguous controls, quotes or assets instead of choosing a random clip.

`schedule_daily` and `morning_queue` create daily brief tasks idempotently. They do **not** wake ChatGPT, write scripts or generate images autonomously. A supported host-side automation must consume them. Two-concept image previews, full analytics, comments/DM management and additional platforms remain future work.

## Supabase

Optional `cloud_sync` backs up secret-free metadata using a user JWT, publishable key and owner RLS in `supabase/schema.sql`. Media, credentials and browser sessions remain local. SQLite is authoritative in this alpha. Cloud job scheduling, distributed workers and automatic JWT renewal are not implemented. Do not apply bootstrap SQL to Orbit or another unrelated app.

## Tests

```bash
python -m unittest discover -s tests -v
node --test tests/flow.test.mjs
python -m compileall -q vso
```

Tests use temporary records and simulated responses, not real provider accounts. For live trials, verify one harmless read, one explicitly budgeted generation, then a private YouTube upload. Never spend credits or publish in CI.

## Source map

- `vso/`: server, OAuth, encrypted store, tools, workflow and optional cloud sync
- `worker/flow.mjs`: original Chrome/CDP browser worker
- `web/`: private setup/review dashboard
- `skills/vegas-social-master/`: master instructions + onboarding/creative references
- `supabase/schema.sql`: optional owner-isolated metadata-backup schema
- `tests/`, `docs/`, `scripts/`: verification, setup and helper commands

MIT · [Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [Research](docs/RESEARCH.md). Independent project, not affiliated with Google, Meta or OpenAI.
