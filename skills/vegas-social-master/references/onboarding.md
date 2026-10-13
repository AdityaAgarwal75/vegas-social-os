# Community account setup

Each operator owns one installation and private data directory, plus their own developer-app credentials. The maintainer supplies no shared Google/Meta app, accounts, VPS, tunnel or server. A central multi-tenant hosted service is outside this alpha's trust model.

YouTube: enable YouTube Data API in your own Google project. Configure an OAuth web client and exact `/callback/youtube` redirect URI. Export `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` server-side. Consent-screen test users, app verification, testing-mode refresh expiry and API audit/upload limits are provider requirements. Connect Brand channels separately and verify the intended channel through a real read.

Instagram: configure **Instagram API with Instagram Login**, professional accounts, exact `/callback/instagram`, basic and content-publish permissions. Export `INSTAGRAM_CLIENT_ID`, `INSTAGRAM_CLIENT_SECRET`, and a currently supported `META_GRAPH_VERSION`. The integration is not Basic Display or a password/private API. App review/business verification controls eligibility. Live validation is required: portions of current Meta documentation were behind a login wall during development.

Flow: request/open the account link; the hosted runtime opens an isolated browser through the dashboard. Enter Google credentials/2FA directly there and open one Flow project. Each identity gets its own Chrome profile/display and a scoped short-lived browser session. The included noVNC/CDP runtime must be provisioned/tested by the setup agent. A temporary URL cannot turn Flow browser login into official OAuth access.

MCP: a connected agent deploys an independent VPS using the VPS-first installer and HTTPS, then optionally packages the remote plugin pointed to that instance. When no connected agent exists, the operator may run the VPS bootstrap. The user opens the private link and accepts host/provider consent. The server implements registration, consent, PKCE and refresh; real ChatGPT connection still requires a live trial. Developer CLI commands are not end-user onboarding.

Start a trial with one harmless account read, one explicitly capped generation, then one private YouTube upload. Never mass-test accounts or publish publicly just to check connectivity.
