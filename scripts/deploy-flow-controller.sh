#!/usr/bin/env bash
# Reviewed, owner-authorized in-place upgrade. No provider services are restarted.
set -euo pipefail
[[ $(id -u) -eq 0 ]] || { echo 'Run through the authorized owner administrator'; exit 1; }
revision=${1:?Pass the reviewed full commit SHA}
public_origin=${2:?Pass the installation HTTPS origin}
[[ $public_origin =~ ^https://[A-Za-z0-9.-]+(:[0-9]+)?$ ]] || exit 1
[[ $revision =~ ^[0-9a-f]{40}$ ]] || { echo 'Full pinned SHA required'; exit 1; }
current=/opt/vegas-social-os
releases=/opt/vegas-social-os-releases
[[ -L $current ]] || { echo 'Expected an atomic-release source symlink; existing layout retained'; exit 1; }
previous=$(readlink -f "$current")
interpreter="$previous/.venv/bin/python"
[[ -x $interpreter ]] || { echo 'Existing service interpreter missing'; exit 1; }
[[ $(systemctl show vegas-social-os.service -p User --value) == vegas-social ]] || exit 1
stage="$releases/flow-engine-$revision"
mkdir -p "$releases"
if [[ ! -d $stage ]]; then
  git clone --quiet --no-checkout https://github.com/AdityaAgarwal75/vegas-social-os.git "$stage"
  git -C "$stage" checkout --quiet --detach "$revision"
fi
[[ $(git -C "$stage" rev-parse HEAD) == "$revision" ]] || exit 1
[[ -z $(git -C "$stage" status --porcelain --untracked-files=no) ]] || exit 1
# Reuse installed locked dependencies; no live package upgrade needed for this release.
if [[ ! -e $stage/.venv ]]; then ln -s "$(readlink -f "$previous/.venv")" "$stage/.venv"; fi
cd "$stage"
runuser -u vegas-social -- env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/var/lib/vegas-social-os PYTHONDONTWRITEBYTECODE=1 "$interpreter" -m unittest discover -s tests -q > "$releases/flow-engine-$revision-tests.log" 2>&1
node --test tests/flow.test.mjs tests/hash.test.cjs > "$releases/flow-engine-$revision-node.log" 2>&1
node --check web/app.js
bash -n scripts/*.sh
# Private, safe receipt and existing media hashes; credentials never printed/copied.
checkpoint="/var/lib/vegas-social-os/deployment-checkpoints/$revision"
mkdir -p "$checkpoint"
chmod 700 /var/lib/vegas-social-os/deployment-checkpoints "$checkpoint"
export VSO_DEPLOY_CHECKPOINT="$checkpoint" VSO_DEPLOY_PREVIOUS="$previous" VSO_DEPLOY_REVISION="$revision"
"$interpreter" - <<'PY'
import hashlib,json,os
from pathlib import Path
root=Path('/var/lib/vegas-social-os');checkpoint=Path(os.environ['VSO_DEPLOY_CHECKPOINT'])
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'media').iterdir() if p.is_file()}
(checkpoint/'media-before.json').write_text(json.dumps(hashes))
(checkpoint/'receipt.json').write_text(json.dumps(dict(previous=os.environ['VSO_DEPLOY_PREVIOUS'],revision=os.environ['VSO_DEPLOY_REVISION'],state='staged')))
PY
switched=0
stopped=0
rollback(){
  result=$?
  if [[ $result -ne 0 && $stopped -eq 1 ]]; then
    if [[ $switched -eq 1 ]]; then
      ln -s "$previous" "$current.rollback"
      mv -Tf "$current.rollback" "$current"
    fi
    systemctl restart vegas-social-os.service
    echo 'Gateway source rolled back; original state and profiles retained'
  fi
  exit "$result"
}
trap rollback EXIT
stopped=1
systemctl stop vegas-social-os.service
# Consistent private SQLite backup after gateway shutdown. Never restore it automatically.
"$interpreter" - <<'PY'
import os,sqlite3
from pathlib import Path
source=sqlite3.connect('/var/lib/vegas-social-os/state.sqlite')
target=sqlite3.connect(Path(os.environ['VSO_DEPLOY_CHECKPOINT'])/'state-before.sqlite')
source.backup(target);target.close();source.close()
PY
ln -s "$stage" "$current.next"
mv -Tf "$current.next" "$current"
switched=1
systemctl start vegas-social-os.service
for attempt in $(seq 1 30); do
  if curl --fail --silent http://127.0.0.1:8899/health > "$checkpoint/health.json"; then break; fi
  sleep 1
done
"$interpreter" - <<'PY'
import hashlib,json,os,sqlite3,time,urllib.request
from pathlib import Path
checkpoint=Path(os.environ['VSO_DEPLOY_CHECKPOINT']);root=Path('/var/lib/vegas-social-os')
health=json.loads((checkpoint/'health.json').read_text());assert health['version']=='0.13.0'
conn=sqlite3.connect(root/'state.sqlite');assert conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
for _ in range(55):
    row=conn.execute("SELECT body FROM records WHERE kind='runtime' AND id='flow-controller'").fetchone()
    worker=json.loads(row[0]) if row else {}
    if worker.get('last_tick',0)>time.time()-120 and worker.get('state') in ('running','resource_paused'):break
    time.sleep(1)
else:raise RuntimeError('Controller heartbeat missing or unhealthy')
for name,digest in json.loads((checkpoint/'media-before.json').read_text()).items():
    assert hashlib.sha256((root/'media'/name).read_bytes()).hexdigest()==digest
for path in ('/login','/control.css','/app.js'):
    with urllib.request.urlopen('http://127.0.0.1:8899'+path,timeout=10) as response:assert response.status==200
try:urllib.request.urlopen('http://127.0.0.1:8899/api/control',timeout=10)
except urllib.error.HTTPError as error:assert error.code==401
else:raise RuntimeError('Unauthenticated API was not rejected')
receipt=json.loads((checkpoint/'receipt.json').read_text());receipt.update(state='deployed',verified_at=time.time(),controller=worker,original_media_preserved=True)
(checkpoint/'receipt.json').write_text(json.dumps(receipt,indent=2))
print('Pinned gateway/controller healthy; existing media, state and provider services retained')
PY
curl --fail --silent "$public_origin/health" > "$checkpoint/https-health.json"
trap - EXIT
