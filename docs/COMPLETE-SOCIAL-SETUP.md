# Complete social connection & publishing runbook (community edition)

**Read this before adding your first account.** This guide documents the verified October 2026 Vegas Social OS workflows and separates real provider capabilities from proposed features. It applies to each self-hosted installation; the founder's app IDs, tokens, Page IDs, redirect URLs, passwords, and account names are **not** reusable credentials for community users.

## 0. What is supported (and what is not)

| Destination | Existing adapter and account type | Upload / metadata / artwork | Deletion and other management |
| --- | --- | --- | --- |
| Instagram professional account via **Instagram Login** | Own Instagram Business/Creator account | Original JPEG single post, MP4 Reel, up to 10 carousel items; caption at publish; JPEG Reel `cover_url` requested when a single MP4 is prepared | **Published Reel/media DELETE** is a separate Facebook Login for Business flow below; requires exact media ID, verified Page-to-IG link, `instagram_manage_contents`, frozen review and approval. Post-publication cover editing is **not** implemented. |
| Facebook Page via **Facebook Login for Business** | Page granted to signed-in Meta account | Page text/link, JPEG/PNG photos, photo sets and Page MP4 video adapters exist; Page publishing requires the actual Page posting permission and eligible Page tasks | Facebook post/video deletion, direct Facebook Reel creation and custom Facebook video covers are **not implemented/verified** by this project's primary publishing tools. Do not infer these from Instagram DELETE success. |
| YouTube via Google OAuth | Own channel or selected Brand channel | MP4 upload; title, description, tags, category, visibility and audience setting; separate PNG/JPEG custom thumbnail request (channel eligibility applies); cover-only retry | Existing default requested scopes **do not** grant blanket video editing/deletion. A separate supported management flow, permissions and acceptance test are required. |
| Google Drive (optional) | Owner's Google account | App-scoped generated-media archive with `drive.file` | No blanket Drive read/write. |
| Google Flow browser (optional) | Owner signs into private VPS Chrome | Model/account-specific jobs with credit review | Flow browser login is **not** YouTube OAuth. Paid/unattended generation needs independent verification. |

Read [Platform permissions](PLATFORM-PERMISSIONS.md), [Social management security](SOCIAL-MANAGEMENT-PERMISSIONS.md), and [Meta MCP](META-MCP-ONBOARDING.md) alongside this guide.

## 1. First install and discover the exact callback URLs

1. Deploy this repository on **your own** HTTPS VPS, sign into the owner dashboard and connect your own ChatGPT MCP client; see [Self hosting](SELF-HOSTING.md) and [Web ChatGPT](CHATGPT-WEB.md).
2. In **Workspace settings → Connections / provider developer settings**, run the read-only `connection_setup` tool. Copy the actual callback(s) returned by **your** installation: `https://YOUR-HOST/callback/instagram`, `https://YOUR-HOST/callback/facebook`, `https://YOUR-HOST/callback/youtube` and optional `/callback/drive`. They may instead be configured operator redirect overrides; use the **actual** reported URL.
3. In the developer portals, register the **full exact HTTPS URI**, including path, not just the domain. Keep other applications' valid callbacks; do not swap a shared app's existing routes blindly. In Meta, “Facebook Login for Business → Configurations” (permission preset / `config_id`) and **Facebook Login Settings → Valid OAuth Redirect URIs** are different screens.
4. App IDs are public identifiers, **App Secrets are confidential**. Enter secrets only in the **private owner dashboard** (encrypted at rest); never in GitHub, issues, screenshots, CLI output, app source, copied prompts, or a shared Google Drive file. Use the appropriate Meta app credentials for **each login family**.
5. Validate with `connection_setup` (`configured: true`, `secret_present: true`, exact callback) and `doctor`. **These prove local config only**, not Meta App Review, provider consent or account permissions.

## 2. Configure Meta: two distinct login integrations

### A. Instagram Login — for Instagram uploads

1. Go to [Meta Developer Apps](https://developers.facebook.com/apps/), create/select a Meta developer app, and configure **Instagram API with Instagram Login** for professional Instagram Business or Creator accounts.
2. In that Instagram setup, obtain the **Instagram App ID and Instagram App Secret** (which may be distinct from the developer app's Facebook Login App ID/Secret). Choose a currently supported Graph API version.
3. Add the installation's exact **Instagram OAuth redirect URI**, privacy policy URL and data-deletion URL where the app's Instagram product requests them. Add/accept the relevant Instagram tester/app role during development.
4. Request `instagram_business_basic` and `instagram_business_content_publish`. Those are Instagram Login scopes; do **not** substitute Facebook Login's `instagram_basic`/`instagram_content_publish`.
5. In the private Vegas dashboard, save the Instagram app ID/secret/version. Start **Connections → Instagram**, complete Instagram's own sign-in/consent for the desired professional account, then confirm the **numeric Instagram user ID and username** using `account_list` and `account_info`.
6. Repeat Instagram consent **for each Instagram profile** you actually intend to publish to. A linked Facebook Page does **not** automatically create an Instagram Login publishing record for that profile.

### B. Facebook Login for Business — for Page identity and Instagram media deletion

1. Within [Meta Developer Apps](https://developers.facebook.com/apps/), select the correct app and enable/configure **Facebook Login for Business**. There must be a **developer App ID + App Secret**; the Facebook Login **Configuration ID** (`config_id`) is an additional permission-preset identifier, **not** a second secret.
2. Create a configuration with the minimum permissions appropriate to the user's action. For the verified **Page-linked Instagram DELETE** path, request `pages_show_list`, `pages_read_engagement`, `instagram_basic` and `instagram_manage_contents`; the owner must also have access to the target Page and associated professional Instagram account. Permission selection in a configuration is not the same as actual granted scopes.
3. In Facebook Login / use-case **Settings**, not simply **Configurations**, find **Valid OAuth Redirect URIs**. Add **your installation's** exact `https://YOUR-HOST/callback/facebook` URI and **Save Changes**. Preserve existing valid redirects. Meta frequently changes dashboard navigation; try **Use cases → Facebook Login / Authentication → Customize / Settings** if product settings are hidden.
4. Use the app's **Basic settings → App Secret → Show** (never Reset unless compromised). In Vegas private **Workspace settings**, save App ID, App Secret, supported Graph version (e.g. `v25.0` only if the app currently supports it), and Facebook Login `config_id` if required.
5. Use `connection_setup`, then the **separate Meta MCP** if connected: `devtools_app_list`, `devtools_app.advanced_settings`, `devtools_app_review.privileges`/`requirements`. The expected full callback must appear in `oauth_redirect_uris`. **Meta MCP cannot write redirects, expose secrets, grant user OAuth consent, or approve App Review**.
6. Call `account_start(provider="facebook", label="My Facebook Page")`. Open the resulting **single-use, ten-minute** link in the owner's browser and complete official Facebook Login consent. Choose only Pages whose access you intend to give; where Meta returns multiple Pages, Vegas can import **several separate Page records despite the label**. Inspect every returned `account_list` entry rather than trusting the label.
7. For every Page record, verify `provider=facebook`, numeric Page `remote_id`, `linked_instagram_id`, `linked_instagram_username`, `status=connected` and its **actual saved permission list**. When deleting Instagram media, its linked numeric IG ID **must equal** the Instagram Login account ID's `remote_id` and the permission list must contain `instagram_manage_contents`, `instagram_basic` and `pages_show_list`.
8. **Never infer permissions from Meta App Review alone**: app-role testers may get functional account-specific grants while `devtools_app_review.privileges` still says Rejected/Not Live. Conversely, a “Ready for testing” badge does not prove production access. Public/community integrations need applicable Advanced Access review, use-case evidence, screencasts, data use, and possibly business verification.

**Facebook Page posting:** the existing Page content composer also requires the **separate** `pages_manage_posts` grant plus correct Page task permissions and a provider acceptance test. The Facebook Login configuration used solely for Instagram DELETE may **not** include it. Obtain consent for the minimum additional privilege rather than assuming every Facebook Page is publish-ready.

## 3. Configure YouTube and optional Drive

1. [Google Cloud Console](https://console.cloud.google.com/apis/credentials): create/select **your** Google Cloud project; enable **YouTube Data API v3** (and Drive API only for optional archive); configure Google OAuth consent screen/branding, audience/test users, support/privacy information, and Web application OAuth client.
2. Add the exact Vegas **YouTube callback URI** reported by `connection_setup` (and optional Drive callback) to **Authorized redirect URIs**. A Google Flow account, API key or ChatGPT Google connection is **not** the YouTube OAuth token.
3. Enter Google Client ID and Client Secret in your private Vegas dashboard. The **currently implemented YouTube login** requests `https://www.googleapis.com/auth/youtube.upload` and `https://www.googleapis.com/auth/youtube.readonly`. Optional Drive requests `https://www.googleapis.com/auth/drive.file` separately.
4. Start `account_start(provider="youtube", label="Channel label")`, complete consent and choose the correct Google/Brand channel. Verify the **YouTube channel ID** in `account_list` and `account_info`. For additional channels, repeat the OAuth flow for each selected identity.
5. A successful private upload does not prove public upload eligibility: **unverified Google API projects can have visibility restrictions**, testing refresh tokens can expire, and quota/thumbnail permissions are independent constraints.
6. **YouTube management is not yet end-to-end implemented**. Supported provider API management may need a reconnection to add `youtube.force-ssl` or `youtube`; simply requesting these scopes in an onboarding guide does not add them to today's code or authorize deletion.

## 4. Exact workflow for media, captions and thumbnails

1. `account_list`: select by **numeric account ID** and provider, never only a similar Page/profile display name. Confirm `provider`, `remote_id`, username and live authorization.
2. Prepare actual imported, validated media with `post_prepare` or the approved `publish_prepare` flow. Review **exact account, caption, hashtag content, visibility, tags, title, audience, assets and optional cover** before `publish_approve` / `post_execute` or `publish_execute`.
3. Instagram single Reel: requires MP4, public secure media URL and optional **JPEG `thumbnail_id`** used as `cover_url` on container creation. Instagram single images use JPEG; the cover selection **can appear differently on the Instagram grid even when API accepts it**. No post-publication Reel cover-change tool exists; verify the actual posted cover before declaring success.
4. YouTube: MP4; title, description, tags and category; explicitly set made-for-kids and visibility. Custom thumbnail is a **separate `thumbnails.set` operation**. If only the cover fails, retry via `post_retry_thumbnail`; **never re-upload the video** to retry a cover.
5. Facebook Page: photos, link/text, MP4 supported by code **only if** correct `pages_manage_posts` grant and Page tasks are present; custom Facebook video thumbnails and dedicated Facebook Reels API are **not** accepted features.
6. Poll/reconcile the original provider job. “Prepared”, “processing”, “OAuth ready”, “posted” and “provider-confirmed deleted” mean different things. Unknown provider outcomes are **not retried automatically** to avoid duplicate posts/deletions.

## 5. Safely delete a previously published Instagram Reel

**Only supported for media Vegas Social OS recorded as `published`** and for which there is **exactly one** suitable connected Facebook Page linked to the same numeric Instagram account. Never delete by a name, caption, guessed URL or account label.

1. `publication_list`: find the **exact** previously published Instagram publication, its target `account_id`, `remote_id` (numeric Instagram **media ID**) and caption. Obtain explicit owner approval for that media.
2. Confirm `account_list` has **one** linked Facebook Page record with matching `linked_instagram_id`, and actual granted `instagram_manage_contents`, `instagram_basic`, `pages_show_list` scopes.
3. Call `instagram_delete_prepare(account_id, media_id, request_id)`; review its frozen Instagram account, Page ID, publication ID, media ID and caption excerpt. This step **does not delete**.
4. After the owner approves that exact destructive action, call `instagram_delete_approve(deletion_id, account_id, media_id)`, then `instagram_delete_execute(deletion_id)` **once**.
5. The executor re-checks the Page → Instagram association **against Meta Graph**, reads media ownership, then requests `DELETE /{IG_MEDIA_ID}` with the **Facebook Page token**. It only marks the Reel **deleted** on Meta response `success: true`; verify with `instagram_delete_status` and the original `publication_list`.
6. On `unknown` or any network/provider error, stop and inspect the same media ID first; **never automatically rerun deletion**. Unsupported media types, permissions, expired tokens or changed Page association require investigation.

**Founder deployment acceptance (16 October 2026):** one owner-authorized 10-second Untamed Plot test Reel was provider-confirmed deleted using the separate Page-linked flow; its deletion record and publication record both said `deleted`. This proves that **one specific app-role/grant + supported media type** worked; it does not approve other apps/accounts, or establish general public Meta Advanced Access.

## 6. Troubleshooting: exact symptom → check

| Symptom | Check and safe remedy |
| --- | --- |
| Developer app “configured=false”, HTTP 400 saving settings | Verify correct App ID **and App Secret** entered together, valid `vNN.0` Graph version and owner session. Do not paste credentials into chat/logs. |
| Facebook consent says invalid redirect / URL unavailable | In Meta **Facebook Login for Business → Settings → Valid OAuth Redirect URIs**, save the **full** exact Vegas callback; then verify `devtools_app.advanced_settings.oauth_redirect_uris`. The old URL may be from a different app route or absent from the visible **Configurations** screen. |
| Facebook “Configurations” created but OAuth still fails | `config_id` and actual **Valid OAuth Redirect URI** are separate requirements; verify the requested permission preset and consent screen. |
| Meta MCP says permission Rejected, but owner testing appears functional | Look at the **actual account OAuth permission list** and perform a controlled acceptance test on an authorized app-role user. Production/other users still require applicable App Review/Advanced Access. |
| Deletion says “Connect exactly one authorized Facebook Page...” | Compare numeric Page-linked Instagram ID with the Instagram Login account ID; inspect actual Page permission list; connect/re-authorize the target Page. Duplicate matching Pages also block safely. |
| Facebook Page shows connected, Instagram publishing says account missing | Each Instagram professional account still needs its **own Instagram Login OAuth record**; Page connection alone is not the same record. |
| Facebook Page publishing fails despite successful Instagram deletion | Verify `pages_manage_posts` and Page tasks; deletion's four scopes are not sufficient for Page feed/videos. |
| Instagram cover accepted but wrong cover appears | Review the JPEG Reel `cover_url`, provider rendering and published media; there is no verified after-publish cover edit. Do not claim cover success from an HTTP acceptance alone. |
| YouTube private upload succeeds but thumbnail/public release fails | Inspect `thumbnail_status`, eligibility, API app verification and scopes; retry only the cover using `post_retry_thumbnail`. |
| Plugin is healthy but new tools missing | Compare authenticated server `tools/list` with the connected ChatGPT tool list, refresh the **exact app/plugin registration release**, then refresh the **host's tool discovery**; reconnect/refresh in a new host session. Reinstalling VPS or changing scopes does not by itself refresh client tool metadata. |
| OAuth says success but multiple unrelated Pages appear | Meta can return multiple Pages from `/me/accounts`; inspect **every** Page ID/linked IG identity and disconnect unneeded records. Do not infer the `label` restricts the imported Pages. |

## 7. Scope and approval boundaries for community users

- **Provider OAuth scopes**: Google `youtube.*` / Meta `instagram_*` and `pages_*` — owner-authorized provider access, separate for each login family. **Meta App Review** controls eligibility for roles/public use; OAuth consent controls actual grants.
- **Vegas ChatGPT MCP scopes**: `social:read`, `social:write`, `social:manage` (for Instagram delete prepare/approve/execute) and separately owner-approved `vps:admin`. Having `vps:admin` or root **does not grant Meta permissions**.
- **Minimum privilege**: only request what each user will use, and enforce per-account IDs, typed writes, distinct approvals and durable audit. Never auto-connect/publish/delete for all Pages returned by a Meta login.
- **No shared maintainer secret or tokens**: each community self-hoster must bring their own registered Google/Meta apps, authorized accounts and review approvals; never commit founder IDs/secrets/account identifiers as installation defaults.

### Official API references

- [Meta Instagram media / deleting](https://developers.facebook.com/docs/instagram-platform/reference/instagram-media/)
- [Meta Instagram API with Instagram Login](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/)
- [Meta Facebook Login for Business](https://developers.facebook.com/documentation/facebook-login/facebook-login-for-business)
- [Meta developer app basic settings / App Secret](https://developers.facebook.com/documentation/development/create-an-app/app-dashboard/basic-settings)
- [Meta manual OAuth login and redirect matching](https://developers.facebook.com/docs/facebook-login/guides/advanced/manual-flow/)
- [YouTube videos.insert](https://developers.google.com/youtube/v3/docs/videos/insert)
- [YouTube thumbnails.set](https://developers.google.com/youtube/v3/docs/thumbnails/set)
- [YouTube videos.delete](https://developers.google.com/youtube/v3/docs/videos/delete) — **not** an implemented Vegas action today
- [Google OAuth Web Server apps](https://developers.google.com/identity/protocols/oauth2/web-server)
