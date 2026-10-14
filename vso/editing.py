"""Durable CPU-bounded local FFmpeg assembly, optional music and subtitles."""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from .media import probe,sha256_file

def start(engine,plan_id,width,height,fps,fade_seconds,music_asset_id,music_volume,subtitles,request_id):
    p=engine.store.get('plan',plan_id)
    if type(width) is not int or type(height) is not int or min(width,height)<64 or max(width,height)>1920 or width%2 or height%2 or type(fps) is not int or not 12<=fps<=60:raise ValueError('Use even 64–1920 pixel dimensions and 12–60 FPS')
    if type(fade_seconds) not in (int,float) or not 0<=fade_seconds<=1 or type(music_volume) not in (int,float) or not 0<=music_volume<=1:raise ValueError('Fade and music volume must be 0–1')
    if not isinstance(subtitles,list) or len(subtitles)>1000:raise ValueError('Provide bounded subtitles with start/end/text')
    last=0
    for item in subtitles:
        if not isinstance(item,dict) or set(item)!={'start','end','text'} or type(item['start']) not in (int,float) or type(item['end']) not in (int,float) or not last<=item['start']<item['end']<=3600 or not isinstance(item['text'],str) or len(item['text'])>1000 or '-->' in item['text']:raise ValueError('Invalid or overlapping subtitle cue')
        last=item['end']
    if not request_id or len(request_id)>200:raise ValueError('Stable editing request ID required')
    count=len(p['concepts'][p['selected']]['scenes']) if p['selected'] is not None else 0
    jobs=[j for j in engine.store.all('job') if j['plan_id']==plan_id]
    if not count or len(jobs)!=count or {j['scene'] for j in jobs}!=set(range(count)) or any(j['status']!='completed' for j in jobs):raise ValueError('Every scene needs one exact completed clip')
    assets=[j['asset_id'] for j in sorted(jobs,key=lambda j:j['scene'])]
    for ident in assets:engine.asset_path(ident)
    if music_asset_id:
        a=engine.store.get('asset',music_asset_id)
        if not a['media_type'].startswith('audio/'):raise ValueError('Music must be an imported authorized audio file')
        engine.asset_path(music_asset_id)
    config=dict(plan_id=plan_id,asset_ids=assets,width=width,height=height,fps=fps,fade_seconds=fade_seconds,music_asset_id=music_asset_id,music_volume=music_volume,subtitles=subtitles)
    ident=engine.store.digest('edit:'+request_id)[:32]
    with engine.store.db() as db:
        row=db.execute("SELECT body FROM records WHERE kind='edit-job' AND id=?",(ident,)).fetchone()
        if row:
            old=json.loads(row[0])
            if old['inputs']!=config:raise ValueError('Request ID belongs to a different edit')
            return old
        active=db.execute("SELECT 1 FROM records WHERE kind='edit-job' AND json_extract(body,'$.status') IN ('queued','running','unknown')").fetchone()
        if active:raise ValueError('Finish or reconcile the existing editing job first')
        if p['status'] not in ('ready','generating','video_review') or p.get('revision_requested'):raise ValueError('Review the current storyboard before editing')
        job={'id':ident,'plan_id':plan_id,'status':'queued','inputs':config,'input_sha256':engine.store.digest(json.dumps(config,sort_keys=True)),'created_at':time.time()};engine.store.write(db,'edit-job',ident,job)
    try:subprocess.Popen([sys.executable,'-m','vso.editing',str(engine.store.root),engine.base,ident],stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,start_new_session=True,cwd=str(Path(__file__).resolve().parents[1]))
    except OSError:job.update(status='failed',error='Local editor could not start');engine.store.put('edit-job',ident,job)
    return job

def run(engine,ident):
    job=engine.store.get('edit-job',ident);cfg=job['inputs'];job.update(status='running',pid=os.getpid(),started_at=time.time());engine.store.put('edit-job',ident,job)
    try:
        os.nice(10)
        with tempfile.TemporaryDirectory(prefix='edit-',dir=engine.store.root) as directory:
            root=Path(directory);normalized=[];durations=[]
            def ff(args):
                r=subprocess.run(['ffmpeg','-nostdin','-v','error','-threads','1','-filter_threads','1','-y',*args],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=300)
                if r.returncode:raise ValueError('FFmpeg rejected edit inputs; original media retained')
            for i,asset_id in enumerate(cfg['asset_ids']):
                src=engine.asset_path(asset_id);metadata=probe(src,'video/mp4');duration=float(metadata.get('duration') or 0)
                if not 0<duration<=600:raise ValueError('Clip must have a finite duration up to 10 minutes')
                durations.append(duration);out=root/f'clip-{i}.mp4';has_audio=any(s['codec_type']=='audio' for s in metadata['streams'])
                filters=f"scale={cfg['width']}:{cfg['height']}:force_original_aspect_ratio=decrease,pad={cfg['width']}:{cfg['height']}:(ow-iw)/2:(oh-ih)/2,setsar=1,fps={cfg['fps']},format=yuv420p"
                fade=min(float(cfg['fade_seconds']),duration/4)
                if fade:filters+=f',fade=t=in:st=0:d={fade},fade=t=out:st={duration-fade}:d={fade}'
                args=['-i',str(src)]
                if not has_audio:args+=['-f','lavfi','-i','anullsrc=r=48000:cl=stereo']
                args+=['-vf',filters,'-map','0:v:0','-map','0:a:0' if has_audio else '1:a:0','-af','aresample=48000','-ac','2','-c:v','libx264','-preset','veryfast','-threads','1','-c:a','aac','-t',str(duration),'-movflags','+faststart',str(out)]
                ff(args);normalized.append(out)
            listing=root/'concat.txt';listing.write_text(''.join(f"file '{p.name}'\n" for p in normalized));joined=root/'joined.mp4'
            ff(['-f','concat','-safe','1','-i',str(listing),'-c','copy','-movflags','+faststart',str(joined)])
            total=sum(durations);output=joined
            if cfg['subtitles'] or cfg['music_asset_id']:
                args=['-i',str(joined)]
                if cfg['music_asset_id']:args+=['-stream_loop','-1','-i',str(engine.asset_path(cfg['music_asset_id']))]
                if cfg['subtitles']:
                    def stamp(seconds):
                        ms=round(seconds*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
                    if cfg['subtitles'][-1]['end']>total:raise ValueError('Subtitle exceeds final video duration')
                    subs=root/'captions.srt';subs.write_text(''.join(f"{i+1}\n{stamp(s['start'])} --> {stamp(s['end'])}\n{s['text']}\n\n" for i,s in enumerate(cfg['subtitles'])))
                    args+=['-vf',f'subtitles={subs.as_posix()}','-c:v','libx264','-preset','veryfast','-threads','1']
                else:args+=['-c:v','copy']
                if cfg['music_asset_id']:args+=['-filter_complex',f"[1:a]volume={cfg['music_volume']}[music];[0:a][music]amix=inputs=2:duration=first:normalize=0[a]",'-map','0:v:0','-map','[a]']
                args+=['-c:a','aac','-t',str(total),'-movflags','+faststart',str(root/'final.mp4')];ff(args);output=root/'final.mp4'
            metadata=probe(output,'video/mp4');asset_id=sha256_file(output);target=engine.store.root/'media'/(asset_id+'.mp4');os.replace(output,target);target.chmod(0o600)
            engine.store.put('asset',asset_id,{'id':asset_id,'file':target.name,'media_type':'video/mp4','size':target.stat().st_size,'technical':metadata,'origin':{'editing_job_id':ident,'input_sha256':job['input_sha256']}})
            engine.video_attach(cfg['plan_id'],asset_id)
            job.update(status='completed',asset_id=asset_id,technical=metadata,creative_review_required=True)
    except Exception:job.update(status='failed',error='Local editing failed; inspect input durations/streams/subtitles. Original assets and generation jobs retained.')
    job['finished_at']=time.time();engine.store.put('edit-job',ident,job)

if __name__=='__main__':
    from .store import Store
    from .engine import Engine
    run(Engine(Store(sys.argv[1]),sys.argv[2]),sys.argv[3])
