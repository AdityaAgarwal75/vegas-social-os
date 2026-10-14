"""Evidence-based operational readiness; no fabricated live provider tests."""
import shutil,time

def status(engine):
    accounts=engine.store.all('account');now=time.time()
    checks=[{'feature':'Runtime','state':'ready','detail':'Private state opened successfully'},
            {'feature':'Media assembly','state':'ready' if shutil.which('ffmpeg') else 'missing','detail':'FFmpeg executable; actual rendering must be checked separately'},
            {'feature':'Creative agent','state':'host_required','detail':'Strategy/daily brief queues need a real connected host; no unattended ChatGPT claim'}]
    from .flow_runtime import installed
    checks.append({'feature':'Flow execution engine','state':'installed' if installed() else 'existing_service_only' if any(a.get('service_alias') for a in accounts) else 'missing',
                   'detail':'Complete managed engine for native profiles; imported accounts retain their existing engine owner. Installed does not mean rendering verified.'})
    for provider in ['flow','youtube','instagram','facebook','drive']:
        entries=[a for a in accounts if a['provider']==provider];verified=[a for a in entries if a['status'] in ('workspace_ready','connected')]
        checks.append({'feature':provider.title(),'state':'connected' if verified else 'needs_connection','detail':f'{len(verified)}/{len(entries)} identities ready; publishing/rendering evidence is separate'})
    jobs=[j for k in ['job','image-job','video-job'] for j in engine.store.all(k)]
    unresolved=[{'id':j['id'],'status':j['status'],'account_id':j['account_id']} for j in jobs if j['status'] in ('unknown','submitting','processing')]
    return {'checked_at':now,'checks':checks,'unresolved_jobs':unresolved,'completed_images':len([j for j in engine.store.all('image-job') if j['status']=='completed']),'completed_clips':len([j for j in jobs if j.get('status')=='completed' and j.get('model','').startswith(('Veo','Omni'))]),'limits':['Live publishing requires eligible accounts, grants and exact release approval','Paid video rendering is not tested by a zero-credit preflight','Availability differs by account/region; refresh model menus before production']}
