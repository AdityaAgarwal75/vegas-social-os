import tempfile,unittest,json
from unittest.mock import patch
from vso.engine import Engine
from vso.store import Store
from vso import content,flow_models,video_service,tools

class ProductionManagerTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.e=Engine(Store(self.tmp.name));self.c=self.e.channel_save('Test','Furniture');self.a='a'*32;self.e.store.put('account',self.a,{'id':self.a,'provider':'flow','service_alias':'test','status':'workspace_ready'})
 def tearDown(self):self.tmp.cleanup()
 def strategy(self):return content.strategy_save(self.e,self.c['id'],'Small apartment owners','Qualified inquiries','Plain and practical',['Space','Materials'])
 def test_calendar_requires_strategy_and_is_idempotent(self):
  with self.assertRaises(ValueError):content.content_request(self.e,self.c['id'],'2026-10-19','week')
  self.strategy();a=content.content_request(self.e,self.c['id'],'2026-10-19','week');b=content.content_request(self.e,self.c['id'],'2026-10-19','week');self.assertEqual(a,b);self.assertEqual(a['status'],'awaiting_agent')
 def test_calendar_review_freezes_without_publication(self):
  self.strategy();r=content.content_request(self.e,self.c['id'],'2026-10-19','week');item=dict(date='2026-10-20',format='reel',pillar='Space',angle='Measure before buying',hook='Your sofa may block this doorway',script='Measure the doorway before choosing the sofa.',caption='Save your measurements.',sources=[])
  content.content_plan_save(self.e,r['id'],[item]);content.content_plan_approve(self.e,r['id'])
  with self.assertRaises(ValueError):content.content_plan_save(self.e,r['id'],[item])
  self.assertEqual(self.e.store.all('publication'),[])
 def test_calendar_rejects_foreign_date_and_pillar(self):
  self.strategy();r=content.content_request(self.e,self.c['id'],'2026-10-19','week')
  with self.assertRaises(ValueError):content.content_plan_save(self.e,r['id'],[dict(date='2027-01-01',format='reel',pillar='Space',angle='a',hook='h',script='s',caption='c')])
 def test_reel_timing_is_labeled_estimate(self):
  r=content.reel_review('One two three four five six.','Hey guys today I will explain this','Too many words in this on screen card',30,150)
  self.assertEqual(r['estimated_seconds'],2.4);self.assertGreaterEqual(len(r['flags']),2);self.assertIn('estimates',r['limitations'])
 def test_model_dependent_settings_and_provenance(self):
  flow_models.validate('Omni 1.1 Flash',10,'360p','9:16')
  with self.assertRaises(ValueError):flow_models.validate('Veo 3.1 - Quality',10,'360p','9:16')
  self.assertFalse(flow_models.catalog(self.e)['live_verified']);self.assertEqual(len(flow_models.catalog(self.e)['video']),4)
 def test_video_once_unknown_never_retries(self):
  with patch('vso.flow_service.binding',return_value=({'status':'workspace_ready'},{})),patch('vso.video_service.submit',side_effect=ValueError('Interrupted')) as submit:
   args=(self.e,self.a,'A boat','Omni 1.1 Flash',4,'360p','9:16',0,'stable')
   a=video_service.request(*args);b=video_service.request(*args);self.assertEqual(a['status'],'unknown');self.assertEqual(a['id'],b['id']);self.assertEqual(submit.call_count,1)
 def test_video_quote_stop_does_not_import_or_resubmit(self):
  self.e.store.put('video-job','job',{'id':'job','account_id':self.a,'status':'processing','worker':{'backend_job_ids':['exact']},'asset_ids':[]})
  with patch('vso.flow_service.binding',return_value=({},{})),patch('vso.flow_service.request',return_value={'jobs':[{'id':'exact','status':'failed','credits':20,'error':'above max_credits=0. Nothing was generated.'}]}) as backend:
   a=video_service.check(self.e,'job');b=video_service.check(self.e,'job');self.assertEqual(a['status'],'stopped');self.assertEqual(a,b);self.assertEqual(backend.call_count,1);self.assertEqual(self.e.store.all('asset'),[])
 def test_invalid_references_never_create_unknown_job(self):
  with patch('vso.video_service.submit') as submit:
   with self.assertRaises(ValueError):video_service.request(self.e,self.a,'A boat','Veo 3.1 - Fast',4,'720p','9:16',0,'invalid',reference_asset_ids=['missing'])
   self.assertEqual(self.e.store.all('video-job'),[]);submit.assert_not_called()
 def test_calendar_preserves_scene_prompts_and_labels_unsourced_ideas(self):
  self.strategy();r=content.content_request(self.e,self.c['id'],'2026-10-19','scenes')
  item=dict(date='2026-10-20',format='reel',pillar='Space',angle='Measure before buying',hook='Measure this doorway',script='Measure the doorway.',caption='Save your measurements.',scenes=[dict(image_prompt='A sofa and tape measure',video_prompt='Slow pan of the measured doorway')])
  saved=content.content_plan_save(self.e,r['id'],[item]);self.assertEqual(saved['items'][0]['evidence_status'],'creative_hypothesis');self.assertEqual(saved['items'][0]['scenes'],item['scenes'])
 def test_video_processing_worker_ids_stay_private(self):
  with patch('vso.flow_service.binding',return_value=({'status':'workspace_ready'},{})),patch('vso.video_service.submit',return_value={'backend_job_ids':['private-exact']}):
   a=video_service.request(self.e,self.a,'A boat','Omni 1.1 Flash',4,'360p','9:16',0,'private')
   self.assertNotIn('worker',a);self.assertNotIn('private-exact',json.dumps(self.e.snapshot()))
 def test_schema_exposes_real_manager_and_video_controls(self):
  defs={x['name']:x for x in tools.definitions(self.e)};self.assertEqual(defs['flow_video_request']['inputSchema']['properties']['duration']['type'],'integer');self.assertEqual(defs['content_plan_save']['inputSchema']['properties']['items']['type'],'array');self.assertIn('reel_review',defs)
