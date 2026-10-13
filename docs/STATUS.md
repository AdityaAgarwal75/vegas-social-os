# Status — 0.2.0 agent-first cloud alpha

End-user contract: share repo link, authorize services/costs, open onboarding, enter details, complete provider/plugin consent, approve creative work. No installation commands, local PC or user-managed VPS.

| Capability | Implementation | Verification |
|---|---|---|
| Agent entrypoint/manifest/capability planner | BOOTSTRAP.md + machine-readable manifest + planner | Missing-tool/native-image/receipt tests; independent setup-skill trial |
| Cloud-only setup policy | Managed app host required; no local-PC/VPS route | Planner/script guards and source review |
| Managed deployment | Docker/compose + Render cloud blueprint | Source only; container build, browser sandbox and live provider deployment not yet tested |
| User profile/channel onboarding | Dashboard name/brand/timezone/goals/connections | Server/form syntax + profile validation; full browser trial pending |
| MCP stdio/HTTP/OAuth | Registration, consent, PKCE, refresh, authenticated tools | Local protocol/HTTP tests; real ChatGPT connection pending |
| Supabase authoritative state | Whole-state encryption, server-only revision RPC, local transaction cache | Mocked round-trip/reload/CAS/outage tests; actual Postgres/RLS grants pending |
| Private cloud volume | Key, profiles and working media | Deployment recipe; actual restart/persistence trial pending |
| Scoped remote Flow login | Per-account Xvfb/Chrome + authenticated noVNC stream | Ticket/account/admin-scope tests; real container/browser login pending |
| YouTube OAuth/read/resumable upload | Adapter included | No live trial |
| Instagram Login/profile/Reels | Adapter included | No live trial; some current Meta docs login-gated |
| Drive OAuth/private media archive/reconciliation | drive.file adapter + optional host connector path | Mocked duplicate/unknown/reconciliation tests; no live Drive trial |
| Native ChatGPT images | Host-native only; agent imports actual bytes | No API fallback; automatic transfer is host-dependent and unverified |
| Flow first-frame generation/download | Original experimental CDP worker | Helper tests; real controls, upload and asset matching need repair/validation |
| Credit caps/reservations | Transactional plan/job guards | Offline cap/idempotency/concurrency tests; actual balances/refunds not implemented |
| FFmpeg assembly | Cloud-runtime command | No media assembly smoke test yet |
| Exact publication approval | Separate immutable publication identity | Offline tests; live publication trial pending |
| Daily brief queue | Idempotent timezone-aware tasks | Local tests; supported ChatGPT host scheduler still needed |
| Silent plugin installation | Not promised | Host consent/install UI remains required when applicable |
| Full cloud provisioning connectors | Capability contract + runtime script/recipes | No universal Render/Supabase/app-registration connector is bundled |
| Photos/carousels/comments/DMs/additional social platforms | Not implemented | Current publishing adapters: YouTube videos and Instagram Reels |
| Advanced Flow edits/Extend/upscale/distributed workers | Not implemented | No verified tools advertised |
| Central multi-tenant hosting/public plugin listing | Not implemented/submitted | Independently managed single-operator deployments only |

Current local checks: **37 Python tests + 3 Node worker helper tests** pass. They do not prove live Google/Meta/Drive, Render, Supabase SQL or ChatGPT integration.

Next validation: provision one authorized managed cloud trial, check database grants/state and volume persistence, test remote browser sandbox/login, connect one real plugin, verify native-image transfer, then one explicitly capped Flow clip and one private YouTube upload. Do not label the workflow production-ready before this passes.
