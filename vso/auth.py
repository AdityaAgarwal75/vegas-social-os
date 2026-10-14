"""Single-owner OAuth 2.1, scope enforcement and bounded public registration."""
import base64
import hashlib
import json
import re
import secrets
import time
from urllib.parse import urlsplit

class RateLimited(ValueError):pass

SCOPES = {'social:read', 'social:write', 'social:manage', 'vps:admin', 'events:subscribe'}
DISCOVERY_METHODS = {'initialize', 'server/discover', 'tools/list', 'events/list', 'ping', 'notifications/initialized'}
READ_TOOLS = {'guide','doctor','get_profile','onboarding_status','workflow_audit','account_list','channel_list','plan_list','job_list','publication_list','account_info','image_tasks','flow_inspect','flow_model_catalog','connection_setup','automation_status','review_queue','content_queue','production_status','media_transfer_status','admin_inventory','admin_metrics','admin_job_status','admin_request_status','event_status','media_probe','edit_status','media_ingest_status'}


def tool_scope(name):
    if name and name.startswith('admin_'): return 'vps:admin'
    return 'social:read' if name in READ_TOOLS else 'social:write'


def scopes(value='social:read social:write'):
    if not isinstance(value,str): raise ValueError('Invalid OAuth scope')
    result=set(value.split())
    if not result or not result <= SCOPES: raise ValueError('Unsupported OAuth scope')
    return ' '.join(sorted(result))


def permits(record, scope):
    granted=set(record.get('scope','social:manage').split())
    if 'social:manage' in granted: granted.update({'social:read','social:write'})
    return scope in granted


def challenge(base, error='invalid_token', description='Connect this owner installation to continue', scope=None):
    result=f'Bearer resource_metadata="{base}/.well-known/oauth-protected-resource/mcp", error="{error}", error_description="{description}"'
    if scope: result+=f', scope="{scope}"'
    return result


def valid_redirect(url):
    if not isinstance(url,str) or len(url)>2048 or any(ord(x)<33 for x in url): return False
    try:
        p=urlsplit(url);port=p.port
        return not p.username and not p.password and not p.fragment and bool(p.hostname) and ((p.scheme=='https' and port in (None,443)) or (p.scheme=='http' and p.hostname in ('127.0.0.1','localhost','::1')))
    except ValueError:return False


def pkce(verifier):
    return base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()


def rate_limit(store, bucket, key, limit, window):
    ident=store.digest(bucket+':'+key+':'+str(int(time.time()//window)))
    with store.db() as db:
        row=db.execute("SELECT body FROM records WHERE kind='rate-limit' AND id=?",(ident,)).fetchone()
        record=json.loads(row[0]) if row else {'count':0,'expires':time.time()+window}
        if record['count']>=limit:raise RateLimited('Rate limit exceeded; wait before retrying')
        record['count']+=1;store.write(db,'rate-limit',ident,record)
        db.execute("DELETE FROM records WHERE kind='rate-limit' AND json_extract(body,'$.expires')<?",(time.time(),))


def register(store, body, peer):
    rate_limit(store,'register',peer,5,60);rate_limit(store,'register-global','installation',100,86400)
    redirects=body.get('redirect_uris',[])
    if not isinstance(redirects,list) or not 1<=len(redirects)<=10 or any(not valid_redirect(x) for x in redirects):raise ValueError('Use exact HTTPS or loopback redirect URIs')
    if body.get('token_endpoint_auth_method','none')!='none':raise ValueError('Use public OAuth client authentication with PKCE')
    if set(body.get('grant_types',['authorization_code','refresh_token']))-{'authorization_code','refresh_token'} or body.get('response_types',['code'])!=['code']:raise ValueError('Only authorization code and refresh grants are supported')
    ident=secrets.token_urlsafe(24)
    store.put('oauth-client',ident,{'id':ident,'redirect_uris':redirects,'name':str(body.get('client_name','MCP client'))[:100],'created_at':time.time()})
    return {'client_id':ident,'redirect_uris':redirects,'token_endpoint_auth_method':'none','grant_types':['authorization_code','refresh_token'],'response_types':['code'],'client_id_issued_at':int(time.time())}


def token(store, base, body):
    if body.get('resource',base+'/mcp')!=base+'/mcp':raise ValueError('Resource mismatch')
    grant=body.get('grant_type');raw=body.get('code' if grant=='authorization_code' else 'refresh_token','')
    if not isinstance(raw,str) or len(raw)>256:raise ValueError('Invalid grant')
    expected='mcp-code' if grant=='authorization_code' else 'mcp-refresh'
    if grant not in ('authorization_code','refresh_token'):raise ValueError('Unsupported grant type')
    digest=store.digest(raw)
    with store.db() as db:
        row=db.execute('SELECT * FROM tickets WHERE hash=? AND kind=?',(digest,expected)).fetchone()
        if not row or row['expires']<time.time():
            if grant=='refresh_token':
                spent=db.execute("SELECT body FROM records WHERE kind='spent-refresh' AND id=?",(digest,)).fetchone()
                if spent:
                    old=json.loads(spent[0])
                    if old['client_id']==body.get('client_id'):
                        db.execute("UPDATE records SET body=json_set(body,'$.revoked',json('true')) WHERE kind='oauth-grant' AND id=?",(old['grant_id'],))
            # Commit replay revocation before returning an error.
            invalid=True;data=None
        else:
            invalid=False;data=json.loads(row['body'])
            if data['client_id']!=body.get('client_id'):raise ValueError('Client mismatch')
            if grant=='authorization_code':
                verifier=body.get('code_verifier','')
                if not isinstance(verifier,str) or not re.fullmatch(r'[A-Za-z0-9._~-]{43,128}',verifier) or data['redirect_uri']!=body.get('redirect_uri') or not secrets.compare_digest(pkce(verifier),data['code_challenge']):raise ValueError('Invalid code or PKCE verifier')
            scope=data.get('scope','social:manage');gid=data.get('grant_id') or secrets.token_hex(16)
            gr=db.execute("SELECT body FROM records WHERE kind='oauth-grant' AND id=?",(gid,)).fetchone()
            record=json.loads(gr[0]) if gr else {'id':gid,'client_id':data['client_id'],'principal':'owner','scope':scope,'resource':base+'/mcp','expires':time.time()+30*86400,'revoked':False}
            if record['revoked'] or record['expires']<time.time():raise ValueError('Grant revoked or expired')
            if body.get('scope') and not set(body['scope'].split())<=set(scope.split()):raise ValueError('Refresh cannot expand scopes')
            scope=body.get('scope',scope);store.write(db,'oauth-grant',gid,record)
            db.execute('DELETE FROM tickets WHERE hash=?',(digest,))
            if grant=='refresh_token':store.write(db,'spent-refresh',digest,{'grant_id':gid,'client_id':data['client_id']})
            access=secrets.token_urlsafe(32);refresh=secrets.token_urlsafe(32)
            store.write(db,'access',store.digest(access),{'expires':time.time()+3600,'issuer':base,'resource':base+'/mcp','client_id':data['client_id'],'scope':scope,'grant_id':gid,'principal':'owner'})
            db.execute('INSERT INTO tickets VALUES(?,?,?,?)',(store.digest(refresh),'mcp-refresh',json.dumps({'client_id':data['client_id'],'scope':scope,'grant_id':gid}),record['expires']))
    if invalid:raise ValueError('Invalid or already used grant')
    return {'access_token':access,'token_type':'Bearer','expires_in':3600,'refresh_token':refresh,'scope':scope}


def validate(store, base, raw):
    try:
        record=store.get('access',store.digest(raw))
        if record['expires']<=time.time() or record['resource']!=base+'/mcp' or record.get('issuer',base)!=base:return None
        if record.get('grant_id'):
            grant=store.get('oauth-grant',record['grant_id'])
            if grant['revoked'] or grant['expires']<=time.time():return None
        return record
    except (ValueError,KeyError):return None


def revoke(store, body):
    raw=body.get('token','');digest=store.digest(raw)
    with store.db() as db:
        record=db.execute("SELECT body FROM records WHERE kind='access' AND id=?",(digest,)).fetchone()
        ticket=db.execute("SELECT body FROM tickets WHERE hash=? AND kind='mcp-refresh'",(digest,)).fetchone()
        data=json.loads((record or ticket)[0]) if (record or ticket) else None
        if data:
            if data.get('client_id')!=body.get('client_id'):raise ValueError('Client mismatch')
            if data.get('grant_id'):db.execute("UPDATE records SET body=json_set(body,'$.revoked',json('true')) WHERE kind='oauth-grant' AND id=?",(data['grant_id'],))
            db.execute("DELETE FROM records WHERE kind='access' AND id=?",(digest,));db.execute('DELETE FROM tickets WHERE hash=?',(digest,))
    return {}
