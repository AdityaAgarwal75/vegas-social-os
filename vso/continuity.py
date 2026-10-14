"""Private last-retained-frame extraction for reviewed segment continuity.

Frame index arithmetic adapted from zysilm/video-producer-skill's extract_frame.py,
MIT (c) 2026 zysilm-ai. See third_party/flow-video-producer/LICENSE.
"""
import base64,json,math,subprocess,tempfile
from fractions import Fraction
from pathlib import Path

def extract(engine,asset_id,retained_seconds=0):
    asset=engine.store.get('asset',asset_id)
    if asset['media_type']!='video/mp4':raise ValueError('Choose an imported MP4 clip')
    if type(retained_seconds) is not int or retained_seconds<0:raise ValueError('Retained seconds must be a nonnegative integer; 0 uses the whole clip')
    source=engine.asset_path(asset_id)
    try:
        info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=avg_frame_rate,duration:format=duration','-of','json',str(source)],text=True,timeout=20))
        stream=info['streams'][0];fps=float(Fraction(stream['avg_frame_rate']));duration=float(stream.get('duration') or info['format']['duration'])
        end=duration if retained_seconds==0 else retained_seconds
        if not all(math.isfinite(n) and n>0 for n in [fps,duration,end]) or end>duration+1e-6:raise ValueError('Retained interval exceeds the source clip')
        # Last frame strictly before the retained interval ends; original is untouched.
        index=max(0,math.ceil(end*fps-1e-6)-1)
        with tempfile.TemporaryDirectory(dir=engine.store.root) as tmp:
            output=Path(tmp)/'continuity.png'
            subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-i',str(source),'-vf',f'select=eq(n\\,{index})','-frames:v','1',str(output)],check=True,capture_output=True,timeout=40)
            frame=engine.asset_import(base64.b64encode(output.read_bytes()).decode(),'image/png')
    except ValueError:raise
    except (OSError,subprocess.SubprocessError,KeyError,IndexError,json.JSONDecodeError):raise ValueError('Could not decode/extract this clip; inspect FFmpeg and the actual media') from None
    result=dict(source_asset_id=asset_id,asset_id=frame['id'],retained_seconds=end,frame_time=index/fps,source_duration=duration,note='Review this actual frame before using it as the next start frame; no video generated')
    engine.store.put('continuity-frame',engine.store.digest(asset_id+':'+str(end))[:32],result)
    return result
