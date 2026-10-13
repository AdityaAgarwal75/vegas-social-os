# Setup agent entrypoint

Follow this when the user gives the repository link and requests setup. The user should only connect/authorize services, approve paid provisioning, complete account consent and approve creative work. **Never ask them to run a command, install a package, paste code/SQL or manage a container.** You perform technical operations using their connected tools.

## 1. Discover capabilities before promising setup

Read `agent-manifest.json`, `AGENTS.md`, `docs/STATUS.md` and the master skill. Inspect actual connected tool schemas, not imaginary tool names. Check authenticated read-only access before depending on each service.

Required for cloud onboarding: public source read; Supabase project/schema management; managed cloud app hosting and process execution; private persistent cloud storage; secret injection; HTTPS routing; plugin creation and provider-app administration. Native ChatGPT images and byte transfer are separate creative-stage requirements, not blockers to presenting the dashboard. GitHub repository creation is optional: checkout public source without creating a fork if unavailable. No local-PC or user-managed-VPS setup route.

Run `vso.bootstrap.plan`/`scripts/agent_bootstrap.py plan` yourself with verified capability flags, or use `setup_plan` if an existing control plugin is connected. A tool is not verified merely because it is listed. Return missing-service connection/install actions. Continue independent safe setup work. Do not give the user terminal instructions.

If only GitHub and Supabase are connected, request a managed cloud app-hosting service providing persistent browser execution, private volume storage and HTTPS. The initial candidate is Render using `deploy/render.yaml`; verify provider capabilities and obtain paid-resource approval. A Sites/Workers/Edge-only deployment cannot execute this Chrome runtime. Do not use a local PC, user-managed VPS or temporary Codex cloud scratch environment as the deployment.

## 2. Provision user-owned resources

- Resolve the intended GitHub/Supabase account from actual tool identity. Select an authorized Supabase organization; if multiple could satisfy the write, ask the user to select one. Follow tool requirements for project creation and cost authorization.
- Use a dedicated project and deployment, never Orbit, the maintainer's VPS, an unrelated database or another user's environment.
- Read/pin the source commit and provision from that revision. Create a private source mirror only if supported/useful; do not make it a prerequisite.
- Apply `supabase/agent-state.sql` using the connected schema tool. Verify table RLS, service-only grants and RPC CAS behavior. Follow the Supabase tool/skill workflow for migrations/advisors.
- Generate a UUID installation ID. Provision a persistent private volume for encryption key, browser profiles, SQLite transaction cache and media. Supabase stores encrypted authoritative state; the runtime key must survive restarts and be backed up securely.
- Deploy `deploy/render.yaml` and its Dockerfile through the connected managed cloud service. Select a current paid plan only after cost authorization and capacity assessment. Keep VNC/CDP private and the app behind a WebSocket-capable HTTPS route. Keep Chrome sandboxing; if the provider cannot support it, evaluate another managed cloud service rather than a local-PC/VPS path or weaker safeguards.
- Inject `VSO_PUBLIC_URL`, `VSO_INSTALLATION_ID`, `VSO_RUNTIME_PERSISTENT=1`, `VSO_CLOUD_MANAGED=1`, `VSO_STATE_BACKEND=supabase`, project URL/server key, vault key and private data directory through managed runtime secrets/config. Never paste credentials into chat/GitHub or put server keys in frontend code.

The recipe is an implementation candidate until built on the chosen provider. Use actual runtime logs/health checks and repair failures; never mark a written Dockerfile as deployed.

## 3. Configure social OAuth as the agent

Use connected provider administration or permitted browser tools to create/configure the user's Google/Meta developer apps, exact callbacks and needed permissions. YouTube callback is `/callback/youtube`; Instagram Login callback is `/callback/instagram`. Store credentials directly through secret tools. Configure a currently supported Meta version after checking official documentation.

If provider-app administration is unavailable, request that tool/connection or surface the provider's unavoidable approval/verification action. Do not ask the user to paste secrets into chat or type configuration code. A shared maintained community OAuth application is not supplied, so each independent installation needs an authorized registration. Do not claim account-login alone eliminates developer registration/review.

Google Flow uses an isolated persistent browser, not YouTube OAuth or a Google API token. Users type passwords/2FA themselves inside their account-scoped dashboard browser. Never extract everyday Google cookies or create an account-rotation workaround for restrictions.

## 4. Prepare the runtime and return onboarding

Execute `scripts/agent_bootstrap.py prepare` **yourself on the persistent runtime**. This verifies dependencies and Supabase access, creates an expiring setup link and returns dashboard/MCP URLs. It refuses ephemeral runtimes and unsupported local-only browser mode. Dependency installation is agent-owned. Start/restart the service through the deployment tool.

Check live HTTPS `/health`; source/version; schema/RPC state; persistence after a harmless restart; private remote-desktop startup and unauthorized/cross-account rejection. No Google login or credit spend is needed to validate browser infrastructure. Keep keys/tickets out of logs and issue bodies.

Only return a clean dashboard URL plus the private temporary onboarding link after those checks. Keep the link private; it expires after 10 minutes. For expiry, generate another yourself through the runtime tool. Do not ask the user to run `setup`.

## 5. Create/connect the one plugin

Package the remote master plugin yourself with `scripts/package_plugin.py`, using the **verified** HTTPS `/mcp` endpoint. Create it through the host's available plugin tool or supported deployment-to-plugin integration. Source-local stdio configuration is for developer testing, not ordinary-chat onboarding.

When the host exposes installation UI, show it using its supported plugin-management action. Otherwise provide the exact host install/consent action. Do not promise silent installation: the host owns this trust boundary. Reuse the created plugin identity on retries/updates; do not create duplicates when a result is uncertain.

After user consent, verify `guide`, `doctor` and `onboarding_status` through the real connected plugin. Record `setup_receipt_save` with actual source SHA, clean HTTPS URLs and real check outcomes. The receipt is an evidence record, not independent third-party verification. False flags keep setup incomplete.

## 6. User-only onboarding

The dashboard collects name, brand, timezone, goals and channel destinations. It provides YouTube/Instagram OAuth sign-in and Flow **Add account** links opening private isolated browsers. Repeated Flow accounts each get their own profile/display/login session; no count is hardcoded. Resource limits and actual Google rules still apply.

The agent reads the resulting profile and account readiness. It does not receive passwords or a general-purpose Google-account API grant. OAuth/provider credentials remain server-side; the browser session stays on the user's runtime.

## 7. Media archive and first creative workflow

Read `docs/CLOUD-ARCHITECTURE.md`. Verify a host Drive connector's actual upload/write actions and intended account before relying on it. Its tokens do not transfer to the backend. Alternatively configure `/callback/drive` with `drive.file`, then archive approved outputs using `asset_archive_drive`. Preserve private sharing and reconcile unknown uploads using `drive_archive_reconcile`.

Follow the master skill: strategy → two concepts → user choice/budget → native ChatGPT scene images → image approval → capped Flow scene jobs → final video review → exact release approval.

Verify native image-tool and generated-byte transfer capabilities before promising an entirely automatic image handoff. If the host cannot transfer bytes, report that stage as blocked and identify the supported host capability needed. Do not replace images, scrape ChatGPT, or shift manual file-upload work onto the user as the default.

No live generation/upload test without an explicit budget/destination. A morning queue is not a running ChatGPT agent: connect a real supported host scheduler and verify the plugin before promising daily unattended preparation.

## Completion report

Report real dashboard/plugin links, resource identity, connected account counts, checks passed, checks still blocked and any approved ongoing resource cost. Never describe source-only infrastructure, simulated provider tests or a packaged archive as a completed deployment/connection.
