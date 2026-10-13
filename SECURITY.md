# Security

This alpha is for independently agent-provisioned, single-operator installations. Do not expose it as a shared hosted service without a separate tenancy/security review.

Keep data outside GitHub, protect its managed-cloud volume permissions and back it up securely. Browser profiles are sensitive even without exported cookie files. Encryption protects database copies alone; anyone with access to both the runtime vault key and ciphertext can decrypt state. Volume permissions and secret injection are setup-agent responsibilities. Local developer tests require equivalent OS protection.

Do not expose Chrome/CDP or VNC ports. The container's app port is private/loopback behind HTTPS. Account-scoped browser sessions mediate the noVNC WebSocket stream. The local VNC layer has no separate password because it is loopback-only inside a single-operator private runtime; do not deploy it in a shared/untrusted OS environment. Keep setup/account links private: they are expiring bearer capabilities. OAuth developer app secrets belong in the backend secret store. Revoke provider grants externally when disconnecting.

Supabase mode stores the whole installation state encrypted and commits through a service-only revision RPC. Never expose its server key to the dashboard or use permissive public table/function grants. Losing the runtime encryption key makes the cloud ciphertext unrecoverable; the setup agent must provision persistent storage and secure backups. Cloud outages block state operations. This whole-state design is an initial small-installation adapter, not a high-volume database architecture.

Provider requests use fixed HTTPS allowlists and do not follow redirects. Provider response bodies/tokens are not echoed on errors. Logs omit request query strings. Media links expire but allow repeated fetches while Instagram processes a video.

Known limits: no OS-keychain integration, integrated public-endpoint rate limiter, multi-tenant isolation, external security audit, automatic unknown-write reconciliation or live remote-ChatGPT OAuth validation. Remote desktop, Chrome sandbox compatibility and Supabase RPC grants require a live host/project trial. Put a rate-limited proxy in front of an internet deployment. Keep browser sandboxing and never add CAPTCHA/verification/safety/quota bypasses.

For a vulnerability, use GitHub private vulnerability reporting when enabled or contact a maintainer privately. Do not post tokens, private links, exploit secrets or affected users' data in a public issue. Ordinary reproducible bugs can use public issues with sanitized examples.
