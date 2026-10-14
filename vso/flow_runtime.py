"""One complete installation-owned execution engine for each native profile.

Imported services retain their existing owner. Native sessions attach to the
Chrome launched by the app, never copy profiles or start a competing browser.
"""
import fcntl
import json
import os
import re
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from .net import NoRedirect


def configured():
    return bool(os.getenv('VSO_FLOW_ENGINE_ROOT'))


def installed():
    code = Path(os.getenv('VSO_FLOW_ENGINE_ROOT', '/not-installed'))
    return configured() and (code / '.vso-contract').is_file() and (code / 'dist/server.js').is_file()


def _alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _health(config):
    try:
        url = f"http://127.0.0.1:{config['port']}/api/health"
        with urllib.request.build_opener(NoRedirect).open(url, timeout=1) as response:
            return json.load(response).get('name') == 'flow-mcp'
    except Exception:
        return False


def ensure(engine, account_id):
    if not re.fullmatch(r'[a-f0-9]{32}', account_id):
        raise ValueError('Invalid managed Flow profile')
    account = engine.store.get('account', account_id)
    if account['provider'] != 'flow' or account.get('service_alias'):
        raise ValueError('Select an app-owned Flow profile')
    code = Path(os.getenv('VSO_FLOW_ENGINE_ROOT', '/not-installed'))
    if not installed():
        raise ValueError('Complete Flow engine missing; setup agent must run scripts/install-flow-engine.sh')
    root = engine.store.root / 'profiles' / account_id
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (root / 'engine.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            browser = json.loads((root / 'browser.json').read_text())
            cdp = browser['port']
            if type(cdp) is not int or not 1024 <= cdp <= 65535:
                raise ValueError('Invalid private browser port')
            args = Path(f"/proc/{browser['pid']}/cmdline").read_bytes().split(b'\0')
            if (f'--user-data-dir={root / "profile"}'.encode() not in args or
                    f'--remote-debugging-port={cdp}'.encode() not in args):
                raise ValueError('Saved browser belongs to another process/profile')
            with urllib.request.build_opener(NoRedirect).open(f'http://127.0.0.1:{cdp}/json/version', timeout=2) as response:
                json.load(response)
        except (OSError, KeyError, ValueError):
            raise ValueError('Open and verify this account’s private Google browser first; no second Chrome was launched') from None
        config_file = root / 'engine.json'
        if config_file.exists():
            saved = json.loads(config_file.read_text())
            # Reject a PID reused by an unrelated process.
            try:
                cmdline = Path(f"/proc/{saved['pid']}/cmdline").read_bytes().split(b'\0')
                own_process = str(Path(__file__).resolve().parents[1] / 'worker/service.mjs').encode() in cmdline
            except OSError:
                own_process = False
            if _alive(saved['pid']) and own_process:
                if saved.get('cdp_port') != cdp:
                    raise ValueError('Browser changed while the original engine is running; reconcile its queue before reconnecting')
                if _health(saved):
                    return saved
                raise ValueError('Original managed engine is unavailable; preserve its queue and inspect before restarting')
        home = root / 'engine'
        home.mkdir(exist_ok=True, mode=0o700)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        env = {**os.environ, 'VSO_FLOW_ATTACH_ONLY': '1', 'FLOW_MCP_HOME': str(home),
               'FLOW_MCP_OUTPUT': str(home / 'outputs'), 'FLOW_MCP_CDP_PORT': str(cdp), 'FLOW_MCP_PORT': str(port)}
        launcher = Path(__file__).resolve().parents[1] / 'worker/service.mjs'
        with (home / 'service.log').open('ab') as log:
            child = subprocess.Popen(['node', str(launcher)], env=env, stdout=log, stderr=log, start_new_session=True)
        saved = {'port': port, 'pid': child.pid, 'cdp_port': cdp, 'token_file': str(home / 'token')}
        config_file.write_text(json.dumps(saved));config_file.chmod(0o600)
        for _ in range(40):
            if child.poll() is not None:
                raise ValueError('Managed Flow engine failed to start; inspect its private service log')
            if _health(saved) and Path(saved['token_file']).exists():
                return saved
            time.sleep(0.1)
        raise ValueError('Managed engine startup uncertain; inspect original process, do not launch another')
