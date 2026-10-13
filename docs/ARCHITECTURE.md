# Architecture

One agent-configured installation belongs to one operator. They can manage multiple channel identities. A centrally hosted multi-tenant service is not implemented. The user shares the repository link and authorizes services; the setup agent provisions the deployment and returns dashboard/plugin links. End-user terminal work is not part of the contract.

ChatGPT/Codex supplies creative reasoning and, where available, native image generation. The MCP server supplies deterministic records and actions. Native images are a host capability, not an MCP image provider or API call. Ordinary ChatGPT needs an HTTPS connection to the installation; local Codex can use stdio.

GitHub is source/control history, Supabase is authoritative encrypted state, and a managed cloud app service executes MCP, dashboard, remote browsers and FFmpeg. No local PC or user-managed VPS is required. Render is the initial blueprint candidate, pending live compatibility validation. SQLite is a transaction cache/developer mode. Profiles, key and working media live on a private cloud volume; authorized Google Drive uploads archive media privately. HTTPS exposes authenticated app endpoints and scoped browser streams; VNC/CDP remain private.

## Data flow

`channel → plan(two concepts) → selected concept → imported keyframes → image approval → scene jobs → final video review → exact publication review → publication`

Each plan has a total cap and conservative reservations. In Supabase mode, transactions load the authoritative encrypted state, apply local SQL work, and commit through a service-only revision-checked RPC before the cache transaction succeeds. Concurrent revisions/network failures are not retried or silently replaced by local state. Stable request IDs, one in-flight job per account and one job per scene suppress duplicates. Interrupted provider writes remain unknown until the agent verifies outcome.

Publication records freeze video checksum, destination and copy. They have separate IDs from video jobs. Network writes are claimed before execution and unknown writes never automatically retry. YouTube resumable-upload session URLs are encrypted. Instagram processing and publication are separate operations using the same container.

## Authentication boundaries

- One-use hashed tickets establish setup sessions or initiate provider login.
- Provider tokens are encrypted with a private local Fernet key; the key is stored separately from SQLite but on the same machine. Host compromise can expose both.
- Dashboard uses HttpOnly SameSite cookies. Tool HTTP requires an authenticated operator session or resource-bound OAuth bearer token.
- MCP OAuth uses registration, explicit operator consent, PKCE, audience/resource checks, hashed access tokens and single-use rotating refresh tokens.
- Social OAuth callbacks verify and consume purpose-specific state before exchanging codes. Tokens never appear in tool results.
- Signed media links expire; Instagram may make repeated/range fetches during processing. They are bearer capabilities, not permanent public media.
- Supabase authoritative state is encrypted as a whole using the private persistent runtime key. The table/RPC are server-only, RLS-enabled and revoked from browser roles. The compare-and-swap revision protects against divergent writers. This encrypted whole-state adapter is an initial single-operator implementation, not a high-volume relational job service. Runtime key/media/browser profiles are not stored there.
- Private Flow login tickets are consumed once into a 30-minute browser cookie scoped to one account. That cookie cannot access administrative APIs or another account's browser. User credentials are entered directly into Google's remote window; no password/cookie-export tools exist.
- The legacy `cloud_sync` helper remains an optional secret-free metadata backup. It is not the primary 0.2 state path.

## Current boundaries

No backend can wake ChatGPT's native image tool by itself. Daily briefs need a supported host scheduler/agent run. Automatic image-byte transfer depends on the host; lacking it blocks the zero-manual creative stage rather than asking users to upload files or run import commands.

Flow has no stable public UI-automation contract. The worker's English controls, first-frame uploader, quote parsing and asset correlation require live validation. The Docker/Xvfb/noVNC browser recipe also needs a real build/host/sandbox trial. A written provisioning recipe is not an actual deployment. Advanced operations, distributed workers, full analytics and other platform adapters are not implemented.
