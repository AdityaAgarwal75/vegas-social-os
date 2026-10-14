#!/usr/bin/env bash
# Install the complete pinned dependency; never touches existing Flow profiles/services.
set -Eeuo pipefail
umask 022
SOURCE="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${VSO_ENGINE_INSTALL_DEST:-/opt/vegas-social-os-flow-engine}"
LOCK="$SOURCE/deploy/flow-engine/lock.json"
REVISION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["revision"])' "$LOCK")"
REPOSITORY="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["repository"])' "$LOCK")"
FINGERPRINT="$(cat "$LOCK" "$SOURCE/deploy/flow-engine/compatibility.patch" "$SOURCE/deploy/flow-engine/attach-only.py" | sha256sum | cut -d' ' -f1)"
if [[ -d "$DEST" ]]; then
  if [[ -f "$DEST/.vso-contract" ]] && [[ "$(cat "$DEST/.vso-contract")" = "$FINGERPRINT" ]] && [[ -f "$DEST/dist/server.js" ]]; then
    echo "Complete pinned Flow engine already installed."
    exit 0
  fi
  echo "Engine destination exists with another contract. Preserve it; install the reviewed engine into a new directory." >&2
  exit 1
fi
for tool in git node npm python3; do command -v "$tool" >/dev/null; done
[[ "$DEST" = /* ]] || { echo "Absolute engine destination required" >&2; exit 2; }
install -d -m 0755 "$(dirname "$DEST")"
STAGE="$(mktemp -d "$(dirname "$DEST")/.vso-engine-XXXXXX")"
trap 'rm -rf -- "$STAGE"' EXIT
git -C "$STAGE" init --quiet
git -C "$STAGE" remote add origin "$REPOSITORY"
git -C "$STAGE" fetch --quiet --depth 1 origin "$REVISION"
git -C "$STAGE" checkout --quiet --detach FETCH_HEAD
[[ "$(git -C "$STAGE" rev-parse HEAD)" = "$REVISION" ]] || exit 1
git -C "$STAGE" apply --check "$SOURCE/deploy/flow-engine/compatibility.patch"
git -C "$STAGE" apply "$SOURCE/deploy/flow-engine/compatibility.patch"
python3 "$SOURCE/deploy/flow-engine/attach-only.py" "$STAGE"
(cd "$STAGE"; npm ci --ignore-scripts --no-audit --no-fund; ./node_modules/.bin/tsc)
printf '%s\n' "$FINGERPRINT" > "$STAGE/.vso-contract"
cp "$LOCK" "$STAGE/.vso-source.json"
chmod -R a+rX "$STAGE"
mv -T "$STAGE" "$DEST"
echo "Installed complete pinned Flow engine at $DEST. No account or browser was opened."
