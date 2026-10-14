# Connect with consent, configure once

The dashboard separates two jobs. Account owners click a provider button, sign in on the provider's own page, Allow the requested permissions, then return automatically to Connections. Operators or their setup agents register the application once and configure it privately. Account owners do not paste provider secrets into the connection screen.

## Independent installations

A public repository cannot ship a reusable Google/Meta client secret or invent an approved application for each hostname. Fully independent hosts register their own applications. The setup agent can install the runtime, create the HTTPS hostname, generate callback/privacy/deletion URLs, and fill saved application settings. Provider account selection, consent, 2FA and any developer-app review remain provider-controlled steps.

A shared, reviewed OAuth service could offer Allow-only onboarding across installations, but it would be a separate operated service with its own registration, callback relay, destination binding, token isolation and privacy obligations. This release does not include or promise that service. Hiding a settings form does not eliminate registration requirements. See PLATFORM-PERMISSIONS.md for exact scopes and eligible account types.

## Reuse an operator-owned registered callback

An operator who already owns an approved app and callback host can route Social OS callbacks through that host without changing another application's normal OAuth flows. Set an **operator environment value** such as:

```
VSO_YOUTUBE_REDIRECT_URI=https://owner.example/api/social/callback/youtube
```

This must be the exact HTTPS URI already registered in the same provider app. The runtime uses it both at consent and token exchange, and prefixes its opaque, one-use state with `vso_youtube_`. Route **only** that exact callback path with that state prefix to `/callback/youtube` on Social OS; preserve the query. Other states must continue to their existing application. Test missing/foreign/incorrect states and normal application routes before enabling the integration. Instagram uses `VSO_INSTAGRAM_REDIRECT_URI`; Facebook uses `VSO_FACEBOOK_REDIRECT_URI`. These overrides are intentionally absent from end-user forms. They are not approval bypasses and do not confer additional permissions.

Google Flow has a separate browser login: Google Flow Studio → Add Google account → Open Google login → sign in/2FA in Google's screen → open a project → Verify access. YouTube OAuth does not sign a browser into Flow. The agent can use the resulting browser session on this VPS; passwords and session cookies are not exported to the repository.

## Existing local Flow services

Existing accounts can be connected without copying profiles or launching a competing browser. This optional adapter requires an administrator-configured local service implementing `/api/status`, `/api/generate`, `/api/wait` and authenticated `/media`. It is **not** a replacement for a new installation's independent browser worker or a bundled third-party implementation.

Set `VSO_FLOW_SERVICES` to an absolute root-owned JSON file, readable by the Social OS service user and not writable by group/others:

```json
{
  "owner-account": {
    "label": "My Google account",
    "port": 8831,
    "token_file": "/private/local-service/token",
    "desktop_ws_port": 6080
  }
}
```

Grant the service user only traversal of the required token parents and read access to the control token. Do not grant access to Chrome cookie/profile files. Ports must bind to loopback. The dashboard proxies desktop WebSockets only through expiring authenticated account-scoped sessions. A shared desktop remains shared even if several account buttons focus different browsers; do not claim desktop isolation for such a setup.

`flow_services_sync` imports stable account references and verifies readiness. `flow_image_request` requests exactly one image with an explicit model, aspect ratio and credit ceiling; 0 means free-only. A stable request ID prevents duplicate submission. `flow_image_poll` retrieves the original job and exact downloaded file into the private media library. Unknown submissions stop for reconciliation; no blind regeneration. 0.6 adds model-explicit clip requests/polling. Paid rendering remains separately unverified; choose a credit ceiling and review settings before submission.
