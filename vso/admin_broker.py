"""Root-owned Unix-socket broker. Install a standalone copy; never import gateway code."""
import argparse
import base64
import hashlib
import hmac
import json
import os
import pwd
import re
import secrets
import shutil
import signal
import stat
import socket
import socketserver
import sqlite3
import struct
import subprocess
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path

STATE=Path(os.getenv('VSO_ADMIN_STATE','/var/lib/vegas-social-admin'))
SOCKET=os.getenv('VSO_ADMIN_SOCKET','/run/vegas-social-admin/broker.sock')
ALLOWED_UID=int(os.getenv('VSO_ADMIN_UID','-1'))
PROTECTED=('/opt/credentials-vault','/var/lib/flowlogin/profiles','/usr/local/lib/vegas-social-admin','/var/lib/vegas-social-admin','/proc','/sys','/dev','/root/.ssh','/etc/shadow','/etc/gshadow','/var/lib/vegas-social-os')
READ_ONLY={'inventory','metrics','file_list','file_read','disk_usage','logs','network','request_status','job_status'}
ROUTINE={'inventory','metrics','file_list','file_read','disk_usage','logs','network','request_status','job_status','backup','job_cancel'}


def redact(text):
    text=re.sub(r"(?i)([\"']?(?:access_token|refresh_token|id_token|client_secret|api_key|cookie|password|secret)[\"']?\s*[:=]\s*)(?:\"[^\"]*\"|'[^']*'|[^\s,;]+)",r'\1[REDACTED]',text)
    text=re.sub(r'(?im)(authorization\s*[:=]\s*bearer\s+|(?:password|passwd|secret|token|api[_-]?key|cookie|code_verifier)\s*[:=]\s*)[^\s,;]+',r'\1[REDACTED]',text)
    text=re.sub(r'-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----','[REDACTED PRIVATE KEY]',text,flags=re.S)
    text=re.sub(r'([?&](?:ticket|token|code|key)=)[^&\s]+',r'\1[REDACTED]',text)
    text=re.sub(r'(?i)(aws_secret_access_key\s*[:=]\s*)[^\s,;]+',r'\1[REDACTED]',text)
    text=re.sub(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b','[REDACTED AWS KEY]',text)
    return text[:65536]


@contextmanager
def db():
    STATE.mkdir(mode=0o700,parents=True,exist_ok=True)
    conn=sqlite3.connect(STATE/'broker.sqlite',timeout=20);conn.row_factory=sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL');conn.execute('CREATE TABLE IF NOT EXISTS records(kind TEXT,id TEXT,body TEXT,PRIMARY KEY(kind,id))');conn.execute('CREATE TABLE IF NOT EXISTS audit(at REAL,action TEXT,entity TEXT)')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback();raise
    finally:conn.close()


def get(kind,ident):
    with db() as conn:r=conn.execute('SELECT body FROM records WHERE kind=? AND id=?',(kind,ident)).fetchone()
    if not r:raise ValueError('Broker record unavailable')
    return json.loads(r[0])


def put(kind,ident,body):
    with db() as conn:conn.execute('INSERT OR REPLACE INTO records VALUES(?,?,?)',(kind,ident,json.dumps(body)))


def audit(action,ident):
    with db() as conn:conn.execute('INSERT INTO audit VALUES(?,?,?)',(time.time(),action,ident))


def target(value,read=False):
    if not isinstance(value,str) or not value.startswith('/') or len(value)>4096:raise ValueError('Use an absolute server path')
    p=Path(value)
    if any(x=='..' for x in p.parts):raise ValueError('Traversal is forbidden')
    # Resolve every parent, including symlinks, before applying protected boundaries.
    real=p.resolve()
    if str(real)=='/':raise ValueError('Root directory is not a file target')
    if read and (any(str(real)==x or str(real).startswith(x+'/') for x in PROTECTED) or any(x in ('profiles','.ssh','.aws') for x in real.parts) or real.name.startswith('.env') or re.search(r'(vault\.key|token|secret|credentials|\.(pem|key|sqlite|db)$)',real.name,re.I)):raise ValueError('Credential/session/protected files cannot be returned through MCP')
    return real


def safe_open(path,flags=os.O_RDONLY,mode=0o600):
    """No symlink following at any component; keep the verified directory FD open."""
    parts=Path(path).parts
    directory=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        for name in parts[1:-1]:
            new=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=directory)
            os.close(directory);directory=new
        return os.open(parts[-1],flags|os.O_NOFOLLOW|os.O_NONBLOCK,mode,dir_fd=directory)
    finally:os.close(directory)


def secured_parent(path):
    """Privileged mutations require a root-owned, non-writable parent chain."""
    fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        for name in Path(path).parts[1:-1]:
            nxt=os.open(name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd)
            os.close(fd);fd=nxt;info=os.fstat(fd)
            if info.st_uid!=0 or info.st_mode&0o022:raise ValueError('Untrusted parent directory; use an explicitly reviewed break-glass operation')
        return os.dup(fd)
    finally:os.close(fd)


def process_matches(pid,ticks):
    try:return Path('/proc',str(pid),'stat').read_text().split(') ',1)[1].split()[19]==ticks
    except (OSError,IndexError):return False


def reconcile(ident):
    job=get('job',ident)
    alive=any(process_matches(job.get(k,0),job.get(t)) for k,t in [('runner_pid','runner_ticks'),('pgid','start_ticks')])
    if job['status']=='starting' and time.time()-job['created_at']<10:return {**job,'original_process_alive':alive,'safe_to_repeat':False}
    if job['status'] in ('unknown','starting','running') and not alive:
        job.update(status='unknown',error='Original process ended without a durable result. Inspect effects before a new operation.');put('job',ident,job)
    return {**job,'original_process_alive':alive,'safe_to_repeat':False}


def service(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_@.-]*\.(service|timer|socket)',value):raise ValueError('Use an exact systemd unit name')
    return value


def run_read(argv):return run_command(argv,15,track=False)


def validate(op,args):
    if not isinstance(args,dict) or len(json.dumps(args))>50000:raise ValueError('Bounded object arguments required')
    keys={'inventory':set(),'metrics':set(),'network':set(),'file_list':{'path'},'file_read':{'path','offset','limit'},'disk_usage':{'path'},'logs':{'unit','lines'},'service':{'unit','action'},'file_write':{'path','content','expected_sha256'},'file_move':{'source','destination'},'backup':{'path'},'restore':{'backup_id'},'packages':{'names','action'},'command':{'command','timeout'},'job_resolve':{'job_id','acknowledge_partial_effects'},'request_status':{'request_id'},'job_status':{'job_id'},'job_cancel':{'job_id'}}
    if op not in keys or set(args)-keys[op]:raise ValueError('Unsupported operation or arguments')
    if op in ('file_list','file_read','disk_usage','backup','file_write'):target(args.get('path'),read=op=='file_read')
    if op in ('service','logs'):service(args.get('unit'))
    if op=='service' and args.get('action') not in ('start','stop','restart','enable','disable','reload'):raise ValueError('Unsupported service action')
    if op=='file_write' and (not isinstance(args.get('content'),str) or len(args['content'].encode())>40000):raise ValueError('Write at most 40 KiB text per operation')
    if op=='file_move':target(args.get('source'));target(args.get('destination'))
    if op=='packages':
        names=args.get('names',[])
        if not isinstance(names,list) or not 1<=len(names)<=30 or any(not isinstance(n,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9+._:-]{0,100}',n) for n in names) or args.get('action') not in ('install','upgrade'):raise ValueError('Provide exact package names and install/upgrade')
    if op=='job_resolve' and args.get('acknowledge_partial_effects') is not True:raise ValueError('Explicitly acknowledge inspected partial effects')
    if op=='command' and (not isinstance(args.get('command'),str) or not args['command'].strip() or len(args['command'])>12000 or type(args.get('timeout',60)) is not int or not 1<=args.get('timeout',60)<=900):raise ValueError('Bounded command and 1–900 second timeout required')


def needs_approval(op,args):
    if op=='service' and args.get('unit')=='vegas-social-os.service' and args.get('action') in ('start','restart','reload'):return False
    return op not in ROUTINE


def request(op,args,request_id):
    validate(op,args)
    if not isinstance(request_id,str) or not request_id or len(request_id)>200:raise ValueError('Stable request ID required')
    ident=hashlib.sha256(('admin:'+request_id).encode()).hexdigest()[:32]
    with db() as conn:
        conn.execute('BEGIN IMMEDIATE');row=conn.execute("SELECT body FROM records WHERE kind='request' AND id=?",(ident,)).fetchone()
        if row:
            old=json.loads(row[0])
            if old['operation']!=op or old['arguments']!=args:raise ValueError('Request ID already has different arguments')
            return view(old)
        body={'id':ident,'operation':op,'arguments':args,'created_at':time.time(),'expires':time.time()+900,'status':'awaiting_owner' if needs_approval(op,args) else 'approved','approved_until':time.time()+300 if not needs_approval(op,args) else 0}
        conn.execute('INSERT INTO records VALUES(?,?,?)',('request',ident,json.dumps(body)))
    audit('request.'+op,ident);return view(body)


def view(record):
    return {**{k:v for k,v in record.items() if k!='arguments'},'arguments':{k:('[content omitted]' if k=='content' else redact(v) if isinstance(v,str) else v) for k,v in record.get('arguments',{}).items()},'authorization':'Owner dashboard TOTP required' if record.get('status')=='awaiting_owner' else 'Bound to this exact operation'}


def totp(secret,counter):
    key=base64.b32decode(secret);raw=hmac.new(key,struct.pack('!Q',counter),hashlib.sha1).digest();offset=raw[-1]&15;return str((int.from_bytes(raw[offset:offset+4],'big')&0x7fffffff)%1000000).zfill(6)


def approve(ident,code):
    with db() as conn:
        conn.execute('BEGIN IMMEDIATE')
        bucket=str(int(time.time()//30));attempt=conn.execute("SELECT body FROM records WHERE kind='approval-rate' AND id=?",(bucket,)).fetchone();count=json.loads(attempt[0]) if attempt else 0
        if count>=5:raise ValueError('Owner approval rate limit reached')
        conn.execute('INSERT OR REPLACE INTO records VALUES(?,?,?)',('approval-rate',bucket,json.dumps(count+1)));conn.commit();conn.execute('BEGIN IMMEDIATE')
        setting=conn.execute("SELECT body FROM records WHERE kind='settings' AND id='totp'").fetchone()
        if not setting:raise ValueError('Owner must enroll administrator approval first')
        setting=json.loads(setting[0]);counter=int(time.time()//30)
        valid=next((n for n in (counter-1,counter,counter+1) if n>setting.get('last_counter',-1) and secrets.compare_digest(totp(setting['secret'],n),str(code))),None)
        if valid is None:raise ValueError('Invalid or already used owner approval code')
        row=conn.execute("SELECT body FROM records WHERE kind='request' AND id=?",(ident,)).fetchone()
        if not row:raise ValueError('Request unavailable')
        record=json.loads(row[0])
        if record['status']!='awaiting_owner' or record['expires']<time.time():raise ValueError('Request expired or no longer awaits approval')
        record.update(status='approved',owner_approved=True,approved_until=time.time()+120);setting['last_counter']=valid
        conn.execute("UPDATE records SET body=? WHERE kind='settings' AND id='totp'",(json.dumps(setting),));conn.execute("UPDATE records SET body=? WHERE kind='request' AND id=?",(json.dumps(record),ident))
    audit('owner.approve',ident);return view(record)


def enrollment(ticket,code=None):
    with db() as conn:
        conn.execute('BEGIN IMMEDIATE');row=conn.execute("SELECT body FROM records WHERE kind='settings' AND id='enrollment'").fetchone()
        if not row:raise ValueError('Request a private root-issued enrollment link')
        record=json.loads(row[0])
        if record['expires']<time.time() or not secrets.compare_digest(record['hash'],hashlib.sha256(ticket.encode()).hexdigest()):raise ValueError('Enrollment link expired or invalid')
        if conn.execute("SELECT 1 FROM records WHERE kind='settings' AND id='totp'").fetchone():raise ValueError('Already enrolled; secret is never returned again')
        if code is None:return {'secret':record['secret'],'instructions':'Add this key to your personal authenticator. Enter the current code here. Never send the key or code in chat.'}
        counter=int(time.time()//30)
        if not any(secrets.compare_digest(totp(record['secret'],n),str(code)) for n in (counter-1,counter,counter+1)):raise ValueError('Invalid authenticator code')
        conn.execute('INSERT INTO records VALUES(?,?,?)',('settings','totp',json.dumps({'secret':record['secret'],'last_counter':counter})));conn.execute("DELETE FROM records WHERE kind='settings' AND id='enrollment'")
    audit('owner.enroll','owner');return {'enrolled':True}


def execute(ident):
    with db() as conn:
        conn.execute('BEGIN IMMEDIATE');row=conn.execute("SELECT body FROM records WHERE kind='request' AND id=?",(ident,)).fetchone()
        if not row:raise ValueError('Request unavailable')
        record=json.loads(row[0])
        if record.get('job_id'):
            row=conn.execute("SELECT body FROM records WHERE kind='job' AND id=?",(record['job_id'],)).fetchone()
            return json.loads(row[0])
        if record['status']!='approved' or record['approved_until']<time.time():raise ValueError('Exact operation needs current owner approval')
        validate(record['operation'],record['arguments'])
        if needs_approval(record['operation'],record['arguments']) and not record.get('owner_approved'):raise ValueError('Owner approval required for these exact arguments')
        active=conn.execute("SELECT 1 FROM records WHERE kind='job' AND json_extract(body,'$.status') IN ('starting','running','unknown')").fetchone()
        if active and record['operation']!='job_resolve':raise ValueError('Finish or cancel active administrator job first')
        job={'id':ident,'request_id':ident,'status':'starting','created_at':time.time(),'operation':record['operation']};record.update(status='executing',job_id=ident)
        conn.execute('INSERT INTO records VALUES(?,?,?)',('job',ident,json.dumps(job)));conn.execute("UPDATE records SET body=? WHERE kind='request' AND id=?",(json.dumps(record),ident))
    runner=subprocess.Popen([sys.executable,'-I',str(Path(__file__).resolve()),'run-job',ident],env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C.UTF-8','VSO_ADMIN_STATE':str(STATE)},start_new_session=True,stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    # The child records its own identity before executing. Never overwrite its newer state here.
    audit('job.start',ident);return job


def backup(path):
    path=target(path)
    if path==STATE or path in STATE.parents or str(path).startswith(('/proc/','/sys/','/dev/')):raise ValueError('Cannot recursively back up broker state or pseudo filesystems')
    ident=secrets.token_hex(16);folder=STATE/'backups'/ident;folder.mkdir(parents=True,mode=0o700)
    dst=folder/'payload'
    if path.is_dir():shutil.copytree(path,dst,symlinks=True)
    else:shutil.copy2(path,dst,follow_symlinks=False)
    put('backup',ident,{'id':ident,'source':str(path),'payload':str(dst),'created_at':time.time()});return {'backup_id':ident,'source':str(path)}


def perform(op,args):
    if op=='inventory':return {'services':run_read(['systemctl','list-units','--type=service','--all','--no-pager']),'processes':run_read(['ps','-eo','pid,ppid,user,comm,%cpu,%mem,rss'])}
    if op=='metrics':return {'memory':run_read(['free','-m']),'disk':run_read(['df','-h']),'load':list(os.getloadavg()),'cpu_count':os.cpu_count()}
    if op=='network':return {'listeners':run_read(['ss','-lntup']),'addresses':run_read(['ip','-brief','address'])}
    if op=='file_list':return {'entries':[{'name':p.name,'directory':p.is_dir(),'symlink':p.is_symlink()} for p in list(target(args['path']).iterdir())[:1000]]}
    if op=='file_read':
        p=target(args['path'],read=True);offset=args.get('offset',0);limit=args.get('limit',16000)
        if type(offset) is not int or type(limit) is not int or offset<0 or not 1<=limit<=65536 or not p.is_file():raise ValueError('Invalid bounded file read')
        with os.fdopen(safe_open(p),'rb') as f:
            info=os.fstat(f.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or not info.st_mode&0o044:raise ValueError('Private, linked or non-regular file cannot be exposed')
            f.seek(offset);raw=f.read(limit)
        text=raw.decode('utf-8');return {'path':str(p),'content':redact(text),'size':info.st_size,'offset':offset,'content_sha256':hashlib.sha256(raw).hexdigest()}
    if op=='disk_usage':return run_read(['du','-h','--max-depth=1',str(target(args['path']))])
    if op=='logs':return run_read(['journalctl','-u',service(args['unit']),'-n',str(min(200,max(1,int(args.get('lines',50))))),'--no-pager'])
    if op=='service':return run_read(['systemctl',args['action'],service(args['unit'])])
    if op=='backup':return backup(args['path'])
    if op=='file_write':
        p=target(args['path']);expected=args.get('expected_sha256','');checkpoint={}
        parent=secured_parent(p);tmp=p.name+'.vso-'+secrets.token_hex(6)
        try:
            try:
                fd=os.open(p.name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=parent)
            except FileNotFoundError:fd=None
            mode=0o644
            if fd is not None:
                with os.fdopen(fd,'rb') as f:
                    info=os.fstat(f.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_size>16*1024**2:raise ValueError('Use a regular bounded file with one link')
                    raw=f.read();mode=info.st_mode&0o777
                if not expected or hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Expected checksum required before replacing existing file')
                checkpoint=backup(str(p))
            with os.fdopen(os.open(tmp,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,mode,dir_fd=parent),'wb') as f:
                f.write(args['content'].encode());f.flush();os.fsync(f.fileno())
            os.replace(tmp,p.name,src_dir_fd=parent,dst_dir_fd=parent);os.fsync(parent)
        finally:
            try:os.unlink(tmp,dir_fd=parent)
            except FileNotFoundError:pass
            os.close(parent)
        return {'path':str(p),'sha256':hashlib.sha256(args['content'].encode()).hexdigest(),**checkpoint}
    if op=='file_move':
        src=target(args['source']);dst=target(args['destination'])
        if dst.exists():raise ValueError('Destination exists; do not overwrite')
        srcfd=secured_parent(src);dstfd=secured_parent(dst)
        try:
            checkpoint=backup(str(src))
            # Both root-owned parent chains remain open; refuse overwriting destinations.
            if dst.exists():raise ValueError('Destination exists')
            os.rename(src.name,dst.name,src_dir_fd=srcfd,dst_dir_fd=dstfd)
        finally:os.close(srcfd);os.close(dstfd)
        return {'source':str(src),'destination':str(dst),**checkpoint}
    if op=='job_resolve':
        job=reconcile(args['job_id'])
        if job['status']!='unknown' or job['original_process_alive']:raise ValueError('Only an inspected, ended unknown job can be resolved')
        job.update(status='resolved',owner_acknowledged_at=time.time());put('job',job['id'],{k:v for k,v in job.items() if k not in ('safe_to_repeat','original_process_alive')})
        return {'resolved_job_id':job['id'],'operation_was_not_repeated':True}
    if op=='restore':
        record=get('backup',args['backup_id']);src=Path(record['payload']);dst=target(record['source']);parent=secured_parent(dst);os.close(parent);checkpoint=backup(str(dst)) if dst.exists() else {}
        if src.is_dir():
            if dst.exists():raise ValueError('Directory restore requires explicit break-glass migration; existing tree retained')
            shutil.copytree(src,dst,symlinks=True)
        else:shutil.copy2(src,dst,follow_symlinks=False)
        return {'restored':str(dst),**checkpoint}
    if op=='packages':return run_command(['apt-get','-y','install','--only-upgrade']+args['names'] if args['action']=='upgrade' else ['apt-get','-y','install']+args['names'],900)
    if op=='command':return run_command(['/bin/bash','--noprofile','--norc','-c',args['command']],args.get('timeout',60),suppress=True)
    raise ValueError('Operation unavailable')


def run_command(argv,timeout,suppress=False,track=True):
    # Bounded drain avoids communicate() retaining arbitrary command output in RAM.
    process=subprocess.Popen(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,env={'PATH':'/usr/sbin:/usr/bin:/sbin:/bin','LANG':'C.UTF-8','DEBIAN_FRONTEND':'noninteractive'})
    if track:
        job=get('job',os.environ['VSO_ADMIN_JOB']);job.update(pgid=process.pid,start_ticks=Path('/proc',str(process.pid),'stat').read_text().split(') ',1)[1].split()[19]);put('job',job['id'],job)
    chunks={};threads=[]
    def drain(pipe,key):
        output=bytearray()
        for chunk in iter(lambda:pipe.read(8192),b''):
            if len(output)<65536:output.extend(chunk[:65536-len(output)])
        pipe.close()
        chunks[key]=redact(output.decode('utf-8','replace')) if not suppress else '[Output suppressed: break-glass commands may read credentials]'
    for pipe,key in [(process.stdout,'stdout'),(process.stderr,'stderr')]:
        thread=threading.Thread(target=drain,args=(pipe,key),daemon=True);thread.start();threads.append(thread)
    timed_out=False
    try:process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:timed_out=True;os.killpg(process.pid,signal.SIGTERM)
    try:process.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
    for thread in threads:thread.join(timeout=2)
    if any(t.is_alive() for t in threads):
        try:os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:pass
    return {'exit_code':process.returncode,'timed_out':timed_out,**chunks}


def run_job(ident):
    os.environ['VSO_ADMIN_JOB']=ident;job=get('job',ident);record=get('request',ident)
    job.update(status='running',started_at=time.time(),runner_pid=os.getpid(),runner_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19]);put('job',ident,job)
    def deadline(signum,frame):raise TimeoutError('Administrator operation exceeded its deadline; reconcile effects')
    signal.signal(signal.SIGALRM,deadline);signal.alarm(1200 if record['operation'] in ('command','packages') else 300)
    try:
        result=perform(record['operation'],record['arguments']);job=get('job',ident);job.update(status='completed' if result.get('exit_code',0)==0 else 'failed',result=result)
    except Exception as e:job=get('job',ident);job.update(status='failed',error=redact(str(e)))
    signal.alarm(0)
    job['finished_at']=time.time();put('job',ident,job);audit('job.'+job['status'],ident)


def cancel(ident):
    job=reconcile(ident)
    if job['status'] not in ('running','unknown') or not job['original_process_alive']:raise ValueError('No cancellable original process exists')
    key,tick=('pgid','start_ticks') if process_matches(job.get('pgid',0),job.get('start_ticks')) else ('runner_pid','runner_ticks')
    if not process_matches(job[key],job[tick]):raise ValueError('Original process ended; never signal a reused PID')
    os.killpg(job[key],signal.SIGTERM);audit('job.cancel',ident)
    if key=='runner_pid':job.update(status='unknown',error='Cancellation requested during filesystem operation; reconcile partial effects');put('job',ident,{k:v for k,v in job.items() if k not in ('safe_to_repeat','original_process_alive')})
    return {'job_id':ident,'cancellation_requested':True,'inspect_partial_effects':True}


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        uid=struct.unpack('3i',self.request.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))[1]
        if uid not in (0,ALLOWED_UID):return
        self.request.settimeout(20)
        try:
            raw=self.rfile.readline(65537)
            if len(raw)>65536:raise ValueError('Broker request too large')
            message=json.loads(raw);action=message['action'];args=message.get('arguments',{})
            if action=='request':result=request(message['operation'],args,message['request_id'])
            elif action=='execute':result=execute(message['request_id'])
            elif action=='approve':result=approve(message['request_id'],message['code'])
            elif action=='enrollment':result=enrollment(message['ticket'],message.get('code'))
            elif action=='request_status':result=view(get('request',message['request_id']))
            elif action=='job_status':result=reconcile(message['job_id'])
            elif action=='job_cancel':result=cancel(message['job_id'])
            elif action in READ_ONLY:validate(action,args);result=perform(action,args)
            else:raise ValueError('Unsupported broker action')
            audit('socket.'+action,str(message.get('request_id',message.get('job_id','read'))))
            self.wfile.write(json.dumps({'result':result}).encode()+b'\n')
        except Exception as e:
            audit('socket.rejected','redacted-request')
            self.wfile.write(json.dumps({'error':redact(str(e))}).encode()+b'\n')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['serve','run-job','enrollment-link']);parser.add_argument('value',nargs='?');args=parser.parse_args()
    if os.geteuid()!=0:raise SystemExit('Broker requires root; public gateway must remain non-root')
    if args.command=='run-job':return run_job(args.value)
    if args.command=='enrollment-link':
        if not args.value or not args.value.startswith('https://'):raise SystemExit('Pass this installation HTTPS origin')
        token=secrets.token_urlsafe(32);put('settings','enrollment',{'hash':hashlib.sha256(token.encode()).hexdigest(),'secret':base64.b32encode(secrets.token_bytes(20)).decode(),'expires':time.time()+600})
        print(args.value.rstrip('/')+'/admin/enroll?ticket='+token);return
    # Interrupted administrator commands are NEVER rerun automatically.
    with db() as conn:
        for row in conn.execute("SELECT id,body FROM records WHERE kind='job'").fetchall():
            record=json.loads(row['body'])
            if record['status'] in ('starting','running'):record.update(status='unknown',error='Broker restarted; inspect original process before retrying');conn.execute("UPDATE records SET body=? WHERE kind='job' AND id=?",(json.dumps(record),row['id']))
    path=Path(SOCKET);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():path.unlink()
    with socketserver.ThreadingUnixStreamServer(SOCKET,Handler) as server:
        os.chmod(SOCKET,0o660);os.chown(SOCKET,0,pwd.getpwuid(ALLOWED_UID).pw_gid);server.serve_forever()


if __name__=='__main__':main()
