#!/usr/bin/env bash
# Vegas Social OS independent Ubuntu/Debian VPS installer.
set -Eeuo pipefail
umask 077
DOMAIN=""; PORT=8899; CHECK=0; NO_CADDY=0
while (( $# )); do
  case "$1" in
    --domain) DOMAIN="$2"; shift 2;;
    --port) PORT="$2"; shift 2;;
    --check) CHECK=1; shift;;
    --no-caddy) NO_CADDY=1; shift;;
    -h|--help) echo "Usage: sudo bash scripts/install-vps.sh --domain social.example.com [--port 8899] [--check] [--no-caddy]"; exit 0;;
    *) echo "Unknown installer option" >&2; exit 2;;
  esac
done
if ! [[ "$DOMAIN" =~ ^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,63}$ ]]; then
  echo "Pass a valid FQDN with --domain; point its DNS at your VPS." >&2; exit 2
fi
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1024 || PORT > 65535 )); then
  echo "Invalid port" >&2; exit 2
fi
SOURCE="$(cd "$(dirname "$0")/.." && pwd)"
DEST=/opt/vegas-social-os
DATA=/var/lib/vegas-social-os
ENV_FILE=/etc/vegas-social-os.env
ORIGIN="https://$DOMAIN"
for tool in python3 node ffmpeg Xvfb x11vnc websockify tar curl; do
  command -v "$tool" >/dev/null || { echo "Required executable missing: $tool" >&2; exit 1; }
done
CHROME="$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)"
[[ -n "$CHROME" ]] || { echo "Install Google Chrome or Chromium first." >&2; exit 1; }
[[ -f /usr/share/novnc/vnc.html ]] || { echo "Install noVNC first." >&2; exit 1; }
NODE_MAJOR="$(node -v | sed 's/^v//' | cut -d. -f1)"
(( NODE_MAJOR >= 22 )) || { echo "Node.js 22+ required" >&2; exit 1; }
[[ "$(uname -s)" = Linux ]] || { echo "Linux VPS required" >&2; exit 1; }
if (( CHECK )); then
  echo "PASS: prerequisites detected; domain $DOMAIN; port $PORT; no changes"
  exit 0
fi
(( EUID == 0 )) || { echo "Run as root (sudo)." >&2; exit 1; }
if [[ -f "$ENV_FILE" ]] && ! grep -Fxq "VSO_PUBLIC_URL=$ORIGIN" "$ENV_FILE"; then
  echo "An existing installation has another domain. Refusing overwrite." >&2; exit 1
fi
# Copy only application code; exclude source credentials, build outputs, local data.
if [[ "$SOURCE" != "$DEST" ]]; then
  install -d -m 0755 "$DEST"
  tar -C "$SOURCE" --exclude=.git --exclude=.venv --exclude=.env --exclude=.env.local \
    --exclude=__pycache__ --exclude='*.pyc' -cf - . | tar -C "$DEST" -xf -
fi
# Keep source traversable by the service user, never expose .git auth/config or .env.
find "$DEST" \( -name .git -o -name .venv -o -name .env -o -name .env.local \) -prune -o \
  -type d -exec chmod a+rx {} + -o -type f -exec chmod a+r {} +
if ! id vegas-social >/dev/null 2>&1; then
  useradd --system --home-dir "$DATA" --shell /usr/sbin/nologin vegas-social
fi
install -d -o vegas-social -g vegas-social -m 0700 "$DATA"
python3 -m venv "$DEST/.venv"
"$DEST/.venv/bin/python" -m pip install --disable-pip-version-check --quiet -r "$DEST/requirements.txt"
# umask 077 protects credentials, but code/virtualenv must be traversable by the service user.
chmod -R a+rX "$DEST/.venv"
if [[ ! -f "$ENV_FILE" ]]; then
  cat > "$ENV_FILE" <<VSO_CONFIG
VSO_PUBLIC_URL=$ORIGIN
VSO_PORT=$PORT
VSO_DATA_DIR=$DATA
VSO_STATE_BACKEND=sqlite
VSO_REMOTE_BROWSER=1
VSO_CHROME=$CHROME
VSO_PYTHON=$DEST/.venv/bin/python
VSO_NOVNC_ROOT=/usr/share/novnc
VSO_CONFIG
  chmod 0600 "$ENV_FILE"
fi
cat > /etc/systemd/system/vegas-social-os.service <<VSO_SERVICE
[Unit]
Description=Vegas Social OS - isolated community installation
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=vegas-social
Group=vegas-social
WorkingDirectory=$DEST
EnvironmentFile=$ENV_FILE
ExecStart=$DEST/.venv/bin/python -m vso serve --host 127.0.0.1 --port $PORT
Restart=on-failure
RestartSec=3
UMask=0077
StateDirectory=vegas-social-os
StateDirectoryMode=0700
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths=$DATA
LimitNOFILE=16384

[Install]
WantedBy=multi-user.target
VSO_SERVICE
chmod 0644 /etc/systemd/system/vegas-social-os.service
if (( ! NO_CADDY )); then
  command -v caddy >/dev/null || { echo "Caddy required; alternatively pass --no-caddy." >&2; exit 1; }
  CADDYFILE=/etc/caddy/Caddyfile
  [[ -f "$CADDYFILE" ]] || { echo "Cannot find Caddyfile. Pass --no-caddy." >&2; exit 1; }
  MARKER="# BEGIN VSO $DOMAIN"
  if ! grep -Fq "$MARKER" "$CADDYFILE"; then
    if grep -Fq "$DOMAIN {" "$CADDYFILE"; then
      echo "Caddy domain is already configured. Refusing duplicate host." >&2; exit 1
    fi
    cp -p "$CADDYFILE" "$CADDYFILE.vso-backup-$(date +%Y%m%d%H%M%S)"
    cat >> "$CADDYFILE" <<VSO_CADDY

# BEGIN VSO $DOMAIN
$DOMAIN {
    encode zstd gzip
    header {
        Strict-Transport-Security "max-age=31536000"
        Referrer-Policy no-referrer
        X-Content-Type-Options nosniff
        X-Robots-Tag "noindex, nofollow"
    }
    reverse_proxy 127.0.0.1:$PORT
}
# END VSO $DOMAIN
VSO_CADDY
    if ! caddy validate --config "$CADDYFILE" >/dev/null 2>&1; then
      sed -i "/^# BEGIN VSO $DOMAIN$/,/^# END VSO $DOMAIN$/d" "$CADDYFILE"
      echo "Caddy config rejected; new Caddy block reverted." >&2; exit 1
    fi
  fi
fi
systemctl daemon-reload
systemctl enable vegas-social-os.service >/dev/null
systemctl restart vegas-social-os.service
# A systemd "activating" state is not proof of a healthy HTTP service.
HEALTHY=0
for attempt in $(seq 1 25); do
  if curl --fail --silent --max-time 2 "http://127.0.0.1:$PORT/health" >/dev/null; then
    HEALTHY=1
    break
  fi
  sleep 1
done
if (( ! HEALTHY )); then
  echo "Service did not become healthy; check systemctl status vegas-social-os.service" >&2
  exit 1
fi
if (( ! NO_CADDY )); then systemctl reload caddy; fi
echo "Installed. Dashboard: $ORIGIN/dashboard"
echo "Private data: $DATA; Generate a temporary onboarding URL using:"
echo "sudo bash $DEST/scripts/new-setup-link.sh"
echo "Google/Meta account sign-in and provider approvals must be completed by each owner."

