# Control panel rebuild — 15 October 2026

## Scope

Version 0.8.0 replaces the former flat review dashboard with a responsive light/dark system control panel. The owner's supplied green/white dashboard reference informed hierarchy, spacing and sidebar structure. Original vanilla HTML/CSS/JS implements the design; no frontend framework or third-party component bundle was added. The pinned shadcn dashboard/sidebar/chart catalog was consulted for interaction patterns, without copying component source. Existing MIT licensing remains unchanged.

Home presents actual host CPU/memory/disk observations, resource history, last observed Flow balances, unique connected publishing identities, recent projects, real specialist activity and upcoming dated work. Navigation exposes projects, channels/planning, schedules, agents, activity, analytics, connections, settings and owner administration. ChatGPT remains the creative workstation.

## Data contract and migration

- `project_create`, `project_rename`, `project_attach_asset`, `project_list` and `project_detail` expose named video collections. Native `asset_import` and standalone Flow requests accept `project_id`. Shared immutable files retain checksums and download paths. There is no destructive move or rename of originals.
- Existing plans backfill only their proven scene images, job outputs, references and final exports. A standalone job gets a default named collection if the caller omits a project. Multi-scene productions should create one descriptive project and reuse its ID. Historical assets without reliable membership remain Unassigned; the owner can assign them visually. A prompt similarity guess is never used to group media.
- The tool dispatcher records real start/completion/failure under six specialist roles. `activity_report` handles actual host-led work outside server tools, with idempotent task IDs, heartbeat expiry and explicit completion. Idle roles are not independent model processes. Restarted runs become interrupted, and unrenewed running reports become unconfirmed after five minutes.
- Credits are observed balances, with timestamps. Unknown/invalid balances do not count toward totals. Read refresh inspects only existing imported Flow services, never starts an unrequested native browser. Reconnected records for the same provider identity count once in the home identity list.
- Project/editorial dates, draft release dates and approved scheduled uploads remain distinct. Calendar dates use the owner timezone, while the browser displays local times. Cancellation does not appear as an upcoming release. No dashboard visit generates media, publishes, or spends credits.
- Resource history begins with actual observations; first CPU delta is unknown. Samples are collected at most once per 30 seconds while observed, with seven-day retention and up to 240 recent chart samples. No background historical samples are synthesized while the app is unobserved.

## Validation

- 139 Python tests and 5 Node tests pass. Coverage includes real in-flight tool visibility, completion/expiry/restart, concurrent activity idempotency, named-project isolation, native scene import, original asset preservation, Flow request/project replay, unknown balances, duplicate identities, planned vs scheduled dates and private API rejection.
- Python/JS compilation, installer shell syntax and diff whitespace checks pass.
- Real Chrome with the sandbox enabled on isolated VPS state passes fourteen control-panel routes at 360/768/1440/1920 widths in both themes. Project creation/scene assignment/search, theme persistence, storyboard approval/revision, provider setup gates and actual fixture schedule distinctions pass. External provider traffic is blocked.
- The separate onboarding browser suite passes password error/recovery/save/login/logout, mobile navigation and real browser consent-to-PKCE exchange with an intercepted synthetic host callback. No real provider authorization is fabricated.
- Light and dark desktop screenshots inspected; mobile overflow and navigation checked. Muted text contrast and single-sample chart visibility improved after inspection.

## Remaining acceptance boundaries

This rebuild does not establish paid Flow success, a fresh AWS install, public publishing, or unattended ChatGPT event continuation. Existing limitations still apply. Host-only specialist work is visible only when the host reports it; old disconnected clients can still submit ungrouped native transfers until their guide/tool discovery is refreshed and project attachment is used. The bundled guide describes the new workflow. Historical unassigned assets require actual owner/agent context before assignment.

The deployment receipt is added after the tested source revision is promoted and live preservation/health checks complete.
