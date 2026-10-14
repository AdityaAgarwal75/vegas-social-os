# Engineering audit — 14 October 2026

Baseline: GitHub main and deployed source `420c11421b05e223629132fdd19364e09e37a70b`; production health 0.6.1; private plugin package 0.6.2. This document distinguishes implementation from acceptance evidence.

| Confirmed finding | Files / boundary | Repair / acceptance |
|---|---|---|
| Repository root advertises a local stdio launcher while its generated package advertises HTTPS | mcp.json, scripts/package_plugin.py | Developer launcher moved to deploy/development; owner-specific packaging is the remote installation path. |
| MCP rejects anonymous discovery, lacks per-tool OAuth schemes and runtime scope challenges | vso/server.py, vso/tools.py | Public discovery, authenticated execution, per-tool scopes and structured OAuth challenges. Real Web login/call remains required. |
| Public registration has no abuse rate limits; token rotation lacks revocation and grant-family replay protection | vso/auth.py | Persistent rate limits; canonical resource/issuer, S256, scoped grants, rotating refresh tokens, family revocation. |
| RPC bodies can be read before authorization, up to 90 MB | vso/server.py | Authorization preflight; 16 KB auth, 64 KB anonymous RPC, 1 MB authenticated RPC; media bytes use separate bounded transfers. |
| Whole-file/base64 media ingestion is unsuitable for host-native images and large videos | vso/media.py, vso/engine.py | Resumable capability-authorized raw-byte chunks, SHA-256, signature and actual FFmpeg decoding; streaming previews. Actual native-host transfer remains a separate test. |
| No same-plugin privileged administration boundary | vso/admin*.py, scripts/install-admin-broker.sh | Root-owned standalone local broker; non-root gateway; Unix peer credentials; exact-operation approval, private owner TOTP, durable bounded jobs and audit. No public root shell. |
| Daily queue does not wake ChatGPT; no event subscription implementation | vso/events.py, vso/store.py | Transactional outbox, signed verified callbacks, durable retries. Mocked webhook tests are not host continuation evidence. |
| Installer replaces active code before health checks; bootstrap assumes Python already exists | scripts/install-vps.sh, scripts/bootstrap-ubuntu.sh | Atomic release/backup/rollback and clean OS acceptance work tracked below. |
| Old Docker/managed-cloud defaults unexpectedly require Supabase | deploy/ | SQLite-first defaults and explicit optional/unsupported boundaries required. |
| Existing complete pinned Flow engine works independently of the experimental worker | deploy/flow-engine, worker/service.mjs | Preserve pinned engine and all five existing profiles; do not rebuild browser automation unnecessarily. |
| Host memory pressure | Existing VPS | Approximately 1.2 GiB available, 1.8/2 GiB swap used at audit; serial tests, no additional concurrent browser fleet. |

## Verification boundaries

- Baseline: 95 Python and 4 Node tests. Added security integration tests use actual local SQLite/HTTP/FFmpeg; the webhook receiver is explicitly mocked.
- No new paid generation, public publication, account restriction bypass or paid instance provisioning is authorized merely by this audit.
- Five existing connected accounts are not evidence that a new owner's clean installation works.
- ChatGPT plugin permission inspection reports the existing plugin **not installed** in the active account context. The separate verification browser is signed out. Manifest validation, HTTP 200 and OAuth client tests cannot satisfy real ChatGPT Web acceptance.
- Existing plugin identity must be preserved. Provider OAuth app registration is installation-specific and cannot be bypassed by an open-source package.

Further test/deployment evidence is appended as checks complete. Unverified features must remain labeled in STATUS.md and the operator guide.

## Verified candidate evidence

- Feature PR #6; candidate f9186d64 passed CI run 38548673466, including Python 3.11/3.12 and actual browser checks. Current local suite: 112 Python / 5 Node tests.
- Real ChatGPT-native image: 1,657,598 bytes, PNG 1254x1254, SHA-256 f785cbfe0d26ef59ca37e14282e08c8b222ccaa3dc2571efd00d5455731105ca. Connector-assisted byte transfer, actual raw HTTP PUT, FFmpeg decoding and exact disposable storyboard attachment passed. This does not establish installed-plugin fileParams delivery or paid Flow rendering.
- Actual booted Debian 12 systemd-nspawn acceptance passed install, reinstall, private vault/SQLite preservation, non-root gateway, Unix broker, public metadata/private data checks and deliberate unhealthy-release rollback. The first package attempt was killed by its 800 MB test cgroup while unpacking Chrome; recovery with distro Chromium succeeded. No owner profile was reset.
- Isolated tests do not cover public DNS/TLS/provider consent or real ChatGPT Work continuation. Those remain separately reported gates. No paid generation/public post/new cloud instance was used.

Dependency audit found SDK 1.30.0 / GHSA-6qxp-vccf-f47h. The advisory concerns OAuth clients, and explicitly excludes MCP servers; the local Flow engine server path is not exposed to that client attack. New pinned engine builds apply an exact 1.31.0 package/lock patch. Existing imported services retain ownership and are not restarted merely for an unreachable client advisory. Upgrades stage a new versioned managed engine rather than overwrite an active tree.

Booted Ubuntu 24.04 acceptance also passed install/reinstall/key and SQLite preservation/non-root broker checks and unhealthy-source rollback. Container-only timezone mounts and the low unpacking memory cap were corrected in the test environment; additional runtime-only test swap is removed after tests. A real locally trusted HTTPS stream sent 4 MiB with matching checksum. Exact native PNG was accepted as Flow first-frame input on account-5: Lite/8s/720p/9:16, quote10, cap0 stopped generation and balance remained50. No paid clip or public post was created.

The separate Work execution/browser environment went offline during final verification. External VPS/GitHub operations remain available, but same-ID plugin archive upload and actual signed-in Web installation/calls cannot be completed from that offline host. Equivalent-client success is not ChatGPT Web acceptance.
