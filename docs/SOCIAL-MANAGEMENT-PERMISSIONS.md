# Vegas Social OS: provider management permissions (v0.11.1)

Each integration is scoped to **one installation-owned account ID**, not the Meta/Google login identity. Never choose a destination by display name alone. Never copy, log, or export provider tokens.

## Current verified connection setup

- Instagram Login: `instagram_business_basic`, `instagram_business_content_publish`. Supports account reads, single-image posts and public Reels; caption and JPEG cover are requested during media creation. Published-media deletion is **not proven or supported** through this integration. `instagram_delete_prepare` + `instagram_delete_approve` + `instagram_delete_execute` capture an account-bound owner request, but execution returns `manual_required` until a documented/provider-tested adapter exists. The corresponding Instagram app action is manual. Never claim remote deletion from a local status.
- YouTube: `youtube.upload`, `youtube.readonly`. Private video upload and cover application have been live-tested on the Untamed Plot account. Additional `youtube.force-ssl` / `youtube` OAuth consent enables supported metadata and video management/deletion API operations, **but requires a provider reconnection and explicit review**. Do not assume current tokens include the scope. The official YouTube `videos.delete` endpoint is documented: https://developers.google.com/youtube/v3/docs/videos/delete
- Facebook Pages: configured app/connection is optional, not yet present. Required Page permissions vary by feature. `pages_show_list`, `pages_read_engagement`, `pages_manage_posts` are the baseline for publishing; permissions like `pages_manage_engagement` / `pages_manage_metadata` are separately reviewed when those operations are implemented.
- Instagram comments/messages: `instagram_business_manage_comments` and `instagram_business_manage_messages` are **separate** permissions. New scopes cannot be granted by AWS IAM or root VPS access; the account owner must consent to a supported Meta app configuration, and app review may be required.

## Operational security

1. Look up live provider account ID, username and media ID before each write.
2. Prepare the exact action with a stable idempotency key. Freeze destination, content, and requested effect.
3. Require an owner approval for each destructive action; OAuth connection alone is not approval.
4. Serialize provider write status before network I/O. Unknown outcomes are not retried blindly.
5. Verify the result against the remote provider and log only nonsecret identifiers.
6. A Meta permission is not an API endpoint. Never guess undocumented DELETE endpoints or use private mobile APIs, browser-copied credentials or another person's account.
7. Uploaded tests on any platform must not spread to the other Instagram accounts belonging to the same login.
8. A posted Instagram Reel can be removed through Instagram's app until Meta documents and enables an API capability for this exact connection.

## Follow-on implementation, after provider consent

- Explicit YouTube management connection with `youtube.force-ssl`; implement an account-bound, approve-then-execute video deletion method with provider ownership checks.
- Instagram comment moderation with `instagram_business_manage_comments`; DM workflows only after approved `instagram_business_manage_messages` and user-directed send boundaries.
- Facebook Page publishing and approved Page content/comment management when the Page is individually connected with the appropriate permissions.
- Location and cover support should be verified against each provider; the Instagram cover URL may be accepted by the API without successfully rendering the desired grid cover.
