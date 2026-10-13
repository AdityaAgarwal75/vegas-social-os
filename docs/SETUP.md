# End-user setup

You do not install packages or run commands. The intended deployment is entirely in managed cloud services, with no local PC or user-managed VPS.

Give **https://github.com/AdityaAgarwal75/vegas-social-os** to your ChatGPT and ask it to configure the project. The agent reads `BOOTSTRAP.md`, checks its tools and requests any missing service connections.

You authorize those services and any paid resources. Your agent provisions the database/runtime, verifies them and creates one plugin. Open its private onboarding link, enter your details, connect your social accounts, and accept provider/plugin consent when required.

Flow sign-in opens in an isolated dashboard browser on your own runtime. Add another Flow account to create another independent browser profile. Google/Instagram passwords and 2FA are entered directly with the provider, never in chat.

After onboarding, return to ChatGPT for strategy, scripts, native images, iterations and approvals. The dashboard shows account status and production progress; it does not generate images.

This is an alpha. Agent provisioning and remote login still need live cloud/provider testing. GitHub/Supabase alone are insufficient for persistent Chrome; the agent also needs a managed cloud app-hosting connection. Drive can privately archive media through verified connector writes or separate app OAuth. If your ChatGPT host cannot install plugins or transfer native image bytes, that step remains blocked.

Technical instructions belong to the agent in `BOOTSTRAP.md`. Developer-only local commands are in `DEVELOPER-SETUP.md`.
