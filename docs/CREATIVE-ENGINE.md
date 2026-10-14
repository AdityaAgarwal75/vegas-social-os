# Vegas Creative Engine — capabilities, provenance, verified boundaries

This document inventories the actual Vegas Social OS 0.7 source as of October
2026, the native creative additions, and the two external projects reviewed.
The native implementation is independent of those projects; names, datasets,
source files and AGPL code have not been copied to conceal provenance.

## Built-in Vegas Social OS capabilities

| Group | Implemented source capabilities | Evidence or limitation |
|---|---|---|
| Agent workstation | MCP registry, documented host workflow, owner dashboard, private plugin archive | Installation, final ChatGPT OAuth code exchange and host image tools require a real connected client |
| Owner and VPS | Independent deployment, bootstrap, health, diagnostics, private session, isolated broker admin requests, snapshots/rollback | Unsafe administration requires separately approved owner requests |
| Content | Channel and brand profile, voice/pillars, research HTTPS fetching, attributed research, two-concept production plans, weekly brief/calendar review, 14 new native first-party studio operations | Does not start ChatGPT by itself |
| Google Flow | Private browser logins, per-account workspace checks, model introspection, generation requests, polling/reconciliation, account budgets, frame/scene continuity | Paid generation must be approved and independently observed; five available account sessions are not proof that all models work |
| Images and assets | Host-native image task instructions, exact image import from host, checksummed media transfer, attachment, archive to authorized Drive | ChatGPT host must supply actual bytes; server does not manufacture native image outputs |
| Video editing | FFmpeg assembly, frame extraction, media normalization, fades, optional owner-approved licensed music/subtitles, editable artifact review | Advanced external provider toolchains need separate setup |
| Publishing | Prepare/approve/schedule/executed release, provider upload reconciliation, YouTube/Instagram/Facebook connectors and official consent, checks | Provider OAuth config and account permissions are installation-specific; no unapproved auto-post |
| Analytics | Authorized provider read/summaries, content performance history, source provenance | No fake engagement or retention figures |
| Automation | Daily brief queue, scheduled releases, event outbox/subscriptions and waiting/review status | Cannot autonomously wake ChatGPT conversations without a supported host continuation |
| Security | OAuth 2.1/PKCE, DCR, exact redirect URI/resource, origin checks, user-bound tokens, no secret disclosure | ChatGPT must still complete final callback and POST /token |

## Native creative studio tools added

- studio_catalog and studio_external_catalog: first-party stage manifests and separately installed AGPL source inspection
- studio_quality and studio_copycheck: explained text heuristics, hook timing/quality, invisible character cleanup without claiming AI detection
- studio_caption_review: caption opening, CTA and hashtag warnings, preview
- studio_carousel_outline and studio_story_sequence: text-only content structures with per-scene image prompts
- studio_engagement_triage: label user-supplied leads, questions, complaints and community replies without sending anything
- studio_profile_audit: field-completeness rubric (not engagement/reach)
- studio_outliers: relative views versus *provided* account median, without external scraping
- studio_repurpose: split rights-cleared source transcript into rough host-review segments
- studio_brief, studio_draft, studio_select and studio_queue: durable, request-idempotent, source-aware brief -> two distinct concepts -> reviewed selection, with optional source links, zero-credit budget and no publishing
- The existing content_request/content_plan_save/content_plan_approve and reel_review tools continue to handle weekly scheduling and script QA.

Native production formats: short Reel/Short, carousel, Stories, documentary,
cinematic short, animated explainer, avatar spokesperson, talking-head,
podcast highlight, screen demo, translated/dubbed adaptation, consistent
character animation, and stock-footage montage. These are **stage contracts**;
not every provider or costly renderer is installed or verified.

## Instagram research reference: 13 workflows

The publicly accessible Jake Schincariol Instagram agent skill contains the
following skill categories. Vegas uses its own logic and API, not a disguised
unattributed copy:

| Reference capability | Vegas integration |
|---|---|
| Reel scripts, hook families, timed beats | studio_quality, studio_brief/draft, existing reel_review |
| Caption prep and preview | studio_caption_review |
| Carousel structure | studio_carousel_outline |
| Story sequences | studio_story_sequence |
| Engagement comments | studio_engagement_triage, host creative drafting required |
| DM outreach | Host-created, approved drafts only; provider send permission not automatically granted |
| Comment replies | studio_engagement_triage, explicit review before delivery |
| Writing hygiene | studio_copycheck; human voice requires brand-voice examples |
| Week scheduling | strategy_save, content_request, content_plan_save, content_plan_approve |
| Profile optimization | studio_profile_audit (completeness heuristic only) |
| Viral outlier swipe research | studio_outliers; observed metrics must be provided; public fetch has robots checks |
| Repurposing long content | studio_repurpose; host must verify quotes/timestamps and reuse rights |
| Post-mortem performance audit | analytics_capture/summary and reviewed feedback |

Not all thirteen original implementation files, its proprietary-seeming example
data, or precise heuristics have been copied. There is no unlicensed cloning.
Its source code is MIT and any direct reused substantial portions **must**
preserve the original license and author notice. Here the native algorithms
were written for Vegas independently.

## External video reference: thirteen pipeline manifests

An optional, separately installed **OpenMontage** checkout is supported at
/opt/vegas-social-os-integrations/openmontage. It is not distributed as Vegas
code. The source includes its own AGPLv3 license. The Vegas tool
studio_external_catalog reads manifest names only; it does not execute
OpenMontage. Source existence is NOT provider or renderer installation.

- animated-explainer, animation, avatar-spokesperson, character-animation
- cinematic, clip-factory, documentary-montage, framework-smoke, hybrid
- localization-dub, podcast-repurpose, screen-demo, talking-head

Features evaluated from that project: reference-video analysis, research,
stock-motion footage library, soundtrack/voiceover production, scene/asset
previews and approval, Remotion composition, word subtitles, provider scoring,
budget projections, output profiles, editorial gates, quality review and
local production storyboard. Some stages overlap existing Vegas functionality;
the others need independent adapters and explicit provider setup. The native
Vegas stage catalogue above is **not** a claim these external pipelines can
all render today.

OpenMontage's AGPLv3 applies to source copied/combined into a network service.
Renaming source files would not remove license obligations. Its isolated,
source-only checkout and original LICENSE are preserved; distributing a
combined derivative requires appropriate AGPL compliance, including source
availability. Review with a license professional before merging external code.

## Owner-chosen password (optional)

In the already-paired owner browser, open https://YOUR-DOMAIN/password.
Enter and confirm a password there. The server revokes old dashboard sessions,
and you sign in at /login. Changing a previously configured password requires
the current password. This does NOT send password fields to ChatGPT.

Alternatively, for a private local terminal on the installation machine:

    python -m vso owner-password

This reads the password twice with getpass; minimum 14 characters. Stores a
salted scrypt hash, **not** the password, and invalidates old dashboard sessions.
Then browse to https://YOUR-DOMAIN/login, sign in, and return to ChatGPT to
complete OAuth. Owner password unlocks the browser session; it cannot be used
as a replacement for ChatGPT's OAuth 2.1 code/PKCE exchange.

Do not paste a password into chat, save it in git, or pass it by CLI flags.
The existing one-use setup link remains an emergency local recovery pathway.
Rate limits slow guessing; HTTPS, SameSite=Lax, origin validation, HttpOnly
cookies and single-installation trust boundary remain. Protect VPS shell
access and use a password manager.

## Community release verification checklist

Run Python unit and MCP contract tests, JS syntax checks, shell script
validation, license scanning, and local real-browser OAuth tests. For new VPS
installs, verify correct DNS/TLS, source revision and persistent storage;
then finish ChatGPT tool authorization and real content/Flow tests using
owned accounts. Until the full pipeline has been tested with account consent,
real imagery, a completed clip, a reviewed export and approved publishing,
**do not call the installation a fully autonomous content factory**.
