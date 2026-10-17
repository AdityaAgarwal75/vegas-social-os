"""Persisted briefs + approved release scheduling; a host agent does creative work."""
import threading
import time
from . import schedule, publishing


def status(engine):
    try: daily = engine.store.get('schedule', 'daily')
    except ValueError: daily = None
    try: worker = engine.store.get('runtime', 'scheduler')
    except ValueError: worker = None
    return {'daily': daily, 'worker': worker, 'briefs': engine.store.all('brief'),
            'agent_endpoint': engine.base + '/mcp',
            'creative_execution': 'A connected host agent must consume briefs. The VPS cannot start a ChatGPT conversation or access native image tools by itself.',
            'publishing_execution': 'The installed scheduler releases exact approved scheduled posts while the VPS is running. Unknown outcomes are never retried.'}


def pause(engine):
    try: daily = engine.store.get('schedule', 'daily')
    except ValueError: return {'paused': True}
    daily['paused'] = True
    engine.store.put('schedule', 'daily', daily)
    return daily


def complete(engine, brief_id, plan_id):
    brief = engine.store.get('brief', brief_id)
    plan = engine.store.get('plan', plan_id)
    if brief['channel_id'] != plan['channel_id']: raise ValueError('Plan belongs to a different channel')
    brief.update(status='prepared', plan_id=plan_id)
    engine.store.put('brief', brief_id, brief)
    return brief


def tick(engine):
    from .events import tick as event_tick
    failures=[]
    try:event_tick(engine)
    except Exception:failures.append('events')
    try:briefs=schedule.tick(engine)
    except Exception:briefs=[];failures.append('briefs')
    for post in engine.store.all('publication'):
        if post.get('kind') != 'composer': continue
        try:
            if post['status'] == 'scheduled' and post['scheduled_at'] <= time.time():
                # Long outages must not release a stale campaign without review.
                with engine.store.db() as db:
                    current = engine._load(db, 'publication', post['id'])
                    if current['status'] != 'scheduled': continue
                    current['status'] = 'missed' if time.time() - current['scheduled_at'] > 3600 else 'approved'
                    engine.store.write(db, 'publication', post['id'], current)
                if current['status'] == 'approved': publishing.execute(engine, post['id'])
            elif post['status'] in ('processing', 'children_processing', 'provider_processing'):
                publishing.poll(engine, post['id'])
        except Exception:
            failures.append(post['id'])
            engine.store.put('runtime','publication-check:'+post['id'],{'last_check':time.time(),'state':'error','detail':'Original publication needs reconciliation; no new upload was attempted'})
    engine.store.put('runtime', 'scheduler', {'last_tick': time.time(), 'state': 'degraded' if failures else 'running','failed_components':failures})
    return briefs


def start(engine):
    stop = threading.Event()
    def loop():
        while not stop.is_set():
            try: tick(engine)
            except Exception:
                engine.store.put('runtime', 'scheduler', {'last_tick': time.time(), 'state': 'error', 'error': 'Check account connections and scheduled releases'})
            stop.wait(30)
    thread = threading.Thread(target=loop, name='vso-scheduler', daemon=True)
    thread.start()
    return stop
