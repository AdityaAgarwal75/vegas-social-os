"""Model choices with provenance; live availability is separate from documentation."""
import json
import subprocess
import time
from pathlib import Path

SOURCE='https://support.google.com/flow/answer/16352836?hl=en'
VIDEO=[{'name':n,'durations':[4,6,8,10] if n.startswith('Omni') else [4,6,8],
        'resolutions':['360p','720p'] if n.startswith('Omni') else ['720p'],
        'references':not n.endswith('Quality'),'extend':n.endswith('Lite'),'editing':n.startswith('Omni')}
       for n in ['Omni 1.1 Flash','Veo 3.1 - Lite','Veo 3.1 - Fast','Veo 3.1 - Quality']]
IMAGE=[{'name':n} for n in ['Nano Banana Pro','Nano Banana 2 Lite','Nano Banana 2.1']]

def catalog(engine,account_id=''):
    observed=None
    if account_id:
        engine.store.get('account',account_id)
        try:observed=engine.store.get('flow-models',account_id)
        except ValueError:pass
    fresh=bool(observed and time.time()-observed['observed_at']<1800)
    result={'source':SOURCE,'documented_on':'2026-10-13','observed_at':observed.get('observed_at') if observed else None,'live_verified':fresh}
    for kind,models in [('video',VIDEO),('image',IMAGE)]:
        labels=observed.get(kind,[]) if fresh else []
        result[kind]=[{**m,'availability':'observed' if m['name'] in labels else 'unavailable' if fresh else 'check_in_flow'} for m in models]
        result[kind]+=[{'name':n,'availability':'observed','durations':[],'resolutions':[],'note':'New live model; settings must be inspected before use'} for n in labels if n not in {m['name'] for m in models}]
    return result

def refresh(engine,account_id):
    from .flow_service import binding
    a=engine.store.get('account',account_id)
    if a['provider']!='flow':raise ValueError('Choose a Flow account')
    if a.get('service_alias'):
        _,config=binding(engine,account_id);port=config.get('cdp_port')
    else:
        try:port=json.loads((engine.store.root/'profiles'/account_id/'browser.json').read_text())['port']
        except (OSError,KeyError,json.JSONDecodeError):raise ValueError('Open this account’s Google browser first') from None
    if type(port) is not int or not 1024<=port<=65535:raise ValueError('Setup agent must configure this service’s private CDP port for model discovery')
    for kind in ['job','image-job','video-job']:
        if any(j['status'] in ('submitting','processing','unknown','preparing') for j in engine.store.all(kind)):
            raise ValueError('Finish or reconcile active browser work before refreshing model menus')
    worker=Path(__file__).parent.parent/'worker/models.mjs'
    try:
        r=subprocess.run(['node',str(worker),str(port)],capture_output=True,text=True,timeout=35)
        result=json.loads(r.stdout)
        if r.returncode or result.get('error'):raise ValueError('Flow model discovery unavailable; inspect the private browser')
    except (subprocess.TimeoutExpired,json.JSONDecodeError):raise ValueError('Model discovery interrupted; no generation submitted') from None
    engine.store.put('flow-models',account_id,{**result,'observed_at':time.time()})
    return catalog(engine,account_id)

def validate(model,duration,resolution,aspect_ratio):
    spec=next((m for m in VIDEO if m['name']==model),None)
    if not spec:raise ValueError('Choose an explicitly supported video model')
    if type(duration) is not int or duration not in spec['durations'] or resolution not in spec['resolutions'] or aspect_ratio not in ('9:16','16:9'):
        raise ValueError('This model does not support the chosen duration, resolution or aspect ratio')
    return spec
