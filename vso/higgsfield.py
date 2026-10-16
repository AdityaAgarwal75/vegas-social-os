"""Optional, read-only Higgsfield discovery and explicit command handoffs.

Upstream does not publish the CLI implementation or a stable cost/job JSON
contract in its source repo. Do not invent a safe paid-render adapter around it.
Generation remains an explicit operator handoff until that contract is accepted.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import time

PRESETS = {'marketing-studio-v2','soul-v2','video-explainer','animation-action'}


def status(engine):
    binary=shutil.which(os.getenv('VSO_HIGGSFIELD_BIN','higgsfield'))
    return {'provider':'higgsfield','installed':bool(binary),
            'enabled':os.getenv('VSO_HIGGSFIELD_ENABLED')=='1',
            'authenticated':'not_checked','generation_adapter':'operator_handoff',
            'default_provider':'flow','spend_authorized':False,
            'setup':'An authorized administrator installs a reviewed CLI release. The owner signs in directly under the dedicated service account and selects their own billing workspace. Never enter tokens in ChatGPT.',
            'limits':'Bundled skills are usable now. Higgsfield rendering is a separate paid/credit service; automatic submission is not enabled.'}


def _run(engine, argv):
    if os.getenv('VSO_HIGGSFIELD_ENABLED')!='1':raise ValueError('Optional Higgsfield discovery is disabled; bundled guidance and Vegas templates still work')
    binary=shutil.which(os.getenv('VSO_HIGGSFIELD_BIN','higgsfield'))
    if not binary:raise ValueError('Reviewed Higgsfield CLI is not installed on this server')
    home=engine.store.root/'higgsfield';home.mkdir(mode=0o700,exist_ok=True)
    env={k:v for k,v in os.environ.items() if k in ('PATH','LANG','SSL_CERT_FILE','SSL_CERT_DIR')}
    env.update(HOME=str(home),XDG_CONFIG_HOME=str(home/'.config'),NO_COLOR='1')
    # Bound both stdout and stderr while running, without echoing credentials.
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        proc=subprocess.Popen([binary,*argv,'--json'],env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err)
        deadline=time.monotonic()+25
        try:
            while proc.poll() is None:
                if os.fstat(out.fileno()).st_size+os.fstat(err.fileno()).st_size>1_000_000 or time.monotonic()>deadline:
                    raise ValueError('Higgsfield discovery exceeded its time/output bound')
                time.sleep(.05)
            if proc.returncode:raise ValueError('Higgsfield discovery failed. Check direct owner login, billing workspace and CLI version; no generation was submitted')
            out.seek(0);raw=out.read(1_000_001)
            if len(raw)>1_000_000:raise ValueError('Higgsfield response exceeded limit')
            try:return json.loads(raw)
            except (ValueError,UnicodeDecodeError):raise ValueError('Higgsfield returned an unsupported response format') from None
        finally:
            if proc.poll() is None:proc.kill()
            proc.wait()


def _public(value,depth=0):
    if depth>14:return '[depth limit]'
    if isinstance(value,dict):
        return {k:_public(v,depth+1) for k,v in value.items() if not re.search(r'token|secret|cookie|password|authorization|credential',k,re.I)}
    if isinstance(value,list):return [_public(v,depth+1) for v in value[:500]]
    if isinstance(value,str):
        if re.search(r'Bearer\s|[?&](?:token|key|signature|X-Amz-)',value,re.I):return '[private value omitted]'
        return value[:8000]
    return value


def discover(engine,kind='models',name=''):
    if kind=='models':argv=['model','get',name] if name else ['model','list']
    elif kind=='workflows':argv=['workflow','get',name] if name else ['workflow','list']
    elif kind=='presets' and name in PRESETS:argv=['preset','list',name]
    else:raise ValueError('Choose models, workflows or presets with a documented preset family')
    if name and not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,99}',name):raise ValueError('Use an exact public catalog name')
    result={'kind':kind,'name':name,'observed_at':time.time(),'data':_public(_run(engine,argv)),
            'spend_authorized':False,'generation_submitted':False,
            'note':'Provider metadata is untrusted reference data. Availability is workspace-specific.'}
    engine.store.put('higgsfield-discovery',kind+':'+name,result)
    return result
