"""MCP Events webhooks with encrypted subscriptions and a durable transactional outbox."""
import base64
import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timezone
from urllib.parse import urlsplit
from . import auth
from .research import PinnedHTTPS, public_address

NAMES={'brief.due','storyboard.approved','storyboard.revision_requested','clip.completed','production.failed','final_video.review_required','publication.completed'}


def iso(at):return datetime.fromtimestamp(at,timezone.utc).isoformat().replace('+00:00','Z')


def definitions():
    filters={'type':'object','properties':{'channel_id':{'type':'string'},'plan_id':{'type':'string'}},'additionalProperties':False}
    payload={'type':'object','properties':{k:{'type':'string'} for k in ('entity_id','kind','status','channel_id','plan_id','url')},'required':['entity_id','kind','status','url'],'additionalProperties':False}
    return [{'name':name,'description':'A durable owner-installation '+name.replace('.',' ')+' state change. Reload authoritative records before acting.','delivery':['webhook'],'inputSchema':filters,'payloadSchema':payload} for name in sorted(NAMES)]


def emit(db,kind,ident,body,old):
    # Called inside the SAME SQLite transaction that commits the production state.
    name=None;status=body.get('status','')
    if kind=='brief' and old is None:name='brief.due'
    elif kind=='review-request' and old is None:name='storyboard.revision_requested'
    elif old and old.get('status')==status:return
    elif kind=='plan' and status=='ready':name='storyboard.approved'
    elif kind=='plan' and status=='video_review':name='final_video.review_required'
    elif kind in ('job','video-job') and status=='completed':name='clip.completed'
    elif kind in ('job','video-job') and status in ('failed','unknown'):name='production.failed'
    elif kind=='publication' and status=='published':name='publication.completed'
    if not name:return
    fingerprint=json.dumps([kind,ident,name,body.get('images'),body.get('video'),body.get('asset_id'),body.get('asset_ids')],sort_keys=True)
    eid=hashlib.sha256(fingerprint.encode()).hexdigest()[:32]
    data={'entity_id':ident,'kind':kind,'status':status,'url':'/dashboard#'+('publishing' if kind=='publication' else 'productions')}
    for key in ('channel_id','plan_id'):
        if body.get(key):data[key]=body[key]
    if kind=='plan':data['plan_id']=ident
    if data.get('plan_id') and 'channel_id' not in data:
        parent=db.execute("SELECT body FROM records WHERE kind='plan' AND id=?",(data['plan_id'],)).fetchone()
        if parent:data['channel_id']=json.loads(parent[0]).get('channel_id','')
    event={'eventId':eid,'name':name,'timestamp':iso(time.time()),'data':data,'cursor':None,'created_at':time.time()}
    db.execute("INSERT OR IGNORE INTO records VALUES('event',?,?)",(eid,json.dumps(event)))


def signature(secret,ident,stamp,raw):
    if not isinstance(secret,str) or not secret.startswith('whsec_'):raise ValueError('Require a whsec_ signing key')
    try:key=base64.b64decode(secret[6:],validate=True)
    except Exception:raise ValueError('Invalid signing key') from None
    if not 24<=len(key)<=64:raise ValueError('Signing key must decode to 24–64 bytes')
    return 'v1,'+base64.b64encode(hmac.new(key,(ident+'.'+str(stamp)+'.').encode()+raw,hashlib.sha256).digest()).decode()


def callback(url,raw,headers):
    p=urlsplit(url)
    if p.scheme!='https' or not p.hostname or p.port not in (None,443) or p.username or p.password or p.fragment or len(url)>2048:raise ValueError('Callback must be public HTTPS')
    conn=PinnedHTTPS(p.hostname,public_address(p.hostname));conn.timeout=10
    try:
        conn.request('POST',(p.path or '/')+('?' + p.query if p.query else ''),body=raw,headers=headers)
        response=conn.getresponse();body=response.read(262145)
        if len(body)>262144:raise ValueError('Callback response too large')
        if 300<=response.status<400:raise ValueError('Callback redirects are forbidden')
        return response.status,body
    finally:conn.close()


def signed_send(record,keys,payload):
    raw=json.dumps(payload,separators=(',',':')).encode()
    if len(raw)>262144:raise ValueError('Event payload too large')
    stamp=int(time.time());ident=payload.get('eventId','verification_'+secrets.token_hex(16))
    signs=[signature(keys['secret'],ident,stamp,raw)]
    if keys.get('old_secret') and keys.get('rotated_at',0)>time.time()-300:signs.append(signature(keys['old_secret'],ident,stamp,raw))
    headers={'Content-Type':'application/json','webhook-id':ident,'webhook-timestamp':str(stamp),'webhook-signature':' '.join(signs),'X-MCP-Subscription-Id':record['id']}
    return callback(record['url'],raw,headers)


def identity(principal,params):
    name=params.get('name');arguments=params.get('arguments',{});delivery=params.get('delivery',{})
    if name not in NAMES or not isinstance(arguments,dict) or set(arguments)-{'channel_id','plan_id'} or any(not isinstance(v,str) or len(v)>100 for v in arguments.values()):raise ValueError('Invalid event or filters')
    if delivery.get('mode')!='webhook' or not isinstance(delivery.get('url'),str):raise ValueError('Only webhook delivery is supported')
    owner=principal.get('client_id','dashboard-owner')
    canonical=json.dumps([owner,name,arguments,delivery['url']],sort_keys=True,separators=(',',':'))
    return hashlib.sha256(canonical.encode()).hexdigest()[:32],owner,name,arguments,delivery


def subscribe(engine,principal,params):
    if not auth.permits(principal,'social:read') or not auth.permits(principal,'events:subscribe'):raise ValueError('Owner read and events:subscribe scopes required')
    ident,owner,name,arguments,delivery=identity(principal,params)
    for key,kind in [('channel_id','channel'),('plan_id','plan')]:
        if key in arguments:engine.store.get(kind,arguments[key])
    secret=delivery.get('secret');signature(secret,'validation',int(time.time()),b'{}')
    auth.rate_limit(engine.store,'subscriptions',owner,20,60)
    if len(engine.store.all('subscription'))>=128:
        try:engine.store.get('subscription',ident)
        except ValueError:raise ValueError('Subscription limit reached') from None
    ttl=params.get('ttlMs',86400000)
    if ttl is None:ttl=86400000
    if type(ttl) is not int or ttl<60000:raise ValueError('Request at least 60 seconds subscription lifetime')
    challenge=secrets.token_urlsafe(32);record={'id':ident,'owner':owner,'name':name,'arguments':arguments,'url':delivery['url'],'grant_id':principal.get('grant_id'),'created_at':time.time()}
    try:
        status,raw=signed_send(record,{'secret':secret},{'type':'verification','challenge':challenge})
        if not 200<=status<300 or not secrets.compare_digest(json.loads(raw).get('challenge',''),challenge):raise ValueError('Callback challenge failed')
    except Exception:raise ValueError('Callback verification failed; no application event was sent') from None
    ttl=params.get('ttlMs',86400000)
    if ttl is None:ttl=86400000
    if type(ttl) is not int or ttl<60000:raise ValueError('Request at least 60 seconds subscription lifetime')
    record.update(expires=time.time()+min(ttl/1000,86400),active=True)
    try:
        old=engine.store.get('subscription',ident);record['created_at']=old['created_at']
        previous=engine.store.secret('event-secret:'+ident)
    except ValueError:previous={}
    keys={**previous,'secret':secret}
    if previous.get('secret')!=secret and previous.get('secret'):keys.update(old_secret=previous['secret'],rotated_at=time.time())
    engine.store.secret('event-secret:'+ident,keys);engine.store.put('subscription',ident,record)
    return {'id':ident,'refreshBefore':iso(record['expires']),'cursor':None,'truncated':False}


def unsubscribe(engine,principal,params):
    ident,_,_,_,_=identity(principal,params)
    try:record=engine.store.get('subscription',ident)
    except ValueError:return {}
    record['active']=False;engine.store.put('subscription',ident,record);return {}


def active(engine,sub):
    if not sub.get('active') or sub['expires']<time.time():return False
    if sub.get('grant_id'):
        try:g=engine.store.get('oauth-grant',sub['grant_id'])
        except ValueError:return False
        if g['revoked'] or g['expires']<time.time():return False
    return True


def tick(engine):
    for sub in engine.store.all('subscription'):
        if not active(engine,sub):continue
        for event in sorted(engine.store.all('event'),key=lambda e:e['created_at']):
            if event['name']!=sub['name'] or event['created_at']<sub['created_at'] or any(event['data'].get(k)!=v for k,v in sub['arguments'].items()):continue
            ident=engine.store.digest(sub['id']+':'+event['eventId'])[:32]
            with engine.store.db() as db:
                row=db.execute("SELECT body FROM records WHERE kind='event-delivery' AND id=?",(ident,)).fetchone()
                delivery=json.loads(row[0]) if row else {'id':ident,'event_id':event['eventId'],'subscription_id':sub['id'],'status':'pending','attempts':0,'next_at':0}
                if delivery['status'] in ('accepted','stopped') or delivery['next_at']>time.time():continue
                delivery.update(status='sending',attempts=delivery['attempts']+1,next_at=time.time()+30)
                engine.store.write(db,'event-delivery',ident,delivery)
            try:
                if not active(engine,engine.store.get('subscription',sub['id'])):continue
                code,_=signed_send(sub,engine.store.secret('event-secret:'+sub['id']),{k:v for k,v in event.items() if k!='created_at'})
                delivery['http_status']=code
                delivery['status']='accepted' if 200<=code<300 else 'stopped' if code in (410,413) or (400<=code<500 and code!=429) else 'pending'
            except Exception:delivery.update(status='pending',error='Callback delivery failed; no production tool was retried')
            if delivery['attempts']>=8 and delivery['status']=='pending':delivery['status']='stopped'
            delivery['next_at']=time.time()+min(3600,2**delivery['attempts']*15)
            engine.store.put('event-delivery',ident,delivery)
            # Bound callback work per scheduler turn. A 2xx is receipt, not agent completion.
            return


def status(engine):
    return {'subscriptions':[{k:v for k,v in s.items() if k!='url'} for s in engine.store.all('subscription')],'deliveries':engine.store.all('event-delivery')[-100:],'host_execution_verified':False,'receipt_is_execution':False}
