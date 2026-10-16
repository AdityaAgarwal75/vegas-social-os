# Meta Social Technologies MCP — guided setup for community installations

**Official remote MCP endpoint:** `https://mcp.facebook.com/devtools`  
**Meta documentation:** https://developers.facebook.com/documentation/mcp/devtools-mcp  
**Authentication:** OAuth in the user's **own** ChatGPT, Codex or IDE client, with per-app access selection.  
**Role:** Developer-app audits and approved webhook administration; NOT a replacement for Instagram/Facebook Page OAuth, social posting, billing approval or app review.

**For the complete click-by-click setup** (separate Instagram vs Facebook apps, Configuration ID vs App Secret, exact redirect URL, deletion scopes, YouTube thumbnails and troubleshooting), open [Complete social setup](COMPLETE-SOCIAL-SETUP.md). This page focuses specifically on what the *separate Meta developer MCP* can and cannot do.

## Quick start for a new Vegas Social OS user

1. Deploy Vegas Social OS using the repository setup instructions. Its owner dashboard stores developer App IDs and App Secrets independently, encrypted at rest.
2. In an eligible ChatGPT client, enable supported custom MCP connectors/Developer mode. Add the official **Meta Social Technologies** connector using the endpoint above; select **OAuth**, sign in, and grant access **only** to developer apps you intend to manage. You may choose Read access for diagnostics or Manage only if you wish the assistant to edit webhook subscriptions. If the connector is not available in that client/account, use the manual Meta Developer dashboard route below.
3. Open **Vegas Social OS → Workspace settings → Meta developer setup · AI-assisted**. Click **Copy agent setup prompt** to get exact callback URLs and locally configured app IDs; use it in the chat where Meta MCP is connected.
4. The agent MUST call `devtools_app_list` before selecting any app. The agent must confirm the returned `app_id`, granted read/manage scope and your role; absence from the list can mean the app wasn't selected during consent.
5. Inspect the exact app: `devtools_app.basic_settings` + `advanced_settings`, `devtools_app_review.privileges` + `requirements` + `status`, `devtools_compliance.status`, `devtools_api_usage.deprecations`, and `devtools_webhook_list.list_subscriptions`.
6. Compare approved OAuth redirect URI(s) to `meta_mcp_setup`'s **installation-specific** Facebook and Instagram callback URLs. A mismatch is a **hard connection blocker**, not something that should be silently changed in the plugin.
7. Use Meta Developer's app dashboard (or supported future Meta MCP tool, when truly available) to configure required use cases and official redirect URIs, and complete App Review if needed. **Ready for testing ≠ approved/advanced access ≠ OAuth consent granted**.
8. Enter the App ID, App Secret and supported Graph API version ONLY in your private Vegas owner dashboard. Never paste the secret into ChatGPT, CLI output, GitHub, documentation or Meta MCP chat prompts.
9. Complete **both** official login flows as required by the task: Instagram Login for upload; Facebook Login for Business for Page-bound media deletion. Verify **every** numeric account ID in `account_list`: one Facebook sign-in can import several separate Pages even if the user-supplied connection label names just one. For deletion, the Page's live linked IG numeric ID, actual `instagram_manage_contents` grant, and the exact recorded publication must match before approval/execution. A Facebook Page record is not an Instagram publishing record.
10. Report the differences between developer-app status, live Meta MCP permissions, provider OAuth scopes and actual Social OS account connectivity. Never infer one from another.

### Tools that are available today (as of October 2026)

| Tool | Agent-safe use |
|---|---|
| `devtools_app_list` | List only developer apps explicitly granted in user's MCP consent |
| `devtools_app` | Inspect basic, advanced, security, restrictions |
| `devtools_app_review` | Check privilege status and incomplete app review requirements |
| `devtools_compliance` | Check app compliance and outstanding actions |
| `devtools_api_usage` | Check rate limits, call volume, deprecations |
| `devtools_discovery`, `devtools_api_changelog` | Search official docs and changelogs |
| `devtools_webhook_list` | Inspect webhook topics and existing subscriptions |
| `devtools_webhook_manage`, `devtools_webhook_test` | **Writes**, only with Manage permission and explicit approval for exact callback/topic/fields/payload |
| `devtools_skill_invocation` | Advisory workflow metadata; not permission granting |

Six **coming soon, not currently exposed** lifecycle tools: `devtools_app_create`, `devtools_app_use_cases`, `devtools_app_use_cases_manage`, `devtools_business_list`, `devtools_business_create`, `devtools_app_business_manage`. They can only be used when the connected Meta MCP actually advertises them. Never fabricate endpoints or claim to have created a Meta app.

**Not supported by current Meta MCP:** reading the App Secret, completing Meta user login, entering private developer-app credentials into Vegas, modifying OAuth redirects directly, automatically obtaining permission approval, conducting App Review submission, managing Instagram content, deleting Reels, or reauthorizing a Facebook Page. These belong to other interfaces and require the owner's consent.

### Installing Meta MCP is strongly recommended, not a hard requirement

Some users may not have access to the beta remote Meta MCP or may use a ChatGPT/IDE configuration that cannot connect it. New users **must receive the Meta MCP onboarding option and status check**, but community installations **must not break** if the user selects the supported manual dashboard alternative.

The same independent Vegas Social OS package still serves private self-hosted installations without the Meta MCP. A user's developer MCP OAuth token belongs to their client; do **not** copy it into the VPS or write it to a shared application database.

### Recommended agent audit (after connecting the Meta MCP)

> Read this repo's AGENTS.md and docs/META-MCP-ONBOARDING.md. Call `meta_mcp_setup` on my own Vegas Social OS plugin for exact callback URLs. Use the separate connected Meta Social Technologies MCP to call `devtools_app_list` and then inspect **only** my explicitly selected app IDs. Compare login redirects, App Review privileges and requirements, app compliance and webhook configuration. Return a readiness table with evidence for each issue. Do not invent or execute app-creation actions, expose credentials, request unnecessary scopes, modify webhooks, or publish/delete content without asking first. Then guide me through only those steps that need my browser consent.

### Developer implementation notes

`vso/meta_mcp.py` exposes the read-only `meta_mcp_setup` guidance tool using ONLY independent installation configuration. It does **not** make a server-side call to the Meta MCP. Agents directly invoke their user-connected `devtools_*` MCP tools, verify app selection, and produce audited findings. Dashboard buttons are instructional and copy official URLs/callback-specific prompts.

**Founder acceptance, 16 October 2026:** the official Meta MCP still reported the chosen app's requested `instagram_manage_contents` as Rejected/Not Live while a Meta app-role user's **actual Facebook OAuth account grant contained** that scope. Vegas Social OS successfully performed one explicitly approved, exact-identity, provider-confirmed test Reel deletion; this **does not** imply Advanced Access for the general public. See [deletion workflow](COMPLETE-SOCIAL-SETUP.md#5-safely-delete-a-previously-published-instagram-reel).

App Review permission states have nuances: a permission visible under "Permissions and features" with "Ready for testing" can simultaneously have no live Advanced Access. Always check `devtools_app_review.privileges`, `requirements`, and the actual provider OAuth scopes. Never mark an app "fully configured" only because `devtools_app_list` succeeded.

### Manual fallback

Use the official [Meta Developer apps console](https://developers.facebook.com/apps/), select the intended app, configure OAuth redirect URIs/use cases, complete review and consent, enter the secret in the Vegas owner dashboard, and verify exact linked Page/Instagram IDs. This workflow does not require Meta MCP and should remain available to all community users.
