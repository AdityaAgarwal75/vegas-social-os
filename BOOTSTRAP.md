# BOOTSTRAP — instructions for ChatGPT/Codex setup agents

A user who shares this repository link wants an independently installed Vegas Social OS. **Do not assume that their provider accounts, this project's maintainer server, Google Flow cookies or paid subscriptions are available.** Start by reading README.md, AGENTS.md, agent-manifest.json, docs/SELF-HOSTING.md and docs/STATUS.md.

## Choose the operating model

**Preferred when a VPS is already available: VPS-first / local SQLite.** Discover the actual VPS tool, read its operational runbook and inspect RAM, disk, existing services, spare ports, Chrome, Node, Python, noVNC, Caddy and DNS. Install via scripts/install-vps.sh if dependencies already exist, otherwise use scripts/bootstrap-ubuntu.sh on supported Debian/Ubuntu hosts. Deploy under a separate Linux user, data directory, port, systemd unit and HTTPS hostname. Do not modify another service or its Google sessions. Require no Render, Supabase, paid managed hosting or locally running personal computer.

**Alternative: managed cloud.** For users who do not control a VPS and authorize an additional persistent cloud host, the original cloud recipe and Supabase encrypted state adapter remain experimental options. Neither GitHub nor Supabase alone can provide durable graphical Chrome. Request approval before paid resources; provision dedicated projects rather than sharing Orbit or another app's database. The cloud-only helper scripts/agent_bootstrap.py still require managed cloud runtime flags; do not run that helper on a VPS.

## Fresh AWS instance

When the user has no VPS and authorizes an AWS install, read docs/AWS-ONBOARDING.md and deploy/aws/instance.json. Discover real connected AWS tools and required IAM permissions. Prepare and validate a pinned deployment and regional costs before paid-resource approval. Provision through the approved change set, verify the instance/SSM/HTTPS/browser, and generate the private setup link only after checks. Do not create a second instance after a timeout. Do not output setup tickets in public cloud-init/CloudFormation/GitHub logs.

## Provision & verify

1. Pin current Git commit, inspect actual connector tool schemas and availability. If the user explicitly wants code synchronized to GitHub, use their authenticated repository integration.
2. Install and configure private source/runtime. For an existing VPS, use **sudo bash scripts/install-vps.sh --domain HOSTNAME --port 8899** through a connected execution tool. Make sure the chosen port/host is unused and the Caddy file validates before reload. Run the offline tests first.
3. Verify systemd status, live internal and external HTTPS /health, authenticated /api/state rejection, app /dashboard, and persistent files after restart. Do not report source-only changes as deployment.
4. Verify that a new **disposable** Flow account can launch an isolated Chrome browser and can be inspected without signing in, then remove its test processes/profile. This proves only browser infrastructure, not provider authentication or generation.
5. Generate a fresh expiring setup link with scripts/new-setup-link.sh after checks. Give the link privately; the user enters details and signs into Google/2FA personally.
6. Verify one signed-in Flow project via flow_inspect. User accounts are not "connected" merely because a Chrome window started.
7. Package one optional remote MCP plugin using the verified https://HOSTNAME/mcp endpoint. Use host consent/installation actions. Check guide/doctor with the installed plugin. Never silently authorize publishing.
8. Verify native image byte transfer before promising zero-manual generation. Obtain explicit account, model and positive credit cap before one experimental Flow generation. Confirm exact asset/result and preserve idempotency. Use dashboard Connections for encrypted provider app settings, exact callback URLs and scopes. YouTube/Instagram/Facebook require separate OAuth permissions and explicit publication approval.
9. Record detailed facts, failed checks, required consent and any additional costs. Never claim community user accounts have been connected on behalf of a different user.

## Community guarantees and limits

The installer works per independent VPS/instance, not as one shared multi-tenant API. Community users may clone and self-host without maintainer infrastructure. Provider account login, app developer credentials, verification and spending consent remain individual steps. There is no universal single click that bypasses those requirements.

Always respect the user's request about spending and existing infrastructure. No secret values in chat, GitHub, terminal logs or app configuration delivered to other users. No Google cookie extraction, CAPTCHA avoidance or quota circumvention.

## Maintainer testing

Run python -m unittest discover -s tests -v and node --test tests/flow.test.mjs, plus installer shell syntax checks. For any production server tests, never publish externally or consume Flow credits without explicit approval and a destination.

## Audit 0.6 workflows

Read docs/AUDIT-0.6.md and docs/FEATURE-AUDIT-0.6.md. Inspect workflow_audit, refresh idle model menus and use the account's actual settings rather than assuming a documented rollout. Original native production scenes support explicit model settings; standalone advanced input modes currently require a configured existing local service. Run zero-credit compatibility preflights and reconcile the original job after a timeout. Never call menu discovery or a quote stop proof of a rendered video or a successful post.
