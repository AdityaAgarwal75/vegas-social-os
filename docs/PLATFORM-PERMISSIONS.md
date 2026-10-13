# Provider permissions and supported operations

Every operator owns their own registrations and credentials. The dashboard derives callback URLs from their installation's HTTPS origin and stores client secrets encrypted. Google Flow sign-in, Google YouTube OAuth, Instagram Login and Facebook Page login are separate connections.

| Integration | Account type | Requested permissions | Composer operations |
| --- | --- | --- | --- |
| Google Flow | Eligible signed-in Google account, isolated browser | Direct provider login/2FA; no claimed public Flow OAuth scope | Experimental keyframe-to-video under explicit credit caps; model/one-output settings must be verified |
| YouTube | Own channel or selected Brand channel | `youtube.upload`, `youtube.readonly` | MP4 upload; title/description/tags/category; explicit made-for-kids setting; visibility; custom PNG/JPEG thumbnail subject to channel eligibility |
| Instagram API with Instagram Login | Business or Creator | `instagram_business_basic`, `instagram_business_content_publish` | JPEG image, MP4 Reel, carousel up to ten items; captions; JPEG cover for a single Reel |
| Facebook Pages | Page with create-content task | `pages_show_list`, `pages_read_engagement`, `pages_manage_posts` | Text/link posts, JPEG/PNG photos, photo sets, single MP4 Page video; personal timelines unsupported |
| Google Drive (optional) | Owner-authorized archive account | `drive.file` | Archive imported generated media; no full-Drive scope required |

Facebook custom video thumbnails and dedicated Facebook Reel endpoints are not implemented in this release. Instagram/YouTube/Facebook analytics expansion, DMs, comments, Stories, TikTok, X, LinkedIn, Pinterest and other providers need separate tested adapters and permissions. Do not show them as connected or silently use login scraping to replace official APIs.

## Google

Create a Google Cloud project, enable YouTube Data API v3 (Drive API only if needed), configure Google Auth Platform branding/audience and create a Web OAuth client. Register **/callback/youtube** and optionally **/callback/drive** using the dashboard's exact HTTPS URLs. Add your own Google accounts as test users when applicable. Reconnect each Brand channel separately.

OAuth testing refresh-token lifetime, verification requirements and quota limits vary by app/account. Uploads from unverified API projects created after Google's stated cutoff can be restricted to **private**, independently of OAuth consent. Native ChatGPT/Google sign-in is not a credential for the VPS publisher. Custom thumbnail authorization can be denied independently of successful video uploads; cover retry does not re-upload the video.

Primary references (reviewed 13 October 2026):
- https://developers.google.com/identity/protocols/oauth2/web-server
- https://developers.google.com/youtube/v3/docs/videos/insert
- https://developers.google.com/youtube/v3/docs/thumbnails/set
- https://developers.google.com/drive/api/guides/api-specific-auth

## Instagram

Use **Instagram API with Instagram Login**, its Instagram app ID/secret and matching permission family. It supports professional accounts without requiring a linked Facebook Page for this path. Register **/callback/instagram**. In development, add/accept appropriate test roles/invitations. For users outside the app roles, obtain applicable Advanced Access/App Review and any required business verification. Business verification does not approve publishing scopes.

Do not mix Facebook Login scopes (`instagram_basic`, `instagram_content_publish`) with Instagram Login scopes (`instagram_business_basic`, `instagram_business_content_publish`). The connector uses the latter path. Media must be reachable through this installation's expiring HTTPS asset URLs. Provider format/ratio/duration/processing restrictions still apply. A provider identity read proves identity access, not a successful publishing trial.

Primary references:
- https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/
- https://developers.facebook.com/documentation/instagram-platform/content-publishing
- https://www.postman.com/meta/instagram/folder/1z5vxzu/instagram-api-with-instagram-login (Meta-maintained collection)

## Facebook

Register a Meta app with the appropriate Facebook Login for Business/use-case configuration. Use its own app ID/secret and a **configuration ID** if required by that app setup. Register **/callback/facebook** and request the three Page scopes above. The connector checks granted permissions, discovers `/me/accounts`, and saves eligible Page identities/tokens separately. The operator needs a Page content-management task; a personal account login alone does not permit Page publication.

Development/app-role testing and access for unrelated users differ. Each independent self-hoster can register their own app and test their own assets according to Meta's role rules; an app serving unrelated users needs applicable permissions review/access. The project cannot approve apps or guarantee review outcomes.

Primary references:
- https://developers.facebook.com/docs/facebook-login/facebook-login-for-business/
- https://developers.facebook.com/docs/pages-api/posts/
- https://developers.facebook.com/docs/graph-api/reference/page/photos/
- https://developers.facebook.com/docs/graph-api/reference/page/videos/
- https://www.postman.com/meta/facebook/documentation/r56bjfd/facebook-api (Meta-maintained collection)

Meta documentation retrieval returned rate limits for several reference pages during this implementation. Adapter request-shape tests do not establish live Meta acceptance; perform controlled authorized account trials before claiming production support. Choose a currently supported Graph API version from your own app dashboard rather than assuming a version from an old tutorial.

## Guided versus automatic

The agent can provision infrastructure through available authorized tools, calculate links, install software, store state, guide app registration and prepare review evidence. The owner must approve paid infrastructure and complete account consent/2FA/any legal verification. Platform review remains external. A new user can be guided through these steps in the dashboard; installation cannot remove provider requirements.
