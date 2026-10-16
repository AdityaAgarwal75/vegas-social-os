# ChatGPT web is the primary workstation

The owner requires Vegas Studio to work in **ChatGPT on the web**, using a supported Work chat. Installing the ChatGPT desktop app, accessing the user's local machine or running a laptop daemon is not a product requirement. The owner's VPS runs Chrome/Flow/FFmpeg and stores state; ChatGPT connects remotely over authenticated HTTPS.

## Package contract

- Root `plugin.json`: `extensions.com.openai.requires_local_executor` is explicitly `false`. For an existing legacy compatibility manifest, top-level `requires_local_executor` must also be `false`.
- `mcp.json` contains only an owner-specific HTTPS Streamable HTTP endpoint, with OAuth/Dynamic Client Registration via discovery. Never a stdio command, localhost URL, local shell hook or hardcoded maintainer connection in a community package.
- Skills direct work through remote tools. Included Python craft examples are reference material; do not run them on the user's PC. Media operations execute through the VPS.
- The same plugin identity, existing connection, personal/workspace scope, default prompts and author metadata are preserved on update. A package upload is distinct from a working web connection.

## Web setup

1. Open ChatGPT web → Plugins. Open the existing Social OS plugin and refresh its updated release. Install/connect through the web flow when available; complete personal consent.
2. If the package page still offers only “Open in desktop,” do not install desktop as the product setup path. In ChatGPT web's Plugins menu choose **+ → Add custom MCP server**, enter the owner's exact `https://YOUR-DOMAIN/mcp`, choose OAuth and create/connect the remote plugin through the supported flow. This registers the web connection; a ZIP alone is not proof of registration. Account/workspace permissions may restrict custom MCP creation.
3. Reuse the verified registered server/plugin mapping with the Social OS instructions when the host exposes the registration ID. Do not invent an App ID, silently create duplicates or publish to the public directory to solve private setup.
4. Start a Work chat on the web, select the connected Social OS plugin and call `guide`, `doctor`, `onboarding_status` and `account_list`. Verify this user's installation and account identities before production. No Flow generation/posting is needed for this check.
5. Sign into Google accounts through the browser dashboard's private VPS screen mirror. Signing into local/laptop Google Chrome does not authenticate the VPS profiles.

[Official connection guide](https://developers.openai.com/plugins/deploy/connect-chatgpt) and [plugin package guide](https://developers.openai.com/plugins/build/plugins) describe the host registration path. [Desktop-only documentation](https://developers.openai.com/plugins/deploy/desktop-only) identifies the local executor flag. Setting it false expresses package eligibility; it does not override workspace policy or prove an OAuth/tool call has succeeded in the user's web account.

## Acceptance and limitations

Required acceptance is a real web Work chat calling authenticated harmless tools, reading an account, saving a draft and transferring an actual host-native image's bytes to the VPS. Remote MCP readiness, package validation and a browser-rendered dashboard are separate evidence. If native image bytes cannot be transferred in a particular web host, pause that stage rather than requiring desktop or substituting a paid API silently.

The primary target is web Work, not a promise that every ordinary Chat mode, account tier or workspace supports every tool. The server now implements signed MCP Events; actual host continuation remains an acceptance gate. the documented MCP Events architecture explicitly targets supported Work chats on web. A desktop-only badge/prompt after package correction must be investigated as a host registration/classification issue, not reported as fixed from manifest read-back alone.
