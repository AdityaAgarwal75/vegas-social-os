#!/usr/bin/env bash
# Optional, isolated source catalogue. No code is copied to Vegas Social OS.
set -Eeuo pipefail
umask 022
ROOT="/opt/vegas-social-os-integrations/openmontage"
if [ -e "$ROOT" ]; then
  printf 'External source already exists; leaving it unchanged: %s\n' "$ROOT"
  exit 0
fi
mkdir -p "$(dirname "$ROOT")"
git clone --depth 1 --filter=blob:none https://github.com/calesthio/OpenMontage.git "$ROOT"
test -f "$ROOT/LICENSE"
grep -q 'GNU AFFERO GENERAL PUBLIC LICENSE' "$ROOT/LICENSE"
printf 'External AGPL source installed separately at %s\n' "$ROOT"
printf 'No provider dependencies, API keys, paid services or execution were configured.\n'
