# Architecture — independent self-hosted control room

One operator owns each installation, its VPS, OAuth applications, account credentials and local media. Any community user can deploy the same public source to their own server. No maintainer IP, account pool or centrally shared secret is required. GitHub distributes source and updates; **SQLite is authoritative by default**. Supabase/managed hosting are optional legacy adapters, not installation prerequisites.

## Components

- **Dashboard:** ten responsive workspaces: overview, setup, connections, channel briefs, productions, media, composer, release queue, automation and research. Plain browser JavaScript/CSS keeps deployment independent of a frontend build service. Embedded private Flow sign-in remains account scoped.
- **API/MCP:** Python server with resource-bound OAuth/PKCE for host agents and HttpOnly owner sessions for the dashboard. Encrypted app settings can only be entered through a private dashboard session; their values are never returned as MCP tools.
- **Account layer:** separate Google YouTube/Drive, Instagram Login and Facebook Login registrations. Flow browser sign-in does not confer YouTube OAuth access. Facebook connector verifies granted Page scopes and create-content tasks, then discovers eligible Pages. No consumer Instagram accounts or Facebook personal timelines are represented as publishing destinations.
- **State:** private SQLite transactions, a local Fernet vault key, encrypted provider credentials, hashed one-use setup/OAuth tickets, audit events, private profiles and checksum-identified media. Back up the complete private data/key directory securely. Encryption does not protect against compromise of the server holding its key.
- **Generation:** original Node/CDP worker controlling isolated graphical Chrome. Identity/project inspection, explicit budgets, first-frame input, one-output checks and unknown-result stops. Current controls remain experimental until signed-in tests succeed on the target host. No cookie harvesting or CAPTCHA bypass.
- **Publishing:** an exact review record freezes account, ordered asset checksums, copy, visibility, YouTube audience/tags/category, optional cover, and scheduled time. The record is claimed before network writes. Retries never re-upload an unknown post. YouTube video upload and thumbnail application are separate; failed covers do not cause duplicate videos. Instagram carousel children, parent creation, processing and final publication are distinct persisted phases. Facebook videos show provider processing until checked.
- **Scheduler:** daemon inside the application queues daily briefs and executes already approved scheduled releases. It polls existing composer processing states. It never starts paid generation or a ChatGPT session. Stale releases delayed over one hour become `missed`; interrupted network writes remain `unknown` for reconciliation.
- **Research:** host web search plus saved source-attributed notes. Optional bounded public HTTPS reader uses DNS-pinned public addresses, per-request robots checks, response limits, no credentials and no login bypass. Returned page text is untrusted data, never executable instructions.
- **Provisioning:** installer for an existing host; pinned CloudFormation recipe for a fresh independent AWS instance. Agent-owned installation requires actual AWS/process tools and paid-resource consent. No cloud account keys appear in the repository, app setup forms or chat.

## Production and release flow

Channel brief → two researched concepts → user selection and total credit cap → actual transferred keyframes → image review → one durable scene job per scene → verified downloaded clips → FFmpeg/final edited video → exact per-platform release review → immediate publication or approved schedule.

A composer can also release existing media or Facebook text/link posts without a video production. Cross-posting means separate exact records and platform-specific text; destinations are never inferred from unrelated channel accounts.

## Independent consent boundaries

1. AWS/service authorization allows infrastructure operations within that connector's permissions.
2. Dashboard pairing establishes an operator session.
3. Host MCP consent connects this particular installation to an agent.
4. Provider-app registration establishes this operator's developer credentials and callback URLs.
5. Each account's OAuth consent/Google login grants its own access.
6. Platform review/verification and quotas determine eligible operations.
7. Creative credit caps and exact release approvals permit specific generation/publication actions.

None substitutes for another. The dashboard reports configured apps, provider read evidence, browser/project readiness and published results separately. Account connection alone does not silently authorize spending or a public post.

## Unattended work

Native ChatGPT images and creative reasoning are host capabilities. A VPS cannot call a Plus subscription as an unattended API or wake the host's image tool. A real host automation/agent trigger must consume daily briefs. Optional API agents would require a separately authorized provider/configuration and may incur costs; they are not silently enabled as a fallback. The installation continues to schedule already approved posts without a creative agent.

Additional platform adapters, messaging/comment automation, a shared multi-tenant SaaS, universal developer-app registration and automatic platform approval are not implemented. Fresh AWS provisioning and full signed-in Flow-to-publication trials are distinct from unit/browser QA.
