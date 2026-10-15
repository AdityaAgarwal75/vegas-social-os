# Community onboarding audit — 15 October 2026

Scope: all remote branch histories/differences, repository-wide automated checks and focused manual review of installation/rollback, authentication, owner recovery, OAuth, dashboard navigation, packaging, first-use guidance and presentation. This is not an external security certification or proof that every provider operation works for every new owner.

## Branch decisions

| Branch | Finding / decision |
| --- | --- |
| `main` | Canonical release source; previous recovery/consent PR #7 merged after successful CI. |
| `feature/community-control-room-04` | No commits ahead of main; preserved, no merge needed. |
| `feature/control-centre-05` | No commits ahead of main; preserved, no merge needed. |
| `feature/production-audit-06` | No commits ahead of main; preserved, no merge needed. |
| `feature/engineering-audit-web-07` | No commits ahead of main; preserved, no merge needed. |
| `feature/community-vps-first-20261013` | Divergent older history contains earlier installer/docs work superseded in current source. Bulk merge would reintroduce old architecture/version claims. Reviewed differences; retained current implementation. |
| `ci/hosted-browser-smoke-20261013` | Draft PR #1 documents sandboxed Chromium failure on default GitHub Docker restrictions. Not merged; do not disable browser sandbox to make CI green. VPS-first support remains separate from optional container hosting. |
| `fix/owner-recovery-oauth` | PR #7 squash-merged; original branch history retained. |

## Confirmed defects repaired

| Finding | Repair |
| --- | --- |
| Consent POST succeeds but browser can block its cross-origin return | Consent routes permit the narrowly scoped ChatGPT callback in CSP; all other forms remain self-only. Verified actual browser redirect and PKCE exchange with a locally intercepted callback. |
| Forgotten-password recovery needed an awkward setup-link/password-clearing sequence | Administrator-issued ten-minute one-use recovery links open the password form directly. Password remains active until save; recovery cookies cannot access dashboard/API/MCP. |
| Anonymous/expired dashboard shows a locked shell without useful sign-in | Owner routes redirect to permanent `/login`; expired API sessions navigate there. Logout also returns to login. |
| Failed login loses the form and OAuth return context | Inline error, blank password, retained validated return destination and visible recovery link. |
| Login rate limit renders raw JSON | Branded HTML retry/recovery state and Retry-After, preserving password throttling. |
| Mobile menu state uses a CSS class mismatch | Unified body state, route-close behavior, Escape support and real mobile click tests. |
| Password validation errors lack a next action | Client-side confirmation validation plus server-side error pages with explicit retry/recovery links. |
| Package/runtime/UI report conflicting versions | Central Python version used by health, doctor and MCP; manifests/UI aligned for 0.7.1. |
| Installer rollback restores proxy file without reloading running configuration | Validates/reloads restored Caddy configuration during rollback. |
| Docs and packaged instructions claim browser password setup is unavailable | Updated agent setup, user journey, product contract and packaged master instructions; new user guide and help/recovery routes. |
| README/owner screens lack a consistent identity | Original MIT-licensed Vegas SVG mark/banner, matched authentication layout and responsive styling; no added UI dependencies. |
| New documentation images omitted from plugin ZIP | Include only supported docs assets with binary-safe packaging; regression coverage includes guide/banner/logo. |

## Verification

- 127 Python tests and 5 Node tests pass locally; Python compile, JavaScript syntax, shell syntax and diff-whitespace checks pass.
- Existing review-browser acceptance passes: provider setup gate, storyboard approval/revision queue, no unintended generation/publication, seven review routes and 360/768/1440 widths.
- New sandboxed Chrome acceptance passes on isolated SQLite state: incorrect password, recovery guidance/link, password replacement, Show/Hide, sign-in, menu opening/closing, help page layout, consent redirect, PKCE token exchange and logout.
- Callback is intercepted at every redirect hop with CDP. This tests browser policy without depending on a live ChatGPT callback. It is not host installation acceptance.
- Visual inspection of the new login screenshot completed. Original components are framework-free; shadcn login/form semantics and Vercel interface guidelines were consulted as references, not copied into a new React dependency tree.
- Authenticated live `custom mcp vegas` doctor call succeeded from this Work session. It reports configured owner password, SQLite, Chrome/Node/FFmpeg and installed Flow engine. This verifies the host tool connection, not every production feature.
- Earlier booted Ubuntu 24.04/Debian 12 install/reinstall/state-preservation/rollback evidence is documented in the 14 October audit. This task does not label that earlier test as a newly provisioned independent-owner install.

## Remaining acceptance gates

A new independent owner's DNS/TLS, Google sign-in/challenges, provider application approval, actual native image transfer through their host, capped paid rendering, exact public publishing, event-driven unattended continuation and private archive access remain installation-specific tests. No paid generation, public post or new cloud instance was created by this audit. An optional Docker/managed-host recipe is not equivalent to verified sandboxed VPS operation.

Self-hosting support is for one trusted owner per installation. It is not multi-tenant SaaS, email-based account recovery, social platform approval or a promise of fully unattended production.
