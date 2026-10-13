# Research decisions — 2026-10-13

This is original implementation, not a fork, repository bundle or copied collection of skills. No researched project's code is vendored. Research clones were kept outside the public checkout. License labels below describe sources, not permissions to copy blindly.

| Source | Material examined | Decision |
|---|---|---|
| [kodelyx/flow-agent](https://github.com/kodelyx/flow-agent) | README: extension/cookie bridge, API, diagnostics, multi-profile warning | Do not make cookie transfer a requirement or assume multi-account reliability |
| [GTAI-1/flow-mcp](https://github.com/GTAI-1/flow-mcp) | README, package metadata, Chrome/session, settings/quote and generation/download source sections | Separate profiles, real UI quote before spend, asynchronous jobs; write our own CDP worker |
| [miyakejima/google-flow-mcp](https://github.com/miyakejima/google-flow-mcp) | README: account onboarding, live capability discovery, exact-asset matching, alpha status | Adopt explicit readiness and ambiguity checks conceptually; no extension/cookie-copy dependency |
| [adelaidasofia/instagram-mcp](https://github.com/adelaidasofia/instagram-mcp) | README, auth and Graph client source sections | Official APIs, secret isolation and fixed provider hosts; build our own token store/OAuth/publication records |
| [Jakeschincariol/instagram-agent-skill](https://github.com/Jakeschincariol/instagram-agent-skill) | README/skill inventory | Creative instruction is separate from publishing infrastructure; write one original master skill |
| [raphaelbgr/ai-video-prompting](https://github.com/raphaelbgr/ai-video-prompting) | Existing Flow skill's reference/source description | Optional prompting research, not a runtime dependency; official Google guide takes precedence |

Primary technical references:
- MCP stdio/HTTP transports: https://modelcontextprotocol.io/specification/2025-06-18/basic/transports
- MCP authorization: https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization
- OpenAI plugin authentication: https://developers.openai.com/plugins/build/auth
- YouTube server-side OAuth: https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps
- Instagram Login/publishing: https://developers.facebook.com/documentation/instagram-platform/instagram-api-with-instagram-login/business-login (portions behind sign-in; live verification pending)
- Google Flow credits: https://support.google.com/flow/answer/16526234
- Veo prompting: https://deepmind.google/models/veo/prompt-guide/
- Supabase RLS: https://supabase.com/docs/guides/database/postgres/row-level-security
- Supabase changelog: https://supabase.com/changelog.md (reviewed; upcoming legacy TLS-cipher change does not require weakening modern Python TLS)

Google currently documents 50 daily Flow credits and non-subscriber peak-hour restrictions. This is dynamic account policy, not a product guarantee. The worker does not assume available balance from that allowance. Browser-session automation is unofficial; no CAPTCHA, security, safety, regional or quota bypass is included.

Meta's current documentation was partially inaccessible without login. Instagram adapter behavior is an implementation candidate awaiting a live test, not claimed verified compatibility.

## REA assessment — 0.5

[REA](https://github.com/morluto/rea) 6.4.0 (MIT; inspected main commit `7e3a19863835215491b55fba7127a78bad6a7709`) was installed separately on the founder's VPS as a development tool. Static analysis ran as an unprivileged research user against source-only snapshots, without account tokens or browser profiles. No agent configuration, native binary engine or paid provider was installed.

Two actual runs reconstructed the existing local Flow source (82 graph nodes / 99 edges) and a representative public Flow browser-MCP source (93 / 101). These are bounded static inventories: expanded relationships and semantic coverage were incomplete at the chosen resource limits. They do not prove runtime behavior or expose cloud-side source. The public reference had no LICENSE file or package license declaration at inspection; no source was copied or vendored. REA itself is not a production dependency.

The useful design conclusion is to keep browser ownership, durable queues and exact-download correlation separate. Our original adapter uses the owner-authorized local service protocol; it does not extract cookies, replay private authentication traffic, bypass verification, or adopt stealth/evasion features from public projects. Instagram/Facebook/YouTube use official OAuth/API paths. REA cannot replace provider registration, consent, permissions or App Review. Examining every automation repository is an unbounded goal; source claims require selected, reproducible checks and a controlled live trial.
