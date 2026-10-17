"""Observable specialist tool runs, not invented independent model workers."""
import threading
import time
import uuid

_REPORT_LOCK=threading.Lock()

ROLES=[('strategist','Strategy','Audience, research and content planning','ST'),('writer','Scripts & hooks','Reel scripts, story arcs and repurposing','WR'),('caption','Captions & copy','Captions, carousels and writing review','CP'),('producer','Production','Scene media, Flow generation and editing','PR'),('publisher','Publishing','Reviewed releases and scheduling','PB'),('operator','Operations','Workspace, connections and infrastructure','OP')]
SKIP={'flow_engine_status','flow_batch_status','template_catalog','higgsfield_status','doctor','guide','get_profile','onboarding_status','account_list','channel_list','plan_list','job_list','publication_list','flow_model_catalog','workflow_audit','connection_setup','control_snapshot','project_list','project_detail','activity_report','event_status','automation_status','review_queue','studio_catalog','studio_queue','analytics_summary','admin_metrics','admin_inventory','project_attach_asset'}

def role_for(name):
    if name in SKIP:return None
    if any(x in name for x in ('caption','copycheck','carousel','story_sequence','engagement_triage')):return 'caption'
    if any(x in name for x in ('strategy','research','content_','studio_brief','studio_draft','studio_select','plan_save','channel_','brief_complete')):return 'strategist'
    if any(x in name for x in ('reel_review','quality','repurpose','outliers','profile_audit')):return 'writer'
    if name.startswith(('post_','publish_')):return 'publisher'
    if name.startswith(('template_','higgsfield_','skill_reference','flow_','image_','video_','media_','asset_','continuity','edit_','storyboard_','images_','concept_')):return 'producer'
    return 'operator'

def start(engine,role,label,project_id='',source='tool',tool=''):
    if role not in {r[0] for r in ROLES}:raise ValueError('Choose an available specialist role')
    if not isinstance(label,str) or not label.strip() or len(label)>160:raise ValueError('Activity label must be 1–160 characters')
    if project_id:engine.store.get('project',project_id)
    ident=uuid.uuid4().hex;now=time.time()
    body={'id':ident,'role':role,'label':label,'project_id':project_id,'source':source,'tool':tool,'status':'running','started_at':now,'updated_at':now,'expires_at':now+300}
    engine.store.put('agent-run',ident,body)
    with engine.store.db() as db:
        db.execute("DELETE FROM records WHERE kind='agent-run' AND id NOT IN (SELECT id FROM records WHERE kind='agent-run' ORDER BY json_extract(body,'$.started_at') DESC LIMIT 1000)")
    return body

def finish(engine,ident,status='completed'):
    record=engine.store.get('agent-run',ident);record.update(status=status,updated_at=time.time(),ended_at=time.time());engine.store.put('agent-run',ident,record);return record

def report(engine,role,label,request_id,status='running',project_id=''):
    with _REPORT_LOCK:return _report(engine,role,label,request_id,status,project_id)

def _report(engine,role,label,request_id,status='running',project_id=''):
    if status not in ('running','completed','failed'):raise ValueError('Choose running, completed or failed')
    if not isinstance(request_id,str) or not request_id or len(request_id)>200:raise ValueError('Stable activity request ID required')
    key=engine.store.digest('activity:'+request_id)[:32]
    try:
        record=engine.store.get('activity-link',key);run=engine.store.get('agent-run',record['run_id'])
        if (run['role'],run['label'],run['project_id'])!=(role,label,project_id):raise ValueError('Activity request ID already used')
        if run['status'] in ('completed','failed'):return run
    except ValueError as e:
        if 'not found' not in str(e):raise
        run=start(engine,role,label,project_id,'host');engine.store.put('activity-link',key,{'run_id':run['id']})
    if status=='running':
        run.update(updated_at=time.time(),expires_at=time.time()+300);engine.store.put('agent-run',run['id'],run);return run
    return finish(engine,run['id'],status)

def snapshot(engine):
    now=time.time();runs=sorted(engine.store.all('agent-run'),key=lambda x:x['started_at'],reverse=True)
    for run in runs:
        if run['status']=='running' and run['expires_at']<now:run['status']='unconfirmed'
    roles=[]
    for ident,name,description,initials in ROLES:
        own=[r for r in runs if r['role']==ident];running=[r for r in own if r['status']=='running']
        roles.append({'id':ident,'name':name,'description':description,'initials':initials,'status':'running' if running else 'idle','active':running[:3],'latest':own[0] if own else None,'today':sum(r['started_at']>now-86400 for r in own)})
    return {'roles':roles,'runs':runs[:80],'running':sum(r['status']=='running' for r in runs),'mode':'ChatGPT-led specialist tools; host-only work requires explicit activity reporting.'}
