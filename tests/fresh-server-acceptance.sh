#!/usr/bin/env bash
# REAL install/upgrade/rollback acceptance. Run only in a disposable booted nspawn OS.
set -Eeuo pipefail
[[ "${VSO_ALLOW_DISPOSABLE_INSTALL:-}" = 1 ]] && [[ "$(systemd-detect-virt --container)" = systemd-nspawn ]] || { echo 'Refusing: this test requires an explicitly marked disposable systemd-nspawn OS.' >&2; exit 2; }
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOMAIN=fresh.example; PORT=19999
bash "$ROOT/scripts/install-vps.sh" --domain "$DOMAIN" --port "$PORT" --no-caddy
set -a; . /etc/vegas-social-os.env; set +a
KEY_BEFORE="$(sha256sum /var/lib/vegas-social-os/vault.key | cut -d' ' -f1)"
runuser -u vegas-social -- /opt/vegas-social-os/.venv/bin/python - <<'PY'
import sys
sys.path.insert(0,'/opt/vegas-social-os')
from vso.store import Store
s=Store('/var/lib/vegas-social-os');s.put('acceptance','preservation',{'synthetic':True,'must_survive_upgrade':True})
PY
bash "$ROOT/scripts/install-vps.sh" --domain "$DOMAIN" --port "$PORT" --no-caddy
[[ "$(sha256sum /var/lib/vegas-social-os/vault.key | cut -d' ' -f1)" = "$KEY_BEFORE" ]]
curl -fsS "http://127.0.0.1:$PORT/health"
[[ "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/api/state")" = 401 ]]
python3 - <<'PY'
import json,urllib.request
req=urllib.request.Request('http://127.0.0.1:19999/mcp',data=json.dumps({'jsonrpc':'2.0','id':1,'method':'tools/list'}).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(req) as r:assert any(t['name']=='doctor' for t in json.load(r)['result']['tools'])
PY
# Inject a runtime-only failure into a disposable SOURCE clone, not the installed release.
FIXTURE="$(mktemp -d /opt/vso-rollback-fixture-XXXXXX)"
cp -a "$ROOT/." "$FIXTURE/"
python3 - "$FIXTURE/vso/server.py" <<'PY'
import sys
from pathlib import Path
p=Path(sys.argv[1]);s=p.read_text().replace('        self.engine = engine','        raise RuntimeError("Disposable rollback acceptance failure")\n        self.engine = engine',1);p.write_text(s)
PY
PREVIOUS="$(readlink -f /opt/vegas-social-os)"
if bash "$FIXTURE/scripts/install-vps.sh" --domain "$DOMAIN" --port "$PORT" --no-caddy; then echo 'FAIL: deliberate unhealthy release was accepted'; exit 1; fi
[[ "$(readlink -f /opt/vegas-social-os)" = "$PREVIOUS" ]]
[[ "$(sha256sum /var/lib/vegas-social-os/vault.key | cut -d' ' -f1)" = "$KEY_BEFORE" ]]
for attempt in $(seq 1 20); do curl -fsS "http://127.0.0.1:$PORT/health" && break; sleep 1; done
runuser -u vegas-social -- /opt/vegas-social-os/.venv/bin/python - <<'PY'
import sys
sys.path.insert(0,'/opt/vegas-social-os')
from vso.store import Store
assert Store('/var/lib/vegas-social-os').get('acceptance','preservation')['must_survive_upgrade']
from vso.admin import call
assert 'memory' in call({'action':'metrics'})
PY
[[ "$(systemctl show -p User --value vegas-social-os.service)" = vegas-social ]]
[[ "$(stat -c '%U:%a' /var/lib/vegas-social-os/vault.key)" = vegas-social:600 ]]
systemctl is-active vegas-social-os.service vegas-social-admin.service
printf '\nPASS: real disposable OS install, reinstall, non-root service, private vault, SQLite preservation, broker, public discovery/private data, unhealthy-release rollback.\n'
printf 'Not covered: public DNS/TLS, Google login, real Web plugin OAuth, paid rendering or publication.\n'
