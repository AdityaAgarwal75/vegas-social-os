# Security

This alpha is for independently self-hosted, single-operator installations. Do not expose it as a shared hosted service without a separate tenancy/security review.

Keep data outside GitHub, protect its OS permissions and back it up securely. Browser profiles are sensitive even without exported cookie files. Fernet encryption protects SQLite alone; anyone with access to both the vault key and database can decrypt credentials. Windows ACLs must be configured by the operator.

Do not expose Chrome/CDP ports. Run HTTP on loopback behind HTTPS when connecting ordinary ChatGPT. Keep setup/account links private: they are expiring bearer capabilities. OAuth developer app secrets belong in the backend environment. Revoke provider grants externally when disconnecting.

Provider requests use fixed HTTPS allowlists and do not follow redirects. Provider response bodies/tokens are not echoed on errors. Logs omit request query strings. Media links expire but allow repeated fetches while Instagram processes a video.

Known limits: no OS-keychain integration, public-endpoint abuse/rate-limit layer, multi-tenant isolation, external security audit, automatic unknown-write reconciliation or live remote-ChatGPT OAuth validation. Put a rate-limited reverse proxy in front of an internet deployment. No CAPTCHA/verification/safety/quota bypass is permitted.

For a vulnerability, use GitHub private vulnerability reporting when enabled or contact a maintainer privately. Do not post tokens, private links, exploit secrets or affected users' data in a public issue. Ordinary reproducible bugs can use public issues with sanitized examples.
