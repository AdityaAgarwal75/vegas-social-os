import tempfile
import unittest

from vso.engine import Engine
from vso.store import Store
from vso import studio
from vso.tools import call, definitions

class StudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.engine=Engine(Store(self.tmp.name))
        self.channel=self.engine.channel_save("studio brand", "marketing")
    def tearDown(self):self.tmp.cleanup()

    def test_pipeline_catalog_has_explicit_review_and_credit_stages(self):
        catalog=call(self.engine,"studio_catalog",{})
        self.assertGreaterEqual(len(catalog["pipelines"]),13)
        for name,stages in catalog["pipelines"].items():
            self.assertEqual(stages[-1],"publish_approval",name)

    def test_complete_brief_lifecycle_no_provider_calls(self):
        cid=self.channel["id"]
        v=call(self.engine,"studio_brief",{"channel_id":cid,"topic":"How to choose a safe backpack","platform":"instagram",
            "pipeline":"short_reel","objective":"education","budget_credits":0,"request_id":"my-test-brief"})
        self.assertEqual(v["status"],"awaiting_host_draft")
        self.assertEqual(v["budget_credits"],0)
        repeat=call(self.engine,"studio_brief",{"channel_id":cid,"topic":"How to choose a safe backpack","platform":"instagram",
            "pipeline":"short_reel","objective":"education","budget_credits":0,"request_id":"my-test-brief"})
        self.assertEqual(v["id"],repeat["id"])
        with self.assertRaises(ValueError):
            call(self.engine,"studio_brief",{"channel_id":cid,"topic":"different","platform":"instagram",
                "pipeline":"short_reel","objective":"education","budget_credits":0,"request_id":"my-test-brief"})
        variants=[
            {"title":"One feature to check","hook":"What should you check before buying a backpack?",
             "script":"First, inspect this specific feature.", "scenes":[{"image_prompt":"A precisely framed backpack",
              "video_prompt":"Pan around the reference, maintain stitching","duration":5}]},
            {"title":"Two options compared","hook":"One bag looks durable; what really lasts?",
             "script":"Compare the seams and straps against visible criteria.","scenes":[
                {"image_prompt":"Backpack side-by-side detail","video_prompt":"Slow camera move on fabric detail","duration":7}]}
        ]
        drafted=call(self.engine,"studio_draft",{"brief_id":v["id"],"variants":variants})
        self.assertEqual(drafted["status"],"creative_review")
        selected=call(self.engine,"studio_select",{"brief_id":v["id"],"variant_index":1})
        self.assertEqual(selected["status"],"storyboard_review")
        self.assertEqual(selected["budget_credits"],0)
        self.assertEqual(self.engine.store.all("publication"),[])
        self.assertEqual(self.engine.store.all("job"),[])
        with self.assertRaises(ValueError):call(self.engine,"studio_select",{"brief_id":v["id"],"variant_index":0})

    def test_draft_validates_artifacts_and_distinct_concepts(self):
        ident=studio.start(self.engine,self.channel["id"],"Topic","instagram","short_reel","awareness",0,"draft-test")["id"]
        with self.assertRaises(ValueError):
            studio.draft(self.engine,ident,[{"title":"a","hook":"x","script":"x","scenes":[]}]*2)
        self.assertEqual(self.engine.store.get("creative-brief",ident)["status"],"awaiting_host_draft")

    def test_outliers_require_measured_baselines(self):
        observations=[{"id":"1","account":"a","views":100,"account_median_views":10},
                      {"id":"2","account":"b","views":500,"account_median_views":1000}]
        results=call(self.engine,"studio_outliers",{"observations":observations})
        self.assertEqual(results["ranked"][0]["relative_views"],10)
        with self.assertRaises(ValueError):studio.outliers([{"id":"f","account":"a","views":10,"account_median_views":0}]*2)

    def test_qa_and_repurpose_and_profile(self):
        q=studio.quality("Hello everyone, let's talk","Hello everyone",caption="A useful tip")
        self.assertTrue(q["flags"])
        self.assertTrue(0<=q["score"]<=100)
        r=studio.repurpose("First fact. Second fact. Third fact.",2)
        self.assertEqual(len(r["segments"]),2)
        score=studio.profile({"bio":"Brand and purpose","content_pillars":["science"]})
        self.assertTrue(0<score["completeness_score"]<100)
        self.assertGreaterEqual(len(definitions(self.engine)),80)

    def test_bad_origin_urls_no_secrets(self):
        with self.assertRaises(ValueError):
            studio.start(self.engine,self.channel["id"],"topic","instagram","short_reel","sales",0,"bad-url",["http://localhost/private"])

if __name__=="__main__":unittest.main()
