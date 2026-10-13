# Status — 0.1.0 alpha

| Capability | Included | Verification |
|---|---|---|
| Master skill/local plugin | Yes | Frontmatter/JSON checks |
| MCP stdio and HTTP | Yes | Offline protocol/local HTTP tests |
| MCP OAuth discovery/registration/consent/PKCE/refresh | Yes | Local tests; actual ChatGPT client pending |
| One-use 10-minute setup/account links | Yes | Expiry/reuse tests |
| Credential encryption | Fernet + local private key file | Offline test; OS keychain not implemented |
| YouTube OAuth/refresh/channel read/resumable upload | Yes | Code only, no live provider trial |
| Instagram Login/token upgrade/refresh/profile/Reels | Yes | No live trial; current Meta docs partly login-gated |
| Flow profile launcher/workspace inspection | Original worker | Syntax/helper tests, live browser pending |
| First-frame Flow generation/new-asset download | Experimental | No live test; English UI/control/upload matching needs verification |
| Concepts/scripts/scene records | Yes | Validation/idempotency tests; ChatGPT writes creative content |
| Native ChatGPT images | Host tool + import bridge | Automatic generated-byte transfer not guaranteed |
| Credit caps/conservative reservations | Yes | Cap/concurrency/unknown-outcome tests |
| Actual balances/spend/refunds | No | Reservations are not charges |
| FFmpeg assembly | Command included | Media smoke test pending |
| Publication approval/duplicate suppression | Yes | Offline tests; live reconciliation manual |
| Review dashboard | Yes | Static/syntax checks; browser trial pending |
| Channel statistics | Basic provider reads | No live test; not full analytics |
| Daily briefs | On-demand timezone-aware queue | Needs host scheduler to launch ChatGPT |
| Supabase metadata backup | Optional REST/schema | Mock tests and owner-isolation live trial needed |
| Supabase jobs/distributed workers | No | Local SQLite authoritative |
| Two-concept preview images | No | Selected concept keyframes only |
| IG photos/carousels/comments/DMs | No | Reels only |
| Facebook/Threads/TikTok/LinkedIn/X | No | No advertised integrations |
| Flow Extend/upscale/ingredients/last frame | No | Current model/duration selected in Flow |
| Public plugin directory release | No | Repository package only |

Next: user-authorized end-to-end onboarding, native-image transfer and one capped Flow job. Repair/verify UI integration before adding generation features. Test Supabase owner isolation in a fresh project before backup. This is a complete initial repository, not a completed full social-management product.
