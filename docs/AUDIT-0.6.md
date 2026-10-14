# Production audit and manager — 0.6

The five account image trials from 0.5 remain real evidence. They do not prove paid video rendering or social publishing. This release adds model-aware video controls, guarded existing-service video submission/polling, a content strategy queue, weekly editorial calendars and original Reel timing/readability review.

## Flow choices

Official reference checked 2026-10-13: https://support.google.com/flow/answer/16352836?hl=en . The live account-1 dropdown showed Omni 1.1 Flash and Veo 3.1 Lite/Fast/Quality. Models and settings can differ by account, plan and region. `flow_models_refresh` inspects idle menus, restores mode, records observation time and expires availability after 30 minutes. Documented fallback choices are clearly marked unverified. New unknown live models can be displayed, but must not be generated using invented capabilities.

Choose model, duration, resolution, portrait/landscape and a credit ceiling. Use references OR first/end frames; never silently discard supplied frames. Quality does not accept ingredient references. Every request uses one output, zero retries and a stable ID. A cap of 0 is a free-only preflight; any positive quote must stop before rendering. Model settings or dropdown success do not establish rendering support.

## Original content manager

Save audience, objective, brand voice and content pillars per channel. Request a week using a stable ID. A real connected host agent consumes `content_queue`, reads sources and prior titles, writes angles/hooks/scripts/captions, then calls `content_plan_save`. Review freezes the editorial calendar through `content_plan_approve`; this is separate from publishing approval. The server does not wake ChatGPT or invent an agent result.

The installed Instagram skill repository was studied for planning, hook alternatives, timed beats, brand voice, caption clarity and reviewing actual performance rather than assuming raw views prove success. Its code and formulas are not copied. Our `reel_review` uses labeled speaking-time estimates and readable-card checks. No score promises virality, retention or authenticity detection.

## Audit coverage

74 Python tests cover prior state/auth/OAuth/publishing/scheduling/research/hosting guards plus strategy request idempotency, calendar date/pillar/freeze boundaries, original Reel estimates, model constraints, uncertain clip suppression and quote-stop behavior. Existing Node tests cover original worker quote/output identity guards. Browser QA covers 12 screens, strategy save, host-agent request, Reel review, model-dependent duration/resolution and responsive widths, in addition to the prior full draft/cancel workflow.

`workflow_audit` reports local dependencies, actual saved connection readiness, unresolved jobs and completed assets. It does not call a mocked publishing adapter a live platform test. Live paid rendering, OAuth consent completion/publication, fresh-account AWS deployment, advanced Flow editing/extension/upscaling and unattended host execution remain separate trials. No paid render or public post is authorized by this audit.
