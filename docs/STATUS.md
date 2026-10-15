# Current engineering checkpoint — 0.7.1 onboarding candidate

See the [community-readiness audit](audits/2026-10-15-community-readiness.md), [user guide](USER-GUIDE.md), [earlier engineering audit](audits/2026-10-14-engineering.md) and [operations](OPERATIONS-0.7.md).

## Current verification

- 127 Python and 5 Node tests passed, plus Python/JS/shell syntax and diff checks. Existing review browser suite and new owner-onboarding browser suite passed on isolated VPS state at 360/768/1440 widths.
- New branded login, browser password setup/recovery, visible help, useful failure/lockout states, mobile menu repair and consistent release versions.
- Previous PR #7 is merged. Live authenticated `custom mcp vegas` doctor succeeded in this Work session; the connection is operational.
- Actual browser consent redirect/PKCE exchange passes with a fully intercepted synthetic callback. Real host-native image handoff, generation, public publishing and unattended event continuation remain separate acceptance gates.
- Version 0.7.1 deployed from `e6623c52b9f7e38665b477bfb81a1d1fbdd257bc` after green CI. Live HTTPS/private-API and authenticated MCP checks pass. Password, vault key, accounts and profile preserved; all five Flow services active. See the 15 October audit for the complete deployment receipt.

## Historical checkpoint — 15 October recovery repair

Administrator-issued one-use recovery links preserve the previous password until save and grant only reset access. Saving revokes owner browser/recovery sessions and unused recovery tickets. The initial repair passed 125 Python and 5 Node tests; later browser evidence above supersedes its earlier local-browser limitation.
