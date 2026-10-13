# Community account setup

Each operator owns one installation and private data directory, plus their own developer-app credentials. The maintainer supplies no shared Google/Meta app, accounts, VPS, tunnel or server. A central multi-tenant hosted service is outside this alpha's trust model.

YouTube: enable YouTube Data API in your own Google project. Configure an OAuth web client and exact `/callback/youtube` redirect URI. Export `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` server-side. Consent-screen test users, app verification, testing-mode refresh expiry and API audit/upload limits are provider requirements. Connect Brand channels separately and verify the intended channel through a real read.

Instagram: configure **Instagram API with Instagram Login**, professional accounts, exact `/callback/instagram`, basic and content-publish permissions. Export `INSTAGRAM_CLIENT_ID`, `INSTAGRAM_CLIENT_SECRET`, and a currently supported `META_GRAPH_VERSION`. The integration is not Basic Display or a password/private API. App review/business verification controls eligibility. Live validation is required: portions of current Meta documentation were behind a login wall during development.

Flow: request/open the setup link, have the agent call `flow_login`, then sign in manually on the worker and open one project. Each identity gets an isolated Chrome profile. A remote worker requires secure graphical desktop access; this repository does not include VNC/remote-login streaming. A temporary URL cannot turn Flow browser login into official OAuth access.

MCP: run `python -m vso setup`, open the private one-use link in a browser, then connect `/mcp` using a host with custom MCP support. Remote ordinary ChatGPT needs a reachable HTTPS origin and running backend. The server implements client registration, consent, PKCE and refresh; real ChatGPT connection has not been live-tested.

Start a trial with one harmless account read, one explicitly capped generation, then one private YouTube upload. Never mass-test accounts or publish publicly just to check connectivity.
