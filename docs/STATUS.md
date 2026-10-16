# Current engineering checkpoint — 0.10.0 Vegas Studio

- Rebranded the product as Vegas Studio with an original SVG logo. Existing installation paths, OAuth identifiers, stored accounts and assets remain compatible.
- Applied Horizon UI's official MIT-licensed free dashboard design language across the control room, templates, login/recovery, owner approvals and private browser. Self-hosted DM Sans uses the OFL. Pinned source, hashes and licenses are in `third_party/horizon-ui` and `web/fonts`.
- This is a native HTML/CSS adaptation of the official Horizon source and preview, not a claim of pixel-perfect extraction of the inaccessible Figma Community frames. Dashboard numbers come from saved installation data; demo financial analytics are not included.
- Local verification: 145 Python tests, 5 Node tests, Python/JavaScript/shell syntax and diff checks pass. GitHub Actions run 38863073222 passes Python 3.11/3.12, CloudFormation lint and real Chromium acceptance: fourteen dashboard routes, template search/selection/references, login/recovery/OAuth and responsive light/dark at 360/768/1440/1920. Desktop, mobile, dark, template and login screenshots were reviewed. The private plugin is saved at 0.10.0 with its MCP connection and owner metadata preserved; deployment receipt remains pending private approval. No paid generation or publishing performed.
- Deployed the combined 0.9/0.10 release on 16 October 2026 after private owner approval. Pinned source `950eaf9eca57c7c2253cc5a418274b215080e615` (merged in PR #13, main merge `86c3be7861897a7ba394f28b8a46a8fced87727e`). Broker job `83e79c9906daf25019eff32fcec6b300` completed with exit 0. Local/HTTPS health reports 0.10.0; unauthenticated API remains 401; template preview, Horizon CSS, self-hosted font and Vegas Studio login branding pass. Plugin doctor independently confirms 0.10.0. Only the gateway was restarted. Existing state and provider browser services were retained. Paid generation/publishing and authenticated live visual inspection were not performed in this deployment.

# Previous checkpoint — 0.9.0 cinematic templates

- Shared template catalog/compilation/project selection, visual dashboard library, pinned MIT Higgsfield skill references and optional read-only CLI discovery are implemented. Six tools expose the same direction to ChatGPT. Native keyframes and Flow remain the default execution path.
- 145 Python tests and 5 Node tests pass, with Python/JavaScript/shell syntax, template-source hash and packaging checks. GitHub Actions run 38860309742 passes Python 3.11/3.12, CloudFormation lint and real Chromium acceptance: template cards/previews, search/filter, prompt preview, persistent project selections, references and responsive light/dark at 360/768/1440/1920, plus existing control-room/login/recovery/OAuth checks. No provider generation or publishing was performed. No paid Higgsfield rendering adapter is claimed; provider login/live catalog, rendering and media recovery remain acceptance gates.
- Live deployment is pending exact owner-admin approval through the newer broker. The previous VPS-control connector returns internal errors. Existing 0.8 remains live until the reviewed update is approved and health-checked.

# Previous checkpoint — 0.8.0 control panel candidate

See the [community-readiness audit](audits/2026-10-15-community-readiness.md), [user guide](USER-GUIDE.md), [earlier engineering audit](audits/2026-10-14-engineering.md) and [operations](OPERATIONS-0.7.md).

## Current verification

- Rebuilt light/dark system control panel, named video projects, real specialist tool activity, last observed Flow balances, deduplicated publishing identities, resource history and planned/scheduled release calendar. ChatGPT remains the creative workstation.
- 139 Python and 5 Node tests pass, plus syntax/diff checks. Real sandboxed Chrome passes fourteen routes at 360/768/1440/1920 in both themes, including project creation/scene assignment/search and storyboard review. Login/recovery/consent/PKCE/mobile/logout browser acceptance also passes on disposable state.
- [Control-panel audit](audits/2026-10-15-control-panel.md) records data contracts, migration behavior and actual validation. Historical media without a reliable project relationship stays Unassigned; no files are moved or deleted. Host-led work needs explicit activity reports; these roles are not pretend autonomous processes.
- 0.8.0 is deployed from `2f0c9f8a4e44d0cacc5c94b8d4d52f3952cc985a` after green CI. Live authenticated browser checks and the installed plugin doctor pass. Password/vault, accounts and original media checksums are preserved; imported Flow services were not restarted. The control-panel audit contains the deployment receipt.
- Paid Flow rendering, fresh AWS onboarding, public publishing and event-driven ChatGPT continuation remain separate acceptance gates. The redesign does not change those claims.

## Historical checkpoint — 15 October recovery repair

Administrator-issued one-use recovery links preserve the previous password until save and grant only reset access. Saving revokes owner browser/recovery sessions and unused recovery tickets. The initial repair passed 125 Python and 5 Node tests; later browser evidence above supersedes its earlier local-browser limitation.
