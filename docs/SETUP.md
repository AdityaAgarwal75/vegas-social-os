# Setup

Use a stable source checkout and private data directory. Install Python requirements into `.venv`; verify Node 22+, Chrome and optionally FFmpeg. Export environment settings: `.env` is not auto-loaded.

Windows PowerShell:
```powershell
$env:VSO_DATA_DIR = "$env:LOCALAPPDATA\vegas-social-os"
$env:VSO_CHROME = "C:\Program Files\Google\Chrome\Application\chrome.exe"
python -m vso doctor
python -m vso setup
python -m vso serve
```

Linux/macOS:
```bash
export VSO_DATA_DIR="$HOME/.local/share/vegas-social-os"
python -m vso doctor
python -m vso setup
python -m vso serve
```

Use the same environment/data directory for all commands. Open the one-use setup link in your browser; it grants an eight-hour dashboard session. Anyone holding that unexpired link can become the operator. Keep it private.

## Local Codex

Use a supported installer for the portable package or explicit current client configuration:
```toml
[mcp_servers.vegas_social_os]
command = "/ABSOLUTE/CHECKOUT/.venv/bin/python"
args = ["-m", "vso", "stdio"]
cwd = "/ABSOLUTE/CHECKOUT"
```

Windows uses the absolute `.venv\Scripts\python.exe` path with appropriate escaping. Preserve other servers and restart the task after connecting. Stdio runs as the OS operator. Native-image capability is still host-dependent.

## Ordinary ChatGPT

Run the backend and browser worker on a machine you control; this alpha keeps both on one machine. Put HTTP behind a reachable HTTPS origin/proxy, set `VSO_PUBLIC_URL`, keep the listener on loopback, and never expose Chrome CDP. Forward `/mcp`, OAuth metadata, `/authorize`, `/register`, `/token`, `/pair`, `/connect`, `/callback/*` and media paths.

Configure exact Google/Meta callbacks, open your setup link, then connect `https://YOUR-ORIGIN/mcp` through your host's supported custom-app/plugin UI. OAuth registration/consent/PKCE is built in but a real remote ChatGPT connection is untested. Current plan/workspace policy controls installation.

`scripts/package_plugin.py` creates a skill/manifest/remote-MCP ZIP; it neither hosts the backend nor submits it to a directory. Read [onboarding](../skills/vegas-social-master/references/onboarding.md) for provider developer-app requirements.

## Image transfer

Use actual native-generated files only. If accessible locally:
```bash
python scripts/import_asset.py /ABSOLUTE/PATH/keyframe.png
```
Use the returned checksum ID in `image_attach`. The helper must share the backend's `VSO_DATA_DIR`. Otherwise use **Import ChatGPT image** in the dashboard. Some ordinary-chat hosts require downloading/importing manually; do not claim automatic transfer.

## Optional Supabase

Create a fresh project, review/apply `supabase/schema.sql`, configure publishable key and a valid user JWT server-side, then invoke `cloud_sync`. RLS restricts rows with `auth.uid()` ownership for all operations. Never put service-role keys in browsers. JWT renewal is manual in this alpha. Test isolation with two users before live backup.

## Disconnect

`account_disconnect` removes local provider credentials/metadata. It does not revoke provider grants, terminate jobs or erase Flow profiles. Revoke externally, stop Chrome, and explicitly review/delete the correct private profile directory. Never delete unknown jobs just to allow a speculative retry.
