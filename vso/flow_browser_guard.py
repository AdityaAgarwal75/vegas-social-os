"""Keep only the minimum browser tabs in an isolated Vegas Flow profile.

This never accesses credentials or cookies, never starts a browser, and never
touches an arbitrary user Chrome profile. Google authentication is exempt so
a user can finish interactive login and 2FA.
"""
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from .net import NoRedirect


def classify(url):
    try:
        parsed = urllib.parse.urlsplit(url)
    except (TypeError, ValueError):
        return 'other'
    if parsed.scheme != 'https':
        return 'other'
    if parsed.hostname in ('flow.google.com', 'labs.google'):
        return 'flow'
    if parsed.hostname in ('accounts.google.com',):
        return 'authentication'
    return 'other'


def allowed_targets(targets):
    """Return target IDs to close; preserve an existing project and sign-in."""
    pages = [t for t in targets if t.get('type') == 'page' and
             isinstance(t.get('id'), str) and re.fullmatch(r'[0-9A-Fa-f-]{8,80}', t['id'])]
    flow = [t for t in pages if classify(t.get('url')) == 'flow']
    authenticating = [t for t in pages if classify(t.get('url')) == 'authentication']
    # The user may be in a Google password/2FA flow. Never interrupt it.
    keep = {t['id'] for t in authenticating}
    if flow:
        primary = next((t for t in flow if '/project/' in urllib.parse.urlsplit(t.get('url', '')).path), flow[0])
        keep.add(primary['id'])
    if not keep and pages:
        # Keep the initial blank tab while Chrome navigates to Flow.
        keep.add(pages[0]['id'])
    return [t['id'] for t in pages if t['id'] not in keep]


def cleanup(root, account_id):
    """Close unrelated/duplicate tabs in one *owned* idle native profile."""
    if not isinstance(account_id, str) or not re.fullmatch(r'[a-f0-9]{32}', account_id):
        raise ValueError('Invalid owned Flow account')
    profile_root = Path(root) / 'profiles' / account_id
    data = json.loads((profile_root / 'browser.json').read_text())
    port, pid = data.get('port'), data.get('pid')
    if type(port) is not int or not 1024 <= port <= 65535 or type(pid) is not int or pid < 1:
        raise ValueError('Invalid owned browser')
    cmdline = Path('/proc') / str(pid) / 'cmdline'
    argv = cmdline.read_bytes().split(b'\0')
    if (f'--user-data-dir={profile_root / "profile"}'.encode() not in argv or
            f'--remote-debugging-port={port}'.encode() not in argv):
        raise ValueError('Browser process ownership changed; not closing tabs')
    opener = urllib.request.build_opener(NoRedirect)
    base = f'http://127.0.0.1:{port}'
    with opener.open(base + '/json/list', timeout=1.5) as response:
        pages = json.load(response)
    if not isinstance(pages, list):
        raise ValueError('Unexpected browser target list')
    closed = 0
    for ident in allowed_targets(pages):
        with opener.open(base + '/json/close/' + ident, timeout=1.5) as response:
            response.read(256)
        closed += 1
    return {'closed': closed}
