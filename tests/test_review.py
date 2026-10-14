import concurrent.futures
import tempfile
import unittest
from vso.engine import Engine
from vso.store import Store
from vso import review, tools

class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.s = Store(self.tmp.name); self.e = Engine(self.s)
        self.channel = self.e.channel_save('Brand', 'Furniture', [])
        self.concepts = [{'title': t, 'hook': 'Hook', 'script': 'Script', 'scenes': [{'image_prompt':'Frame','video_prompt':'Motion'}]} for t in ('A','B')]
        self.p = self.e.plan_save(self.channel['id'], self.concepts, 'old')
    def tearDown(self): self.tmp.cleanup()
    def test_duplicate_feedback_preserves_original_and_blocks_new_renders(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda _: review.request(self.e,self.p['id'],'Change opening','once'),range(3)))
        self.assertEqual(len(self.s.all('review-request')),1)
        self.assertEqual(len({r['id'] for r in results}),1)
        old=self.s.get('plan',self.p['id']); self.assertEqual(old['concepts'],self.p['concepts']);self.assertTrue(old['revision_requested'])
        with self.assertRaises(ValueError): review.request(self.e,self.p['id'],'Different','once')
    def test_revision_does_not_inherit_approval_and_must_match_channel(self):
        r=review.request(self.e,self.p['id'],'New angle','one')
        with self.assertRaises(ValueError): review.complete(self.e,r['id'],self.p['id'])
        other=self.e.channel_save('Other','Other',[]);wrong=self.e.plan_save(other['id'],self.concepts,'new')
        with self.assertRaises(ValueError):review.complete(self.e,r['id'],wrong['id'])
        new=self.e.plan_save(self.channel['id'],self.concepts,'review:'+r['id'])
        done=review.complete(self.e,r['id'],new['id']);self.assertEqual(done['status'],'completed');self.assertEqual(review.complete(self.e,r['id'],new['id']),done)
        self.assertEqual(new['status'],'concept_review');self.assertEqual(new['budget'],0);self.assertEqual(new['images'],{})
    def test_tools_expose_queue_but_do_not_claim_execution(self):
        r=tools.call(self.e,'storyboard_regenerate',{'plan_id':self.p['id'],'feedback':'Simpler','request_id':'one'})
        self.assertEqual(tools.call(self.e,'review_queue',{})[0]['id'],r['id']);self.assertEqual(r['status'],'awaiting_agent')
        self.assertIn('review-request',self.e.snapshot())
    def test_revision_feedback_stops_new_paid_scene_before_submission(self):
        from unittest.mock import patch
        self.s.put('account','a'*32,{'id':'a'*32,'provider':'flow','status':'workspace_ready'})
        plan=self.s.get('plan',self.p['id']);plan.update(selected=0,status='ready',budget=100,images={'0':'keyframe'});self.s.put('plan',plan['id'],plan)
        review.request(self.e,plan['id'],'Change scene','one')
        with patch('vso.flow_runtime.installed',return_value=True),patch('vso.flow_models.validate_observed'),patch.object(self.e,'flow') as flow:
            with self.assertRaisesRegex(ValueError,'revision requested'):
                self.e.video_request(plan['id'],0,'a'*32,20,'new-job',{'model':'Veo 3.1 - Fast','duration':8,'resolution':'720p','aspect_ratio':'9:16'})
            flow.assert_not_called()
        self.assertEqual(self.s.all('job'),[]);self.assertEqual(self.s.get('plan',plan['id'])['reserved'],0)
