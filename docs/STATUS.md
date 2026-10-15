# Current engineering checkpoint — 0.8.0 control panel candidate

See the [community-readiness audit](audits/2026-10-15-community-readiness.md), [user guide](USER-GUIDE.md), [earlier engineering audit](audits/2026-10-14-engineering.md) and [operations](OPERATIONS-0.7.md).

## Current verification

- Rebuilt light/dark system control panel, named video projects, real specialist tool activity, last observed Flow balances, deduplicated publishing identities, resource history and planned/scheduled release calendar. ChatGPT remains the creative workstation.
- 139 Python and 5 Node tests pass, plus syntax/diff checks. Real sandboxed Chrome passes fourteen routes at 360/768/1440/1920 in both themes, including project creation/scene assignment/search and storyboard review. Login/recovery/consent/PKCE/mobile/logout browser acceptance also passes on disposable state.
- [Control-panel audit](audits/2026-10-15-control-panel.md) records data contracts, migration behavior and actual validation. Historical media without a reliable project relationship stays Unassigned; no files are moved or deleted. Host-led work needs explicit activity reports; these roles are not pretend autonomous processes.
- 0.8.0 is deployed from `2f0c9f8a4e44d0cacc5c94b8d4d52f3952cc985a` after green CI. Live authenticated browser checks and the installed plugin doctor pass. Password/vault, accounts and original media checksums are preserved; imported Flow services were not restarted. The control-panel audit contains the deployment receipt.
- Paid Flow rendering, fresh AWS onboarding, public publishing and event-driven ChatGPT continuation remain separate acceptance gates. The redesign does not change those claims.

## Historical checkpoint — 15 October recovery repair

Administrator-issued one-use recovery links preserve the previous password until save and grant only reset access. Saving revokes owner browser/recovery sessions and unused recovery tickets. The initial repair passed 125 Python and 5 Node tests; later browser evidence above supersedes its earlier local-browser limitation.
