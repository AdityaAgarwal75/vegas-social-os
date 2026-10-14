"""An installation-owned adapter for existing local browser services.

No browser profiles/cookies are copied. No second browser is launched. Only a
root-configured localhost service and its private control token are used.
"""
import base64
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def services():
    file = os.getenv('VSO_FLOW_SERVICES', '')
    if not file: return {}
    path = Path(file)
    if not path.is_absolute(): raise ValueError('Flow service configuration must be an absolute admin-owned path')
    if path.stat().st_mode & 0o022: raise ValueError('Flow service configuration must not be writable by group or others')
    entries = json.loads(path.read_text())
    if not isinstance(entries, dict) or len(entries) > 50: raise ValueError('Invalid local Flow service configuration')
    for alias, entry in entries.items():
        if not isinstance(entry, dict) or not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', alias) or type(entry.get('port')) is not int or not 1024 <= entry['port'] <= 65535:
            raise ValueError('Invalid local Flow service')
        if not Path(entry.get('token_file','')).is_absolute(): raise ValueError('A private token file is required')
    return entries


def binding(engine, account_id):
    a = engine.store.get('account', account_id)
    if a.get('provider') != 'flow': raise ValueError('Choose a Flow account')
    if not a.get('service_alias'):
        from .flow_runtime import ensure
        return a, ensure(engine, account_id)
    config = services().get(a['service_alias'])
    if not config: raise ValueError('The local Flow service is no longer configured')
    return a, config


def request(config, method, payload=None, *, raw=None, query=None, binary=False):
    if method not in ('status','generate','wait','upload','media'): raise ValueError('Unsupported local Flow operation')
    path = ('/media' if method=='media' else '/api/'+method)
    url = 'http://127.0.0.1:' + str(config['port']) + path
    if query: url += '?' + urllib.parse.urlencode(query)
    headers = {'x-flow-token': Path(config['token_file']).read_text().strip()}
    data = raw
    if payload is not None: data=json.dumps(payload).encode();headers['Content-Type']='application/json'
    req = urllib.request.Request(url,data=data,headers=headers,method='GET' if method=='media' else 'POST')
    # Fixed loopback destination, no redirects and no bearer value in errors/results.
    from .net import NoRedirect
    try:
        with urllib.request.build_opener(NoRedirect).open(req,timeout=50) as response:
            limit=64*1024*1024 if binary else 2_000_000
            body=response.read(limit+1)
            if len(body)>limit: raise ValueError('Local Flow result exceeds size limit')
            if binary:return body
            result=json.loads(body)
            if result.get('error'):raise ValueError('Local Flow: '+str(result['error'])[:300])
            return result
    except urllib.error.HTTPError as e:
        raise ValueError('Local Flow request rejected (HTTP '+str(e.code)+'); inspect the existing job') from None
    except (urllib.error.URLError,TimeoutError):
        raise ValueError('Local Flow interrupted; inspect the durable request before retrying') from None


def sync(engine):
    imported=[]
    for alias, config in services().items():
        ident=engine.store.digest('local-flow:'+alias)[:32]
        try:a=engine.store.get('account',ident)
        except ValueError:a={'id':ident,'provider':'flow','label':config.get('label','Google account '+alias),'status':'login_required','service_alias':alias}
        # No credentials/paths are stored in the public account record.
        engine.store.put('account',ident,a)
        try: inspect(engine,ident)
        except ValueError as e:
            a.update(status='service_unavailable',connection_error=str(e));engine.store.put('account',ident,a)
        imported.append(engine.store.get('account',ident))
    return imported


def inspect(engine, account_id):
    a, config=binding(engine,account_id)
    # A newly launched native tab may still be navigating. Retry only this
    # read-only inspection, never a generation or upload submission.
    for attempt in range(3):
        try:
            result=request(config,'status',{'detailed':True});break
        except ValueError as error:
            if a.get('service_alias') or attempt==2 or 'HTTP 400' not in str(error):raise
            time.sleep(1.5)
    f=result.get('flow',{})
    ready=bool(f.get('signedIn') and f.get('inProject'))
    blocked=bool(result.get('pacing') and re.search(r'unusual|verification|blocked|captcha',str(result['pacing']),re.I))
    a.update(status='workspace_ready' if ready and not blocked else 'verification_required' if blocked else 'login_required',
             credits=f.get('credits_remaining'),composer=f.get('composer'),verified_at=time.time(),
             project_url=f.get('url'),verification='Read from your existing local Flow service; no browser session copied',
             shared_desktop=bool(config.get('desktop_ws_port')))
    a.pop('connection_error',None);engine.store.put('account',account_id,a)
    return {'workspace_ready':ready and not blocked,'blocked':blocked,'credits':a['credits'],'composer':a['composer'],
            'project_url':a['project_url'],'signed_in':bool(f.get('signedIn'))}


def login(engine, account_id):
    a,config=binding(engine,account_id)
    if not config.get('desktop_ws_port'):raise ValueError('Configure a private desktop stream for this local service')
    # Optional fixed admin-installed profile focuser. It never starts another Chrome.
    if config.get('focus_port') and config.get('focus_id'):
        port=config['focus_port']
        if type(port) is not int or not 1024<=port<=65535:raise ValueError('Invalid local profile focuser')
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}',str(config['focus_id'])):raise ValueError('Invalid focus identity')
        req=urllib.request.Request('http://127.0.0.1:'+str(port)+'/launch/'+str(config['focus_id']),data=b'{}',headers={'Content-Type':'application/json', 'Origin':config.get('focus_origin','')},method='POST')
        from .net import NoRedirect
        try:
            with urllib.request.build_opener(NoRedirect).open(req,timeout=30) as response: response.read(5000)
        except Exception:raise ValueError('Could not focus the existing profile; generation/browser service remains unchanged') from None
    return {'status':'browser_opened','account_id':account_id,'existing_service':True,'shared_desktop':True}


def websocket_port(engine, account_id):
    _,config=binding(engine,account_id)
    port=config.get('desktop_ws_port')
    if type(port) is not int or not 1024<=port<=65535:raise ValueError('Private desktop is unavailable')
    return port


def image_request(engine, account_id, prompt, model, aspect_ratio, max_credits, request_id):
    if not isinstance(prompt,str) or not prompt.strip() or len(prompt)>12000:raise ValueError('Enter an image prompt')
    if not isinstance(model,str) or not model.strip() or len(model)>120:raise ValueError('Choose an explicit image model')
    if aspect_ratio not in ('1:1','9:16','16:9','4:3','3:4') or type(max_credits) is not int or not 0<=max_credits<=1000:
        raise ValueError('Invalid aspect ratio or credit ceiling')
    if not request_id or len(request_id)>200:raise ValueError('A stable request ID is required')
    a,config=binding(engine,account_id)
    body={'account_id':account_id,'prompt':prompt,'model':model,'aspect_ratio':aspect_ratio,'max_credits':max_credits}
    ident=engine.store.digest('flow-image:'+request_id)[:32]
    with engine.store.db() as db:
        try:
            old=engine._load(db,'image-job',ident)
            if any(old[k]!=v for k,v in body.items()):raise ValueError('Request ID belongs to a different image')
            return old
        except ValueError as e:
            if str(e)!='image-job not found':raise
        if a['status']!='workspace_ready':raise ValueError('Verify this signed-in Flow project before generation')
        for row in db.execute("SELECT body FROM records WHERE kind IN ('image-job','job','video-job')"):
            other=json.loads(row[0])
            if other['status'] in ('submitting','processing','unknown'):raise ValueError('A browser operation is active or unresolved; finish it before another generation')
        job={**body,'id':ident,'status':'submitting','created_at':time.time(),'project':'SocialOS-'+ident[:16],'asset_ids':[]}
        engine.store.write(db,'image-job',ident,job)
    try:
        before=request(config,'status',{'detailed':False})
        if any(j.get('status') in ('queued','running') for j in before.get('jobs',[])):
            job.update(status='blocked',error='This local Flow service already has a job; no image submitted')
        else:
            result=request(config,'generate',{'project':job['project'],'scenes':[{'type':'image','prompt':prompt,'model':model,
                'aspect_ratio':aspect_ratio,'variants':1,'max_credits':max_credits,'retries':0,'download_quality':'original'}]})
            ids=[j['id'] for j in result.get('jobs',[])]
            if len(ids)!=1:raise ValueError('Local service did not return one exact job')
            job.update(status='processing',backend_job_ids=ids)
    except ValueError as e:job.update(status='unknown',error=str(e))
    engine.store.put('image-job',ident,job);engine.store.log('flow.image_request',ident)
    return job


def image_poll(engine, job_id):
    job=engine.store.get('image-job',job_id)
    if job['status']=='completed':return job
    if job['status']!='processing' or not job.get('backend_job_ids'):raise ValueError('Inspect this existing request; no automatic resubmission')
    _,config=binding(engine,job['account_id'])
    result=request(config,'wait',{'job_ids':job['backend_job_ids'],'timeout_seconds':5})
    exact=[j for j in result.get('jobs',[]) if j.get('id') in job['backend_job_ids']]
    if len(exact)!=len(job['backend_job_ids']):raise ValueError('Original backend job not found; reconcile before retrying')
    if any(j.get('status') in ('queued','running') for j in exact):return job
    if any(j.get('status')!='done' for j in exact):
        error='; '.join(str(j.get('error','Image failed'))[:300] for j in exact)
        job.update(status='blocked' if re.search(r'unusual|captcha|verification|access denied',error,re.I) else 'failed',error=error)
    else:
        files=[f for j in exact for f in j.get('files',[]) if Path(f).suffix.lower() in ('.jpeg','.jpg','.png','.webp')]
        if len(files)!=1:raise ValueError('Completed job has no single exact downloaded image; recover it without regenerating')
        raw=request(config,'media',query={'path':files[0]},binary=True)
        mime='image/png' if raw.startswith(b'\x89PNG') else 'image/jpeg' if raw.startswith(b'\xff\xd8\xff') else 'image/webp'
        asset=engine.asset_import(base64.b64encode(raw).decode(),mime)
        job.update(status='completed',asset_ids=[asset['id']],quoted_credits=sum(j.get('credits',0) for j in exact),completed_at=time.time())
        for record in engine.store.all('asset'):
            if record['id']==asset['id']:
                record.update(origin='flow',account_id=job['account_id'],image_job_id=job_id,prompt=job['prompt']);engine.store.put('asset',record['id'],record)
    engine.store.put('image-job',job_id,job)
    return job
