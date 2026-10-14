# Status — 0.6.0 community alpha

Verified on 13 October 2026. This is an independently self-hosted project; the maintainer's accounts and credentials are not distributed.

## Observed checks

- **74 Python tests pass**: state/permissions, OAuth state isolation, encrypted dashboard app settings, Page discovery/grants, exact-release idempotency, duplicate-upload suppression, unknown-write stops, carousel phases, cover-only failure/retry separation, original YouTube-session reconciliation/resume, scheduling/cancel/missed handling, robots/private-network research guards and AWS template boundaries.
- **3 Node Flow worker tests pass**, plus Python compilation, JavaScript syntax, installer shell syntax and clean diff checks.
- **CloudFormation schema lint passes** using cfn-lint 1.57.2. This is source/schema validation; no fresh AWS instance or billable resource was created by these tests. Live IAM/quota/change-set/SSM/bootstrap checks and cfn-guard validation remain separate deployment checks.
- **Real sandboxed Google Chrome dashboard QA passes** on the founder's VPS, against disposable localhost data, separate from the live service. Profile → encrypted app configuration → channel brief → actual image import → exact composer draft → cancellation → daily schedule/pause all passed. Eleven workspace routes and 360/768/1440 layouts passed, with no JavaScript page exceptions.
- QA accounts are explicitly simulated local fixtures; they do not represent verified provider connections. Browser QA never submits a provider login, post or credit-consuming generation.
- **Live authenticated dashboard QA passed** with the founder’s real account references, exact imported image queue, authenticated embedded existing desktop and 360/768/1440 layouts. A real WebSocket subprotocol mismatch was corrected and covered by a socket-level regression test.
- The rebuilt 0.5 dashboard passed a separate staged localhost browser trial. The reviewed 0.5 runtime was deployed behind HTTPS; `/health` returned 0.5.0, Orbit remained HTTP 200, the scheduler was running, all five existing Flow services remained active, and anonymous `/api/state` and `/mcp` were denied.

## 0.6 audit extension

Model-aware existing-service video jobs and production-scene selection, current documented/live model provenance, content strategy requests and weekly editorial calendar review, original Reel beat/timing checks and truthful workflow readiness. See AUDIT-0.6.md. These additions require staged/live checks before claiming deployment; paid rendering and social publication remain unverified.

## Implemented in this release

Rebuilt control centre with direct official-consent buttons, advanced-only operator credentials, a dedicated Google Flow Studio and durable one-image local-service jobs. Dashboard-owned onboarding with exact callback URLs, official developer-console links, encrypted client settings, multiple independent Flow profiles and an embedded private login browser. Imported existing service accounts preserve their existing workstation and may share its display; they are not described as isolated desktops. Provider identity inspection is separate from publishing evidence. Facebook discovers eligible Pages and checks grants/content tasks; Instagram uses professional-account Instagram Login.

Composer/review queue for YouTube MP4s and thumbnails, Instagram JPEG posts/Reels/carousels, Facebook Page text/links/photos/photo sets/videos, and provider-specific fields. Original YouTube upload sessions can be inspected/resumed without creating a second video. Failed thumbnails do not re-upload videos. Scheduled exact approved posts execute while the server runs; stale schedules over one hour become missed.

Daily creative brief queue and visible scheduler heartbeat; public bounded research reader and source-attributed notes; native-image/scene review controls; FFmpeg final assembly; independent existing-host installer; pinned AWS instance/IP/HTTPS bootstrap template and agent-readable setup/permission documentation.

## Remaining verification and gaps

- **Independent-worker signed-in Flow video generation remains unverified.** The optional existing-service adapter imported and verified all five founder accounts without copying profiles; one free-only image trial per account completed and imported its exact downloaded output. Each was a decodable 1024×1024 JPEG with a matching SHA-256 and zero quoted credits. Accounts 1–3 used the tool registry; accounts 4–5 used the live authenticated HTTPS dashboard API. No videos or social posts were created in these trials. The founder's separate working browser automation was studied for workflow/queue/budget behavior, without copying source or importing cookies. It does not validate this project's worker. English selectors, model/first-frame controls, exact output correlation and live quote parsing remain experimental.
- **Live consent completion and YouTube, Instagram and Facebook publishing remain unverified.** Official Google/Instagram consent redirects and exact operator-owned callback paths were checked; own state prefixes reach Social OS and foreign/missing states remain on Orbit. The founder’s Google/Instagram app settings were configured privately. Facebook has no configured app. The adapters are implemented and their request sequences are tested with mocked responses. Provider app registration, eligible accounts, redirect registration, consent/2FA, access scopes and platform review remain operator-specific. Business verification alone is insufficient.
- Meta reference retrieval was rate-limited for several official pages; current version/permission/media acceptance must be checked against the operator's app and controlled live trials. Do not describe mocks as platform acceptance.
- **Fresh-VPS/AWS provisioning is not yet tested end to end.** Template/schema tests are not proof of every new-account AMI, quota, permission, SSM or certificate condition. Use docs/AWS-ONBOARDING.md for the actual checks and cost/approval boundaries.
- **Unattended creative execution needs a real host agent trigger.** The VPS cannot access a ChatGPT Plus account or wake native image generation as an API. Daily queue entries alone do not produce scripts/images. Host tools must expose actual image bytes before transfer can be claimed.
- Facebook dedicated Reels/custom video thumbnail adapters, other social platforms, DMs/comments/full analytics and multi-tenant hosting are not implemented. Do not market all platforms as working.
- Publishing/generation still use exact approvals and credit caps. No arbitrary autoposting or hidden paid API fallback is enabled.

## Deployment checks to repeat

Verify reviewed Git commit, systemd, HTTPS `/health` returning 0.5.0, authenticated connection/automation state, unauthenticated `/api/state` and `/mcp` denial, Orbit health, existing Flow services and the live scheduler heartbeat. Preserve private data/key/profile directories across update. Run an isolated disposable signed-out browser check, then complete owner sign-in and one controlled generation/publishing trial only when its exact account/model/budget or destination/media/text is authorized.
