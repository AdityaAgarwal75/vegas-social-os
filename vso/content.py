"""Original strategy manager: evidence-backed agent requests, calendar and script QA."""
import json
import re
import time
from datetime import date,timedelta

def strategy_save(engine,channel_id,audience,goal,voice,pillars):
    engine.store.get('channel',channel_id)
    if any(not isinstance(x,str) or not x.strip() or len(x)>2000 for x in [audience,goal,voice]) or not isinstance(pillars,list) or not 1<=len(pillars)<=8 or any(not isinstance(x,str) or not x.strip() or len(x)>120 for x in pillars):raise ValueError('Provide audience, goal, voice and 1–8 clear content pillars')
    body=dict(channel_id=channel_id,audience=audience,goal=goal,voice=voice,pillars=pillars,updated_at=time.time())
    engine.store.put('strategy',channel_id,body);return body

def content_request(engine,channel_id,week_start,request_id):
    channel=engine.store.get('channel',channel_id);strategy=engine.store.get('strategy',channel_id)
    start=date.fromisoformat(week_start)
    if not request_id or len(request_id)>200:raise ValueError('Stable request ID required')
    research=[n for n in engine.store.all('research') if n['channel_id']==channel_id]
    recent_titles=[p['concepts'][p['selected'] or 0]['title'] for p in engine.store.all('plan') if p['channel_id']==channel_id][-15:]
    from .learning import context
    learning_context=context(engine,channel_id)
    ident=engine.store.digest('content:'+request_id)[:32]
    with engine.store.db() as db:
        row=db.execute("SELECT body FROM records WHERE kind='content-request' AND id=?",(ident,)).fetchone()
        if row:
            old=json.loads(row[0])
            if old['channel_id']!=channel_id or old['week_start']!=week_start:raise ValueError('Request ID already used')
            return old
        body=dict(learning_context=learning_context,id=ident,channel_id=channel_id,week_start=start.isoformat(),status='awaiting_agent',strategy=strategy,created_at=time.time(),channel=channel,
                  research=research,
                  recent_titles=recent_titles,
                  instruction='Read content_context and the bundled instagram/ig-reel, instagram/ig-viral, instagram/ig-plan and marketing/content-strategy references through skill_reference. Retrieve this channel’s actual prior prompts and observations. Treat low-sample lessons as hypotheses; choose one next variable and a measurable checkpoint. Save exact creative decisions through content_memory_save before release. Act as content strategy manager. Research current audience needs with actual sources. Propose a balanced week across the saved pillars, avoid recent repeats, give distinct hooks and specific useful angles. Draft scripts, captions and optional scenes with separate image_prompt/video_prompt in the brand voice. Use empty sources only for clearly labeled creative hypotheses, never current trend claims. Never invent results, testimonials or metrics. Save drafts with content_plan_save; await review. Do not publish, spend credits or claim an unattended ChatGPT run.')
        engine.store.write(db,'content-request',ident,body)
    return body

def content_plan_save(engine,request_id,items):
    request=engine.store.get('content-request',request_id)
    if request['status']=='approved':raise ValueError('Approved calendar is frozen; request a new plan')
    if not isinstance(items,list) or not 1<=len(items)<=14:raise ValueError('Provide 1–14 calendar entries')
    start=date.fromisoformat(request['week_start'])
    for item in items:
        if not isinstance(item,dict) or set(item)-{'date','format','pillar','angle','hook','script','caption','sources','scenes','evidence_status'}:raise ValueError('Invalid calendar item')
        if not all(isinstance(item.get(k),str) and item[k].strip() for k in ['date','format','pillar','angle','hook','script','caption']):raise ValueError('Each entry needs date, format, pillar, angle, hook, script and caption')
        if not start<=date.fromisoformat(item['date'])<start+timedelta(days=7) or item['format'] not in ['reel','short','carousel','story','post'] or item['pillar'] not in request['strategy']['pillars']:raise ValueError('Entry outside week, format or saved pillars')
        if not isinstance(item.get('sources',[]),list) or any(not isinstance(u,str) or not u.startswith('https://') for u in item.get('sources',[])):raise ValueError('Sources must be real HTTPS references')
        scenes=item.get('scenes',[])
        if not isinstance(scenes,list) or len(scenes)>12 or any(not isinstance(s,dict) or set(s)!={'image_prompt','video_prompt'} or any(not isinstance(v,str) or not v.strip() or len(v)>12000 for v in s.values()) for s in scenes):
            raise ValueError('Scenes require separate image_prompt and video_prompt, up to 12 scenes')
        item['evidence_status']='source_links_provided' if item.get('sources') else 'creative_hypothesis'
    with engine.store.db() as db:
        request=engine._load(db,'content-request',request_id)
        if request['status']=='approved':raise ValueError('Approved calendar is frozen; request a new plan')
        request.update(items=items,status='review');engine.store.write(db,'content-request',request_id,request)
    return request

def content_plan_approve(engine,request_id):
    with engine.store.db() as db:
        r=engine._load(db,'content-request',request_id)
        if r['status']!='review':raise ValueError('Review a saved draft calendar first')
        r.update(status='approved',approved_at=time.time());engine.store.write(db,'content-request',request_id,r)
    return r

def reel_review(script,hook,on_screen,target_seconds,words_per_minute=150):
    if not script.strip() or not hook.strip() or type(target_seconds) is not int or not 5<=target_seconds<=180 or type(words_per_minute) is not int or not 80<=words_per_minute<=240:raise ValueError('Provide script/hook and valid target seconds/speaking rate')
    words=re.findall(r'\S+',script);hook_words=re.findall(r'\S+',hook);duration=round(len(words)*60/words_per_minute,1);flags=[]
    if re.match(r'(?i)^(hey guys|hello everyone|in this video|today i|stop scrolling)',hook.strip()):flags.append('Opening spends attention on a greeting/preamble; start with the actual event or question')
    if len(hook_words)*60/words_per_minute>3:flags.append('Hook exceeds an estimated 3 seconds')
    if duration>target_seconds:flags.append('Spoken script exceeds target length at the selected speaking rate')
    if '{{' in script:flags.append('Unresolved factual placeholder; verify before production')
    if any(len(line.split())>6 for line in on_screen.splitlines() if line.strip()):flags.append('On-screen card exceeds six words; simplify for readability')
    beats=[{'line':line.strip(),'estimated_seconds':round(len(line.split())*60/words_per_minute,1)} for line in script.splitlines() if line.strip()]
    if any(b['estimated_seconds']>4 for b in beats):flags.append('A spoken beat exceeds an estimated 4 seconds; plan a visual change within it')
    return dict(word_count=len(words),estimated_seconds=duration,words_per_minute=words_per_minute,beats=beats,flags=flags,limitations='Text heuristics and timing estimates; no virality, retention or lip-sync guarantee. Verify spoken delivery and actual edit.')
