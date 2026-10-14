"""Permission-bounded account snapshots for subsequent channel planning."""
import time

def capture(engine,account_id,request_id):
    account=engine.store.get('account',account_id)
    if account['provider'] not in ('youtube','instagram','facebook'):raise ValueError('Choose a connected publishing account')
    if not request_id or len(request_id)>200:raise ValueError('Stable snapshot request ID required')
    ident=engine.store.digest('analytics:'+account_id+':'+request_id)[:32]
    try:return engine.store.get('analytics',ident)
    except ValueError:pass
    observed=engine.accounts.info(account_id)
    if account['provider']=='youtube':
        values=observed.get('items',[])
        metrics=values[0].get('statistics',{}) if len(values)==1 else {}
    else:metrics={k:observed[k] for k in ('media_count','followers_count') if k in observed}
    record={'id':ident,'account_id':account_id,'provider':account['provider'],'observed_at':time.time(),'metrics':metrics,'scope_note':'Only metrics exposed by the existing authorized basic/read scopes. Full retention, revenue, attribution and Page Insights are not implemented.'}
    engine.store.put('analytics',ident,record);return record

def summary(engine,channel_id):
    channel=engine.store.get('channel',channel_id)
    return {'channel':channel,'productions':[p for p in engine.store.all('plan') if p['channel_id']==channel_id],'publications':[p for p in engine.store.all('publication') if p['account_id'] in channel['account_ids']],'account_snapshots':sorted([s for s in engine.store.all('analytics') if s['account_id'] in channel['account_ids']],key=lambda s:s['observed_at']),'interpretation':'Snapshots are observations, not causal performance predictions; use them with source-backed research for the next concept.'}
