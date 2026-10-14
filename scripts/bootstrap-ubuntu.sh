#!/usr/bin/env bash
# Optional one-command prerequisites + install for Ubuntu/Debian x86_64.
set -Eeuo pipefail
(( EUID == 0 )) || { echo "Run with sudo." >&2; exit 1; }
[[ -r /etc/os-release ]] || { echo "Unsupported operating system" >&2; exit 1; }
. /etc/os-release
case "$ID" in ubuntu|debian) ;; *) echo "Ubuntu/Debian required" >&2; exit 1;; esac
[[ "$(uname -m)" = x86_64 ]] || { echo "Automatic Chrome install requires x86_64." >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOMAIN=""
PORT=8899
NO_CADDY=0
while (( $# )); do
  case "$1" in
    --domain) DOMAIN="$2"; shift 2;;
    --port) PORT="$2"; shift 2;;
    --no-caddy) NO_CADDY=1; shift;;
    *) echo "Unsupported bootstrap option: $1" >&2; exit 2;;
  esac
done
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq ca-certificates curl gnupg git tar xz-utils python3 python3-venv iproute2 util-linux \
  ffmpeg xvfb x11vnc websockify novnc
if (( ! NO_CADDY )); then apt-get install -y -qq caddy; fi
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11+ required"'
NEED_NODE=1
if command -v node >/dev/null 2>&1; then
  if (( $(node -v | sed 's/^v//' | cut -d. -f1) >= 22 )) && command -v npm >/dev/null 2>&1; then NEED_NODE=0; fi
fi
if (( NEED_NODE )); then
  NODE_URL="https://nodejs.org/dist/latest-v22.x"
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  curl --fail --silent --show-error --location "$NODE_URL/SHASUMS256.txt" -o "$TMP/SHASUMS256.txt"
  ARCHIVE="$(grep -E 'node-v[0-9.]+-linux-x64\.tar\.xz$' "$TMP/SHASUMS256.txt" | awk '{print $2}' | head -n1)"
  [[ -n "$ARCHIVE" ]] || { echo "Cannot resolve Node 22 archive" >&2; exit 1; }
  curl --fail --silent --show-error --location "$NODE_URL/$ARCHIVE" -o "$TMP/$ARCHIVE"
  (cd "$TMP"; grep -F " $ARCHIVE" SHASUMS256.txt | sha256sum -c -)
  install -d /opt/vegas-social-os-node
  tar -xJf "$TMP/$ARCHIVE" --strip-components=1 -C /opt/vegas-social-os-node
  ln -sfn /opt/vegas-social-os-node/bin/node /usr/local/bin/node
  ln -sfn /opt/vegas-social-os-node/bin/npm /usr/local/bin/npm
  ln -sfn /opt/vegas-social-os-node/bin/npx /usr/local/bin/npx
fi
if ! command -v google-chrome >/dev/null 2>&1 && ! command -v chromium >/dev/null 2>&1; then
  TMPKEY="$(mktemp)"
  curl --fail --silent --show-error --location https://dl.google.com/linux/linux_signing_key.pub -o "$TMPKEY"
  gpg --dearmor --yes --output /usr/share/keyrings/google-chrome-signing.gpg "$TMPKEY"
  rm -f "$TMPKEY"
  echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-signing.gpg] https://dl.google.com/linux/chrome/deb/ stable main' \
    >/etc/apt/sources.list.d/google-chrome.list
  apt-get update -qq
  apt-get install -y -qq google-chrome-stable
fi
if [[ -z "$DOMAIN" ]]; then
  IP="$(curl --fail --silent --show-error --max-time 6 --ipv4 https://api.ipify.org || true)"
  if ! [[ "$IP" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "Cannot determine public IPv4. Pass --domain your-host.example.com" >&2
    exit 1
  fi
  DOMAIN="social.$(printf '%s' "$IP" | tr . -).sslip.io"
fi
if (( NO_CADDY )); then
  exec bash "$ROOT/scripts/install-vps.sh" --domain "$DOMAIN" --port "$PORT" --no-caddy
fi
exec bash "$ROOT/scripts/install-vps.sh" --domain "$DOMAIN" --port "$PORT"

