"""Private, resumable raw-byte media ingestion. Capability URLs carry no OAuth token."""
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import time
from pathlib import Path

TYPES={'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp','video/mp4':'.mp4','audio/wav':'.wav','audio/mpeg':'.mp3','audio/mp4':'.m4a'}
MAX_SIZE=2*1024**3
MAX_CHUNK=8*1024**2


def probe(path,media_type):
    with Path(path).open('rb') as f:head=f.read(32)
    checks={'image/png':head.startswith(b'\x89PNG\r\n\x1a\n'),'image/jpeg':head.startswith(b'\xff\xd8\xff'),'image/webp':head.startswith(b'RIFF') and head[8:12]==b'WEBP','video/mp4':head[4:8]==b'ftyp','audio/mp4':head[4:8]==b'ftyp','audio/wav':head.startswith(b'RIFF') and head[8:12]==b'WAVE','audio/mpeg':head.startswith(b'ID3') or (len(head)>1 and head[0]==255 and head[1]&224==224)}
    if not checks.get(media_type):raise ValueError('File signature does not match declared media type')
    r=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)],capture_output=True,timeout=15)
    if r.returncode or len(r.stdout)>100000:raise ValueError('Media decoder rejected this file')
    data=json.loads(r.stdout);streams=data.get('streams',[])
    expected='audio' if media_type.startswith('audio/') else 'video'
    stream=next((s for s in streams if s.get('codec_type')==expected),None)
    if not stream:raise ValueError('Expected media stream is missing')
    if expected=='video' and not 0<int(stream.get('width',0))*int(stream.get('height',0))<=64_000_000:raise ValueError('Invalid or excessive image dimensions')
    # Decode actual content, not only a MIME label or header. Longer playback QA is separate.
    args=['ffmpeg','-v','error','-threads','1','-i',str(path)]
    args+=['-frames:v','1'] if expected=='video' else ['-t','1']
    r=subprocess.run(args+['-f','null','-'],capture_output=True,timeout=30)
    if r.returncode:raise ValueError('Actual media decoding failed')
    return {'streams':[{k:s[k] for k in ('codec_type','codec_name','width','height','avg_frame_rate','sample_rate','channels','duration') if k in s} for s in streams],'duration':data.get('format',{}).get('duration')}


def sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()


def prepare(engine,filename,media_type,size,sha256,request_id):
    if media_type not in TYPES or type(size) is not int or not 0<size<=MAX_SIZE or not re.fullmatch('[0-9a-f]{64}',sha256):raise ValueError('Provide supported type, size (up to 2 GiB) and SHA-256')
    filename=Path(filename).name
    if not filename or len(filename)>200 or any(ord(c)<32 for c in filename) or not request_id or len(request_id)>200:raise ValueError('Invalid filename or request ID')
    if shutil.disk_usage(engine.store.root).free<size+128*1024**2:raise ValueError('Insufficient disk capacity for this transfer')
    ident=engine.store.digest('transfer:'+request_id)[:32];signature={'filename':filename,'media_type':media_type,'size':size,'sha256':sha256}
    with engine.store.db() as db:
        row=db.execute("SELECT body FROM records WHERE kind='transfer' AND id=?",(ident,)).fetchone()
        if row:
            record=json.loads(row[0])
            if any(record[k]!=v for k,v in signature.items()):raise ValueError('Request ID belongs to another transfer')
            if record['status']=='completed':return public(record)
            if record['status']=='rejected':raise ValueError('Rejected transfer; use a new request ID')
        else:record={**signature,'id':ident,'status':'pending','offset':0,'created_at':time.time()}
        token=secrets.token_urlsafe(32);record.update(capability_hash=engine.store.digest(token),expires=time.time()+900)
        engine.store.write(db,'transfer',ident,record)
    return {**public(record),'upload_url':engine.base+'/transfer/'+ident+'?ticket='+token,'method':'PUT','max_chunk_bytes':MAX_CHUNK,'instructions':'Transfer actual file bytes with Content-Range. This private capability expires in 15 minutes. Never paste file base64 into chat.'}


def public(record):return {k:v for k,v in record.items() if k not in ('capability_hash',)}


def receive(engine,ident,token,stream,length,content_range):
    if not re.fullmatch('[0-9a-f]{32}',ident):raise ValueError('Invalid transfer')
    record=engine.store.get('transfer',ident)
    if record.get('expires',0)<time.time() or not secrets.compare_digest(record.get('capability_hash',''),engine.store.digest(token)):raise PermissionError('Transfer authorization expired or invalid')
    match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',content_range or '')
    if not match or type(length) is not int or not 0<length<=MAX_CHUNK:raise ValueError('Use Content-Range and chunks up to 8 MiB')
    start,end,total=map(int,match.groups())
    if total!=record['size'] or end-start+1!=length or end>=total:raise ValueError('Transfer range mismatch')
    root=engine.store.root/'transfers';root.mkdir(mode=0o700,exist_ok=True)
    lock=root/(ident+'.lock');part=root/(ident+'.partial')
    with lock.open('a+b') as guard:
        os.chmod(lock,0o600)
        fcntl.flock(guard,fcntl.LOCK_EX)
        record=engine.store.get('transfer',ident);offset=part.stat().st_size if part.exists() else record.get('offset',0)
        if record['status']=='completed':return public(record)
        if record['status']=='rejected':raise ValueError('Rejected transfer; use a new request ID')
        if start>offset or (start<offset and end>=offset):raise ValueError('Upload offset mismatch; query media_transfer_status')
        duplicate=start<offset
        with part.open('r+b' if part.exists() else 'w+b') as f:
            f.seek(start);remaining=length
            try:
                while remaining:
                    chunk=stream.read(min(65536,remaining))
                    if not chunk:raise ValueError('Interrupted upload; resume from returned offset')
                    if duplicate:
                        if f.read(len(chunk))!=chunk:raise ValueError('Repeated chunk differs from stored bytes')
                    else:f.write(chunk)
                    remaining-=len(chunk)
                f.flush();os.fsync(f.fileno())
            finally:
                record['offset']=f.seek(0,2);engine.store.put('transfer',ident,record)
        if record['offset']==total:
            if sha256_file(part)!=record['sha256']:
                record['status']='rejected';engine.store.put('transfer',ident,record);raise ValueError('Checksum mismatch; start a new transfer request')
            try:metadata=probe(part,record['media_type'])
            except (ValueError,subprocess.SubprocessError):
                record['status']='rejected';engine.store.put('transfer',ident,record);raise ValueError('Media validation failed; use a new request ID') from None
            asset_id=record['sha256'];target=engine.store.root/'media'/(asset_id+TYPES[record['media_type']]);os.replace(part,target);target.chmod(0o600)
            asset={'id':asset_id,'file':target.name,'media_type':record['media_type'],'size':total,'original_filename':record['filename'],'technical':metadata}
            engine.store.put('asset',asset_id,asset);record.update(status='completed',asset_id=asset_id,completed_at=time.time());engine.store.put('transfer',ident,record)
        return public(record)


def preview(engine,asset_id):
    engine.asset_path(asset_id);token=engine.store.ticket('media-download',{'asset_id':asset_id},ttl=900)
    return {'asset':engine.store.get('asset',asset_id),'preview_url':engine.base+'/media-download?ticket='+token,'expires_in':900}
