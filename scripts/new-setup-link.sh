#!/usr/bin/env bash
set -Eeuo pipefail
(( EUID == 0 )) || { echo "Run with sudo" >&2; exit 1; }
FILE=/etc/vegas-social-os.env
[[ -f "$FILE" ]] || { echo "Install Vegas Social OS first." >&2; exit 1; }
set -a
source "$FILE"
set +a
cd /opt/vegas-social-os
runuser -u vegas-social -- env VSO_DATA_DIR="$VSO_DATA_DIR" VSO_PUBLIC_URL="$VSO_PUBLIC_URL" VSO_STATE_BACKEND=sqlite \
  /opt/vegas-social-os/.venv/bin/python -m vso setup

