# Feature audit — 0.6 alpha

This is a verification map, not a claim that every external provider works. Offline tests use simulated provider responses. Browser trials run on disposable local data and block provider network access. Live trials use the founder's installation only.

| Area | Checks completed | Remaining boundary |
| --- | --- | --- |
| Owner onboarding/auth | Expiring single-use links, cookie sessions, private APIs, MCP OAuth/state isolation, encrypted app configuration | Each new owner completes personal consent and 2FA |
| Provider connections | Missing-app UX, official redirects/callback isolation, account/grant/Page request tests | Live consent completion and publishing identities still needed |
| Flow accounts | Five existing signed-in workspaces and seven model choices inspected; scoped existing desktop stream previously tested | Native new-account sign-in is an owner action; no cookies distributed |
| Image diagnostics | Five exact original free JPEGs imported in 0.5; durable IDs, quote/error states tested | Other image models' real output not validated by menu inspection |
| Video controls | Four families, compatible duration/resolution/aspect fields, invalid settings rejection, stable requests, quote stops, original-job polling | Paid clips and advanced Flow features require separate trials |
| Production scenes | Two concepts, selection, native-image attachment/review, credit reservation and duplicate suppression tested | Host must expose actual native image bytes; independent paid worker experimental |
| Content strategy | Audience/voice/pillars, stable weekly requests, dated calendars, freeze boundary, source labels and optional scene prompts tested | Real research/creative work needs a connected host agent |
| Reel review | Speaking-time estimates, hook/preamble checks, long beats/cards and placeholders tested; readable UI output | Text checks cannot establish retention, virality or lip-sync quality |
| Media library/assembly | Checksummed actual byte imports, private delivery, FFmpeg prerequisite and assembly request tests | Rendered production clips still need visual/audio QA |
| Composer/publishing | Exact destination/media/copy/audience/timing review, cancellation, provider request sequences and uncertain-write suppression tested | No live posts published by this audit |
| YouTube recovery | Saved resumable session inspection, original upload resume, cover-only failure/retry tests | A real controlled upload is needed to confirm provider acceptance |
| Instagram/Facebook | Eligible account/Page/grant checks and photo/video/carousel request sequences tested | Permissions, app review and live media acceptance remain operator-specific |
| Scheduling | Brief queue idempotency, enabled/paused state, approved releases, missed schedules and heartbeat tested | VPS must run; daily requests do not wake ChatGPT |
| Research/archives | Public-reader network/robots guards, source notes and private Drive request/recovery tests | Actual external grants/source availability must be verified |
| VPS/AWS installation | Installer syntax, private runtime defaults, CloudFormation schema and HTTPS founder deployment previously checked | Fresh AWS-account provisioning still needs an end-to-end trial |
| Dashboard | Profile/app config/channel/media/draft/cancel/schedule/strategy/Reel controls, 12 routes, 360/768/1440, no page exceptions | Real external consent/render/publication is separate from UI QA |

Native and imported profiles now use one complete engine family through the same API adapter. The installer installs a pinned full engine and attaches it to the app-owned private browser. Legacy independent submission is disabled. Complete engine settings passed 33 no-credit probes across the five existing accounts; new native sign-in/rendering still needs owner acceptance. See FLOW-EXECUTION-CONTRACT.md for the operation matrix and dependency provenance. Extend, editing, upscale, advanced voice/character features and live publication remain separate gaps.

Run `workflow_audit` for saved readiness and unresolved jobs. An unknown or processing job must be inspected/polled; do not create a second request because a timeout occurred. Invalid references are rejected before reserving a durable submission. A positive credit quote must stop a cap-zero request before rendering.
