# ChatGPT-first product contract

Accepted owner direction, 14 October 2026. This supersedes dashboard-as-production-studio descriptions. **A design contract is not evidence that every integration already works.**

## Purpose and positioning

**Your social production team inside ChatGPT, executing on your own server.** ChatGPT is the workstation for market research, strategy, two daily ideas, scripts, scene direction, native images, revisions, Flow direction and quality review. The independently owned VPS executes browser/render/edit/upload jobs and preserves state. The dashboard is the private sign-in and review surface.

One owner, one installation, one plugin endpoint. Giving someone this repository gives them the software and instructions, never the maintainer's accounts or server. Google Drive is an optional archive, not a prerequisite or the authoritative job database.

## Responsibilities

| Surface | User does | Agent/runtime does |
| --- | --- | --- |
| ChatGPT | Discuss channel strategy, scripts/scenes, constraints, budget and automation policy | Research, write, generate native scene images, transfer actual bytes, direct Flow, inspect and assemble outputs |
| Connections dashboard | Sign into each VPS Chrome profile, complete challenges and official social consent | Create profiles, open the private screen mirror, inspect project/identity, show connection health |
| Storyboards dashboard | Read ideas/scripts, select an idea, approve keyframes or request changes | Present actual scene images, persist feedback and approvals, preserve revisions |
| Clips dashboard | Watch scene clips and final exports | Download exact results, run technical/creative QA, report failures |
| Release review | Review exact platform/destination/copy/cover/time or an explicitly configured release policy | Prepare and execute only authorized publishing records, reconcile uncertain provider results |
| VPS | No terminal work in the agent-assisted path | Persist state, execute durable jobs, enforce approvals/caps, host private browser and HTTPS |

The dashboard has no required manual image/video generation, model-setting, scripting, research or composer flow. Those capabilities remain available to the plugin. Settings/connection repair are secondary onboarding utilities.

## Plugin boundary

A per-installation package contains `plugin.json`, generated `mcp.json`, `skills/vegas-social-master/SKILL.md`, its references and the bundled `flow-production` craft skill. The generator writes the owner's verified HTTPS `/mcp` URL; the repository carries no shared credential or live owner endpoint. OAuth/PKCE connects the host to that installation. Refreshing a plugin package is separate from deploying server code or consenting to a connection.

| Tool family | Existing interface | Planned addition / limitation |
| --- | --- | --- |
| Setup and health | guide, doctor, onboarding_status, setup_plan, profile_save | Full bootstrap uses AWS Core/SSM before this MCP exists |
| Connections | account_start/list/info/disconnect, flow_account_add/login/inspect, connection_setup | Sequential first-login wizard; persistent convenient owner sign-in still pending |
| Strategy and content | channel_save, strategy_save, research_fetch/save, plan_save, content_queue | Host provides web research/reasoning; no invented background execution |
| Native images and assets | image_tasks, asset_import, image_attach, images_approve | Actual host tool and transferable bytes required; no silent API substitute |
| Google Flow | flow_model_catalog/models_refresh, video_request/poll, flow_video_request/poll | Use live account controls, caps, exact jobs. Edit/extend/upscale/voice/characters are not fully exposed |
| Editing and review | continuity_frame, video_assemble/attach, storyboard_regenerate, review_queue/complete | New feedback creates a new plan; approval never follows a revision automatically |
| Publication | post_prepare/execute/poll/schedule/reconcile, publish_prepare/approve/execute | Real OAuth consent and end-to-end provider acceptance remain unverified |
| Storage | asset_archive_drive, drive_archive_reconcile | Host Drive connector or separate server OAuth; connections do not share tokens |
| Automation | schedule_daily, morning_queue, brief_complete, automation_status/pause | Host notification delivery and real event-driven creative continuation are not yet implemented |
| VPS administration | Existing bootstrap via AWS Core/SSM or authorized VPS connector | Proposed same-plugin admin broker described below; Social OS currently has no arbitrary root shell |

“Full access” means all operations needed to operate this owner's installation. The proposed admin family is `host_inventory`, `service_status`, `logs_read`, `files_read/write`, `job_start/status`, `backup_create`, `deployment_prepare/apply/rollback`. File scope defaults to this project's source/state/media; secret values and browser-cookie exports are never returned. A separate local broker grants explicit privileged actions for this service, with durable job IDs and audit receipts. Changes to other apps, IAM, firewall or destructive filesystem operations require owner authorization. Do not label these proposed tools as installed. AWS Core remains necessary for initial provisioning and recovery when the VPS is stopped.

## Morning and approval lifecycle

A channel policy should record timezone, due time, two proposed videos, brand/reference locks, allowed accounts/models, total daily/per-video credit ceilings, destinations, visibility, publishing mode and pause state. Existing daily briefs produce **two concepts for one plan**, not two finished videos. Two videos require two distinct plan IDs, each with two ideas. Automatic selection before storyboard review requires an explicit agent-selection policy; otherwise the user selects first and keyframes follow. Generating both concept storyboards before selection is a separate unimplemented preview milestone.

1. When the channel becomes due, enqueue a stable dated brief. A verified host subscription/agent trigger consumes it.
2. ChatGPT researches and creates the proposals, scripts and actual native scene images; transfers/imports and verifies their checksums; saves the reviewable storyboard.
3. User reviews the selected storyboard. Approval freezes actual attached images and the production ceiling. It authorizes rendering, not an unrelated public release.
4. The approval event should resume the subscribed ChatGPT workflow. It reloads authoritative state and checks current budget/account/model settings before requesting each scene once.
5. The agent polls original jobs, downloads exact outputs, inspects clips, assembles and reviews the final video, then prepares platform-specific releases.
6. Default release mode is final review. The desired “approve storyboard, then upload automatically” mode requires an explicit persisted policy binding the destination, copy rules, visibility, time window and output QA requirements. **That policy engine is not implemented today.** Until then, exact release approval remains required.
7. Regenerate persists feedback through `storyboard_regenerate`. ChatGPT reads `review_queue`, creates a new plan using a request-derived revision ID, transfers new images and calls `review_complete`. Old jobs/media/approvals remain intact; changed content needs fresh review. It never silently retries a previous paid job.

Current runtime persists the feedback queue and approvals. It does not emit host callbacks or launch ChatGPT when a button is pressed. Show **Waiting for ChatGPT** rather than “generating” until an actual host run has begun.

## Event bridge: required next implementation

Official [MCP Events documentation](https://developers.openai.com/plugins/build/mcp-events), checked 14 October 2026, provides a supported architecture: Work chats on web, Work + Cloud on desktop, or dots can subscribe and receive webhook events. Workspace controls apply. It requires MCP 2.0 `2026-07-28`, `server/discover`, event listing/subscription/unsubscription, persistent subscription state and outbound HTTPS. Our current MCP server supports older tool RPC only; it must be upgraded and host-tested before claiming automatic continuation.

Proposed events: `brief.due`, `storyboard.approved`, `storyboard.revision_requested`, `clip.completed`, `production.failed`, `release.review_required`, `release.completed`. Filters bind installation, channel and optional plan ID. Payloads contain stable IDs, revision/hash and a private dashboard route, never cookies, passwords, media bytes or bearer URLs. The receiving agent reloads the record; an event is a hint, not authorization.

Implement transactional event outbox alongside state changes. Bind each subscription to its authenticated principal and scopes; deterministic identity, canonical filters, expiration and refresh, encrypted signing secret. Verify callbacks with the documented signed short-lived challenge before sending application data. Restrict HTTPS callbacks to host-approved public destinations, block private/link-local/metadata addresses and redirects, defend DNS changes, use bounded timeouts. Sign deliveries per specification, persist attempts/backoff, expire disconnected subscriptions and stop after unsubscribe. Redelivery is permitted for notification delivery only; generation/publication IDs remain idempotent. Track webhook acceptance separately from agent acknowledgment and completed work. Reconnection/restart must retain the outbox and avoid duplicate creative runs or feedback loops.

Acceptance: real supported host subscribes; due brief produces native images with transferable bytes while user is away; dashboard approval resumes the right chat; revision creates a new review; duplicate delivery does not spend/post twice; failure/revocation/restart are visible. No cron entry, mocked webhook or HTTP 2xx substitutes for these tests. A host without events stays in **ChatGPT-connected manual-resume mode**. An optional paid API worker would require separate consent and is not this default product.

## New-owner release gates

Fresh AWS install, personal 4–5-profile sign-in and restart persistence; harmless MCP consent; native image transfer; one capped Flow scene; clip/assembly QA; actual publishing OAuth and authorized release; actual host event subscription/continuation; optional private Drive archive; pause/recovery/backup/restore. Report these separately. Founder accounts already connected do not prove another owner's onboarding.
