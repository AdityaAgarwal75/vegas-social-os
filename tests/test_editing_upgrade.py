"""Actual FFmpeg integration with synthetic local clips, no provider usage."""
import copy
import subprocess
import tempfile
import unittest
from pathlib import Path
from vso.engine import Engine
from vso.store import Store
from vso.media import sha256_file,probe
from vso.production import channel_settings,enforce
from vso.editing import run,start
from unittest.mock import patch

class EditingUpgrade(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name);self.e=Engine(self.s)
  self.s.put('account','flow',{'id':'flow','provider':'flow','status':'workspace_ready'})
  self.c=self.e.channel_save('Example','Education')
  scene={'image_prompt':'a red cube','video_prompt':'cube rotates','continuity':{'subject':'red cube'}}
  self.concepts=[{'title':str(i),'hook':'hook','script':'script','scenes':[copy.deepcopy(scene)]} for i in range(2)]
  self.p=self.e.plan_save(self.c['id'],self.concepts,'plan')
 def tearDown(self):self.tmp.cleanup()
 def test_scene_identifiers_immutable_and_request_idempotent(self):
  self.assertEqual(self.p,self.e.plan_save(self.c['id'],self.concepts,'plan'))
  a=self.p['concepts'][0]['scenes'][0];b=self.p['concepts'][1]['scenes'][0]
  self.assertNotEqual(a['scene_id'],b['scene_id']);self.assertEqual(len(a['input_sha256']),64)
 def test_channel_credit_and_account_boundary(self):
  c=channel_settings(self.e,self.c['id'],{'daily_credit_limit':10,'approved_flow_accounts':['flow']})
  with self.s.db() as db:
   enforce(db,c,'flow',10)
   with self.assertRaises(ValueError):enforce(db,c,'other',1)
   with self.assertRaises(ValueError):enforce(db,c,'flow',11)
 def test_actual_normalization_silent_audio_subtitles_and_idempotency(self):
  source=self.s.root/'media'/'synthetic.mp4'
  subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=red:s=80x64:r=15','-t','1','-c:v','libx264','-threads','1','-pix_fmt','yuv420p',str(source)],check=True)
  ident=sha256_file(source);target=source.with_name(ident+'.mp4');source.rename(target)
  self.s.put('asset',ident,{'id':ident,'file':target.name,'media_type':'video/mp4','size':target.stat().st_size})
  p=self.p;p.update(status='generating',selected=0);self.s.put('plan',p['id'],p)
  self.s.put('job','clip',{'id':'clip','plan_id':p['id'],'scene':0,'status':'completed','asset_id':ident})
  args=[self.e,p['id'],64,96,24,0.1,'',0.2,[{'start':0,'end':0.8,'text':'Review exact output'}],'edit-test']
  with patch('vso.editing.subprocess.Popen') as launch:
   job=start(*args);self.assertEqual(start(*args)['id'],job['id']);self.assertEqual(launch.call_count,1)
  run(self.e,job['id']);out=self.s.get('edit-job',job['id']);self.assertEqual(out['status'],'completed',out)
  info=probe(self.e.asset_path(out['asset_id']),'video/mp4')
  video=next(s for s in info['streams'] if s['codec_type']=='video');self.assertEqual((video['width'],video['height']),(64,96))
  self.assertTrue(any(s['codec_type']=='audio' for s in info['streams']));self.assertTrue(out['creative_review_required']);self.assertEqual(self.s.get('plan',p['id'])['status'],'video_review')

if __name__=='__main__':unittest.main()
