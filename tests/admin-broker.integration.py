"""Actual root Unix-socket integration using disposable private broker state only.

Runs one explicitly harmless /usr/bin/true job. Does not install services, edit
host configuration, read credentials or touch the production broker database.
"""
import base64,json,os,pwd,subprocess,sys,tempfile,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vso import admin_broker as b
from vso.admin import call
assert os.geteuid()==0,'Run only with an authorized root test connector'
owner=pwd.getpwnam('vegas-social')
with tempfile.TemporaryDirectory(prefix='vso-broker-accept-',dir='/var/tmp') as folder:
 root=Path(folder);root.chmod(0o750);os.chown(root,0,owner.pw_gid)
 state=root/'state';sock=root/'broker.sock';env={**os.environ,'VSO_ADMIN_STATE':str(state),'VSO_ADMIN_SOCKET':str(sock),'VSO_ADMIN_UID':str(owner.pw_uid)}
 os.environ.update({k:env[k] for k in ('VSO_ADMIN_STATE','VSO_ADMIN_SOCKET','VSO_ADMIN_UID')});b.STATE=state
 broker=subprocess.Popen([sys.executable,'-I',str(Path(b.__file__).resolve()),'serve'],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  for _ in range(100):
   if sock.exists():break
   time.sleep(.05)
  assert call({'action':'metrics'})['cpu_count']>=1
  request=call({'action':'request','operation':'command','arguments':{'command':'/usr/bin/true','timeout':5},'request_id':'harmless-integration'})
  try:call({'action':'execute','request_id':request['id']});raise AssertionError('Unapproved root command accepted')
  except ValueError:pass
  # Private test enrollment; no key/code is returned to ChatGPT or the MCP gateway.
  secret=base64.b32encode(os.urandom(20)).decode();b.put('settings','totp',{'secret':secret,'last_counter':0})
  b.approve(request['id'],b.totp(secret,int(time.time()//30)))
  job=call({'action':'execute','request_id':request['id']})
  assert call({'action':'execute','request_id':request['id']})['id']==job['id']
  for _ in range(100):
   result=call({'action':'job_status','job_id':job['id']})
   if result['status'] not in ('starting','running'):break
   time.sleep(.05)
  assert result['status']=='completed' and result['result']['exit_code']==0,result
  code="import sys;sys.path.insert(0,sys.argv[1]);from vso.admin import call;assert call({'action':'metrics'})['cpu_count']>=1"
  good=subprocess.run(['runuser','-u','vegas-social','--',sys.executable,'-c',code,str(Path(__file__).resolve().parents[1])],env=env,capture_output=True,timeout=20)
  assert good.returncode==0,good.stderr.decode()
  bad=subprocess.run(['runuser','-u','nobody','--',sys.executable,'-c',code,str(Path(__file__).resolve().parents[1])],env=env,capture_output=True,timeout=20)
  assert bad.returncode!=0
  print(json.dumps({'unix_peer_owner_pass':True,'unrelated_user_rejected':True,'unapproved_command_rejected':True,'exact_test_totp_approval':True,'idempotent_harmless_root_job':True,'bounded_output':True,'production_state_modified':False}))
 finally:broker.terminate();broker.wait(timeout=10)
