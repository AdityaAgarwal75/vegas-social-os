# Vegas Social OS — proposed product plan

14 October 2026. Product definition and acceptance plan; not a claim that the complete product is already implemented. The operator accepted this direction; the Flow execution milestone is in progress. This document remains a product contract rather than a completed-feature claim.

## Purpose

An independently self-hosted AI content studio that turns a channel brief into original, consistent social content using a connected ChatGPT agent and the operator's Google Flow account, then prepares reviewed publication to their own social channels.

Positioning: **Your own AI content studio, running on your server.** Initial users: solo creators and small agencies already using ChatGPT/Flow, including operators deploying an independent installation for a brother or client. One owner per installation. The maintainer does not supply accounts, media, cookies or a shared private server.

The user's recurring job is: open a channel, choose one of two useful ideas, review the creative output, and release it to selected destinations. Technical settings remain accessible in a proper studio; credentials belong to operator setup.

## Product contract

| Layer | Required behavior | Acceptance evidence |
| --- | --- | --- |
| Account onboarding | Own VPS/HTTPS, private Google login, multiple isolated profiles, official social consent, visible eligibility | Fresh installation, persistence after restart, real account/project checks, OAuth completion |
| Flow Studio | Actual available models/settings, text/image/frame/ingredient modes, original media download, supported edit/extend/upscale controls | A per-account capability matrix plus a successful controlled operation for every exposed control |
| Channel strategy | Audience, voice, pillars, product/reference locks, source-attributed research, two distinct ideas | A real channel brief produces useful reviewable drafts and records sources/assumptions |
| Production | Scripts, separate scene images, reliable frame handoff, one controlled clip job, exact output validation, assembly | A real complete Reel with reviewed image/video/audio/joins and no manual file shuffling |
| Publishing | Platform-specific copy, thumbnail/cover, destination, schedule and exact approval | Authorized controlled YouTube/Instagram/Facebook releases, including provider processing/recovery |
| Feedback | Actual post metrics and an evidence-based next-content decision | Metrics attach to the original creative and inform the next brief |

Desired workflow: brief → research → two ideas → selection → script/scene images → Flow clips → edit/QA → review → approved publish → measured feedback. Every state is durable and visible; a connected badge is not output evidence.

## Architecture recommendation

Keep one web app, private SQLite/media store, API/MCP boundary and one browser execution engine behind a complete Flow adapter. Use one account/session manager and one serialized job queue. Consolidate the current independent experimental worker and imported-service path after selecting a single engine against the same acceptance tests; do not keep drifting settings implementations indefinitely.

First evaluate the existing installed Flow engine because it already owns the five working profiles and has generated real media. Integrate a licensed existing engine completely if it passes the capability matrix. Replace it only if required operations fail. Premade skills supply planning/execution playbooks; they are not interchangeable with a tested engine. Preserve licenses, pinned revisions, tool compatibility, explicit caps and exact output identity. An open-source installer must install the chosen engine and its dependencies for a new operator, not depend on founder-only setup.

The dashboard owns profiles, account/model/mode selection, drafts, assets, jobs, approvals, schedules and diagnostics. The agent owns reasoning/research/writing and invokes the same API/MCP as the dashboard. The renderer owns Flow browser operations. Official provider adapters own publication. One layer must not silently impersonate another.

## Honest automation boundary

Keep the zero-additional-SaaS approach. Native creative work runs through the connected host agent. A VPS brief schedule is not a running ChatGPT agent; unattended creation needs an actually supported trigger/host path that is verified. Do not add a paid API fallback silently or promise 24/7 native generation without proving it.

Social account connection can be an official sign-in/Allow flow after developer-app registration. Registration, exact redirects, eligible professional/Page accounts, platform approval and personal consent still exist. A paid application's shared registration does not transfer automatically to every independent VPS. A centrally hosted OAuth broker would be a separate product/operating commitment; it is not the default architecture.

## Implementation order

1. Keep feature expansion focused. Write the current failure list and record which controls are implemented, live verified, unsupported or broken.
2. Complete Flow Studio first. Build a real capability inventory from each account's current UI. Test exact model/mode/settings, uploads, generation, download and restart/recovery. Include advanced controls only when they are wired and verified. Use no-spend probes first; paid acceptance trials need an explicit cap/account/model.
3. Prove one vertical content workflow: one real channel, two ideas, separate images, complete short Reel, review and one authorized destination. Success means usable final content, not passing unit tests or seeing a menu.
4. Make the same workflow installable on a fresh independently owned VPS with its own accounts and callbacks. Keep secrets/state/profiles out of source and setup links private.
5. Extend to verified social destinations, calendar scheduling, actual feedback metrics and then unattended creative triggers. DMs/comments, shared SaaS, teams/billing and extra platforms wait until the production path works.

## Release gates

- A fresh operator can install and sign into their own accounts.
- Every visible control maps to a real implemented operation; unsupported account features are explained and disabled.
- A supported complete Reel can be generated, downloaded, assembled and reviewed with no manual media handoff.
- Account/model/mode/duration/reference choices are not silently changed.
- Credit caps are enforced before submission; unknown jobs are never blindly repeated.
- Approved publishing completes to the chosen destination, with correct media/copy/cover/timing and original-job recovery.
- Secrets stay private; restart retains state; other VPS apps remain operational.
- Tests and documentation distinguish menus, quote guards, rendering, creative quality and publication.

## Current checkpoint

Live server remains 0.5.0. The 0.6 candidate is on PR 5; it is not merged/deployed. The candidate passed 79 Python / 4 Node tests and disposable browser QA across 12 routes. New continuity/skill additions pass 81 Python / 4 Node tests locally and still need final staged/live validation.

All five existing account menus were observed. Omni exposed 4/6/8/10s and 360p/720p; Veo controls exposed fixed 8s/720p during this audit. Model quote guards stopped Omni/Lite/Fast/Quality at zero cap (7/10/20/100 quoted credits for those exact diagnostic settings); account 1 stayed at 951 credits. No paid render or public post was created by this audit. A historical 8s 1280×720 H.264/AAC clip was recovered/imported and decoded; that proves download/import, not a new production run.

Pinned Flow skill source packs have been reviewed and copied with licenses. The adapted active skill routes them through Vegas controls. Its last-retained-frame helper passed a synthetic two-color test and preserved the source. No claim that the full new product works follows from these partial checks.

## Accepted direction checkpoint

The next execution checkpoint packages one complete pinned engine for new profiles, disables legacy independent submission, and adds actual-engine settings and disposable native-session/restart tests. See FLOW-EXECUTION-CONTRACT.md. This does not satisfy the complete Reel/publishing release gates by itself.
