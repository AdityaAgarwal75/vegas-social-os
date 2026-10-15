"""Named video collections. Immutable asset bytes stay checksummed and deduplicated."""
import json
import time
from datetime import datetime

KINDS={'storyboard','image','clip','final','reference','audio'}

def create(engine,name,request_id,channel_id='',planned_for=''):
    if not isinstance(name,str) or not name.strip() or len(name)>160:raise ValueError('Give this project a name of 1–160 characters')
    if not isinstance(request_id,str) or not request_id or len(request_id)>200:raise ValueError('Stable project request ID required')
    if channel_id:engine.store.get('channel',channel_id)
    if planned_for:
        try:
            value=datetime.fromisoformat(planned_for.replace('Z','+00:00'))
            if value.tzinfo is None:raise ValueError()
        except (ValueError,AttributeError):raise ValueError('Use a planned date with timezone') from None
    ident=engine.store.digest('project:'+request_id)[:32]
    body={'id':ident,'name':name.strip(),'channel_id':channel_id,'planned_for':planned_for,'created_at':time.time(),'status':'planning'}
    with engine.store.db() as db:
        row=db.execute("SELECT body FROM records WHERE kind='project' AND id=?",(ident,)).fetchone()
        if row:
            old=json.loads(row[0])
            if any(old.get(k,'')!=body[k] for k in ('name','channel_id','planned_for')):raise ValueError('Project request ID is already used')
            return old
        engine.store.write(db,'project',ident,body)
    return body

def attach(engine,project_id,asset_id,kind='image',scene=-1):
    if kind not in KINDS or type(scene) is not int or not -1<=scene<=1000:raise ValueError('Invalid project asset category or scene')
    engine.store.get('project',project_id);asset=engine.store.get('asset',asset_id)
    if kind in ('clip','final') and not asset['media_type'].startswith('video/'):raise ValueError('Choose a video for clips/final')
    ident=engine.store.digest('project-asset:'+project_id+':'+asset_id+':'+kind+':'+str(scene))[:32]
    link={'id':ident,'project_id':project_id,'asset_id':asset_id,'kind':kind,'scene':scene,'created_at':time.time()}
    engine.store.put('project-asset',ident,link)
    return link

def rename(engine,project_id,name,planned_for=''):
    project=engine.store.get('project',project_id)
    if not isinstance(name,str) or not name.strip() or len(name)>160:raise ValueError('Give this project a name of 1–160 characters')
    if planned_for:
        try:
            if datetime.fromisoformat(planned_for.replace('Z','+00:00')).tzinfo is None:raise ValueError()
        except (ValueError,AttributeError):raise ValueError('Use a planned date with timezone') from None
    project.update(name=name.strip(),planned_for=planned_for,updated_at=time.time());engine.store.put('project',project_id,project)
    return project

def ensure_plan(engine,plan):
    pid=plan.get('project_id') or plan['id']
    try:
        project=engine.store.get('project',pid)
        if not project.get('plan_id'):
            project.update(plan_id=plan['id'],channel_id=project.get('channel_id') or plan['channel_id']);engine.store.put('project',pid,project)
        return project
    except ValueError:
        selected=plan.get('selected');concepts=plan.get('concepts',[])
        title=(concepts[selected if selected is not None else 0].get('title') if concepts else None) or 'Untitled production'
        body={'id':pid,'name':title,'channel_id':plan.get('channel_id',''),'plan_id':plan['id'],'created_at':plan.get('created_at',time.time()),'status':plan.get('status','planning'),'planned_for':''}
        engine.store.put('project',body['id'],body);return body

def collect(engine):
    """Backfill only provable relationships. Never guess orphan media membership."""
    store=engine.store;plans=store.all('plan');assets={a['id']:a for a in store.all('asset')}
    projects={p['id']:p for p in store.all('project')};links=store.all('project-asset')
    def link(project,ident,kind,scene=-1):
        if ident in assets and not any(x['project_id']==project and x['asset_id']==ident and x['kind']==kind and x['scene']==scene for x in links):
            links.append(attach(engine,project,ident,kind,scene))
    for plan in plans:
        p=ensure_plan(engine,plan);projects[p['id']]={**p,'status':plan['status'],'plan':plan}
        for scene,ident in plan.get('images',{}).items():link(p['id'],ident,'storyboard',int(scene))
        if plan.get('video'):link(p['id'],plan['video'],'final')
    plan_projects={p['id']:p.get('project_id') or p['id'] for p in plans}
    jobs=[]
    for kind in ('job','image-job','video-job','edit-job'):
        for job in store.all(kind):
            jobs.append({**{k:v for k,v in job.items() if k not in ('worker','backend_project','flow_project_url')},'job_kind':kind})
            pid=job.get('project_id') or plan_projects.get(job.get('plan_id'),job.get('plan_id'))
            if pid not in projects:continue
            ids=job.get('asset_ids',[])+([job['asset_id']] if job.get('asset_id') else [])
            for ident in ids:link(pid,ident,'image' if kind=='image-job' else 'final' if kind=='edit-job' else 'clip',job.get('scene',-1))
            for ident in [job.get('first_frame_id'),job.get('last_frame_id'),*job.get('reference_asset_ids',[])]:
                if ident:link(pid,ident,'reference')
    publications=store.all('publication');result=[];assigned=set()
    for pid,p in projects.items():
        own=[x for x in links if x['project_id']==pid and x['asset_id'] in assets];assigned.update(x['asset_id'] for x in own)
        media=[{**assets[x['asset_id']],'category':x['kind'],'scene':x['scene']} for x in own]
        ownjobs=[j for j in jobs if (j.get('project_id') or plan_projects.get(j.get('plan_id'),j.get('plan_id')))==pid]
        pubs=[r for r in publications if r.get('plan_id')==p.get('plan_id',pid) or r.get('project_id')==pid or bool(set(r.get('asset_ids',[]))&{x['asset_id'] for x in own})]
        if not p.get('plan_id'):
            active=any(j.get('status') in ('submitting','processing','queued','running') for j in ownjobs)
            p={**p,'status':'processing' if active else 'media_ready' if media else 'planning'}
        result.append({**p,'assets':media,'jobs':ownjobs,'publications':pubs,'image_count':len({a['id'] for a in media if a['media_type'].startswith('image/')}),'clip_count':len({a['id'] for a in media if a['media_type'].startswith('video/')}),'cover_id':next((a['id'] for a in media if a['media_type'].startswith('image/')),None)})
    return {'projects':sorted(result,key=lambda p:p.get('created_at',0),reverse=True),'unassigned':[a for a in assets.values() if a['id'] not in assigned]}

def prepare_job(engine,project_id,title,request_id):
    if project_id:
        engine.store.get('project',project_id);return project_id
    return create(engine,title[:160],request_id)['id']
