# Current engineering checkpoint — 0.7.0 candidate

See [dated audit](audits/2026-10-14-engineering.md) and [operations](OPERATIONS-0.7.md). PR #6 carries the engineering repairs; actual ChatGPT Web installation, plugin upload and subscribed host continuation remain acceptance gates. The evidence below is chronological history, not a single statement of the current deployed version.



## 15 October 2026 — owner recovery and ChatGPT consent redirect

- Fixed the authorize/consent CSP to permit the ChatGPT OAuth callback path while keeping other forms self-only. Founder VPS received the initial hotfix; final host token exchange remains unverified until reconnect.
- Added administrator-issued `owner-recovery` / `new-setup-link.sh --reset-password` links that open the new-password form directly, preserving the previous password until save. Recovery cookies grant no dashboard/MCP access; password save revokes browser and recovery sessions and unused recovery tickets.
- Added HTTP recovery and CSP regression tests. Validation: 125 Python tests, 5 Node tests, installer shell syntax and git diff checks passed. Browser execution was unavailable in the local runtime (Chromium missing); these checks do not prove Google login, Flow rendering, publishing or ChatGPT host acceptance.
- Repository synchronization is now an explicit maintainer completion requirement in AGENTS.md.
