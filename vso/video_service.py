"""Durable model-explicit clips through the operator's existing local service."""
import base64
import json
import time
from pathlib import Path
from . import flow_service,flow_models

class NotSubmitted(ValueError):
    """Provider generation was never called; safe terminal admission failure."""

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

def submit(engine,account_id,prompt,options,first_frame_id='',last_frame_id='',reference_asset_ids=None,submission_id=''):
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
    if any(j.get('status') in ('queued','running') for j in status.get('jobs',[])):raise NotSubmitted('Existing service is busy; no clip submitted')
    # Every intentional take needs its own output directory, even if prompt,
    # model and settings are identical to an earlier completed request.
    if not submission_id:
        import uuid
        submission_id=uuid.uuid4().hex
    result=flow_service.request(config,'generate',{'project':'SocialOS-video-'+engine.store.digest(submission_id)[:24],'scenes':[scene]})
    ids=[j['id'] for j in result.get('jobs',[])]
    if len(ids)!=1:raise ValueError('Expected one durable backend video job')
    return {'backend_job_ids':ids,'project':result.get('output_dir'),'expected':options}

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
    from .media import probe
    evidence=probe(engine.asset_path(asset['id']),'video/mp4')
    if float(evidence.get('duration') or 0)<=0:raise ValueError('Downloaded clip has no valid duration; recover original output')
    expected=worker.get('expected',{})
    stream=next(s for s in evidence['streams'] if s.get('codec_type')=='video')
    if expected.get('duration') and abs(float(evidence['duration'])-expected['duration'])>max(1,expected['duration']*0.15):raise ValueError('Original output duration differs from the requested clip; review without regeneration')
    if expected.get('aspect_ratio'):
        w,h=map(int,expected['aspect_ratio'].split(':'))
        if abs(stream['width']/stream['height']-w/h)>0.07:raise ValueError('Original output aspect differs from the request; review without regeneration')
    asset.update(technical_verification=evidence,verified_at=time.time())
    engine.store.put('asset',asset['id'],asset)
    return {'completed':True,'status':'completed','asset_id':asset['id'],'quoted_credits':j.get('credits')}

def request(engine,account_id,prompt,model,duration,resolution,aspect_ratio,max_credits,request_id,first_frame_id='',last_frame_id='',reference_asset_ids=None,project_id=''):
    if not prompt.strip() or len(prompt)>12000 or not request_id or len(request_id)>200:raise ValueError('Prompt and stable request ID required')
    opts=settings(model,duration,resolution,aspect_ratio,max_credits)
    flow_models.validate_observed(engine,account_id,opts)
    validate_inputs(engine,opts,first_frame_id,last_frame_id,reference_asset_ids)
    from .projects import prepare_job
    try:prior=engine.store.get('video-job',engine.store.digest('flow-video:'+request_id)[:32])
    except ValueError:prior=None
    if prior and not project_id:project_id=prior.get('project_id','')
    project_id=prepare_job(engine,project_id,'Video · '+prompt.strip()[:80],'flow-video:'+request_id) if not prior else project_id
    a,_=flow_service.binding(engine,account_id)
    body=dict(account_id=account_id,prompt=prompt,**opts,first_frame_id=first_frame_id,last_frame_id=last_frame_id,reference_asset_ids=reference_asset_ids or [])
    ident=engine.store.digest('flow-video:'+request_id)[:32]
    with engine.store.db() as db:
        row=db.execute("SELECT body FROM records WHERE kind='video-job' AND id=?",(ident,)).fetchone()
        if row:
            old=json.loads(row[0])
            if any(old[k]!=v for k,v in body.items()) or (project_id and old.get('project_id')!=project_id):raise ValueError('Request ID belongs to a different clip or project')
            return {k:v for k,v in old.items() if k!='worker'}
        if a['status']!='workspace_ready':raise ValueError('Verify this Flow workspace before generation')
        from .flow_controller import assert_idle
        assert_idle(db,a if 'id' in a else {**a,'id':account_id})
        from .flow_controller import assert_daily_budget
        assert_daily_budget(db,account_id,opts['max_credits'])
        job={**body,'project_id':project_id,'id':ident,'input_sha256':engine.store.digest(json.dumps(body,sort_keys=True)),'flow_project_url':a.get('project_url'),'status':'submitting','created_at':time.time(),'asset_ids':[]}
        engine.store.write(db,'video-job',ident,job)
    try:job.update(status='processing',worker=submit(engine,account_id,prompt,opts,first_frame_id,last_frame_id,reference_asset_ids,submission_id=ident))
    except NotSubmitted as e:job.update(status='blocked',error=str(e))
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


def locate(engine,job):
    _,config=flow_service.binding(engine,job['account_id']);view=flow_service.request(config,'status',{'detailed':True})
    ids=job.get('worker',{}).get('backend_job_ids',[])
    project='SocialOS-video-'+engine.store.digest(job['id'])[:24]
    matches=[j for j in view.get('jobs',[]) if j.get('id') in ids] if ids else [j for j in view.get('jobs',[]) if Path(j.get('project','')).name==project]
    if len(matches)!=1:raise ValueError('Cannot identify one original backend job; preserve unknown state and inspect the exact project. Never resubmit.')
    return config,matches[0]


def reconcile(engine,job_id):
    try:job=engine.store.get('video-job',job_id);kind='video-job'
    except ValueError:job=engine.store.get('job',job_id);kind='job'
    if job['status'] in ('completed','stopped','failed','cancelled'):return {k:v for k,v in job.items() if k!='worker'}
    try:
        _,original=locate(engine,job)
    except ValueError as error:return {**{k:v for k,v in job.items() if k!='worker'},'reconciliation':str(error),'safe_to_resubmit':False}
    job.update(worker={**job.get('worker',{}),'backend_job_ids':[original['id']]},backend_project=original.get('project'),status='processing');engine.store.put(kind,job_id,job)
    return check(engine,job_id) if kind=='video-job' else engine.video_poll(job_id)


def cancel(engine,job_id):
    try:job=engine.store.get('video-job',job_id);kind='video-job'
    except ValueError:job=engine.store.get('job',job_id);kind='job'
    if job['status']=='cancelled':return {k:v for k,v in job.items() if k!='worker'}
    config,original=locate(engine,job)
    if original['status']!='queued':return {'id':job_id,'cancelled':False,'provider_status':original['status'],'reason':'Pinned engine only cancels locally queued jobs. Active provider generation cancellation is not supported; reconcile the original output.'}
    result=flow_service.request(config,'cancel',{'job_id':original['id']})
    if result.get('status')=='cancelled':job.update(status='cancelled',cancelled_at=time.time());engine.store.put(kind,job_id,job)
    return {'id':job_id,'cancelled':result.get('status')=='cancelled','provider_status':result.get('status'),'credit_reservation_retained':True}
