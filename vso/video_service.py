"""Durable model-explicit clips through the operator's existing local service."""
import base64
import json
import time
from pathlib import Path
from . import flow_service,flow_models

def settings(model,duration,resolution,aspect_ratio,max_credits):
    flow_models.validate(model,duration,resolution,aspect_ratio)
    if type(max_credits) is not int or not 0<=max_credits<=1000:raise ValueError('Credit ceiling must be 0–1000')
    return dict(model=model,duration=duration,resolution=resolution,aspect_ratio=aspect_ratio,max_credits=max_credits)

def validate_inputs(engine,options,first_frame_id='',last_frame_id='',reference_asset_ids=None):
    refs=reference_asset_ids or []
    if not isinstance(refs,list) or len(refs)>3 or len(set(refs))!=len(refs) or (refs and (first_frame_id or last_frame_id)):
        raise ValueError('Use up to three distinct references OR start/end frames')
    if last_frame_id and not first_frame_id:raise ValueError('An end frame requires a start frame')
    spec=flow_models.validate(options['model'],options['duration'],options['resolution'],options['aspect_ratio'])
    if refs and not spec['references']:raise ValueError('This model does not support reference ingredients')
    if refs and options['model'].startswith('Veo') and options['duration']!=8:
        raise ValueError('Veo ingredient videos require 8 seconds')
    for ident in [first_frame_id,last_frame_id,*refs]:
        if ident and not engine.store.get('asset',ident)['media_type'].startswith('image/'):
            raise ValueError('Frame/reference must be an imported image')

def submit(engine,account_id,prompt,options,first_frame_id='',last_frame_id='',reference_asset_ids=None):
    validate_inputs(engine,options,first_frame_id,last_frame_id,reference_asset_ids)
    _,config=flow_service.binding(engine,account_id)
    scene={'type':'video','prompt':prompt,**options,'variants':1,'retries':0,'download_quality':'original'}
    # Veo has fixed 720p output. The local service's resolution selector is
    # explicitly Omni-only; asking it to click 720p for Veo fails unnecessarily.
    if options['model'].startswith('Veo'):scene.pop('resolution')
    refs=reference_asset_ids or []
    if len(refs)>3 or (refs and (first_frame_id or last_frame_id)):raise ValueError('Use up to three references OR start/end frames')
    if last_frame_id and not first_frame_id:raise ValueError('An end frame requires a start frame')
    if refs and not flow_models.validate(options['model'],options['duration'],options['resolution'],options['aspect_ratio'])['references']:
        raise ValueError('This model does not support reference ingredients')
    def upload(ident):
        a=engine.store.get('asset',ident)
        if not a['media_type'].startswith('image/'):raise ValueError('Frame/reference must be an imported image')
        raw=engine.asset_path(ident).read_bytes()
        r=flow_service.request(config,'upload',raw=raw,query={'name':a['file']})
        if not isinstance(r.get('path'),str) or not Path(r['path']).is_absolute():raise ValueError('Reference upload could not be verified')
        return r['path']
    if first_frame_id:scene['first_frame']=upload(first_frame_id)
    if last_frame_id:scene['last_frame']=upload(last_frame_id)
    if refs:scene['reference_images']=[upload(i) for i in refs]
    status=flow_service.request(config,'status',{'detailed':False})
    if any(j.get('status') in ('queued','running') for j in status.get('jobs',[])):raise ValueError('Existing service is busy; no clip submitted')
    result=flow_service.request(config,'generate',{'project':'SocialOS-video-'+engine.store.digest(prompt+json.dumps(options))[:16],'scenes':[scene]})
    ids=[j['id'] for j in result.get('jobs',[])]
    if len(ids)!=1:raise ValueError('Expected one durable backend video job')
    return {'backend_job_ids':ids}

def poll(engine,account_id,worker):
    _,config=flow_service.binding(engine,account_id)
    result=flow_service.request(config,'wait',{'job_ids':worker['backend_job_ids'],'timeout_seconds':5})
    jobs=[j for j in result.get('jobs',[]) if j.get('id') in worker['backend_job_ids']]
    if len(jobs)!=1:raise ValueError('Original video job not found; do not regenerate')
    j=jobs[0]
    if j['status'] in ('queued','running'):return {'completed':False,'status':'processing'}
    if j['status']!='done':return {'completed':False,'status':'stopped' if 'max_credits' in str(j.get('error','')) else 'failed','error':str(j.get('error','Video failed'))[:500],'quoted_credits':j.get('credits')}
    files=[f for f in j.get('files',[]) if Path(f).suffix.lower()=='.mp4']
    if len(files)!=1:raise ValueError('No single exact MP4 download; recover without regenerating')
    raw=flow_service.request(config,'media',query={'path':files[0]},binary=True)
    asset=engine.asset_import(base64.b64encode(raw).decode(),'video/mp4')
    return {'completed':True,'status':'completed','asset_id':asset['id'],'quoted_credits':j.get('credits')}

def request(engine,account_id,prompt,model,duration,resolution,aspect_ratio,max_credits,request_id,first_frame_id='',last_frame_id='',reference_asset_ids=None):
    if not prompt.strip() or len(prompt)>12000 or not request_id or len(request_id)>200:raise ValueError('Prompt and stable request ID required')
    opts=settings(model,duration,resolution,aspect_ratio,max_credits)
    flow_models.validate_observed(engine,account_id,opts)
    validate_inputs(engine,opts,first_frame_id,last_frame_id,reference_asset_ids)
    a,_=flow_service.binding(engine,account_id)
    body=dict(account_id=account_id,prompt=prompt,**opts,first_frame_id=first_frame_id,last_frame_id=last_frame_id,reference_asset_ids=reference_asset_ids or [])
    ident=engine.store.digest('flow-video:'+request_id)[:32]
    with engine.store.db() as db:
        row=db.execute("SELECT body FROM records WHERE kind='video-job' AND id=?",(ident,)).fetchone()
        if row:
            old=json.loads(row[0])
            if any(old[k]!=v for k,v in body.items()):raise ValueError('Request ID belongs to a different clip')
            return {k:v for k,v in old.items() if k!='worker'}
        if a['status']!='workspace_ready':raise ValueError('Verify this Flow workspace before generation')
        for row in db.execute("SELECT body FROM records WHERE kind IN ('job','image-job','video-job')"):
            if json.loads(row[0])['status'] in ('submitting','processing','unknown'):raise ValueError('Finish or reconcile active browser work first')
        job={**body,'id':ident,'status':'submitting','created_at':time.time(),'asset_ids':[]}
        engine.store.write(db,'video-job',ident,job)
    try:job.update(status='processing',worker=submit(engine,account_id,prompt,opts,first_frame_id,last_frame_id,reference_asset_ids))
    except ValueError as e:job.update(status='unknown',error=str(e))
    engine.store.put('video-job',ident,job)
    return {k:v for k,v in job.items() if k!='worker'}

def check(engine,job_id):
    job=engine.store.get('video-job',job_id)
    if job['status']=='processing':
        result=poll(engine,job['account_id'],job['worker'])
        if result['completed']:job.update(status='completed',asset_ids=[result['asset_id']],quoted_credits=result['quoted_credits'])
        elif result['status'] in ('failed','stopped'):job.update(status=result['status'],error=result['error'],quoted_credits=result.get('quoted_credits'))
        engine.store.put('video-job',job_id,job)
    return {k:v for k,v in job.items() if k!='worker'}
