"""Reconcile interrupted local work without repeating provider writes."""
from pathlib import Path
import time

def alive(record):
    try:return Path('/proc',str(record['pid']),'stat').read_text().split(') ',1)[1].split()[19]==record['start_ticks']
    except (OSError,KeyError,IndexError):return False

def startup(engine):
    for kind in ('job','video-job','image-job'):
        for job in engine.store.all(kind):
            if job['status']=='submitting':
                job.update(status='unknown',error='Gateway restarted during submission; reconcile the original provider project. Never retry automatically.');engine.store.put(kind,job['id'],job)
    for kind in ('edit-job','media-ingest'):
        for job in engine.store.all(kind):
            if job['status'] in ('queued','running') and not alive(job):
                job.update(status='unknown',error='Original local worker ended without a durable result; inspect partial assets before a new request.');engine.store.put(kind,job['id'],job)
    engine.store.put('health','recovery',{'checked_at':time.time(),'provider_writes_retried':False})
