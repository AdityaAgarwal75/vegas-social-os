import concurrent.futures
import json
import tempfile
import time
import unittest
from unittest.mock import patch
from vso import flow_controller as fc, flow_service, video_service, tools, auth
from vso.engine import Engine
from vso.store import Store
from vso.projects import create


class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.e=Engine(Store(self.tmp.name))
        self.p=create(self.e,'Controller test','project')['id']
        self.ids=['a'*32,'b'*32]
        for i,ident in enumerate(self.ids):
            self.e.store.put('account',ident,dict(id=ident,provider='flow',status='workspace_ready',service_alias=str(i),credits=100,verified_at=time.time(),health_checked_at=time.time()))
        self.scene=dict(prompt='A red paper boat on water',model='Omni 1.1 Flash',duration=4,resolution='360p',aspect_ratio='9:16',max_credits=0)
    def tearDown(self):self.tmp.cleanup()
    def batch(self,request_id='batch',scenes=None):return fc.submit(self.e,self.p,scenes or [self.scene],self.ids,0,request_id)
    def backend(self,*args,**kwargs):return {'backend_job_ids':['original']}
    def tick(self):
        with patch('vso.flow_controller.resources_ok',return_value=''),patch('vso.flow_service.binding',side_effect=lambda e,i:(e.store.get('account',i),{})),patch('vso.video_service.submit',side_effect=self.backend):fc.tick(self.e)
    def test_queue_is_atomic_idempotent_and_does_not_call_provider(self):
        with patch('vso.video_service.submit') as provider:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:batches=list(pool.map(lambda _:self.batch(),range(2)))
        self.assertEqual(batches[0],batches[1]);provider.assert_not_called()
        with self.assertRaisesRegex(ValueError,'different inputs'):self.batch(scenes=[{**self.scene,'prompt':'Changed'}])
    def test_caps_inputs_and_boolean_ceilings_rejected_before_queue(self):
        for bad in ({**self.scene,'max_credits':1},{**self.scene,'max_credits':True},{**self.scene,'reference_asset_ids':['missing']}):
            with self.assertRaises(ValueError):self.batch(scenes=[bad])
        self.assertEqual(self.e.store.all('flow-batch'),[])
    def test_background_dispatch_and_poll_never_needs_host(self):
        batch=self.batch();self.tick()
        child=self.e.store.all('video-job')[0];self.assertEqual(child['status'],'processing')
        with patch('vso.video_service.poll',return_value=dict(completed=True,asset_id='verified',quoted_credits=0)) as poll,patch('vso.flow_controller.resources_ok',return_value=''):
            fc.tick(self.e);fc.tick(self.e)
        done=self.e.store.get('flow-batch',batch['id']);self.assertEqual(done['status'],'completed');self.assertEqual(done['tasks'][0]['asset_ids'],['verified']);self.assertEqual(poll.call_count,1)
    def test_unknown_is_quarantined_and_other_account_can_work(self):
        self.e.store.put('video-job','old',dict(id='old',account_id=self.ids[0],status='unknown',created_at=time.time(),next_check_at=time.time()+300))
        batch=self.batch();self.tick();task=self.e.store.get('flow-batch',batch['id'])['tasks'][0]
        self.assertEqual(task['account_id'],self.ids[1]);self.assertEqual(task['status'],'processing')
    def test_alias_accounts_cannot_bypass_the_same_browser_lock(self):
        a=self.e.store.get('account',self.ids[1]);a['service_alias']='0';self.e.store.put('account',a['id'],a)
        self.e.store.put('image-job','original',dict(id='original',account_id=self.ids[0],status='unknown'))
        with self.e.store.db() as db:
            with self.assertRaisesRegex(ValueError,'unresolved'):fc.assert_idle(db,a)
    def test_restart_after_claim_never_resubmits_missing_child(self):
        batch=self.batch();batch['tasks'][0]['status']='dispatching';self.e.store.put('flow-batch',batch['id'],batch)
        with patch('vso.video_service.submit') as submit,patch('vso.flow_controller.resources_ok',return_value=''):fc.tick(self.e)
        submit.assert_not_called();self.assertEqual(self.e.store.get('flow-batch',batch['id'])['status'],'needs_review')
    def test_restart_recovers_existing_child_without_duplicate_submission(self):
        batch=self.batch();self.tick()
        b=self.e.store.get('flow-batch',batch['id']);b['tasks'][0]['status']='dispatching';self.e.store.put('flow-batch',b['id'],b)
        with patch('vso.video_service.submit') as submit,patch('vso.video_service.poll',return_value={'completed':False,'status':'processing'}),patch('vso.flow_controller.resources_ok',return_value=''):fc.tick(self.e)
        submit.assert_not_called();self.assertEqual(self.e.store.get('flow-batch',batch['id'])['tasks'][0]['status'],'processing')
    def test_cancel_only_queued_tasks_and_keeps_original_submission(self):
        batch=self.batch(scenes=[self.scene,self.scene]);self.tick();fc.cancel(self.e,batch['id'])
        with patch('vso.video_service.poll',return_value={'completed':False,'status':'processing'}),patch('vso.flow_controller.resources_ok',return_value=''):fc.tick(self.e)
        tasks=self.e.store.get('flow-batch',batch['id'])['tasks'];self.assertEqual([t['status'] for t in tasks],['processing','cancelled']);self.assertEqual(len(self.e.store.all('video-job')),1)
    def test_resource_pause_does_not_prevent_existing_output_retrieval(self):
        batch=self.batch();self.tick()
        with patch('vso.video_service.poll',return_value=dict(completed=True,asset_id='verified',quoted_credits=0)),patch('vso.flow_controller.resources_ok',return_value='Low disk'):fc.tick(self.e)
        self.assertEqual(self.e.store.get('flow-batch',batch['id'])['status'],'completed');self.assertEqual(fc.status(self.e)['worker']['state'],'resource_paused')
    def test_failed_dispatch_is_not_rotated_to_another_account(self):
        batch=self.batch()
        with patch('vso.flow_controller.resources_ok',return_value=''),patch('vso.flow_service.binding',side_effect=lambda e,i:(e.store.get('account',i),{})),patch('vso.video_service.submit',side_effect=ValueError('Uncertain')) as submit:
            fc.tick(self.e);fc.tick(self.e)
        self.assertEqual(submit.call_count,1);self.assertEqual(self.e.store.get('flow-batch',batch['id'])['status'],'needs_review')
    def test_poll_failure_backoff_does_not_resubmit(self):
        self.batch();self.tick()
        with patch('vso.video_service.poll',side_effect=ValueError('Unavailable')) as poll,patch('vso.flow_controller.resources_ok',return_value=''):fc.tick(self.e);fc.tick(self.e)
        self.assertEqual(poll.call_count,1);self.assertEqual(self.e.store.all('video-job')[0]['poll_errors'],1)
    def test_tools_have_typed_schemas_and_read_scopes(self):
        defs={d['name']:d for d in tools.definitions(self.e)}
        self.assertEqual(defs['flow_batch_submit']['inputSchema']['properties']['scenes']['type'],'array')
        self.assertEqual(auth.tool_scope('flow_engine_status'),'social:read');self.assertEqual(auth.tool_scope('flow_batch_submit'),'social:write')
    def test_invalid_download_is_not_completed(self):
        self.e.store.put('video-job','job',dict(id='job',status='processing',account_id=self.ids[0],worker={'backend_job_ids':['original']},asset_ids=[]))
        with patch('vso.flow_service.binding',return_value=({},{})),patch('vso.flow_service.request',side_effect=[{'jobs':[dict(id='original',status='done',files=['/exact.mp4'])]},b'\0\0\0\x18ftypmp42invalid-data']),patch('vso.media.probe',side_effect=ValueError('Invalid MP4')):
            with self.assertRaises(ValueError):video_service.check(self.e,'job')
        self.assertEqual(self.e.store.get('video-job','job')['status'],'processing')

if __name__=='__main__':unittest.main()

class ProductionControllerTests(unittest.TestCase):
    setUp=ControllerTests.setUp
    tearDown=ControllerTests.tearDown
    def ready(self):
        import base64
        c=self.e.channel_save('Test','Boats')
        scene=dict(image_prompt='A boat',video_prompt='Move the boat')
        concepts=[dict(title='A',hook='First',script='Boat',scenes=[scene]),dict(title='B',hook='Second',script='Boat',scenes=[scene])]
        plan=self.e.plan_save(c['id'],concepts,'approved')
        self.e.concept_select(plan['id'],0,10)
        image=self.e.asset_import(base64.b64encode(b'\x89PNG\r\n\x1a\nfixture').decode(),'image/png')
        self.e.image_attach(plan['id'],0,image['id']);return self.e.images_approve(plan['id'])
    def test_production_preserves_approval_caps_and_assembles_once(self):
        plan=self.ready();opts={k:self.scene[k] for k in ('model','duration','resolution','aspect_ratio')};opts['max_credits']=5
        batch=fc.production_submit(self.e,plan['id'],self.ids,opts,5,'production')
        with patch.object(self.e,'flow',return_value={'backend_job_ids':['original']}),patch('vso.flow_controller.resources_ok',return_value=''):fc.tick(self.e)
        self.assertEqual(self.e.store.get('plan',plan['id'])['reserved'],5)
        asset=self.e.asset_import(__import__('base64').b64encode(b'\x00\x00\x00\x18ftypmp42fixture').decode(),'video/mp4')
        self.e.store.put('edit-job','edit',dict(id='edit',status='running'))
        with patch.object(self.e,'flow',return_value=dict(completed=True,asset_id=asset['id'],quoted_credits=3)),patch.object(self.e,'video_assemble',return_value={'id':'edit'}) as assemble,patch('vso.flow_controller.resources_ok',return_value=''):
            fc.tick(self.e);fc.tick(self.e)
            self.assertEqual(assemble.call_count,1)
        self.assertEqual(self.e.store.get('flow-batch',batch['id'])['status'],'assembling')
        self.e.store.put('edit-job','edit',dict(id='edit',status='completed',asset_id='final'))
        with patch('vso.flow_controller.resources_ok',return_value=''):fc.tick(self.e)
        self.assertEqual(self.e.store.get('flow-batch',batch['id'])['final_asset_id'],'final');self.assertEqual(self.e.store.all('publication'),[])
    def test_unapproved_plan_and_excess_batch_ceiling_rejected(self):
        plan=self.ready();opts={**{k:self.scene[k] for k in ('model','duration','resolution','aspect_ratio')},'max_credits':5}
        with self.assertRaises(ValueError):fc.production_submit(self.e,plan['id'],self.ids,opts,11,'excess')
        p=self.e.store.get('plan',plan['id']);p['revision_requested']=True;self.e.store.put('plan',p['id'],p)
        with self.assertRaises(ValueError):fc.production_submit(self.e,plan['id'],self.ids,opts,5,'revision')


class SchedulerIsolationTests(unittest.TestCase):
    def test_one_poll_failure_does_not_stop_other_publications(self):
        from vso.automation import tick
        with tempfile.TemporaryDirectory() as root:
            e=Engine(Store(root))
            for ident in ('first','second'):e.store.put('publication',ident,dict(id=ident,kind='composer',status='processing'))
            def poll(engine,ident):
                if ident=='first':raise ValueError('Expired token')
            with patch('vso.events.tick',side_effect=ValueError('Event endpoint down')),patch('vso.schedule.tick',return_value=[]),patch('vso.publishing.poll',side_effect=poll) as provider:tick(e)
            self.assertEqual(provider.call_count,2);self.assertEqual(e.store.get('runtime','scheduler')['state'],'degraded')

class FlowTransportTests(unittest.TestCase):
    def test_real_local_transport_download_decode_and_no_duplicate_submission(self):
        """Synthetic provider only: verifies HTTP adapter and real media decoding."""
        import base64
        from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
        from pathlib import Path
        import subprocess,os,threading
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);clip=root/'synthetic.mp4'
            subprocess.run(['ffmpeg','-v','error','-threads','1','-f','lavfi','-i','color=c=blue:s=90x160:d=4','-c:v','libx264','-threads','1','-pix_fmt','yuv420p',str(clip)],check=True)
            counts={'generate':0,'upload':0};payloads=[]
            class Handler(BaseHTTPRequestHandler):
                def log_message(self,*args):pass
                def do_POST(self):
                    self.assert_token();body=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))) or '{}')
                    if self.path=='/api/status':result={'jobs':[],'flow':{'signedIn':True,'inProject':True,'credits_remaining':100}}
                    elif self.path=='/api/generate':counts['generate']+=1;payloads.append(body);result={'jobs':[{'id':'original'}]}
                    elif self.path=='/api/wait':result={'jobs':[dict(id='original',status='done',credits=0,files=['/synthetic.mp4'])]}
                    else:raise AssertionError(self.path)
                    data=json.dumps(result).encode();self.send_response(200);self.end_headers();self.wfile.write(data)
                def assert_token(self):
                    if self.headers.get('x-flow-token')!='private-fixture':raise AssertionError('Missing private service authorization')
                def do_GET(self):
                    self.assert_token();self.send_response(200);self.end_headers();self.wfile.write(clip.read_bytes())
            server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            token=root/'token';token.write_text('private-fixture');config=root/'services.json';config.write_text(json.dumps({'synthetic':dict(port=server.server_port,token_file=str(token))}))
            try:
                with patch.dict(os.environ,{'VSO_FLOW_SERVICES':str(config)}),patch('vso.flow_controller.resources_ok',return_value=''):
                    e=Engine(Store(root/'state'));account=flow_service.sync(e)[0]
                    p=create(e,'Synthetic transport','transport')['id']
                    batch=fc.submit(e,p,[dict(prompt='Synthetic test',model='Omni 1.1 Flash',duration=4,resolution='360p',aspect_ratio='9:16',max_credits=0)],[account['id']],0,'transport')
                    fc.tick(e);fc.tick(e);fc.tick(e)
                    done=e.store.get('flow-batch',batch['id']);self.assertEqual(done['status'],'completed');self.assertEqual(counts['generate'],1)
                    asset=e.store.get('asset',done['tasks'][0]['asset_ids'][0]);self.assertEqual(asset['technical_verification']['streams'][0]['width'],90)
                    self.assertEqual(e.asset_path(asset['id']).read_bytes(),clip.read_bytes());self.assertEqual(payloads[0]['scenes'][0]['max_credits'],0)
            finally:server.shutdown();server.server_close();thread.join(5)
