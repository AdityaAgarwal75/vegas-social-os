# Vegas Social OS verification — 0.3.0 community VPS alpha

Updated 2026-10-13.

The community distribution is **single-operator self-hosted**, not a centrally shared SaaS. Every brother/client/community user deploys their own trusted VPS or independently managed runtime, with their own local SQLite state, browser profiles and provider consent. No maintainer credentials or Supabase service keys are distributed.

| Area | Verified result | Remaining gaps |
| --- | --- | --- |
| Ubuntu VPS installer | Live install succeeded on founder's AWS Ubuntu instance after fixing a virtualenv permission issue | Bootstrap on a completely fresh Debian/Ubuntu host not yet verified |
| Application service | systemd started isolated vegas-social-os.service as vegas-social; 127.0.0.1:8899; Caddy HTTPS /health returned version | Uptime/operational hardening need continued review |
| Existing apps | Orbit, Caddy and five independent Flow-MCP services remained active during install | Do not migrate/copy those legacy browser profiles into community instances |
| Database | SQLite local default and vault key under /var/lib/vegas-social-os. No Supabase involved in VPS service | Encrypted off-host backup/restore not yet tested |
| Flow browser | Fresh new account launched graphical Chrome and returned private scoped login URL | No owner-signed-in Google Flow project inspected; no video generation in this edition yet |
| No-credit inspection | Worker returned workspace_ready=false, blocked=false for disposable signed-out account | This does **not** prove Google sign-in eligibility or current model controls |
| Account separation | Account-scoped browser ticket tests and HTTP guards passed in existing Python tests | Cross-tenant SaaS not supported |
| Test suite | 37 Python + 3 Node worker helper tests passed on VPS prior to community changes; community tests added to branch | Full updated branch CI must pass before merge |
| Remote MCP | Source endpoint and OAuth consent code implemented | Actual connected ChatGPT plugin installation/guide/doctor call not yet verified |
| Native image transfer | Native ChatGPT tool only, actual bytes required | Fully automatic host-to-VPS transfer not verified |
| Official social platforms | YouTube and Instagram OAuth/publishing adapters included | Real consent and exact private test upload still needed |
| Daily scheduling | Due-queue supported in source | Requires a separate real host scheduler; no unattended image generation promise |
| Drive archive | Optional drive.file adapter | Real write/restore not yet verified |
| Multi-user roles/DMs/automated comment moderation | Not implemented | Use independent installations, not shared credentials |

## Tests and next milestones

Run python -m unittest discover -s tests -v; node --test tests/flow.test.mjs; bash -n scripts/install-vps.sh scripts/bootstrap-ubuntu.sh scripts/new-setup-link.sh. Verify externally served /health and local /api/state unauthenticated rejection. Test backend restarts without deleting /var/lib/vegas-social-os. Use one manually authorized Google Flow account to confirm real sign-in, model controls, credit quote and downloaded asset after explicit capped approval. Confirm browser sandbox stays enabled.

No video generation or social publication has been performed by this new community edition. Google providers can change their UIs, terms, quotas and eligibility; a successful smoke test does not guarantee continued automation.

The optional managed-cloud Render/Supabase recipe remains a separate unverified path, not a requirement for community VPS installs. Old managed-only BOOTSTRAP instructions were superseded by the VPS-first guide.
