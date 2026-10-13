#!/usr/bin/env bash
# Fresh private one-use 10-minute link. Only nonsecret runtime fields are read.
set -Eeuo pipefail
(( EUID == 0 )) || { echo "Run with sudo." >&2; exit 1; }
FILE=/etc/vegas-social-os.env
[[ -f "$FILE" ]] || { echo "Install Vegas Social OS first." >&2; exit 1; }
read_field() {
  grep -m 1 "^$1=" "$FILE" | cut -d= -f2-
}
PUBLIC_URL="$(read_field VSO_PUBLIC_URL)"
DATA_DIR="$(read_field VSO_DATA_DIR)"
[[ "$PUBLIC_URL" == https://* ]] || { echo "Missing secure app origin." >&2; exit 1; }
[[ "$DATA_DIR" = /var/lib/vegas-social-os ]] || { echo "Unexpected private data path." >&2; exit 1; }
cd /opt/vegas-social-os
runuser -u vegas-social -- env VSO_DATA_DIR="$DATA_DIR" VSO_PUBLIC_URL="$PUBLIC_URL" VSO_STATE_BACKEND=sqlite \
  /opt/vegas-social-os/.venv/bin/python -m vso setup
