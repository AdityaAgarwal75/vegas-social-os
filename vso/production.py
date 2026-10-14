"""Channel policy, immutable scene identities and an authoritative production summary."""
import copy
import hashlib
import json
import time

FIELDS={'audience','brand_voice','content_rules','references','production_preferences','approved_flow_accounts','daily_credit_limit','posting_preferences'}

def channel_settings(engine,channel_id,settings):
    if not isinstance(settings,dict) or set(settings)-FIELDS:raise ValueError('Unsupported channel setting')
    current=engine.store.get('channel',channel_id);settings=copy.deepcopy(settings)
    for k in ('audience','brand_voice'):
        if k in settings and (not isinstance(settings[k],str) or len(settings[k])>8000):raise ValueError('Bounded text required')
    for k in ('content_rules','references'):
        if k in settings and (not isinstance(settings[k],list) or len(settings[k])>100 or any(not isinstance(x,str) or len(x)>4000 for x in settings[k])):raise ValueError('Provide bounded lists of text/references')
    refs=settings.get('approved_flow_accounts',current.get('settings',{}).get('approved_flow_accounts',[]))
    if not isinstance(refs,list) or len(refs)>30:raise ValueError('Choose owner Flow account IDs')
    for ident in refs:
        if engine.store.get('account',ident)['provider']!='flow':raise ValueError('Approved generation accounts must be Flow accounts')
    if 'daily_credit_limit' in settings and (type(settings['daily_credit_limit']) is not int or not 0<=settings['daily_credit_limit']<=10000):raise ValueError('Daily credit limit must be 0–10000')
    for k in ('production_preferences','posting_preferences'):
        if k in settings and (not isinstance(settings[k],dict) or len(json.dumps(settings[k]))>10000):raise ValueError('Bounded preference object required')
    current['settings']={**current.get('settings',{}),**settings};engine.store.put('channel',channel_id,current)
    return current

def scenes(concepts,plan_id):
    result=copy.deepcopy(concepts)
    for ci,concept in enumerate(result):
        for si,scene in enumerate(concept['scenes']):
            scene['scene_id']=hashlib.sha256(f'{plan_id}:{ci}:{si}'.encode()).hexdigest()[:24]
            material={k:v for k,v in scene.items() if k!='input_sha256'}
            scene['input_sha256']=hashlib.sha256(json.dumps(material,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return result

def enforce(db,channel,account_id,max_credits):
    settings=channel.get('settings',{});allowed=settings.get('approved_flow_accounts',[])
    if allowed and account_id not in allowed:raise ValueError('Flow account is not approved for this channel')
    if 'daily_credit_limit' not in settings:return
    spent=0
    for row in db.execute("SELECT body FROM records WHERE kind='job'"):
        j=json.loads(row[0]);parent=db.execute("SELECT body FROM records WHERE kind='plan' AND id=?",(j.get('plan_id'),)).fetchone()
        if parent and json.loads(parent[0])['channel_id']==channel['id'] and j.get('created_at',0)>time.time()-86400:
            # Conservative reservation: failed/unknown paid operations retain their ceilings until reconciled.
            spent+=j.get('max_credits',0)
    if spent+max_credits>settings['daily_credit_limit']:raise ValueError('Channel rolling 24-hour credit ceiling exceeded')

def status(engine,plan_id):
    p=engine.store.get('plan',plan_id);channel=engine.store.get('channel',p['channel_id']);jobs=[engine.public_job(j) for j in engine.store.all('job') if j['plan_id']==plan_id]
    return {'plan':p,'channel':channel,'clips':jobs,'editing':[j for j in engine.store.all('edit-job') if j.get('plan_id')==plan_id],'revisions':[r for r in engine.store.all('review-request') if r.get('plan_id')==plan_id],'publications':[r for r in engine.store.all('publication') if r.get('plan_id')==plan_id],'host_execution_required':p['status'] in ('concept_review','images_pending'),'approved_credit_ceiling':p['budget'],'reserved_credits':p['reserved']}
