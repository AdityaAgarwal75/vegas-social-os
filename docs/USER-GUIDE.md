# Your first Vegas Studio workspace

Vegas Studio is independently hosted: every owner has their own server, password, browser profiles, media and plugin connection. It is not a shared public service or a multi-user team dashboard.

## 1. Get your installation

Give [the repository](https://github.com/AdityaAgarwal75/vegas-social-os) to a supported ChatGPT Work agent that can manage your own VPS or AWS account. Ask it to follow BOOTSTRAP.md, prepare any new hosting costs for approval, install a pinned revision and verify HTTPS. No local terminal is required when your agent has authorized server tools.

Use Ubuntu 24.04 or supported Debian x86_64, persistent storage and ports 80/443. The installer checks RAM, disk, dependencies and conflicting ports. Existing VPS hosting is supported; new infrastructure and provider credits can cost money. There is no shared maintainer Google account, subscription or universal approved social app.

## 2. Set your owner password

Your agent provides a private setup link. Open it **once within 10 minutes**. In that paired browser open **Owner password**, choose 14–256 characters and save. Existing browser sessions end when a password is saved; sign in again with the new password.

Bookmark `https://YOUR-HOST/login`, not the setup link. Your login page has a Show/Hide password control. Password managers and pasted passwords are supported. Your password is stored as a salted scrypt hash, never plain text.

If a setup link expired, ask your agent for a fresh one. Do not repeatedly reopen an old link. Help is always at `https://YOUR-HOST/help`.

## 3. Connect the ChatGPT plugin

Use the **MCP endpoint shown in your setup guide/workspace settings**, ending in `/mcp`. Add it through your supported ChatGPT custom-plugin connection flow with OAuth. Sign into your Social OS installation and review the client, return address and requested permissions. Click **Authorize Vegas Studio** once.

Return to ChatGPT and ask it to run `guide`, `doctor` and `account_list`. Verify your installation and your accounts. A dashboard, a healthy `/health`, a generated ZIP or a consent redirect alone does not verify the host connection.

If the authorization page stays on “Redirecting,” close it and reconnect from ChatGPT to start a fresh request. Do not refresh/reuse the previous approval. Your administrator should verify the current release, response CSP/Referrer-Policy and token exchange. Other MCP hosts may need a separately scoped callback policy.

## 4. Connect your accounts

- **Google Flow:** Open Connections → Google account login. Add a label, open the private browser, sign into Google yourself, complete verification, open a Flow project, then verify access. Repeat for your own profiles. The browser runs on your server; laptop Chrome sign-in does not connect it.
- **YouTube:** Configure your own official Google OAuth application through the agent/operator setup, then sign in and approve upload/read scopes. Flow login alone does not authorize YouTube publishing.
- **Instagram:** Use an eligible professional account and your installation’s official app registration and callback. Required review/permissions remain provider-controlled.
- **Facebook:** Configure the owner’s Page application and consent. Facebook publishing is not automatically enabled by Instagram login.

A “setup required” message means the installation’s provider application is missing; it is not a request to paste your provider password into ChatGPT. You enter passwords/2FA directly into the provider’s private screen.

## 5. Your control panel

The home page shows host CPU, memory and storage, last observed Flow balances, connected publishing identities, actual specialist activity, recent video projects and upcoming releases. Use the theme button in the top bar for light/dark mode; the choice stays on this device. Resource history begins when the dashboard is first observed, without invented historical samples. Refresh Flow balances explicitly to read existing imported services. Native Google profiles require your explicit browser sign-in/verification.

Specialists are ChatGPT-led roles. Tool calls record real activity; work performed only inside ChatGPT appears when the agent reports it. Idle means no observed running task. A stale report becomes unconfirmed after five minutes. These cards do not create independent background model workers.

Use **Projects → New project** to name each video, or ask ChatGPT to do it. Reuse its project ID for scene images, clips and final exports. Plan-based productions group their known media automatically. **Unassigned media** preserves older files whose project is unknown; choose **Assign to project** to organize them. Original bytes and downloads remain intact.

**Schedule** shows the destination and local display time for each dated item. Editorial plans and draft release times are labeled separately from approved scheduled uploads. A project date never schedules publication.

## 6. Review one production

Tell ChatGPT your audience, language, references, objective and budget. Review its two concepts. Choose one, review actual transferred scene images and approve a credit ceiling. Watch the exact clips and assembled video. Approve the exact platform, account, media, copy and visibility before publishing.

A queued brief is not an unattended generation. Events and schedules need a real supported host-continuation trial. Unknown generation or upload outcomes must be inspected before retrying, to avoid duplicate spending or posts.

## 7. Sign out and return

Use **Sign out** in the sidebar; return through `/login`. Sessions last eight hours. Mobile navigation opens from the menu button, closes after route selection and supports Escape.

## Forgot your password?

Open `/forgot-password`. Ask your connected infrastructure agent for a **password recovery link**, not an ordinary setup link. The authorized administrator runs:

```bash
sudo bash /opt/vegas-social-os/scripts/new-setup-link.sh --reset-password
```

Open the new private link once. It goes straight to the password form; no current password is needed. Save a new password, then sign in. The previous password remains active until replacement. Saving revokes owner browser sessions, recovery sessions and unused recovery tickets. It preserves your projects, provider accounts and media. MCP OAuth grants are separate; revoke a plugin connection separately if needed.

No email service is required. If no authorized infrastructure connection is available, recover access through your own hosting provider; a public page cannot safely grant server ownership.

## Troubleshooting

| What you see | What to do |
| --- | --- |
| Owner session required | Sign in. For a forgotten password request a fresh recovery link. |
| Recovery/setup link expired or used | Request a fresh link and open it once in the intended browser. |
| Incorrect password | Retry on the same page or use Forgot password. Rate limits apply. |
| Connection service needs setup | Ask the installation agent to configure the provider’s official application. |
| Google sign-in challenge | Complete the provider challenge personally; do not bypass it. |
| Flow project not ready | Open a signed-in Flow project in the VPS browser and verify again. |
| Plugin tools unavailable | Reconnect in a supported ChatGPT host; verify an authenticated harmless tool call. |
| Unknown rendering/upload outcome | Ask the agent to inspect the original job; do not start a duplicate. |

See [self-hosting](SELF-HOSTING.md), [current evidence](STATUS.md), [platform permissions](PLATFORM-PERMISSIONS.md) and [security](../SECURITY.md). Keep passwords, recovery links, browser profiles and backups private.
