# Production audit and manager — 0.6

The five account image trials from 0.5 remain real evidence. They do not prove paid video rendering or social publishing. This release adds model-aware video controls, guarded existing-service video submission/polling, a content strategy queue, weekly editorial calendars and original Reel timing/readability review.

## Flow choices

Official reference checked 2026-10-14: https://support.google.com/flow/answer/16352836?hl=en . All five founder account dropdowns showed Omni 1.1 Flash and Veo 3.1 Lite/Fast/Quality. Models and settings can differ by account, plan and region. `flow_models_refresh` inspects idle menus, restores mode, reads actual per-model duration/resolution controls, records observation time and expires availability after 30 minutes. Fresh live controls override documented rollout choices; requests outside those observed controls are rejected before submission. Documented fallback choices are clearly marked unverified. New unknown live models can be displayed, but must not be generated using invented capabilities.

Choose model, duration, resolution, portrait/landscape and a credit ceiling. Use references OR first/end frames; never silently discard supplied frames. Quality does not accept ingredient references. Every request uses one output, zero retries and a stable ID. A cap of 0 is a free-only preflight; any positive quote must stop before rendering. Model settings or dropdown success do not establish rendering support.

## Original content manager

Save audience, objective, brand voice and content pillars per channel. Request a week using a stable ID. A real connected host agent consumes `content_queue`, reads sources and prior titles, writes angles/hooks/scripts/captions, then calls `content_plan_save`. Review freezes the editorial calendar through `content_plan_approve`; this is separate from publishing approval. The server does not wake ChatGPT or invent an agent result.

The installed Instagram skill repository was studied for planning, hook alternatives, timed beats, brand voice, caption clarity and reviewing actual performance rather than assuming raw views prove success. Its code and formulas are not copied. Our `reel_review` uses labeled speaking-time estimates and readable-card checks. No score promises virality, retention or authenticity detection.

## Audit coverage

79 Python tests cover prior state/auth/OAuth/publishing/scheduling/research/hosting guards plus strategy request idempotency, calendar date/pillar/freeze boundaries, original Reel estimates, model constraints, uncertain clip suppression and quote-stop behavior. Four Node tests cover original worker quote/output identity guards. Browser QA covers 12 screens, strategy save, host-agent request, Reel review, model-dependent duration/resolution and responsive widths, in addition to the prior full draft/cancel workflow.

`workflow_audit` reports local dependencies, actual saved connection readiness, unresolved jobs and completed assets. It does not call a mocked publishing adapter a live platform test. Live paid rendering, OAuth consent completion/publication, fresh-account AWS deployment, advanced Flow editing/extension/upscaling and unattended host execution remain separate trials. No paid render or public post is authorized by this audit.

## Live findings, 14 October 2026

All five founder workspaces reported signed-in project readiness. Their menus exposed all four video families and all three image models. This verifies menus, not every model's paid output. An Omni 10s / 360p preflight quoted seven credits and stopped with cap zero; the balance was unchanged.

The first Veo preflights exposed actual integration faults: Veo has no Omni resolution selector, model switching closes the settings popover, and text-only requests were routed through Ingredients mode. The public adapter omits the Omni-only resolution field for fixed-720p Veo. The founder's existing service was backed up and its original source was patched privately to focus the page, reopen settings after model selection use Frames for text-only input, verify the selected model and recognize an already selected fixed duration. These private compatibility fixes are not vendored into this repository. Preserve upstream license and do not claim an unpatched optional service is equivalent.

The original independent worker now applies and checks explicit model/duration/aspect/resolution settings for approved first-frame production scenes. Native frame attachment, paid rendering and output correlation remain experimental.

A separate forward workflow saved a seven-day fictional furniture calendar, verified stable replay and date/freeze boundaries, and read it through MCP with no jobs or publications. Browser QA used disposable accounts/data and blocked provider network access. Its calendar requests do not represent a running unattended agent. See FEATURE-AUDIT-0.6.md for feature boundaries.

The founder's Veo menus exposed fixed eight-second controls during this audit even though current documentation lists 4/6/8 seconds. Menu observation must override documentation for that account; shorter requests failed before any credit charge. Do not silently change a requested duration to eight seconds.
