"""Durable owner feedback for the connected creative agent; never renders by itself."""
import json
import time


def request(engine, plan_id, feedback, request_id):
    if not feedback.strip() or len(feedback) > 4000 or not request_id.strip():
        raise ValueError('Provide feedback (up to 4000 characters) and a stable request ID')
    ident = engine.store.digest('review:' + plan_id + ':' + request_id)[:32]
    with engine.store.db() as db:
        plan = engine._load(db, 'plan', plan_id)
        row = db.execute("SELECT body FROM records WHERE kind='review-request' AND id=?", (ident,)).fetchone()
        if row:
            old = json.loads(row[0])
            if old['feedback'] != feedback: raise ValueError('Request ID already has different feedback')
            return old
        record = {'id': ident, 'plan_id': plan_id, 'channel_id': plan['channel_id'],
                  'feedback': feedback, 'status': 'awaiting_agent', 'created_at': time.time(),
                  'replacement_plan_id': None}
        plan['revision_requested'] = True
        engine.store.write(db, 'plan', plan_id, plan)
        engine.store.write(db, 'review-request', ident, record)
    engine.store.log('review.request', ident)
    return record


def complete(engine, request_id, replacement_plan_id):
    with engine.store.db() as db:
        record = engine._load(db, 'review-request', request_id)
        plan = engine._load(db, 'plan', replacement_plan_id)
        if plan['channel_id'] != record['channel_id'] or plan['id'] == record['plan_id']:
            raise ValueError('Save a new revision for the same channel; preserve the original plan')
        if record['status'] == 'completed':
            if record['replacement_plan_id'] != replacement_plan_id: raise ValueError('Request already completed')
            return record
        record.update(status='completed', replacement_plan_id=replacement_plan_id, completed_at=time.time())
        engine.store.write(db, 'review-request', request_id, record)
    return record
