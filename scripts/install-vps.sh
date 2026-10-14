#!/usr/bin/env bash
# Isolated, SQLite-first Ubuntu 24.04 / Debian 12 installation and atomic upgrades.
set -Eeuo pipefail
umask 077
DOMAIN=""; PORT=8899; CHECK=0; NO_CADDY=0
while (( $# )); do
  case "$1" in
    --domain) DOMAIN="${2:?domain required}"; shift 2;;
    --port) PORT="${2:?port required}"; shift 2;;
    --check) CHECK=1; shift;;
    --no-caddy) NO_CADDY=1; shift;;
    -h|--help) echo 'Usage: sudo bash scripts/install-vps.sh --domain social.example.com [--port 8899] [--check] [--no-caddy]'; exit 0;;
    *) echo 'Unknown installer option' >&2; exit 2;;
  esac
done
[[ "$DOMAIN" =~ ^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,63}$ ]] || { echo 'Pass a valid FQDN with --domain.' >&2; exit 2; }
[[ "$PORT" =~ ^[0-9]+$ ]] && (( PORT >= 1024 && PORT <= 65535 )) || { echo 'Invalid port' >&2; exit 2; }
[[ "$(uname -s)" = Linux ]] || { echo 'Linux VPS required' >&2; exit 1; }
. /etc/os-release
case "$ID:$VERSION_ID" in ubuntu:24.04|debian:12|debian:13) ;; *) echo 'Tested targets are Ubuntu 24.04 and Debian 12; inspect compatibility before installing.' >&2; exit 1;; esac
[[ "$(uname -m)" = x86_64 ]] || { echo 'This pinned browser/engine distribution currently requires x86_64.' >&2; exit 1; }
SOURCE="$(cd "$(dirname "$0")/.." && pwd)"
DEST=/opt/vegas-social-os; DATA=/var/lib/vegas-social-os; ENV_FILE=/etc/vegas-social-os.env
UNIT=/etc/systemd/system/vegas-social-os.service; ORIGIN="https://$DOMAIN"
for tool in python3 node npm git ffmpeg Xvfb x11vnc websockify tar curl flock ss runuser; do
  command -v "$tool" >/dev/null || { echo "Missing $tool. The setup agent should run scripts/bootstrap-ubuntu.sh." >&2; exit 1; }
done
CHROME="$(command -v google-chrome || command -v chromium || command -v chromium-browser || true)"
[[ -n "$CHROME" && -f /usr/share/novnc/vnc.html ]] || { echo 'Chrome/Chromium and noVNC required.' >&2; exit 1; }
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"'
NODE_MAJOR="$(node -v | sed 's/^v//' | cut -d. -f1)"
(( NODE_MAJOR >= 22 )) || { echo 'Node.js 22+ required' >&2; exit 1; }
if (( CHECK )); then
  echo "PASS: prerequisite check only; domain $DOMAIN, loopback port $PORT; DNS, TLS, install and provider login still need acceptance."
  exit 0
fi
(( EUID == 0 )) || { echo 'Run with sudo.' >&2; exit 1; }
install -d -m 0755 /run/lock
exec 9>/run/lock/vegas-social-os-install.lock
flock -n 9 || { echo 'Another installation/upgrade is running.' >&2; exit 1; }
if [[ -f "$ENV_FILE" ]]; then
  grep -Fxq "VSO_PUBLIC_URL=$ORIGIN" "$ENV_FILE" || { echo 'Existing domain differs; refusing overwrite.' >&2; exit 1; }
  grep -Fxq "VSO_PORT=$PORT" "$ENV_FILE" || { echo 'Existing port differs; refusing overwrite.' >&2; exit 1; }
fi
if ss -H -ltn "sport = :$PORT" | grep -q . && ! systemctl is-active --quiet vegas-social-os.service; then
  echo 'Port occupied by another service; select another --port.' >&2; exit 1
fi
if (( ! NO_CADDY )); then
  command -v caddy >/dev/null && [[ -f /etc/caddy/Caddyfile ]] || { echo 'Caddy missing; use --no-caddy for an owner-managed proxy.' >&2; exit 1; }
fi
id vegas-social >/dev/null 2>&1 || useradd --system --home-dir "$DATA" --shell /usr/sbin/nologin vegas-social
install -d -o vegas-social -g vegas-social -m 0700 "$DATA"
install -d -m 0755 /opt/vegas-social-os-releases
RELEASE="$(mktemp -d /opt/vegas-social-os-releases/release-XXXXXXXX)"
chmod 0755 "$RELEASE"
# Source allowlist avoids bundling developer credentials, browser profiles or local artifacts.
for path in vso worker web scripts skills third_party docs deploy requirements.txt plugin.json mcp.json agent-manifest.json BOOTSTRAP.md AGENTS.md README.md LICENSE; do
  [[ -e "$SOURCE/$path" ]] && cp -a "$SOURCE/$path" "$RELEASE/"
done
find "$RELEASE" -type d -name __pycache__ -prune -exec rm -rf -- {} +
if git -C "$SOURCE" rev-parse HEAD > "$RELEASE/.vso-source-commit" 2>/dev/null; then :; elif [[ -f "$SOURCE/.vso-source-commit" ]]; then cp "$SOURCE/.vso-source-commit" "$RELEASE/"; fi
chmod -R a+rX "$RELEASE"
python3 -m venv "$RELEASE/.venv"
"$RELEASE/.venv/bin/python" -m pip install --disable-pip-version-check --quiet -r "$RELEASE/requirements.txt"
chmod -R a+rX "$RELEASE/.venv"
"$RELEASE/.venv/bin/python" -m compileall -q "$RELEASE/vso"
ENGINE_CONTRACT="$(cat "$RELEASE/deploy/flow-engine/lock.json" "$RELEASE/deploy/flow-engine/compatibility.patch" "$RELEASE/deploy/flow-engine/attach-only.py" "$RELEASE/deploy/flow-engine/sdk-security.patch" | sha256sum | cut -d' ' -f1)"
ENGINE_ROOT=/opt/vegas-social-os-flow-engine
if [[ -d "$ENGINE_ROOT" ]] && { [[ ! -f "$ENGINE_ROOT/.vso-contract" ]] || [[ "$(cat "$ENGINE_ROOT/.vso-contract")" != "$ENGINE_CONTRACT" ]]; }; then
  ENGINE_ROOT="/opt/vegas-social-os-flow-engine-${ENGINE_CONTRACT:0:12}"
fi
VSO_ENGINE_INSTALL_DEST="$ENGINE_ROOT" bash "$RELEASE/scripts/install-flow-engine.sh"
# Verify imports and a disposable store as the REAL service user, before cutover.
runuser -u vegas-social -- env VSO_ACCEPT_SOURCE="$RELEASE" "$RELEASE/.venv/bin/python" - <<'PY'
import os,sys,tempfile
sys.path.insert(0,os.environ['VSO_ACCEPT_SOURCE'])
from vso.store import Store
from vso.engine import Engine
from vso.tools import definitions
with tempfile.TemporaryDirectory() as root:
 assert definitions(Engine(Store(root)))
PY
STAMP="$(date -u +%Y%m%dT%H%M%SZ)-$(basename "$RELEASE")"
BACKUP="/var/backups/vegas-social-os/$STAMP"
install -d -m 0700 "$BACKUP"
OLD="$(readlink -f "$DEST" || true)"
printf '%s\n' "$OLD" > "$BACKUP/source-path"
[[ -f "$ENV_FILE" ]] && cp -a "$ENV_FILE" "$BACKUP/environment"
[[ -f "$UNIT" ]] && cp -a "$UNIT" "$BACKUP/service"
[[ -f /etc/caddy/Caddyfile ]] && cp -a /etc/caddy/Caddyfile "$BACKUP/Caddyfile"
WAS_ACTIVE=0; systemctl is-active --quiet vegas-social-os.service && WAS_ACTIVE=1
BROKER_ACTIVE=0; systemctl is-active --quiet vegas-social-admin.service && BROKER_ACTIVE=1
[[ -f /usr/local/lib/vegas-social-admin/broker.py ]] && cp -a /usr/local/lib/vegas-social-admin/broker.py "$BACKUP/broker.py"
[[ -f /etc/systemd/system/vegas-social-admin.service ]] && cp -a /etc/systemd/system/vegas-social-admin.service "$BACKUP/broker-service"
SWITCHED=0; COMMITTED=0
rollback() {
  status=$?
  if (( ! COMMITTED )); then
    echo "Upgrade failed; rollback checkpoint: $BACKUP" >&2
    if (( SWITCHED )); then
      if [[ -n "$OLD" && -d "$OLD" ]]; then ln -s "$OLD" "$DEST.rollback"; mv -Tf "$DEST.rollback" "$DEST"; fi
      [[ -f "$BACKUP/environment" ]] && cp -a "$BACKUP/environment" "$ENV_FILE"
      [[ -f "$BACKUP/service" ]] && cp -a "$BACKUP/service" "$UNIT"
      [[ -f "$BACKUP/Caddyfile" ]] && cp -a "$BACKUP/Caddyfile" /etc/caddy/Caddyfile
      if [[ -f "$BACKUP/broker.py" ]]; then cp -a "$BACKUP/broker.py" /usr/local/lib/vegas-social-admin/broker.py; fi
      if [[ -f "$BACKUP/broker-service" ]]; then cp -a "$BACKUP/broker-service" /etc/systemd/system/vegas-social-admin.service; fi
      systemctl daemon-reload
      if (( BROKER_ACTIVE )); then systemctl restart vegas-social-admin.service || true; else systemctl stop vegas-social-admin.service || true; fi
    fi
    if (( WAS_ACTIVE )); then systemctl restart vegas-social-os.service || true; else systemctl stop vegas-social-os.service || true; fi
  fi
  exit "$status"
}
trap rollback EXIT
if (( WAS_ACTIVE )); then systemctl stop vegas-social-os.service; fi
# Complete private state includes media, encryption key and app-owned profiles. Imported profiles stay with their original owner.
tar -C "$DATA" -cpf "$BACKUP/state.tar" .
"$RELEASE/.venv/bin/python" - "$DATA" "$BACKUP" <<'PY'
import sqlite3,sys
from pathlib import Path
src=Path(sys.argv[1])/'state.sqlite'
if src.exists():
 with sqlite3.connect(src) as a,sqlite3.connect(Path(sys.argv[2])/'state.sqlite') as b:a.backup(b)
PY
if [[ -n "$OLD" && -d "$OLD" ]]; then tar -C "$OLD" --exclude=.git -cpf "$BACKUP/source.tar" .; fi
if [[ ! -f "$ENV_FILE" ]]; then
  cat > "$ENV_FILE" <<CFG
VSO_PUBLIC_URL=$ORIGIN
VSO_PORT=$PORT
VSO_DATA_DIR=$DATA
VSO_STATE_BACKEND=sqlite
VSO_REMOTE_BROWSER=1
VSO_CHROME=$CHROME
VSO_PYTHON=$DEST/.venv/bin/python
VSO_NOVNC_ROOT=/usr/share/novnc
VSO_FLOW_ENGINE_ROOT=$ENGINE_ROOT
CFG
  chmod 0600 "$ENV_FILE"
fi
if grep -q '^VSO_FLOW_ENGINE_ROOT=' "$ENV_FILE"; then
  sed -i "s|^VSO_FLOW_ENGINE_ROOT=.*|VSO_FLOW_ENGINE_ROOT=$ENGINE_ROOT|" "$ENV_FILE"
else
  echo "VSO_FLOW_ENGINE_ROOT=$ENGINE_ROOT" >> "$ENV_FILE"
fi
if [[ -d "$DEST" && ! -L "$DEST" ]]; then
  LEGACY="/opt/vegas-social-os-releases/legacy-$STAMP"
  mv "$DEST" "$LEGACY"; OLD="$LEGACY"; printf '%s\n' "$OLD" > "$BACKUP/source-path"
fi
ln -s "$RELEASE" "$DEST.next"; mv -Tf "$DEST.next" "$DEST"; SWITCHED=1
cat > "$UNIT" <<CFG
[Unit]
Description=Vegas Social OS - isolated community installation
After=network-online.target vegas-social-admin.service
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
TasksMax=512
[Install]
WantedBy=multi-user.target
CFG
chmod 0644 "$UNIT"
# A separate root-owned broker is installed; no root Python code is imported from app state.
bash "$RELEASE/scripts/install-admin-broker.sh"
if (( ! NO_CADDY )); then
  CADDYFILE=/etc/caddy/Caddyfile; MARKER="# BEGIN VSO $DOMAIN"
  if ! grep -Fq "$MARKER" "$CADDYFILE"; then
    if grep -Fq "$DOMAIN {" "$CADDYFILE"; then echo 'Caddy host already exists; use --no-caddy and preserve its routing.' >&2; exit 1; fi
    cat >> "$CADDYFILE" <<CFG

# BEGIN VSO $DOMAIN
$DOMAIN {
    encode zstd gzip
    header Strict-Transport-Security "max-age=31536000"
    header Referrer-Policy no-referrer
    header X-Content-Type-Options nosniff
    header X-Robots-Tag "noindex, nofollow"
    reverse_proxy 127.0.0.1:$PORT
}
# END VSO $DOMAIN
CFG
  fi
  caddy validate --config "$CADDYFILE" --adapter caddyfile >/dev/null
fi
systemctl daemon-reload
systemctl enable vegas-social-os.service >/dev/null
systemctl restart vegas-social-os.service
HEALTHY=0
for attempt in $(seq 1 25); do
  if curl --fail --silent --max-time 2 "http://127.0.0.1:$PORT/health" >/dev/null; then HEALTHY=1; break; fi
  sleep 1
done
(( HEALTHY )) || { echo 'HTTP health failed; restoring prior source/configuration.' >&2; exit 1; }
if (( ! NO_CADDY )); then systemctl reload caddy; fi
COMMITTED=1
printf 'Installed. Dashboard: %s/dashboard\nRollback checkpoint: %s\n' "$ORIGIN" "$BACKUP"
echo "The setup agent can generate a private owner link: sudo bash $DEST/scripts/new-setup-link.sh"
echo 'Verify external HTTPS, provider consent and a real authenticated ChatGPT Web tool call. No firewall or SSH rules were changed.'
