"""Installation-owned durable Flow orchestration. No AI inference or blind retries.

The gateway runs a singleton controller thread, independently of host tool polls.
Provider jobs remain authoritative; ambiguous submissions quarantine their account.
"""
import fcntl
import json
import os
import re
import shutil
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from . import flow_service, video_service

ACTIVE = {'submitting', 'processing', 'unknown'}
KINDS = ('job', 'video-job', 'image-job')
TERMINAL = {'completed', 'failed', 'stopped', 'blocked', 'cancelled'}


def daily_policy_limit():
    """Owner's conservative per-account daily *spend ceiling*, not a provider credit claim."""
    raw = os.getenv('VSO_FLOW_DAILY_CREDIT_LIMIT', '50')
    try: limit = int(raw)
    except (TypeError, ValueError): raise ValueError('Invalid daily Flow credit policy') from None
    if not 0 <= limit <= 1000: raise ValueError('Daily credit policy must be 0–1000')
    return limit


def daily_reserved(db, account_id, now=None):
    """Reserve the full quoted maximum for every submitted/uncertain job this day.

    Never interpret provider cash/bonus/free credit balances as a verified daily
    grant. A failed/unknown submission remains conservatively counted; provider
    reconciliation is required before adjusting credit records.
    """
    now = time.time() if now is None else now
    zone = ZoneInfo(os.getenv('VSO_FLOW_DAILY_TIMEZONE', 'Asia/Kolkata'))
    today = datetime.fromtimestamp(now, zone).date()
    total = 0
    for row in db.execute("SELECT body FROM records WHERE kind IN ('job','video-job','image-job')"):
        job = json.loads(row[0])
        if job.get('account_id') != account_id or job.get('status') == 'cancelled':
            continue
        timestamp = job.get('created_at', 0)
        if not isinstance(timestamp, (int, float)) or datetime.fromtimestamp(timestamp, zone).date() != today:
            continue
        quoted = job.get('max_credits', 0)
        if type(quoted) is int and quoted > 0: total += quoted
    return total


def assert_daily_budget(db, account_id, max_credits):
    if type(max_credits) is not int or max_credits < 0:
        raise ValueError('Invalid credit reservation')
    limit = daily_policy_limit()
    reserved = daily_reserved(db, account_id)
    if reserved + max_credits > limit:
        raise ValueError('Daily Flow per-account credit ceiling reached; do not spend additional credits')
    return limit - reserved - max_credits


def account_key(account):
    return account.get('service_alias') or account['id']


def assert_idle(db, account):
    """SQLite transaction admission: aliases of the same browser share a lock."""
    accounts = {json.loads(r[0])['id']: json.loads(r[0]) for r in db.execute("SELECT body FROM records WHERE kind='account'")}
    key = account_key(account)
    for row in db.execute("SELECT body FROM records WHERE kind IN ('job','video-job','image-job')"):
        job = json.loads(row[0])
        other = accounts.get(job.get('account_id'), {'id': job.get('account_id')})
        if job.get('status') in ACTIVE and account_key(other) == key:
            raise ValueError('This account has active or unresolved browser work; reconcile the original job')


def submit(engine, project_id, scenes, account_ids, max_credits, request_id, plan_id='', assemble=False):
    """Freeze an authorized batch. Only the controller performs provider I/O."""
    engine.store.get('project', project_id)
    if not isinstance(request_id, str) or not 1 <= len(request_id) <= 160:
        raise ValueError('Stable batch request ID required')
    if type(max_credits) is not int or not 0 <= max_credits <= 10000:
        raise ValueError('Batch credit ceiling must be 0–10000')
    if not isinstance(account_ids, list) or not 1 <= len(account_ids) <= 30 or len(set(account_ids)) != len(account_ids):
        raise ValueError('Provide explicitly authorized Flow account IDs')
    for ident in account_ids:
        if engine.store.get('account', ident)['provider'] != 'flow':
            raise ValueError('Choose Flow generation accounts')
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 12:
        raise ValueError('Provide 1–12 independent video scenes')
    normalized = []
    for scene in scenes:
        fields = {'prompt', 'model', 'duration', 'resolution', 'aspect_ratio', 'max_credits', 'first_frame_id', 'last_frame_id', 'reference_asset_ids', 'scene'}
        if not isinstance(scene, dict) or set(scene) - fields:
            raise ValueError('Unsupported scene fields')
        prompt = scene.get('prompt', '')
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 12000:
            raise ValueError('Each scene needs a bounded video prompt')
        opts = video_service.settings(*(scene.get(k) for k in ('model', 'duration', 'resolution', 'aspect_ratio', 'max_credits')))
        refs = {k: scene.get(k, [] if k == 'reference_asset_ids' else '') for k in ('first_frame_id', 'last_frame_id', 'reference_asset_ids')}
        video_service.validate_inputs(engine, opts, **refs)
        for ident in [refs['first_frame_id'], refs['last_frame_id'], *refs['reference_asset_ids']]:
            if ident: engine.asset_path(ident)
        if scene.get('scene',len(normalized))!=len(normalized):raise ValueError('Scene numbers must be sequential from zero')
        normalized.append({'prompt': prompt, **opts, **refs, 'scene': scene.get('scene', len(normalized))})
    if sum(s['max_credits'] for s in normalized) > max_credits:
        raise ValueError('Scene ceilings exceed the authorized batch ceiling')
    if plan_id:
        if any(s['max_credits']<1 for s in normalized):raise ValueError('Approved production scenes require a positive authorized ceiling; use a standalone zero-credit preflight instead')
        plan = engine.store.get('plan', plan_id)
        if plan['status'] not in ('ready', 'generating') or plan.get('revision_requested'):
            raise ValueError('Approve the current storyboard first')
        selected = plan['concepts'][plan['selected']]['scenes']
        if len(normalized) != len(selected) or any(s['scene'] != i or s['prompt'] != selected[i]['video_prompt'] or s['first_frame_id'] != plan['images'].get(str(i)) or s['last_frame_id'] or s['reference_asset_ids'] for i, s in enumerate(normalized)):
            raise ValueError('Batch must match every approved scene and original keyframe')
        if project_id != (plan.get('project_id') or plan_id): raise ValueError('Plan belongs to another project')
    elif assemble:
        raise ValueError('Automatic assembly requires an approved production plan')
    body = dict(project_id=project_id, scenes=normalized, account_ids=account_ids, max_credits=max_credits, plan_id=plan_id, assemble=assemble)
    ident = engine.store.digest('flow-batch:' + request_id)[:32]
    with engine.store.db() as db:
        row = db.execute("SELECT body FROM records WHERE kind='flow-batch' AND id=?", (ident,)).fetchone()
        if row:
            old = json.loads(row[0])
            if old['inputs'] != body: raise ValueError('Batch request ID belongs to different inputs')
            return old
        if plan_id:
            plan = engine._load(db, 'plan', plan_id)
            if plan['reserved'] + max_credits > plan['budget']: raise ValueError('Batch exceeds remaining production budget')
            for row in db.execute("SELECT body FROM records WHERE kind='flow-batch'"):
                prior = json.loads(row[0])
                if prior['inputs'].get('plan_id') == plan_id and prior['status'] != 'cancelled':
                    raise ValueError('Plan already has a batch; inspect it before requesting another take')
            if any(json.loads(r[0]).get('plan_id') == plan_id for r in db.execute("SELECT body FROM records WHERE kind='job'")):
                raise ValueError('Plan already has scene jobs; reconcile them first')
        batch = {'id': ident, 'inputs': body, 'status': 'queued', 'created_at': time.time(), 'tasks': [dict(scene=i, status='queued', request_id='batch-' + ident + '-' + str(i)) for i in range(len(normalized))]}
        engine.store.write(db, 'flow-batch', ident, batch)
    engine.store.log('flow.batch.queued', ident)
    return batch


def production_submit(engine, plan_id, account_ids, options, max_credits, request_id):
    plan = engine.store.get('plan', plan_id)
    if plan['selected'] is None: raise ValueError('Select and approve a concept first')
    if not isinstance(options, dict) or set(options) != {'model', 'duration', 'resolution', 'aspect_ratio', 'max_credits'}:
        raise ValueError('Provide exact model, duration, resolution, aspect_ratio and per-scene max_credits')
    scenes = [dict(prompt=s['video_prompt'], first_frame_id=plan['images'].get(str(i), ''), scene=i, **options) for i, s in enumerate(plan['concepts'][plan['selected']]['scenes'])]
    return submit(engine, plan.get('project_id') or plan_id, scenes, account_ids, max_credits, request_id, plan_id, True)


def cancel(engine, batch_id):
    with engine.store.db() as db:
        batch = engine._load(db, 'flow-batch', batch_id)
        batch['cancel_requested'] = True
        for task in batch['tasks']:
            if task['status'] == 'queued': task['status'] = 'cancelled'
        engine.store.write(db, 'flow-batch', batch_id, batch)
    return batch


def resources_ok(engine):
    if shutil.disk_usage(engine.store.root).free < 512 * 1024**2: return 'Less than 512 MiB disk free'
    try:
        available = next(int(line.split()[1]) for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))
        if available < 1024 * 1024: return 'Less than 1 GiB memory available for Flow generation'
        if os.getloadavg()[0] > (os.cpu_count() or 1) * 2.5: return 'Host load is above the submission limit'
    except (OSError, StopIteration): return 'Host resource observations unavailable'
    return ''


def status(engine):
    try: heartbeat = engine.store.get('runtime', 'flow-controller')
    except ValueError: heartbeat = {'state': 'not_started'}
    return {'worker': heartbeat, 'batches': engine.store.all('flow-batch'), 'accounts': [dict(id=a['id'], label=a.get('label'), status=a.get('status'), credits=a.get('credits'), verified_at=a.get('verified_at')) for a in engine.store.all('account') if a.get('provider') == 'flow'], 'execution': 'VPS-owned queue; no host polling required. Unknown submissions are never retried.'}


def _note(engine, kind, ident, **values):
    with engine.store.db() as db:
        record = engine._load(db, kind, ident)
        record.update(values)
        engine.store.write(db, kind, ident, record)
    return record


def _poll(engine, kind, job):
    now = time.time()
    if now < job.get('next_check_at', 0): return
    try:
        if kind == 'image-job':
            if job['status'] == 'unknown':
                _, config = flow_service.binding(engine, job['account_id'])
                view = flow_service.request(config, 'status', {'detailed': False})
                ids = job.get('backend_job_ids', [])
                matches = [j for j in view.get('jobs', []) if j.get('id') in ids or (not ids and Path(j.get('project', '')).name == job.get('project'))]
                if len(matches) != 1: raise ValueError('Original image job cannot be identified; account remains quarantined')
                _note(engine, kind, job['id'], status='processing', backend_job_ids=[matches[0]['id']])
            result = flow_service.image_poll(engine, job['id'])
        elif job['status'] == 'unknown':
            result = video_service.reconcile(engine, job['id'])
        else:
            result = video_service.check(engine, job['id']) if kind == 'video-job' else engine.video_poll(job['id'])
        values = {'last_checked_at': now, 'next_check_at': now + (60 if result.get('status') == 'unknown' else 15), 'poll_errors': 0}
        if result.get('status') == 'processing' and now - job.get('created_at', now) > 1200:
            values.update(status='unknown', error='Provider job exceeded twenty minutes; reconcile original output. No resubmission.', timed_out_at=now)
        _note(engine, kind, job['id'], **values)
        if result.get('status') in ('blocked','failed') and re.search(r'unusual|captcha|verification|access denied|rate.limit|quota',result.get('error',''),re.I):
            _note(engine,'account',job['account_id'],status='verification_required',generation_blocked_at=now)
    except Exception:
        # No exception or private provider URL is published. Preserve exact worker IDs.
        errors = job.get('poll_errors', 0) + 1
        values = dict(last_checked_at=now, next_check_at=now + min(300, 15 * 2**min(errors, 4)), poll_errors=errors, poll_error='Original output check failed; retained for reconciliation')
        if now - job.get('created_at', now) > 1200: values.update(status='unknown', timed_out_at=now)
        _note(engine, kind, job['id'], **values)


def _choose(engine, batch, scene):
    eligible = []
    for ident in batch['inputs']['account_ids']:
        a = engine.store.get('account', ident)
        if a.get('generation_blocked_at'):continue
        if a.get('status') != 'workspace_ready' or time.time() - a.get('verified_at', 0) > 600: continue
        if type(a.get('credits')) not in (int, float) or a['credits'] < scene['max_credits']: continue
        try:
            from .flow_models import validate_observed
            validate_observed(engine, ident, scene)
            with engine.store.db() as db:
                assert_idle(db, a)
                assert_daily_budget(db, ident, scene['max_credits'])
                if batch['inputs']['plan_id']:
                    from .production import enforce
                    plan = engine._load(db, 'plan', batch['inputs']['plan_id'])
                    enforce(db, engine._load(db, 'channel', plan['channel_id']), ident, scene['max_credits'])
        except ValueError: continue
        # Fair normal routing, never used as a retry after a provider refusal.
        last = max((j.get('created_at', 0) for kind in KINDS for j in engine.store.all(kind) if j.get('account_id') == ident), default=0)
        # Use smaller observed balances first; do not infer free-versus-paid provenance.
        eligible.append((a['credits'] > daily_policy_limit(), last, ident))
    return min(eligible)[2] if eligible else None


def _advance(engine, batch):
    # Recover exact deterministic child after an interrupted claim; never recreate it.
    for task in batch['tasks']:
        if task['status'] not in ('dispatching', 'processing', 'unknown'): continue
        kind = 'job' if batch['inputs']['plan_id'] else 'video-job'
        child_id = engine.store.digest(('video:' if kind == 'job' else 'flow-video:') + task['request_id'])[:32]
        try: child = engine.store.get(kind, child_id)
        except ValueError:
            task.update(status='unknown', error='Controller interrupted before durable child receipt; no automatic resubmission')
            continue
        task.update(status=child['status'], job_id=child_id, account_id=child['account_id'])
        if child.get('error'): task['error'] = child['error']
        if child['status'] == 'completed':
            task['asset_ids'] = child.get('asset_ids', []) or [child['asset_id']]
    if all(t['status'] == 'completed' for t in batch['tasks']):
        batch['status'] = 'completed'
        if batch['inputs']['assemble']:
            try:
                if not batch.get('edit_job_id'):
                    # start() is idempotent even if the controller restarts before saving this receipt.
                    edit = engine.video_assemble(batch['inputs']['plan_id'])
                    batch['edit_job_id'] = edit['id']
                edit = engine.store.get('edit-job',batch['edit_job_id'])
                batch['status'] = 'completed' if edit['status']=='completed' else 'assembling' if edit['status'] in ('queued','running') else 'needs_review'
                if edit.get('asset_id'):batch['final_asset_id']=edit['asset_id']
                if batch['status']=='needs_review':batch['assembly_error']='Original edit needs review; no automatic rerender'
            except Exception:
                batch['status']='needs_review'
                batch['assembly_error'] = 'Assembly needs review; original verified clips retained'
    elif all(t['status'] in TERMINAL for t in batch['tasks']): batch['status'] = 'cancelled' if batch.get('cancel_requested') else 'failed'
    elif any(t['status'] == 'unknown' for t in batch['tasks']): batch['status'] = 'needs_review'
    else: batch['status'] = 'processing' if any(t['status'] != 'queued' for t in batch['tasks']) else 'queued'
    with engine.store.db() as db:
        latest=engine._load(db,'flow-batch',batch['id'])
        if latest.get('cancel_requested'):
            batch['cancel_requested']=True
            for task in batch['tasks']:
                if task['status']=='queued':task['status']='cancelled'
        engine.store.write(db,'flow-batch',batch['id'],batch)
    return batch


def tick(engine):
    # Heartbeat precedes bounded provider I/O, so a slow provider is observable.
    engine.store.put('runtime','flow-controller',{'state':'checking','last_tick':time.time()})
    # Read/download existing results even under resource pressure or after restart.
    for kind in KINDS:
        for job in engine.store.all(kind):
            if job.get('status') in ('processing', 'unknown'): _poll(engine, kind, job)
    # Inspect at most one idle, already configured browser each tick. No new profiles.
    for account in sorted(engine.store.all('account'), key=lambda a: a.get('verified_at', 0)):
        if account.get('provider') != 'flow' or not account.get('service_alias') or time.time() - account.get('health_checked_at', 0) < 120: continue
        try:
            with engine.store.db() as db: assert_idle(db, account)
        except ValueError: continue
        if account.get('generation_blocked_at'):continue
        try:
            flow_service.inspect(engine, account['id'])
        except Exception:
            _note(engine, 'account', account['id'], status='service_unavailable', connection_error='Background Flow inspection failed')
        _note(engine, 'account', account['id'], health_checked_at=time.time())
        break
    # Keep each owned idle Chrome limited to a Flow project tab (and any active
    # accounts.google.com sign-in/verification tab). Never touch a busy account.
    from . import flow_browser_guard
    inspected = 0
    for account in sorted(engine.store.all('account'), key=lambda a: a.get('tab_guard_checked_at', 0)):
        if inspected >= 2: break
        if account.get('provider') != 'flow' or account.get('service_alias'): continue
        if time.time() - account.get('tab_guard_checked_at', 0) < 25: continue
        try:
            with engine.store.db() as db: assert_idle(db, account)
            result = flow_browser_guard.cleanup(engine.store.root, account['id'])
        except (OSError, ValueError, KeyError):
            continue
        _note(engine, 'account', account['id'],
              tab_guard_checked_at=time.time(), last_closed_extra_tabs=result['closed'])
        inspected += 1
    reason = resources_ok(engine)
    active = sum(j.get('status') in ('submitting', 'processing') for kind in KINDS for j in engine.store.all(kind))
    limit = max(1, min(5, int(os.getenv('VSO_FLOW_MAX_ACTIVE', '1'))))
    for batch in sorted(engine.store.all('flow-batch'), key=lambda b: b['created_at']):
        if batch['status'] in TERMINAL: continue
        batch = _advance(engine, batch)
        if reason or active >= limit or batch.get('cancel_requested'): continue
        task = next((t for t in batch['tasks'] if t['status'] == 'queued'), None)
        if task is None: continue
        scene = batch['inputs']['scenes'][task['scene']]
        ident = _choose(engine, batch, scene)
        if not ident:
            batch['waiting_reason'] = 'No idle authorized account with fresh health, compatible settings and known sufficient credits'
            engine.store.put('flow-batch', batch['id'], batch)
            continue
        # Durable claim precedes any upload/generate; a restart cannot duplicate spend.
        with engine.store.db() as db:
            current = engine._load(db, 'flow-batch', batch['id'])
            if current.get('cancel_requested') or current['tasks'][task['scene']]['status'] != 'queued': continue
            current['tasks'][task['scene']].update(status='dispatching', account_id=ident, dispatched_at=time.time())
            current.pop('waiting_reason', None)
            engine.store.write(db, 'flow-batch', batch['id'], current)
        try:
            if batch['inputs']['plan_id']:
                opts = {k: scene[k] for k in ('model', 'duration', 'resolution', 'aspect_ratio')}
                engine.video_request(batch['inputs']['plan_id'], task['scene'], ident, scene['max_credits'], task['request_id'], opts)
            else:
                args = {k: v for k, v in scene.items() if k != 'scene'}
                video_service.request(engine, account_id=ident, request_id=task['request_id'], project_id=batch['inputs']['project_id'], **args)
        except Exception:
            current = engine.store.get('flow-batch', batch['id'])
            current['tasks'][task['scene']].update(status='unknown', error='Dispatch interrupted; reconcile exact child before a new take')
            engine.store.put('flow-batch', batch['id'], current)
        _advance(engine, engine.store.get('flow-batch', batch['id']))
        active += 1
    engine.store.put('runtime', 'flow-controller', {'state': 'resource_paused' if reason else 'running', 'last_tick': time.time(), 'pause_reason': reason, 'max_active': limit, 'active_jobs': active})


def start(engine):
    stop = threading.Event()
    def loop():
        with (engine.store.root / 'flow-controller.lock').open('a+b') as guard:
            try: fcntl.flock(guard, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError: return
            while not stop.is_set():
                try: tick(engine)
                except Exception:
                    engine.store.put('runtime', 'flow-controller', {'state': 'error', 'last_tick': time.time(), 'error': 'Controller cycle failed; durable queue retained'})
                stop.wait(10)
    threading.Thread(target=loop, name='vso-flow-controller', daemon=True).start()
    return stop
