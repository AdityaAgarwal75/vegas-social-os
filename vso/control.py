"""Owner control-plane observations. Read-only providers; no generation/publishing."""
import json
import math
import os
import shutil
import threading
import time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from . import __version__, activity, projects

_LOCK=threading.Lock()

def resources(engine):
    now=time.time();minute=str(int(now//30));root=engine.store.root
    try:
        mem={line.split(':')[0]:int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith(('MemTotal:','MemAvailable:'))}
        parts=Path('/proc/stat').read_text().splitlines()[0].split()[1:];cpu=list(map(int,parts));total=sum(cpu[:8]);idle=cpu[3]+cpu[4]
        uptime=float(Path('/proc/uptime').read_text().split()[0]);memory_total=mem['MemTotal'];memory_used=memory_total-mem['MemAvailable']
    except (OSError,ValueError,KeyError):
        total=idle=None;uptime=memory_total=memory_used=None
    disk=shutil.disk_usage(root);cpu_percent=None
    try:previous=engine.store.get('runtime','cpu-observation')
    except ValueError:previous=None
    if previous and total is not None and total>previous.get('total',total):
        cpu_percent=round(max(0,min(100,100*(1-(idle-previous['idle'])/(total-previous['total'])))),1)
    if total is not None:engine.store.put('runtime','cpu-observation',{'total':total,'idle':idle,'at':now})
    sample={'id':minute,'at':now,'cpu_percent':cpu_percent,'memory_percent':round(100*memory_used/memory_total,1) if memory_total else None,'memory_used':memory_used,'memory_total':memory_total,'disk_used':disk.used,'disk_total':disk.total,'disk_percent':round(100*disk.used/disk.total,1),'load':list(os.getloadavg()) if hasattr(os,'getloadavg') else [],'cpu_count':os.cpu_count(),'uptime_seconds':uptime}
    with engine.store.db() as db:
        db.execute("INSERT OR IGNORE INTO records VALUES('resource-sample',?,?)",(minute,json.dumps(sample)))
        db.execute("DELETE FROM records WHERE kind='resource-sample' AND json_extract(body,'$.at')<?",(now-7*86400,))
        history=[json.loads(row[0]) for row in db.execute("SELECT body FROM records WHERE kind='resource-sample' AND json_extract(body,'$.at')>? ORDER BY json_extract(body,'$.at') DESC LIMIT 240",(now-86400,))]
    return {**sample,'history':list(reversed(history)),'scope':'Host /proc and storage observations; chart begins when this release is installed.'}

def schedules(engine,collection):
    accounts={a['id']:a for a in engine.store.all('account')};channels={c['id']:c for c in engine.store.all('channel')};items=[]
    for post in engine.store.all('publication'):
        at=post.get('scheduled_at') or post.get('options',{}).get('schedule_at')
        if not at:continue
        try:stamp=float(at) if isinstance(at,(int,float)) else datetime.fromisoformat(at.replace('Z','+00:00')).timestamp()
        except (ValueError,TypeError):continue
        account=accounts.get(post.get('account_id'),{})
        items.append({'id':post['id'],'name':post.get('title') or post.get('caption','Untitled release')[:90],'at':stamp,'kind':'scheduled' if post['status']=='scheduled' else 'release','status':post['status'],'account_id':account.get('id'),'destination':account.get('name') or account.get('label') or post.get('destination_name','Disconnected account'),'provider':post.get('provider'),'project_id':post.get('project_id') or post.get('plan_id'),'thumbnail_id':post.get('options',{}).get('thumbnail_id') or next(iter(post.get('asset_ids',[])),None)})
    for project in collection['projects']:
        if not project.get('planned_for'):continue
        try:stamp=datetime.fromisoformat(project['planned_for'].replace('Z','+00:00')).timestamp()
        except ValueError:continue
        channel=channels.get(project.get('channel_id'),{})
        items.append({'id':'project-'+project['id'],'name':project['name'],'at':stamp,'kind':'planned','status':'planned','destination':channel.get('name','Destination not selected'),'project_id':project['id'],'thumbnail_id':project.get('cover_id')})
    for calendar in engine.store.all('content-request'):
        for index,item in enumerate(calendar.get('items',[])):
            try:
                zone=ZoneInfo(engine.store.get('profile','owner').get('timezone','UTC'))
            except (ValueError,ZoneInfoNotFoundError):zone=ZoneInfo('UTC')
            try:stamp=datetime.fromisoformat(item['date']).replace(tzinfo=zone).timestamp()
            except (ValueError,KeyError,TypeError):continue
            items.append({'id':calendar['id']+'-'+str(index),'name':item.get('angle') or item.get('hook') or 'Editorial plan','at':stamp,'kind':'editorial','status':'planned','destination':channels.get(calendar.get('channel_id'),{}).get('name','Channel'),'project_id':None})
    return sorted(items,key=lambda item:item['at'])

def snapshot(engine):
    with _LOCK:
        collection=projects.collect(engine);metrics=resources(engine)
    accounts=engine.store.all('account');observed=[a for a in accounts if a.get('provider')=='flow' and type(a.get('credits')) in (int,float) and math.isfinite(a['credits']) and a['credits']>=0]
    unique={}
    for account in accounts:
        if account.get('provider') in ('youtube','instagram','facebook') and account.get('status')=='connected':
            key=(account['provider'],account.get('remote_id') or account['id']);unique[key]=account
    team=activity.snapshot(engine);timeline=schedules(engine,collection)
    jobs=[j for p in collection['projects'] for j in p['jobs']]
    # Include unassigned historical jobs in operations, with no invented project link.
    known={(j['job_kind'],j['id']) for j in jobs}
    for kind in ('job','image-job','video-job','edit-job'):
        for job in engine.store.all(kind):
            if (kind,job['id']) not in known:jobs.append({**{k:v for k,v in job.items() if k not in ('worker','backend_project','flow_project_url')},'job_kind':kind})
    day=int(time.time()//86400);daily=[]
    for offset in range(6,-1,-1):
        start=(day-offset)*86400;own=[j for j in jobs if start<=j.get('created_at',0)<start+86400]
        daily.append({'at':start,'jobs':len(own),'completed':sum(j.get('status')=='completed' for j in own)})
    return {'version':__version__,'observed_at':time.time(),'resources':metrics,'accounts':accounts,'connected_identities':list(unique.values()),'credits':{'total_observed':sum(a['credits'] for a in observed),'observed_accounts':len(observed),'total_accounts':sum(a.get('provider')=='flow' for a in accounts),'unknown_accounts':sum(a.get('provider')=='flow' and a not in observed for a in accounts),'oldest_observation':min([a.get('verified_at',0) for a in observed],default=None)},'team':team,**collection,'schedules':timeline,'daily_activity':daily,'jobs':sorted(jobs,key=lambda j:j.get('created_at',0),reverse=True)[:100],'analytics':engine.store.all('analytics'),'channels':engine.store.all('channel'),'creative_briefs':engine.store.all('creative-brief'),'automation':__import__('vso.automation',fromlist=['status']).status(engine),'features':[{'id':'strategy','name':'Research & strategy','detail':'Audience, sources, creative briefs and two concepts','route':'#planning'},{'id':'copy','name':'Scripts & copy','detail':'Hooks, captions, carousels and story sequences','route':'#agents'},{'id':'production','name':'Media production','detail':'ChatGPT keyframes, Flow clips, editing and review','route':'#projects'},{'id':'publishing','name':'Publishing','detail':'Exact approvals, schedules and reconciliation','route':'#publishing'},{'id':'analytics','name':'Analytics','detail':'Observed account metrics and production history','route':'#analytics'},{'id':'system','name':'VPS administration','detail':'Resource health and owner-approved operations','route':'#system'}]}

def refresh_accounts(engine):
    """Refresh only existing configured services. Never launch a fresh browser."""
    from . import flow_service
    results=[]
    for account in engine.store.all('account'):
        if account.get('provider')!='flow':continue
        if not account.get('service_alias'):
            results.append({'id':account['id'],'status':'not_refreshed','reason':'Open and verify this private browser explicitly'});continue
        try:
            flow_service.inspect(engine,account['id']);results.append({'id':account['id'],'status':'refreshed'})
        except (ValueError,OSError):results.append({'id':account['id'],'status':'unavailable','reason':'Inspect this connection; last known balance retained'})
    return {'accounts':results,'observed_at':time.time()}
