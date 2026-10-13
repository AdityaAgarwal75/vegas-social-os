# Architecture

One self-hosted installation belongs to one operator. They can manage multiple channel identities. A centrally hosted multi-tenant service is not implemented.

ChatGPT/Codex supplies creative reasoning and, where available, native image generation. The MCP server supplies deterministic records and actions. Native images are a host capability, not an MCP image provider or API call. Ordinary ChatGPT needs an HTTPS connection to the installation; local Codex can use stdio.

The backend and Node/CDP browser worker currently share one machine/private data directory. Browser profiles, credentials, SQLite and media are outside the checkout. The Python HTTP listener is loopback by default; a user's reverse proxy/tunnel may expose authenticated MCP/OAuth endpoints. Chrome debugging stays on loopback.

## Data flow

`channel → plan(two concepts) → selected concept → imported keyframes → image approval → scene jobs → final video review → exact publication review → publication`

Each plan has a total cap and conservative reservations. Each job reserves before submission in a SQLite transaction. Stable request IDs return existing jobs; one in-flight job per account and one job per scene suppress duplicates. Browser/provider interruptions become unknown and retain reservations. Recovery is intentionally manual until provider outcome is verified.

Publication records freeze video checksum, destination and copy. They have separate IDs from video jobs. Network writes are claimed before execution and unknown writes never automatically retry. YouTube resumable-upload session URLs are encrypted. Instagram processing and publication are separate operations using the same container.

## Authentication boundaries

- One-use hashed tickets establish setup sessions or initiate provider login.
- Provider tokens are encrypted with a private local Fernet key; the key is stored separately from SQLite but on the same machine. Host compromise can expose both.
- Dashboard uses HttpOnly SameSite cookies. Tool HTTP requires an authenticated operator session or resource-bound OAuth bearer token.
- MCP OAuth uses registration, explicit operator consent, PKCE, audience/resource checks, hashed access tokens and single-use rotating refresh tokens.
- Social OAuth callbacks verify and consume purpose-specific state before exchanging codes. Tokens never appear in tool results.
- Signed media links expire; Instagram may make repeated/range fetches during processing. They are bearer capabilities, not permanent public media.
- Supabase sync verifies a user JWT against Auth and relies on owner RLS. It excludes secrets, browser state, media bytes and worker URLs. It is a metadata backup, not the job backend.

## Current boundaries

No server here can wake ChatGPT's native image tool by itself. The daily queue needs a supported host scheduler/agent run. Automatic image-byte transfer depends on the host; manual import remains a valid explicit pause.

Flow has no stable public UI-automation contract. The worker's English semantic-control discovery, first-frame uploader, quote parsing and exact-new-asset correlation require live validation. It stops on ambiguity. Advanced video operations, distributed workers, full analytics and other platform adapters are not implemented.
