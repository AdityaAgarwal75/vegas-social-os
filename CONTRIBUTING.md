# Contributing

Start with README, status and architecture. Use a virtual environment, install pinned requirements, then run the Python and Node offline suites. Small focused PRs should describe actual behavior, validation and any untested provider assumptions.

Do not commit credentials, tokens, profiles, private content or generated media. Do not run live generation/publishing in CI. Use mocked provider responses in ordinary tests. Any live trial must name the account/destination and authorized credit ceiling.

Priority work: verify/fix real account onboarding; native-image transfer in supported ChatGPT hosts; exact Flow asset identity, first-frame attachment and settings discovery; resumable-upload reconciliation; Supabase owner-isolation tests; portable packaging; then comments, carousels, analytics and additional platform adapters.

Maintain original code or document a license-reviewed dependency with attribution. Never market unsupported features as implemented. Read `AGENTS.md` when using an AI coding agent.
