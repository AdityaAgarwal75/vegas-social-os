# Social management permissions and safety (October 2026)

**Start with the tested [complete social setup & troubleshooting runbook](COMPLETE-SOCIAL-SETUP.md).** This file is the condensed policy and capability boundary, not a list of every platform operation implemented.

## Permission groups and verified outcomes

| Action | Required provider OAuth flow and permissions | Actual adapter / result |
| --- | --- | --- |
| Instagram professional account uploads | **Instagram Login**: `instagram_business_basic`, `instagram_business_content_publish` | One JPEG, MP4 Reel, JPEG Reel `cover_url` supplied at media-container creation, and carousel supported by the Vegas Instagram publishing adapter; original media must be an actual validated file. An HTTP acceptance does not guarantee displayed grid cover. |
| Delete previously published Instagram media | **Facebook Login for Business** with Page linked to the **same numeric IG account**: `pages_show_list`, `pages_read_engagement`, `instagram_basic`, `instagram_manage_contents` | `instagram_delete_prepare` → exact owner approval via `instagram_delete_approve` → `instagram_delete_execute` once → `instagram_delete_status`. **One real test Reel deletion was Meta-provider-confirmed 16 October 2026** on an authorized app-role account. Supports only a Vegas-recorded published media ID, not arbitrary unknown older posts. |
| Facebook Page posts/photos/videos | Facebook Page OAuth plus **separate `pages_manage_posts` grant**, eligible Page tasks | Code implements Page text/link, JPEG/PNG photos, photo sets and MP4 video. Must verify granted permission and live provider acceptance **for each Page**. Instagram deletion permission alone doesn't authorize Page publishing. |
| YouTube private uploads, title/description/tags and custom thumbnail | Google YouTube OAuth: `youtube.upload`, `youtube.readonly` (current code); thumbnail eligibility applies | Private MP4 upload and `thumbnails.set` have been tested on one owner channel. Failed cover can be retried **without a second video upload**. |
| Delete/update YouTube video beyond initial upload | Separate compatible YouTube management consent, such as `youtube.force-ssl` / `youtube`, and an implemented audited workflow | **Not yet a verified Vegas delete operation**; do not claim capability just because Google's API has such an endpoint. |
| Instagram comments/messages or Facebook page DMs | Dedicated reviewed privileges and distinct explicitly authorized sending actions | Not blanket-enabled by the above scopes. Don't infer community write access from the Meta app's configuration list. |

**Three independent layers must all align:** (1) Meta/Google developer app configured and where needed reviewed; (2) the specific owner/app-role user granted OAuth scopes and the correct Page/IG IDs; (3) Vegas ChatGPT MCP scopes. `social:manage` is required for Instagram delete prepare/approve/execute; `social:read` covers statuses, `social:write` covers publishing; `vps:admin` is unrelated to social-provider consent. A Meta MCP 'Manage' role also is **not** Instagram management authorization.

## Strict identity and approval rules

1. Select destination from a real `account_list` record using **internal account ID and numeric provider remote ID**, never from display name or a reused OAuth label.
2. For Instagram deletion, an authorized Facebook **Page** record must have `linked_instagram_id` matching the exact Instagram Login account numeric ID, `linked_instagram_username` matching, and actual saved `instagram_manage_contents`, `instagram_basic`, `pages_show_list`. Only one matching Page is allowed. Recheck Page→IG and media ownership with Meta at execute time.
3. Freeze the exact original Vegas-published media/publication ID, media ID and owner; get explicit approval before destructive calls. Never interpret 'connect all my accounts' as permission to delete unrelated content.
4. Record provider outcomes honestly: **deleted** only on provider `success: true`. For unknown/ambiguous outcomes, stop and reconcile without automatic retry.
5. Never print, store in source code, or export tokens, App Secrets, Chrome profiles or Page credentials. A public GitHub repo cannot ship a universal approved developer app.
6. Facebook OAuth may import **several Pages** from `/me/accounts` even when `account_start` is called with one label. After every connection, review every new Page by exact remote ID; its `label` is not a Page allowlist. A Page connection does **not** automatically connect its Instagram Login publishing account.
7. Published Instagram cover editing, Facebook custom video thumbnails, Facebook Reel-specific publishing and direct Page post deletion are not verified primary plugin features. No automatic cross-post or automatic thumbnail correction should be promised.

## Correct connection order

1. Configure **Instagram Login** developer app (own Instagram App ID/Secret, professional account, `instagram_business_basic`, `instagram_business_content_publish`, exact Instagram callback); authorize each Instagram profile separately.
2. Configure **Facebook Login for Business** developer app (Meta App ID/Secret, Graph version, optional `config_id`, **Valid OAuth Redirect URI** registered separately from Configurations). Consent to Page/IG scopes, verify every imported Page and linked IG numeric ID.
3. Configure **Google YouTube OAuth** separately, register exact callback, connect each owned Google/Brand channel. Don't confuse Flow login, Google Drive connection or ChatGPT access with YouTube OAuth.
4. Verify content, account, captions, cover, permissions, idempotency, and owner approval; only then execute. Use live returned status for each remote API operation.

For errors and exact end-user steps, including the OAuth redirect screen, rejected-vs-live Meta App Review, missing Page deletion grant, and ChatGPT's stale tool-discovery metadata, see [the full guide](COMPLETE-SOCIAL-SETUP.md). Official media deletion reference: https://developers.facebook.com/docs/instagram-platform/reference/instagram-media/ .
