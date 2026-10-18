# Video Intelligence — isolated MVP (18 October 2026)

This is the research input layer for **Vegas Social OS**, not an autonomous
viral-video factory. It queues limited public video analysis and YouTube
discovery without posting, spending Google Flow credits or accessing browser
cookies. It is **not enabled by default** on existing installations.

## MCP tools

- `intelligence_discover(query, request_id, limit=10)`: public YouTube
  search through installed yt-dlp. Returns video *candidates* only; the
  provider may deny headless search. Filters out videos longer than 180s.
- `intelligence_analyze(url, request_id)`: submit exactly one public
  YouTube/Instagram Reel URL of known duration <=180s. Metadata, private
  downloaded media (<=100 MiB), one 4x4 contact sheet sampled every
  3 seconds and estimated FFmpeg scene-cut timestamps are produced locally.
- `intelligence_status(job_id)`: poll an existing job. On success,
  `contact_sheet_asset_id` can be given to `media_preview` for a private
  preview. The agent must **actually view the sheet** and, if necessary,
  the authorized reference video before asserting anything about shots,
  story, characters, music, narration or camera movements.
- Existing `studio_outliers(observations)` ranks posts only if supplied
  actual views and creator-specific median view baselines are available.
- Existing `instagram_media_list(account_id)` and
  `instagram_media_insights(account_id, media_id)` are the official
  owner-scoped Instagram read path on compatible connected installations.

Each request requires a stable ID; duplicate IDs do not create duplicate
downloads. Only one new research task can run at a time. If a worker dies,
the stored record becomes `interrupted`, never silently replays.

## Install and sandboxing

Requires Python >=3.11, yt-dlp, FFmpeg and ffprobe. Set the absolute path
`VSO_INTELLIGENCE_YTDLP` in the **Vegas service environment** to a
dedicated, pinned yt-dlp binary, or install a provider-approved yt-dlp
executable in PATH. Do not use a generic curl|bash installer.
Run the tool only as the unprivileged Vegas service account, not root.
Use private state storage with bounded disk and a network egress policy.

The module **does not** access Chrome/Flow profiles, login cookies or any
existing session. Instagram download may fail because the provider
requires login; the module will return a failure rather than circumvent
access controls. The user must have permission to analyze any input media.
Keep reference footage private, impose retention limits and never
republish source footage without rights.

`python3 -m unittest tests.test_intelligence -v`

## Discovery limitations

Public YouTube results are relevance-ranked suggestions and can be biased,
stale or incomplete. Reported views and upload dates are hints, not a
certified viral leaderboard. Views per day are labeled estimates based
on snapshot-age assumptions. A true relative outlier score requires
multiple observed videos per creator; weak engagement is not proof of ads.
Discovery is not guaranteed on VPS IPs because provider blocks and network
restrictions change. No discovery of arbitrary Instagram viral Reels is
implemented.

No model in this module can see frames or generate an actual concept by
itself. ChatGPT or another authorized visual host should analyze the
contact sheet, extract **abstract techniques** (hook, stakes, pacing,
reveal, emotional payoff) and author materially original scripts,
character designs and shots. Every claim about a reference needs evidence.

## Operator workflow for Untamed Plot

1. Read the current approved channel niche, uploaded content and own
   Instagram metrics (when official insights are available).
2. Discover 10–20 relevant public YouTube Shorts and screen for duration,
   niche, dates, observed views, competing creator baselines and rights.
3. Analyze the top 2–3 accepted reference links. Save source URLs,
   asset IDs, observed data and unknowns, with video-specific provenance.
4. In the host, prepare two contrasting *original* 25–35-second story
   concepts, each with a first-two-second hook, 2–3 meaningful reversals,
   clear resolution, and matching short clip prompts for the Flow provider.
5. Present concepts and actual images for owner review, not simply
   automatically spend all free credits. Assemble and verify the final
   clip, then request exact publishing approval.
6. Post only to the explicitly connected channel, measure 24h/72h
   performance with the official provider API and compare against its
   historic median. Evaluate retention and shares only when actually
   returned by the provider. Maintain a log of hypotheses and results.

## Actual initial test evidence (18 October 2026)

- Five local unit tests passed, including extraction of a synthetic
  FFmpeg clip into an actual JPEG contact sheet.
- Anonymous VPS YouTube search returned candidate IDs, reported views and
  durations. Long films appeared in initial results, so the extractor
  now filters durations over 180 seconds.
- A live YouTube Shorts metadata request returned **“Sign in to confirm
  you're not a bot.”** End-to-end public link downloading and visual
  review are **not verified**. No browser cookies were imported.
- Instagram link downloading, official Instagram Insights from a live
  service instance, and posting automation have not been tested by this
  module. The module has not been deployed into production.

## Release gates

MVP: video link validation, short-form provider metadata, local contact
sheet, scene-cut estimates, asynchronous jobs, and transparent discovery.

Next: approved video transcript adapter, verified per-creator baselines,
rights-aware source cache cleanup, quotas, worker recovery, JSON storyboard
schema, host asset-preview acceptance and private dashboard. In a later
verified stage, explore official YouTube API and Meta insights for daily
performance collection. **No approval bypass, login bypass, bot
evasion, copyrighted footage reuse or guaranteed virality.**
