import base64,shutil,subprocess,tempfile,unittest
from pathlib import Path
from vso.engine import Engine
from vso.store import Store
from vso.continuity import extract

class ContinuityTests(unittest.TestCase):
 @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'FFmpeg and ffprobe required')
 def test_last_retained_frame_uses_correct_interval_and_preserves_clip(self):
  with tempfile.TemporaryDirectory() as tmp:
   e=Engine(Store(Path(tmp)/'data'));clip=Path(tmp)/'test.mp4'
   subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=red:s=32x32:r=4:d=1','-f','lavfi','-i','color=c=blue:s=32x32:r=4:d=1','-filter_complex','[0:v][1:v]concat=n=2:v=1:a=0[v]','-map','[v]','-c:v','libx264','-pix_fmt','yuv420p',str(clip)],check=True,capture_output=True)
   source=clip.read_bytes();a=e.asset_import(base64.b64encode(source).decode(),'video/mp4')
   retained=extract(e,a['id'],1);full=extract(e,a['id'])
   def pixel(ident):return subprocess.check_output(['ffmpeg','-v','error','-i',str(e.asset_path(ident)),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','pipe:1'])[:3]
   red,blue=pixel(retained['asset_id']),pixel(full['asset_id']);self.assertGreater(red[0],red[2]);self.assertGreater(blue[2],blue[0]);self.assertLess(retained['frame_time'],1);self.assertEqual(e.asset_path(a['id']).read_bytes(),source)
   self.assertEqual(extract(e,a['id'])['asset_id'],full['asset_id'])
   with self.assertRaises(ValueError):extract(e,a['id'],3)
 def test_image_cannot_be_misrepresented_as_clip(self):
  with tempfile.TemporaryDirectory() as tmp:
   e=Engine(Store(tmp));e.store.put('asset','image',{'id':'image','media_type':'image/png'})
   with self.assertRaises(ValueError):extract(e,'image')
   self.assertEqual(e.store.all('continuity-frame'),[])
