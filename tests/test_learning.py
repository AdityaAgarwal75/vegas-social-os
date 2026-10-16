import json,tempfile,time,unittest
from unittest.mock import patch
from vso.store import Store
from vso.engine import Engine
from vso import learning,projects
from vso.tools import call,definitions

class LearningTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.e=Engine(Store(self.tmp.name));self.s=self.e.store
  self.s.put('account','yt',{'id':'yt','provider':'youtube','remote_id':'UCowner','name':'Example','status':'connected'})
  self.c=self.e.channel_save('Channel','Audience',account_ids=['yt']);self.p=projects.create(self.e,'Film','p',channel_id=self.c['id']);self.now=time.time()
 def tearDown(self):self.tmp.cleanup()
 def post(self,i,**extra):
  p={'id':str(i),'account_id':'yt','provider':'youtube','status':'published','remote_id':'video_'+str(i),'visibility':'public','published_at':self.now-86400,'project_id':self.p['id'],'asset_ids':[],'title':'Title','caption':'Caption','options':{},**extra};self.s.put('publication',p['id'],p);return p
 def memory(self,request='m',**fields):
  return learning.memory_save(self.e,self.c['id'],self.p['id'],{'hook':'The actual hook','video_prompts':['The exact motion, action and ending.'],'format':'short','duration_seconds':24,'aspect_ratio':'9:16','hook_family':'reveal',**fields},request)
 def test_immutable_channel_memory_and_freeze(self):
  a=self.memory();self.assertEqual(a,self.memory())
  with self.assertRaises(ValueError):self.memory(hook='Different')
  other=self.e.channel_save('Other','Other',account_ids=[])
  with self.assertRaises(ValueError):learning.memory_save(self.e,other['id'],self.p['id'],a['fields'],'other')
  post=self.post('one');f=learning.freeze(self.e,post);self.memory('next',hook='New draft')
  self.assertEqual(learning.freeze(self.e,post),f);self.assertEqual(f['fields']['hook'],'The actual hook');self.assertEqual(self.s.all('job'),[])
 def test_provider_capture_checks_ownership_and_idempotency(self):
  self.memory();p=self.post('a');published=__import__('datetime').datetime.fromtimestamp(self.now-86400,__import__('datetime').timezone.utc).isoformat()
  row={'items':[{'id':p['remote_id'],'snippet':{'channelId':'UCowner','publishedAt':published},'statistics':{'viewCount':'19','likeCount':'2'},'status':{'privacyStatus':'public'}}]}
  with patch.object(self.e.accounts,'token',return_value='private'),patch('vso.learning.net.request',return_value=(row,{})) as net:
   a=learning.capture(self.e,p['id'],'24',24);self.assertTrue(a['comparable_age']);self.assertNotIn('comments',a['metrics']);self.assertEqual(a,learning.capture(self.e,p['id'],'24',24));self.assertEqual(net.call_count,1)
  row['items'][0]['snippet']['channelId']='UCother'
  with patch.object(self.e.accounts,'token',return_value='private'),patch('vso.learning.net.request',return_value=(row,{})):
   with self.assertRaises(ValueError):learning.capture(self.e,p['id'],'other',24)
 def test_owner_metrics_are_not_provider_evidence(self):
  self.memory();p=self.post('a');args=(self.e,p['id'],{'views':50},'https://studio.youtube.com/','manual',self.now,self.now-86400,24)
  a=learning.observe(*args);self.assertEqual(a,learning.observe(*args));self.assertFalse(a['source']['verified_by_provider']);self.assertEqual(learning.context(self.e,self.c['id'])['comparisons'],[])
  with self.assertRaises(ValueError):learning.observe(self.e,p['id'],{'views':51},'https://studio.youtube.com/','manual',self.now,self.now-86400,24)
  for value in [-1,float('nan'),float('inf'),True]:
   with self.assertRaises(ValueError):learning.observe(self.e,p['id'],{'views':value},'https://studio.youtube.com/','bad',self.now,self.now-86400)
  self.assertEqual(learning._numbers({'average_view_percentage':125})['average_view_percentage'],125)
  with self.assertRaises(ValueError):learning.observe(self.e,p['id'],{'views':1},'https://example.com/?token=private','secret',self.now,self.now-86400)
 def test_comparisons_require_five_other_posts_same_account_age_and_format(self):
  self.memory()
  for i,views in enumerate([100,100,100,100,100,400]):
   p=self.post(i);learning._record(self.e,p,{'views':views},str(i),self.now,self.now-86400,{'type':'provider_api','verified_by_provider':True},24)
  result=learning.context(self.e,self.c['id']);self.assertEqual(len(result['comparisons']),6);self.assertEqual(max(x['views_multiple'] for x in result['comparisons']),4);self.assertTrue(all(not x['causal_claim'] for x in result['comparisons']))
  # A late/current metric cannot masquerade as the 6h measurement; private records are excluded.
  p=self.post('late');learning._record(self.e,p,{'views':99999},'late',self.now,self.now-86400,{'type':'provider_api','verified_by_provider':True},6)
  p=self.post('private',visibility='private');learning._record(self.e,p,{'views':99999},'private',self.now,self.now-86400,{'type':'provider_api','verified_by_provider':True},24)
  self.assertEqual(len(learning.context(self.e,self.c['id'])['comparisons']),6)
 def test_few_posts_and_channel_isolation(self):
  self.memory();p=self.post('a');learning._record(self.e,p,{'views':3},'a',self.now,self.now-86400,{'type':'provider_api','verified_by_provider':True},24)
  result=learning.context(self.e,self.c['id']);self.assertEqual(result['comparisons'][0]['finding'],'insufficient_comparable_posts')
  other=self.e.channel_save('Other','Other',account_ids=[]);self.assertEqual(learning.context(self.e,other['id'])['observations'],[])
  with self.assertRaises(ValueError):learning.lesson_save(self.e,other['id'],'claim',[result['observations'][0]['id']],'next test','bad')
 def test_scheduler_disabled_by_default_and_failure_does_not_republish(self):
  p=self.post('a')
  with patch('vso.learning.capture') as capture:
   learning.tick(self.e);capture.assert_not_called()
  learning.policy(self.e,True)
  with patch('vso.learning.capture',side_effect=ValueError('provider unavailable')) as capture,patch.object(self.e,'publish_execute') as publish:
   result=learning.tick(self.e);self.assertEqual(len(result['failures']),1);learning.tick(self.e);self.assertEqual(capture.call_count,1);publish.assert_not_called()
  self.assertEqual(self.s.get('publication',p['id'])['status'],'published')
 def test_lesson_is_idempotent_hypothesis_with_exact_evidence(self):
  self.memory();p=self.post('a');obs=learning._record(self.e,p,{'views':4},'a',self.now,self.now-86400,{'type':'provider_api','verified_by_provider':True},24)
  a=learning.lesson_save(self.e,self.c['id'],'Test a more concrete opening',[obs['id']],'Change only opening action','lesson')
  self.assertEqual(a['status'],'hypothesis');self.assertFalse(a['causal_claim']);self.assertEqual(a,learning.lesson_save(self.e,self.c['id'],a['claim'],[obs['id']],a['next_test'],'lesson'))
  with self.assertRaises(ValueError):learning.lesson_save(self.e,self.c['id'],'Different',[obs['id']],'Test','lesson')
 def test_schema_parameter_types(self):
  defs={x['name']:x for x in definitions(self.e)};self.assertEqual(defs['performance_observe']['inputSchema']['properties']['metrics']['type'],'object');self.assertEqual(defs['learning_policy']['inputSchema']['properties']['enabled']['type'],'boolean')
  self.assertEqual(defs['learning_lesson_save']['inputSchema']['properties']['evidence_ids']['items']['type'],'string')

if __name__=='__main__':unittest.main()
