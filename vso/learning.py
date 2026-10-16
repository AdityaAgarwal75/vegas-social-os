"""Private creative memory and bounded, read-only post-performance observation.

This is retrieval and experiment bookkeeping, not model training or causal proof.
"""
import copy
import json
import math
import re
import statistics
import threading
import time
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit
from . import net

CHECKPOINTS=(6,24,72,168)
METRICS={'views','likes','comments','reach','shares','saves','follows','average_watch_seconds','average_view_percentage','hold_3s_percentage','engaged_views'}
LOCK=threading.RLock()

def optional(engine,kind,ident,default=None):
    try:return engine.store.get(kind,ident)
    except ValueError:return default

def bounded_text(value,name,limit=12000):
    if not isinstance(value,str) or len(value)>limit:raise ValueError('Invalid '+name)
    return value

def memory_save(engine,channel_id,project_id,fields,request_id):
    channel=engine.store.get('channel',channel_id);project=engine.store.get('project',project_id)
    if project.get('channel_id') and project['channel_id']!=channel_id:raise ValueError('Project belongs to another channel')
    if not isinstance(request_id,str) or not request_id or len(request_id)>200:raise ValueError('Stable request ID required')
    allowed={'hook','visual_hook','hook_family','format','script','video_prompts','image_prompts','template_ids','audio_plan','edit_plan','hypothesis','primary_metric','duration_seconds','aspect_ratio','content_pillar','reference_asset_ids'}
    if not isinstance(fields,dict) or set(fields)-allowed:raise ValueError('Unsupported creative memory field')
    fields=copy.deepcopy(fields)
    for key,value in fields.items():
        if key in ('video_prompts','image_prompts','template_ids','reference_asset_ids'):
            if not isinstance(value,list) or len(value)>20 or any(not isinstance(x,str) or not x.strip() or len(x)>12000 for x in value):raise ValueError('Invalid '+key)
        elif key=='duration_seconds':
            if type(value) not in (int,float) or not math.isfinite(value) or not 0<value<=600:raise ValueError('Invalid duration')
        elif key=='aspect_ratio':
            if value not in ('9:16','16:9','1:1','4:3','3:4','21:9'):raise ValueError('Invalid aspect ratio')
        else:bounded_text(value,key)
    for ident in fields.get('reference_asset_ids',[]):engine.store.get('asset',ident)
    if not fields.get('hook') or not fields.get('video_prompts'):raise ValueError('Save the actual hook and at least one exact video prompt')
    ident=engine.store.digest('creative-memory:'+request_id)[:32]
    material={'channel_id':channel_id,'project_id':project_id,'fields':fields}
    with engine.store.db() as db:
        row=db.execute("SELECT body FROM records WHERE kind='creative-memory' AND id=?",(ident,)).fetchone()
        if row:
            old=json.loads(row[0])
            if any(old.get(k)!=v for k,v in material.items()):raise ValueError('Request ID already has another creative record')
            return old
        body={'id':ident,**material,'created_at':time.time(),'evidence_status':'creative_hypothesis'}
        engine.store.write(db,'creative-memory',ident,body)
    return body

def freeze(engine,post):
    """Freeze exact local decisions before release; no provider call or guessed relationship."""
    ident=engine.store.digest('creative-release:'+post['id'])[:32]
    old=optional(engine,'creative-release',ident)
    if old:return old
    plan=optional(engine,'plan',post.get('plan_id',''),{})
    project_id=post.get('project_id') or plan.get('project_id') or plan.get('id','')
    assets=post.get('asset_ids') or ([post['asset_id']] if post.get('asset_id') else [])
    if not project_id:
        matching={x['project_id'] for x in engine.store.all('project-asset') if x['asset_id'] in assets and x['kind']=='final'}
        if len(matching)==1:project_id=next(iter(matching))
    project=optional(engine,'project',project_id,{})
    channel_id=plan.get('channel_id') or project.get('channel_id','')
    if not channel_id:
        matches=[c['id'] for c in engine.store.all('channel') if post['account_id'] in c.get('account_ids',[])]
        if len(matches)==1:channel_id=matches[0]
    concept={}
    if plan.get('selected') is not None and plan.get('concepts'):concept=plan['concepts'][plan['selected']]
    decisions=[r for r in engine.store.all('creative-memory') if r['project_id']==project_id and r['channel_id']==channel_id]
    decision=max(decisions,key=lambda r:r['created_at']) if decisions else None
    shots=concept.get('scenes',[])
    selections=[x for x in engine.store.all('template-selection') if x['project_id']==project_id]
    fields={'hook':concept.get('hook',''),'script':concept.get('script',''),'hook_family':'unclassified','format':'video' if any((optional(engine,'asset',a,{}) or {}).get('media_type','').startswith('video/') for a in assets) else 'post',
            'video_prompts':[x['video_prompt'] for x in shots if x.get('video_prompt')],
            'image_prompts':[x['image_prompt'] for x in shots if x.get('image_prompt')],
            'template_ids':[x['template_id'] for x in selections]}
    if decision:fields.update(copy.deepcopy(decision['fields']))
    job_refs=[]
    for kind in ('job','video-job','image-job','edit-job'):
        for job in engine.store.all(kind):
            if (plan.get('id') and job.get('plan_id')==plan['id']) or (project_id and job.get('project_id')==project_id):
                job_refs.append({k:copy.deepcopy(job[k]) for k in ('id','scene','prompt','video_prompt','image_prompt','model','duration','resolution','aspect_ratio','status','asset_id','asset_ids') if k in job})
    body={'production_jobs':job_refs,'id':ident,'publication_id':post['id'],'account_id':post['account_id'],'provider':post['provider'],'project_id':project_id,'channel_id':channel_id,
          'fields':fields,'decision_id':decision['id'] if decision else None,'template_selections':copy.deepcopy(selections),
          'asset_manifest':[{k:a[k] for k in ('id','sha256','media_type','size') if k in a} for a in [optional(engine,'asset',x,{}) for x in assets]],
          'release':{k:copy.deepcopy(post[k]) for k in ('title','caption','visibility','options') if k in post},
          'created_at':time.time(),'completeness':'recorded' if fields.get('hook') and fields.get('video_prompts') else 'creative_details_missing',
          'note':'Immutable release context. Missing old prompts stay missing; later edits do not rewrite this record.'}
    with engine.store.db() as db:
        row=db.execute("SELECT body FROM records WHERE kind='creative-release' AND id=?",(ident,)).fetchone()
        if row:return json.loads(row[0])
        engine.store.write(db,'creative-release',ident,body)
    return body

def policy(engine,enabled=None):
    current=optional(engine,'learning-policy','owner',{'enabled':False,'checkpoints_hours':list(CHECKPOINTS),'max_posts_per_tick':1,'interval_seconds':300})
    if enabled is not None:
        if type(enabled) is not bool:raise ValueError('Enabled must be true or false')
        current={**current,'enabled':enabled,'updated_at':time.time()};engine.store.put('learning-policy','owner',current)
        if enabled:
            for post in engine.store.all('publication'):
                if post.get('status')=='published':freeze(engine,post)
    return current

def stamp(value):
    if not value:return None
    try:return datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
    except (ValueError,TypeError,AttributeError):return None

def _numbers(values):
    if not isinstance(values,dict) or len(values)>len(METRICS):raise ValueError('Metrics must be a bounded object')
    result={}
    for key,value in values.items():
        if key not in METRICS:raise ValueError('Unsupported metric: '+key)
        if type(value) not in (int,float) or not math.isfinite(value) or value<0 or (key=='hold_3s_percentage' and value>100):raise ValueError('Invalid numeric metric: '+key)
        result[key]=value
    return result

def _record(engine,post,metrics,request_id,observed_at,published_at,source,checkpoint_hours=0,availability=None):
    metrics=_numbers(metrics);creative=freeze(engine,post)
    ident=engine.store.digest('performance:'+post['id']+':'+request_id)[:32]
    age=max(0,observed_at-published_at) if published_at else None
    hours=checkpoint_hours
    comparable=bool(hours and age is not None and abs(age-hours*3600)<=max(3600,hours*3600*.2))
    body={'id':ident,'publication_id':post['id'],'account_id':post['account_id'],'provider':post['provider'],'remote_id':post['remote_id'],
          'creative_record_id':creative['id'],'channel_id':creative['channel_id'],'observed_at':observed_at,'published_at':published_at,
          'age_seconds':age,'checkpoint_hours':hours,'comparable_age':comparable,'metrics':metrics,'source':source,
          'availability':availability or {},'visibility':post.get('visibility','public'),
          'note':'Counts are observations. A view count alone cannot diagnose the hook, retention or cause of an outcome.'}
    old=optional(engine,'performance-observation',ident)
    if old:
        if source['type']=='owner_supplied' and any(old.get(k)!=body[k] for k in ('metrics','observed_at','published_at','source','checkpoint_hours')):raise ValueError('Observation request ID already used with different evidence')
        return old
    engine.store.put('performance-observation',ident,body)
    if post.get('status')=='published' and published_at and not post.get('published_at'):
        post={**post,'published_at':published_at,'published_at_source':source['type']};engine.store.put('publication',post['id'],post)
    review_id=engine.store.digest('performance-review:'+post['id'])[:32]
    if not optional(engine,'learning-review',review_id):engine.store.put('learning-review',review_id,{'id':review_id,'publication_id':post['id'],'channel_id':creative['channel_id'],'status':'awaiting_agent','created_at':time.time(),'instruction':'Read content_context. Separate observation from hypothesis. Compare public posts on the same account at the same publication age and format; specify missing retention data. Propose one next test, never claim causal proof or rewrite prompts silently.'})
    return body

def observe(engine,publication_id,metrics,source_url,request_id,observed_at,published_at,checkpoint_hours=0):
    post=engine.store.get('publication',publication_id)
    if post.get('status')!='published' or not post.get('remote_id'):raise ValueError('Choose a confirmed published record')
    if not isinstance(source_url,str) or len(source_url)>2048:raise ValueError('Source URL required')
    p=urlsplit(source_url)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.query or p.fragment:raise ValueError('Use a source URL without credentials, query or fragment')
    if not isinstance(request_id,str) or not request_id or len(request_id)>200:raise ValueError('Stable request ID required')
    for value in (observed_at,published_at):
        if type(value) not in (int,float) or not math.isfinite(value) or value<=0:raise ValueError('Use real Unix observation/publication timestamps')
    if observed_at>time.time()+60 or observed_at<published_at:raise ValueError('Observation time must follow publication and not be in the future')
    if checkpoint_hours not in (0,*CHECKPOINTS):raise ValueError('Unsupported checkpoint')
    return _record(engine,post,metrics,request_id,observed_at,published_at,{'type':'owner_supplied','url':source_url,'verified_by_provider':False},checkpoint_hours)

def capture(engine,publication_id,request_id,checkpoint_hours=0):
    post=engine.store.get('publication',publication_id)
    if post.get('status')!='published' or not post.get('remote_id'):raise ValueError('Choose a provider-confirmed published record')
    if not isinstance(request_id,str) or not request_id or len(request_id)>200 or checkpoint_hours not in (0,*CHECKPOINTS):raise ValueError('Invalid capture request')
    ident=engine.store.digest('performance:'+post['id']+':'+request_id)[:32]
    old=optional(engine,'performance-observation',ident)
    if old:return old
    account=engine.store.get('account',post['account_id'])
    if account.get('status')!='connected' or account.get('provider')!=post['provider']:raise ValueError('Publishing account disconnected or mismatched')
    remote=str(post['remote_id'])
    if not re.fullmatch(r'[A-Za-z0-9_-]{3,100}',remote):raise ValueError('Invalid stored provider media ID')
    token=engine.accounts.token(account['id']);metrics={};published=post.get('published_at');availability={}
    provider=post['provider']
    if provider=='youtube':
        url='https://www.googleapis.com/youtube/v3/videos?'+urlencode({'part':'snippet,statistics,status','id':remote})
        value,_=net.request(url,token=token);items=value.get('items',[])
        if len(items)!=1 or items[0]['id']!=remote or items[0].get('snippet',{}).get('channelId')!=account['remote_id']:raise ValueError('Video ownership could not be verified')
        row=items[0];published=stamp(row.get('snippet',{}).get('publishedAt')) or published
        metrics={out:int(row['statistics'][key]) for key,out in [('viewCount','views'),('likeCount','likes'),('commentCount','comments')] if key in row.get('statistics',{})}
        actual=row.get('status',{}).get('privacyStatus')
        if actual in ('private','unlisted','public'):post={**post,'visibility':actual}
        availability={'retention':'Requires separate authorized YouTube Analytics data or an owner-supplied observation','view_definition':'YouTube Data API viewCount; Shorts starts/replays are not engagedViews'}
    elif provider=='instagram':
        root='https://graph.instagram.com/'+engine.accounts.config.version('instagram')
        url=root+'/'+remote+'?fields=id,media_type,timestamp,like_count,comments_count'
        value,_=net.request(url,token=token)
        if str(value.get('id'))!=remote:raise ValueError('Media identity mismatch')
        published=stamp(value.get('timestamp')) or published
        metrics={out:int(value[key]) for key,out in [('like_count','likes'),('comments_count','comments')] if key in value}
        availability={'retention':'Not available from basic media counts','insights':'Not granted or not requested'}
        grants=set(account.get('scopes',[]))
        if grants & {'instagram_business_manage_insights','instagram_manage_insights'}:
            try:
                insights,_=net.request(root+'/'+remote+'/insights?metric=views,reach,saved,shares',token=token)
                for metric in insights.get('data',[]):
                    key={'saved':'saves'}.get(metric['name'],metric['name']);values=metric.get('values',[])
                    value=(values[-1].get('value') if values else metric.get('total_value',{}).get('value'))
                    if key in METRICS and type(value) in (int,float):metrics[key]=value
                availability['insights']='Returned by the existing provider grant'
            except Exception:availability['insights']='Provider did not return these metrics; reconnect/eligibility may be required'
    elif provider=='facebook':
        url='https://graph.facebook.com/'+engine.accounts.config.version('facebook')+'/'+remote+'?fields=id,created_time'
        value,_=net.request(url,token=token)
        if str(value.get('id'))!=remote:raise ValueError('Media identity mismatch')
        published=stamp(value.get('created_time')) or published
        availability={'views':'Page/video Insights needs additional granted permissions; no counts inferred','retention':'Unavailable'}
    else:raise ValueError('Unsupported publishing provider')
    return _record(engine,post,metrics,request_id,time.time(),published,{'type':'provider_api','url':url.split('?')[0],'verified_by_provider':True},checkpoint_hours,availability)

def due(engine):
    now=time.time();observations=engine.store.all('performance-observation');result=[]
    for p in engine.store.all('publication'):
        if p.get('status')!='published' or not p.get('remote_id') or p.get('visibility') in ('private','unlisted'):continue
        freeze(engine,p)
        existing=[x for x in observations if x['publication_id']==p['id'] and x['source']['verified_by_provider']]
        if not existing:result.append({'publication_id':p['id'],'checkpoint_hours':0,'reason':'First recorded provider observation'});continue
        published=p.get('published_at') or existing[-1].get('published_at')
        if not published:continue
        age=(now-published)/3600
        targets=[h for h in CHECKPOINTS if h<=age and abs(age-h)<=max(1,h*.2) and not any(x['checkpoint_hours']==h for x in existing)]
        if targets:result.append({'publication_id':p['id'],'checkpoint_hours':max(targets),'reason':'Due age-matched checkpoint'})
    return result

def tick(engine):
    if not policy(engine)['enabled']:return {'enabled':False,'captured':0}
    with LOCK:
        now=time.time();last=optional(engine,'runtime','learning-worker',{})
        if now-last.get('last_tick',0)<300:return last
        result={'enabled':True,'last_tick':now,'captured':0,'failures':[]}
        pending=[item for item in due(engine) if now-optional(engine,'performance-attempt',item['publication_id'],{}).get('at',0)>=3600]
        for item in pending[:1]:
            p=engine.store.get('publication',item['publication_id']);attempt=optional(engine,'performance-attempt',p['id'],{})
            if now-attempt.get('at',0)<3600:continue
            try:
                capture(engine,p['id'],'checkpoint-'+str(item['checkpoint_hours']),item['checkpoint_hours']);result['captured']+=1
                engine.store.put('performance-attempt',p['id'],{'at':now,'status':'captured'})
            except Exception:
                result['failures'].append({'publication_id':p['id'],'error':'Provider observation unavailable; no publication or retry submission occurred'})
                engine.store.put('performance-attempt',p['id'],{'at':now,'status':'unavailable'})
        engine.store.put('runtime','learning-worker',result);return result

def start(engine,stop):
    def loop():
        while not stop.is_set():
            try:tick(engine)
            except Exception:engine.store.put('runtime','learning-worker',{'last_tick':time.time(),'error':'Observation worker unavailable; inspect records/connections'})
            stop.wait(300)
    thread=threading.Thread(target=loop,name='vso-performance-observer',daemon=True);thread.start();return thread

def context(engine,channel_id):
    channel=engine.store.get('channel',channel_id)
    records=[x for x in engine.store.all('creative-release') if x['channel_id']==channel_id]
    memory=[x for x in engine.store.all('creative-memory') if x['channel_id']==channel_id]
    observations=[x for x in engine.store.all('performance-observation') if x.get('channel_id')==channel_id]
    # One observation per publication/checkpoint; manual imports never silently become provider data.
    grouped={}
    for x in observations:
        if not x['comparable_age'] or x['visibility']!='public' or not x['source']['verified_by_provider'] or 'views' not in x['metrics']:continue
        record=next((r for r in records if r['id']==x['creative_record_id']),None)
        if not record:continue
        fields=record['fields'];duration=fields.get('duration_seconds');duration_bucket='unknown' if not duration else '<=15' if duration<=15 else '<=30' if duration<=30 else '<=60' if duration<=60 else '>60'
        if duration_bucket=='unknown' or fields.get('aspect_ratio') not in ('9:16','16:9','1:1','4:3','3:4','21:9'):continue
        key=(x['account_id'],x['checkpoint_hours'],fields.get('format','unknown'),duration_bucket,fields.get('aspect_ratio','unknown'))
        dedupe=(x['publication_id'],key)
        old=grouped.get(dedupe)
        if not old or abs(x['age_seconds']-x['checkpoint_hours']*3600)<abs(old['age_seconds']-old['checkpoint_hours']*3600):grouped[dedupe]=x
    comparisons=[]
    for (publication,key),x in grouped.items():
        peers=[row for (pid,k),row in grouped.items() if k==key and pid!=publication]
        baseline=statistics.median([p['metrics']['views'] for p in peers]) if len(peers)>=5 else None
        multiple=x['metrics']['views']/baseline if baseline else None
        comparisons.append({'publication_id':publication,'observation_id':x['id'],'peer_count':len(peers),'account_id':key[0],'checkpoint_hours':key[1],'format':key[2],'duration_bucket':key[3],'median_peer_views':baseline,'views_multiple':round(multiple,3) if multiple is not None else None,
                            'finding':'insufficient_comparable_posts' if multiple is None else 'above_account_baseline' if multiple>=1.5 else 'below_account_baseline' if multiple<=.67 else 'near_account_baseline','confidence':'descriptive_only','causal_claim':False})
    return {'channel':channel,'strategy':optional(engine,'strategy',channel_id), 'creative_memory':sorted(memory,key=lambda x:x['created_at'],reverse=True)[:30],
            'release_records':sorted(records,key=lambda x:x['created_at'],reverse=True)[:30], 'observations':sorted(observations,key=lambda x:x['observed_at'],reverse=True)[:100],
            'comparisons':comparisons,'reviews':[x for x in engine.store.all('learning-review') if x.get('channel_id')==channel_id],
            'lessons':[x for x in engine.store.all('learning-lesson') if x['channel_id']==channel_id], 'policy':policy(engine),
            'next_step':'Use the saved creative decisions and actual observations to propose one changed variable. If fewer than five comparable peers, keep the idea a hypothesis. Never diagnose hook failure from views alone. Retention/hold data must be supplied or legitimately authorized.',
            'learning_type':'Persistent retrieval and reviewed experiments; no model weight training or autonomous rewriting of agent instructions.'}

def lesson_save(engine,channel_id,claim,evidence_ids,next_test,request_id):
    engine.store.get('channel',channel_id)
    for key,value in [('claim',claim),('next_test',next_test),('request_id',request_id)]:
        if not bounded_text(value,key,4000).strip():raise ValueError('Blank '+key)
    if not isinstance(evidence_ids,list) or not 1<=len(evidence_ids)<=30 or len(set(evidence_ids))!=len(evidence_ids):raise ValueError('Choose 1–30 unique real observation IDs')
    evidence=[engine.store.get('performance-observation',i) for i in evidence_ids]
    if any(x.get('channel_id')!=channel_id for x in evidence):raise ValueError('Evidence belongs to another channel')
    ident=engine.store.digest('lesson:'+request_id)[:32]
    body={'id':ident,'channel_id':channel_id,'claim':claim,'evidence_ids':evidence_ids,'next_test':next_test,'status':'hypothesis','confidence':'limited_observational','causal_claim':False,'created_at':time.time()}
    old=optional(engine,'learning-lesson',ident)
    if old:
        if any(old[k]!=body[k] for k in ('channel_id','claim','evidence_ids','next_test')):raise ValueError('Request ID already used')
        return old
    engine.store.put('learning-lesson',ident,body)
    publications={x['publication_id'] for x in evidence}
    for review in engine.store.all('learning-review'):
        if review.get('channel_id')==channel_id and review.get('publication_id') in publications:
            engine.store.put('learning-review',review['id'],{**review,'status':'reviewed','lesson_id':ident,'reviewed_at':time.time()})
    return body
