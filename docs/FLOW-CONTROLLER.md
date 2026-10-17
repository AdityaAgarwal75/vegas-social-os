# Vegas Flow Engine — durable controller

ChatGPT supplies creative decisions, exact prompts and real transferred images. The VPS owns account routing, uploads, provider job polling, output download and local assembly. It does not run another language model or require a second plugin, API subscription or database service.

## Plugin contract

- `flow_batch_submit(project_id, scenes, account_ids, max_credits, request_id)` freezes 1–12 expressly authorized standalone video scenes. Each scene supplies `prompt`, `model`, `duration`, `resolution`, `aspect_ratio`, `max_credits`, and optional `first_frame_id`, `last_frame_id` or `reference_asset_ids`. References must be real imported image IDs. Use frames OR ingredients. Sum of scene ceilings cannot exceed the batch ceiling. A cap of zero permits only a free operation/preflight; it does not grant paid rendering. The caller must have the owner's generation and spending authorization.
- `flow_production_submit(plan_id, account_ids, options, max_credits, request_id)` queues every scene from a selected, image-approved plan. Options contain model, duration, resolution, aspect_ratio and positive per-scene max_credits. The controller uses the original scene prompts/keyframes, enforces existing production/channel caps and permitted accounts, and starts FFmpeg assembly after every clip completes. A queued batch never approves a storyboard or a release.
- `flow_batch_status(batch_id)` observes an existing batch; repeated host polling is optional.
- `flow_engine_status()` returns controller heartbeat, last cycle, queue, account observations, pause/wait reasons and outputs.
- `flow_batch_cancel(batch_id)` stops undispatched scenes. Original provider work stays visible and continues reconciliation. It does not claim to cancel an active Google render.

`guide` returns these instructions along with the existing master workflow. Existing single-image/video tools remain compatible and are automatically polled by the controller. New tool discovery may require refreshing the existing ChatGPT connection; server deployment alone does not refresh a cached host tool list.

## Durable lifecycle

`queued → dispatching → processing → completed`, or `failed / stopped / blocked / unknown`.

Batch inputs and deterministic child IDs are committed before provider operations. An interrupted claim finds its exact child, or becomes `needs_review` if no receipt exists. It never requeues that scene. Backend completion must name the original job and exact file. Videos pass signature, ffprobe and first-frame decoder checks; new worker receipts also validate requested duration and aspect. Technical validation is separate from creative review. A completed production batch includes its final export only after the existing editor finishes; `assembling` and `needs_review` remain distinct.

Browser locks are keyed by installation account/service alias, so duplicate records for one service cannot bypass a lock. An unresolved account cannot accept another job. Other eligible owner-authorized accounts can do independent work; a failed scene is never silently retried on another account. Provider security/rate-limit refusals pause that account's routing until an explicit successful account inspection after normal remediation. No CAPTCHA bypass or quota evasion is implemented.

The controller reconciles original image/video/production jobs every cycle with bounded backoff. Twenty-minute stale jobs become `unknown`, retaining backend identifiers and continuing read-only recovery. This releases the global active slot, not the affected account's lock. It does not prove Google cancelled or refunded anything. Reservations remain conservative.

## Runtime and resource policy

The controller is a daemon thread in `vegas-social-os.service`, separate from scheduled publishing/events. A private `flock` under the state root permits only one controller per installation. SQLite remains authoritative. Restarting the gateway preserves queue/receipts and never resubmits ambiguous writes.

Default concurrency is **one** active provider job on a shared host. Set administrator environment `VSO_FLOW_MAX_ACTIVE=2` (up to 5) only after independent browser input isolation and measured capacity are verified. Browser accounts are not proof of safe parallel UI operation. Unrelated legacy direct callers have account admission locks but are not scheduled by the batch resource governor; use the batch endpoints for governed dispatch.

Before new dispatch, require 512 MiB available memory and disk, and a one-minute load below 2.5 times CPU count. Existing output recovery continues while new submissions are paused. No automatic deletion of user media is performed. Idle imported service health is refreshed one account per cycle, at most every two minutes/account. Native profiles are not launched in the background; explicitly open and inspect them first. Credentials stay in the existing private service binding.

The dashboard's **System → Vegas Flow Engine** panel shows measured controller state, batches, scene states and waiting/assembly errors. Named project links retain existing media storage and checksums. Specialist activity records remain real tool/host activity; the controller heartbeat is not presented as another thinking AI.

## Other backend responsibilities

Local FFmpeg workers already own their durable subprocesses. Scheduled publication polling, event delivery and due-brief creation now isolate failures so one bad provider connection does not stop unrelated scheduled work. Approved publishing records and host-native creative queues retain their existing authorization rules. The VPS cannot start native ChatGPT image generation on its own.

## Recovery and deployment

Never delete locks/jobs to force a new paid submission. Use `flow_job_reconcile` or the exact image/video poll, inspect the provider's original project, and retrieve existing output. A truly new take needs a new request and authorized ceiling. Queued batch cancellation does not release an uncertain credit reservation. Inspect login/verification failures through the private browser.

Deploy a reviewed pinned commit with `scripts/deploy-flow-controller.sh COMMIT_SHA HTTPS_ORIGIN`; it stages an isolated release, reuses the existing interpreter, runs offline tests as the service user, switches only the Social OS source symlink, and rolls back if health/controller checks fail. The installer for new instances also starts the controller through the normal serve command. Profiles, vault, private environment, media and provider services are retained. The deployment script needs the existing owner's exact-operation administrator authorization.

Offline tests use fake provider receipts and synthetic media; they do not establish fresh live Google rendering or artistic quality. Real acceptance requires a bounded owner-authorized render and playable downloaded output. Report source checks, deployed runtime, host discovery and generation separately.


## Four-account daily credit and low-RAM operating policy

The owner may configure `VSO_FLOW_DAILY_CREDIT_LIMIT=50` (default 50) and
`VSO_FLOW_DAILY_TIMEZONE=Asia/Kolkata` (default Asia/Kolkata). All three
generation entry points (approved production, standalone video and standalone
image) reserve their maximum quoted credits against each account's daily limit.
Unknown/unreconciled jobs remain conservatively reserved. A new local calendar
day resets *this spending cap only*; it **does not** imply Google's provider
balance resets or that 50 free credits have actually been granted. Google Flow
credits and reset/expiry rules must be read from each live account. The agent
must never infer a free-credit component from a large combined balance, or
generate content without approved prompts, assets and an explicit credit cap.

The durable batch controller prefers eligible accounts with low observed
remaining balances (within the daily ceiling), then least-recently used. This
is a best-effort use of the owner's permitted allowance, not an automatic
daily spending instruction, a guarantee that credits are free, or permission
to circumvent provider restrictions. Any provider verification/refusal stops
submission. Unused quota is not a reason to create filler content.

The owned-browser guard checks **idle** native profiles at most two per
controller tick. It retains one Google Flow tab (preferring an existing
project), temporarily retains Google sign-in/2FA tabs, and closes unrelated
pages, Chrome welcome/extension tabs and duplicate Flow tabs. It does not
touch non-Vegas Chrome sessions, provider work in flight, profiles, passwords,
cookies or browser extensions on other computers. New Vegas-launched Chrome
sessions disable unnecessary extensions and background features.

`resources_ok` pauses new Flow submissions under 1 GiB available RAM, high
CPU load or low disk; existing job reconciliation continues. Set
`VSO_FLOW_MAX_ACTIVE=1` on small VPS installations. A single tab per Chrome
profile still consumes substantial memory, so **four simultaneously running
Chrome profiles on a 4-GiB VPS may still overwhelm the host**. Run accounts
sequentially and close idle browsers before starting additional ones. A future
browser lifecycle manager must preserve profiles, reconcile original job IDs,
and retire old attach-only engines before reopening changed CDP ports; killing
Chrome behind a live worker will cause a reconnection refusal.

