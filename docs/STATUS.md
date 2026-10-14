# Status — 0.6.0 community alpha

Updated on 14 October 2026. Live is 0.6.0 alpha, deployed from reviewed main 61dc2e786354a8f8a65f8b111b78e1c240f09e02; earlier observations below retain their historical scope. This is an independently self-hosted project; the maintainer's accounts and credentials are not distributed.

## Observed checks

- **79 Python tests pass**: state/permissions, OAuth state isolation, encrypted dashboard app settings, Page discovery/grants, exact-release idempotency, duplicate-upload suppression, unknown-write stops, carousel phases, cover-only failure/retry separation, original YouTube-session reconciliation/resume, scheduling/cancel/missed handling, robots/private-network research guards and AWS template boundaries.
- **4 Node Flow worker tests pass**, plus Python compilation, JavaScript syntax, installer shell syntax and clean diff checks.
- **CloudFormation schema lint passes** using cfn-lint 1.57.2. This is source/schema validation; no fresh AWS instance or billable resource was created by these tests. Live IAM/quota/change-set/SSM/bootstrap checks and cfn-guard validation remain separate deployment checks.
- **Real sandboxed Google Chrome dashboard QA passes** on the founder's VPS, against disposable localhost data, separate from the live service. Profile → encrypted app configuration → channel brief → actual image import → exact composer draft → cancellation → daily schedule/pause all passed. Twelve workspace routes and 360/768/1440 layouts passed, with no JavaScript page exceptions.
- QA accounts are explicitly simulated local fixtures; they do not represent verified provider connections. Browser QA never submits a provider login, post or credit-consuming generation.
- **Live authenticated dashboard QA passed** with the founder’s real account references, exact imported image queue, authenticated embedded existing desktop and 360/768/1440 layouts. A real WebSocket subprotocol mismatch was corrected and covered by a socket-level regression test.
- The rebuilt 0.5 dashboard passed a separate staged localhost browser trial. The reviewed 0.5 runtime was deployed behind HTTPS; `/health` returned 0.5.0, Orbit remained HTTP 200, the scheduler was running, all five existing Flow services remained active, and anonymous `/api/state` and `/mcp` were denied.

## 0.6 audit extension

Model-aware existing-service video jobs and production-scene selection, current documented/live model provenance, content strategy requests and weekly editorial calendar review, original Reel beat/timing checks and truthful workflow readiness. See AUDIT-0.6.md. The candidate passed staged disposable browser QA across 12 routes, strategy/calendar/Reel/model controls and 360/768/1440 layouts. All five existing-account model menus were inspected live; paid rendering and social publication remain unverified.

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

Verify reviewed Git commit, systemd, HTTPS `/health` returning 0.6.0, authenticated connection/automation state, unauthenticated `/api/state` and `/mcp` denial, Orbit health, existing Flow services and the live scheduler heartbeat. Preserve private data/key/profile directories across update. Run an isolated disposable signed-out browser check, then complete owner sign-in and one controlled generation/publishing trial only when its exact account/model/budget or destination/media/text is authorized.

## Product planning checkpoint, 14 October 2026

The live server remains 0.5.0; 0.6 is an unmerged candidate on PR 5. The user requested product definition before further feature work/deployment. See PRODUCT-PLAN.md. The reviewed candidate passed 79 Python / 4 Node tests and 12-route disposable browser QA. Additional licensed skill/continuity work passes 81 Python / 4 Node tests locally; staged/live checks remain pending for those additions. Do not describe them as deployed.

All four model zero-credit guards completed: Omni 7, Lite 10, Fast 20, Quality 100 quoted for the exact diagnostic combinations, zero spent. Account 1 remained at 951. Historical clip import decoded as 8s 1280x720 H.264/AAC; no new paid clip or post was made.

## Accepted plan: complete engine checkpoint

Direction accepted on 14 October 2026. Complete engine installation/compilation succeeded in an isolated candidate directory. Native profiles now use an attached full engine rather than the independent experimental submission algorithm. Native signed-out browser inspection, one engine owner, anonymous API denial, private token permissions and synthetic interrupted-queue recovery passed after initial page navigation settled. The same Chrome remained in use after the engine restart. These are infrastructure tests, not owner login or newly rendered video proof.

33 real settings probes passed across five accounts: account 1 covered all Omni durations/resolutions, both aspects, all four video model families and compatible Frames/Ingredients mode selection; accounts 2–5 covered four model families each. No Generate was clicked and controls were restored. No image/reference attachment or new render follows from these probes. The current original suite passes 88 Python / 4 Node tests. Advanced edit/extend/upscale/voice features remain unwired. See FLOW-EXECUTION-CONTRACT.md.

Exact complete-engine candidate 59c278973f3b84f28f6a984640f00017cef58dc8 passed 88 Python / 4 Node tests and shell checks on the VPS. Its 12-route sandboxed Chrome QA passed against disposable data, and both GitHub CI jobs passed (run 56). Native read-only startup retries also passed without a manual delay. Re-running the exact engine installer was a no-op. All five accounts remained signed in/project-ready and idle at balances 951, 443, 50, 50, 50; no credits spent.

Final menu discovery checks enabled/disabled choices in Frames mode before reading video families, restores the previous input mode, and the dashboard refreshes models after account verification. This avoids presenting account-disabled models as usable or treating Ingredients restrictions as account-wide model absence.

Final native profile ownership hardening also rejects stale browser/CDP mappings that belong to another process or profile. The suite now passes 89 Python / 4 Node tests, including rejection before attachment or job reservation.

## Live alpha deployment, 14 October 2026

PR 5 was merged as main 61dc2e786354a8f8a65f8b111b78e1c240f09e02 and deployed with an atomic source pointer and a private source/environment/state rollback checkpoint. All six media records/files and existing Flow profiles were preserved. HTTPS health returned 0.6.0, dashboard and Orbit returned HTTP 200, authenticated state showed five ready Flow accounts and a complete installed engine, and anonymous API/MCP requests returned 401.

Existing engine source was backed up, compiled with the tested settings/final-quote guards, and activated one idle service at a time. All five returned signed-in/project-ready at unchanged balances 951/443/50/50/50. The normal complete engine is installed separately for new native profiles; imported profiles keep their existing owner.

Live authenticated Chrome verified all four model selectors and actual account-specific durations/resolutions with no page exceptions. A five-reference mobile layout overflow absent from the one-image fixtures was found and fixed with a bounded grid/fieldset layout. The correction passed actual-data 360px viewport checks without clipping controls. These UI checks did not submit generation. No paid video or public post was created by this audit. Newly rendered output, advanced operations and real end-to-end publication remain unverified.
