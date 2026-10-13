# Cloud-only architecture

No local computer and no user-managed VPS are required for the intended community deployment. All technical setup belongs to the agent through connected cloud-management tools.

## Recommended initial structure

| Component | Responsibility |
|---|---|
| GitHub | Source, pinned versions, CI and agent setup instructions |
| Supabase | Authoritative encrypted installation state and revision-checked updates |
| Managed cloud app service, initially Render | HTTPS dashboard/MCP, isolated remote Chrome login, Flow worker and FFmpeg |
| Private managed-cloud volume | Encryption key, browser profiles and working media/cache |
| Google Drive, when authorized | Private archive of generated images and final videos |
| ChatGPT | Strategy, native images, iteration, approvals and host-supported scheduled agent runs |

The agent connects to the managed host, deploys the Docker recipe, injects secrets and verifies the HTTPS/browser/persistence checks. The user does not provision a VM, administer Ubuntu, type commands or keep a computer awake. Render is an initial deployment candidate; its browser sandbox/desktop compatibility still needs a live trial. The blueprint is not a working deployment.

## Why GitHub and Supabase alone are insufficient

Codex cloud can build/test/change the repository during a task, but that temporary task environment is not the deployed social-management service. GitHub-hosted runners use fresh environments. Supabase Edge Functions have bounded memory/CPU/wall time. Neither provides this project's persistent logged-in graphical Chrome profile.

The extra managed app service is cloud infrastructure, automatically administered through the user's connected deployment tools. Its bill is separate from Google Flow credits. Do not promise completely free operations merely because source/Supabase/Flow have free allowances.

## Drive is storage, not execution

Verify the host's actual Drive write/upload actions and account first. A preconnected ChatGPT Drive reader may not support uploads, and its token is not automatically available to a separately hosted plugin. The agent may archive through a permitted host connector, or use the installation's explicit Drive OAuth flow and `asset_archive_drive`.

The included Drive adapter uses `drive.file`, creates private files tagged with the asset checksum and preserves existing sharing. It does not enable public link sharing. Unknown uploads require `drive_archive_reconcile`, not blind resubmission. This adapter is mocked-tested, not live-verified.

Drive archives supplement the working cloud volume. The plugin still needs actual bytes for Flow/FFmpeg/uploading. A generic Drive sharing link is not a reliable Instagram ingestion URL; the existing expiring HTTPS media endpoint serves approved bytes. Do not replace working media with a Drive link without implementing verified authenticated retrieval.

## Browser scaling

Connect one Google identity per isolated profile and never share sessions across accounts. Account count is not the same as simultaneous generation capacity. Start with one live-tested account and sequential jobs; measure memory, browser runtime limits and credits before scaling. Do not treat daily allowances as current balance or use account rotation to bypass security/quota restrictions.

Browserbase was also researched: its contexts persist login state and its Live View supports user interaction, but Google sign-in/Flow compatibility is not established by those general features. It is a future provider adapter, not included as a verified Flow integration. Keeping it optional avoids an extra dependency before a pilot.

## Remaining platform boundaries

User provider/2FA and plugin installation consent still apply. Native images stay in ChatGPT; automatically transferring them requires real host-byte access. Scheduled briefs need a real supported host scheduler. A cloud backend cannot launch ChatGPT's native image tool by itself.

## Primary sources checked

- GitHub runners: https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- Supabase function limits: https://supabase.com/docs/guides/functions/limits
- Render web services: https://render.com/docs/web-services
- Render disks: https://render.com/docs/disks
- Render blueprint spec: https://render.com/docs/blueprint-spec
- Browserbase persistence: https://docs.browserbase.com/platform/browser/core-features/contexts
- Browserbase Live View: https://docs.browserbase.com/platform/browser/observability/session-live-view
- Drive scope: https://developers.google.com/workspace/drive/api/guides/api-specific-auth
- Drive uploads: https://developers.google.com/workspace/drive/api/guides/manage-uploads
