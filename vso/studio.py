"""Vegas native creative command center. Original code; no external service spend."""
import hashlib
import json
import math
import re
import time
from datetime import date, timedelta

# Formats route to existing Flow/native image/FFmpeg services, not third-party code.
PIPELINES = {
    "short_reel": ("research", "creative_brief", "hook_selection", "script",
                   "storyboard", "native_image_review", "flow_video", "edit", "quality_review", "publish_approval"),
    "carousel": ("research", "creative_brief", "slide_outline", "native_image_review",
                 "caption_review", "publish_approval"),
    "story": ("research", "creative_brief", "story_sequence", "sticker_plan",
              "native_image_review", "publish_approval"),
    "documentary": ("research", "source_validation", "script", "shot_list",
                    "stock_rights_review", "asset_review", "edit", "quality_review", "publish_approval"),
    "cinematic": ("creative_brief", "style_reference", "shot_list", "native_image_review",
                  "flow_video", "sound_design", "edit", "quality_review", "publish_approval"),
    "animated_explainer": ("research", "fact_check", "script", "storyboard",
                           "animation_assets", "voiceover", "edit", "quality_review", "publish_approval"),
    "avatar_spokesperson": ("creative_brief", "script", "identity_permission",
                           "voice_permission", "avatar_assets", "lip_sync_review", "quality_review", "publish_approval"),
    "talking_head": ("creative_brief", "hook_selection", "script",
                     "teleprompter", "subtitles", "edit", "quality_review", "publish_approval"),
    "podcast_clips": ("source_permission", "transcript", "highlight_selection",
                      "clip_review", "subtitles", "quality_review", "publish_approval"),
    "screen_demo": ("product_validation", "capture_permission", "screencast",
                    "redaction_review", "subtitles", "quality_review", "publish_approval"),
    "localization": ("source_permission", "transcript", "translation_review",
                     "voice_permission", "dub", "subtitle_review", "publish_approval"),
    "character_animation": ("identity_reference", "continuity", "script",
                            "storyboard", "native_image_review", "flow_video", "edit", "quality_review", "publish_approval"),
    "stock_montage": ("research", "stock_rights_review", "footage_select",
                      "edit", "sound_design", "quality_review", "publish_approval"),
}
FORMATS = {"reel": "short_reel", "short": "short_reel", "story": "story", "carousel": "carousel",
           "video": "cinematic", "documentary": "documentary", "podcast": "podcast_clips",
           "demo": "screen_demo"}
OBJECTIVES = ("awareness", "engagement", "leads", "education", "sales", "community")
MAX_TEXT = 16000
# Original creative families, not scraped third-party library/regex collections.
HOOK_FAMILIES = [
    ("contradiction", "A common belief is challenged by a demonstrable counterexample"),
    ("before_after", "Show the outcome first, then explain what changed"),
    ("specificity", "Begin with a measurable, verifiable detail"),
    ("mistake", "Lead with a preventable error the target viewer recognizes"),
    ("open_loop", "Set up a legitimate question answered in the same video"),
    ("demonstration", "Show the result through an observable action"),
    ("comparison", "Contrast two relevant alternatives against a clear criterion"),
    ("micro_story", "Start at the moment when the situation changed"),
    ("question", "Ask one concrete, answerable question"),
    ("myth_check", "Separate a popular claim from substantiated evidence"),
    ("checklist", "Promise a bounded set of practical steps"),
    ("objection", "Answer a genuine objection from the intended audience"),
]


def bounded(value, name, limit=MAX_TEXT):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{name} must be nonblank and at most {limit} characters")
    return value.strip()


def safe_urls(values):
    if not isinstance(values, list) or len(values) > 25:
        raise ValueError("Use up to 25 verified HTTPS references")
    for u in values:
        if not isinstance(u, str) or len(u) > 2048 or not re.fullmatch(r"https://[^\s@/?#]+(?:[/?#][^\s]*)?", u):
            raise ValueError("References require public HTTPS URLs, without credentials")


def catalog():
    return {
        "pipelines": {name: list(stages) for name, stages in PIPELINES.items()},
        "hook_families": [{"key": k, "guidance": d} for k, d in HOOK_FAMILIES],
        "features": ["editorial brief and content pillars", "brand voice and audience memory",
                     "source-provenance gate", "hook analysis", "speech pacing", "caption first-line audit",
                     "carousel and story planning", "profile critique", "competitor outlier analysis",
                     "transcript repurposing", "paid-credit ceiling", "storyboard approval",
                     "asset permission checks", "Flow/native image stage matching",
                     "editable FFmpeg assembly", "safe platform publishing approvals",
                     "community installation diagnostics"],
        "integrations": {"chatgpt": "MCP host writes strategic proposals and generates native image assets",
                         "flow": "Existing private, account-scoped generation and reconciliation",
                         "media": "Existing checksummed asset import and FFmpeg processing",
                         "research": "Existing consented/robots-aware HTTPS reader",
                         "publisher": "Existing owner-approved destination adapters"},
        "limitations": ["Tools below create deterministic briefs and review submitted facts, not autonomous ChatGPT conversations.",
                        "Trend/virality judgments require observed metrics; never fabricate them.",
                        "No unapproved account action, provider spend, downloading media or publishing."]
    }


def quality(hook, script, caption="", platform="instagram", target_seconds=30):
    bounded(hook, "hook", 320)
    bounded(script, "script")
    if not isinstance(caption, str) or len(caption) > MAX_TEXT: raise ValueError("Invalid caption")
    if platform not in ("instagram", "youtube", "facebook", "tiktok", "general"): raise ValueError("Unsupported platform")
    if type(target_seconds) is not int or not 5 <= target_seconds <= 600: raise ValueError("Invalid duration")
    hook_words=re.findall(r"\b[\w'-]+\b",hook,flags=re.UNICODE)
    words=re.findall(r"\b[\w'-]+\b",script,flags=re.UNICODE)
    estimated=round(len(words)/2.5,1)
    deductions=[]
    def flag(when, reason, points):
        if when: deductions.append({"reason":reason,"points":points})
    flag(len(hook_words)>13, "First spoken hook is likely longer than five seconds", 12)
    flag(len(hook_words)<3, "Hook may not provide enough concrete context", 8)
    flag(bool(re.match(r"(?i)^(hey guys|hello everyone|today we|in this video|welcome back)\b",hook)), "Greeting delays the opening promise", 15)
    flag(estimated>target_seconds*1.15, "Script exceeds approximate speech budget at 150 words/minute", 15)
    flag(estimated<target_seconds*0.35, "Script may leave excess dead air; plan deliberate visual beats", 5)
    flag(not any(ch in hook for ch in "?!:0123456789"), "Hook may benefit from a more specific question, action or result", 7)
    flag("\u200b" in script or "\ufeff" in script, "Invisible formatting characters present", 6)
    flag(bool(re.search(r"(?i)\b(revolutionary|game.changing|unleash|delve into)\b",script)), "Check generic claims for brand voice and evidence", 7)
    if caption:
        flag(len(caption.splitlines()[0])>130, "Caption opening may be truncated; review the first 125 characters", 9)
        flag(len(re.findall(r"#\w+",caption))>12,"Many hashtags; choose only genuinely relevant terms",5)
    return {
        "score":max(0,100-sum(d["points"] for d in deductions)),
        "score_meaning":"Text QA heuristic, not a forecast of virality or performance",
        "speech_seconds_estimate":estimated, "caption_preview":caption[:125],
        "hook_words":len(hook_words), "flags":deductions,
        "recommendation":"Verify any factual promises with supplied research; approve creative before provider spend."
    }


def start(engine, channel_id, topic, platform, pipeline, objective, budget_credits, request_id, references=None):
    channel=engine.store.get("channel",bounded(channel_id,"channel_id",150))
    topic=bounded(topic,"topic",1000)
    if platform not in ("instagram","youtube","facebook","tiktok","multi"):raise ValueError("Unsupported platform")
    if pipeline not in PIPELINES:raise ValueError("Unknown production pipeline")
    if objective not in OBJECTIVES:raise ValueError("Unsupported objective")
    if type(budget_credits) is not int or not 0<=budget_credits<=10000:raise ValueError("Invalid credit ceiling")
    request_id=bounded(request_id,"request_id",180)
    references=[] if references is None else references
    safe_urls(references)
    ident=hashlib.sha256(("creative:"+request_id).encode()).hexdigest()[:32]
    prior=engine.store.all("research")
    research=[r for r in prior if r.get("channel_id")==channel_id]
    try:strategy=engine.store.get("strategy",channel_id)
    except ValueError:strategy={}
    body={"id":ident,"channel_id":channel_id,"topic":topic,"platform":platform,
          "pipeline":pipeline,"objective":objective,"budget_credits":budget_credits,
          "references":references,"strategy":strategy,"channel_brief":{"name":channel["name"],"niche":channel.get("niche")},
          "research":[{"title":r.get("title"),"sources":r.get("sources",[])} for r in research[-12:]],
          "stages":[{"name":name,"status":"pending"} for name in PIPELINES[pipeline]],
          "status":"awaiting_host_draft","variants":None,"chosen":None,"created_at":time.time(),
          "host_instruction":"Use current ChatGPT-hosted reasoning and authorized public research to propose two genuinely different ideas; provide factual sources, scripts, captions, image and video scene prompts; never pretend generated media exist; hand off to native host images and existing Flow only after review. Do not spend or publish."}
    with engine.store.db() as db:
        row=db.execute("SELECT body FROM records WHERE kind='creative-brief' AND id=?",(ident,)).fetchone()
        if row:
            saved=json.loads(row["body"])
            if any(saved.get(k)!=body[k] for k in ("channel_id","topic","platform","pipeline","objective","budget_credits","references")):
                raise ValueError("This request ID already belongs to another creative brief")
            return saved
        engine.store.write(db,"creative-brief",ident,body)
    return body


def draft(engine, brief_id, variants):
    if not isinstance(variants,list) or len(variants)!=2:raise ValueError("Provide exactly two distinctive concepts")
    clean=[]
    for v in variants:
        if not isinstance(v,dict) or set(v)-{"title","hook","script","caption","sources","scenes","content_warning"}:raise ValueError("Unrecognized draft fields")
        title=bounded(v.get("title"),"title",160)
        hook=bounded(v.get("hook"),"hook",320)
        script=bounded(v.get("script"),"script")
        caption=v.get("caption","")
        if not isinstance(caption,str) or len(caption)>MAX_TEXT:raise ValueError("Invalid caption")
        sources=v.get("sources",[])
        safe_urls(sources)
        scenes=v.get("scenes",[])
        if not isinstance(scenes,list) or not 1<=len(scenes)<=12:raise ValueError("Provide 1-12 original scenes compatible with the primary plan interface")
        cleaned_scenes=[]
        for scene in scenes:
            if not isinstance(scene,dict) or set(scene)-{"image_prompt","video_prompt","duration","rights_confirmed"}:
                raise ValueError("Invalid scene schema")
            ip=bounded(scene.get("image_prompt"),"image prompt",5000)
            vp=bounded(scene.get("video_prompt"),"video prompt",5000)
            seconds=scene.get("duration",5)
            if type(seconds) not in (int,float) or not math.isfinite(seconds) or not 1<=seconds<=30:raise ValueError("Scene duration outside 1-30 sec")
            cleaned_scenes.append({"image_prompt":ip,"video_prompt":vp,"duration":seconds,
                                   "rights_confirmed":scene.get("rights_confirmed",False) is True})
        check=quality(hook,script,caption,target_seconds=min(600,max(5,round(sum(x["duration"] for x in cleaned_scenes)))))
        clean.append({"title":title,"hook":hook,"script":script,"caption":caption,
                      "sources":sources,"scenes":cleaned_scenes,"review":check,
                      "evidence_status":"references_supplied" if sources else "creative_hypothesis",
                      "content_warning":v.get("content_warning","")[:700]})
    if clean[0]["title"].casefold()==clean[1]["title"].casefold() or clean[0]["hook"].casefold()==clean[1]["hook"].casefold():
        raise ValueError("Concepts must have genuinely distinct titles and hooks")
    with engine.store.db() as db:
        b=engine._load(db,"creative-brief",brief_id)
        if b["status"] not in ("awaiting_host_draft","creative_review"):raise ValueError("Draft is frozen; start a new brief")
        b.update(variants=clean,status="creative_review")
        engine.store.write(db,"creative-brief",brief_id,b)
    return {"id":brief_id,"status":"creative_review","variants":clean,
            "next_step":"Ask owner to select a concept. This does not approve Flow credit spend or publishing."}


def select(engine, brief_id, variant_index):
    if type(variant_index) is not int or variant_index not in (0,1):raise ValueError("Select concept 0 or 1")
    with engine.store.db() as db:
        b=engine._load(db,"creative-brief",brief_id)
        if b["status"]!="creative_review":raise ValueError("The two concepts must be reviewed first")
        b.update(chosen=variant_index,status="storyboard_review",selected_at=time.time())
        engine.store.write(db,"creative-brief",brief_id,b)
    return {"brief_id":brief_id,"selected":variant_index,"status":"storyboard_review",
            "pipeline_stages":b["stages"],"scenes":b["variants"][variant_index]["scenes"],
            "budget_credits":b["budget_credits"],
            "next":"Create native images with the ChatGPT host; attach exact outputs with media_ingest or media_transfer_prepare. No generation, credits or publication happened."}


def outliers(observations):
    if not isinstance(observations,list) or not 2<=len(observations)<=150:raise ValueError("Supply 2-150 observed posts")
    for a in observations:
        if not isinstance(a,dict) or set(a)-{"id","account","views","account_median_views","topic","hook","url"}:raise ValueError("Invalid observation")
        if not isinstance(a.get("views"),int) or a["views"]<0 or not isinstance(a.get("account_median_views"),int) or a["account_median_views"]<1:raise ValueError("Supply observed nonnegative views and a positive median baseline")
        bounded(a.get("account"),"account",160);bounded(a.get("id"),"id",180)
        if a.get("url"):safe_urls([a["url"]])
    result=sorted([{"id":a["id"],"account":a["account"],"views":a["views"],
                    "relative_views":round(a["views"]/a["account_median_views"],2),
                    "topic":a.get("topic",""),"hook":a.get("hook",""),"url":a.get("url","")}
                   for a in observations],key=lambda x:x["relative_views"],reverse=True)
    return {"ranked":result,"basis":"User-supplied observed post views divided by user-supplied account median; not independently verified or live-scraped","notes":"No platform API call, account scraping or unsupported causal virality claims."}


def repurpose(text, target_clips=4):
    text=bounded(text,"transcript",60000)
    if type(target_clips) is not int or not 1<=target_clips<=12:raise ValueError("Choose 1-12 clips")
    pieces=[p.strip() for p in re.split(r"(?<=[.!?।])\s+|\n+",text) if p.strip()]
    if not pieces:raise ValueError("No transcript passages")
    per=math.ceil(len(pieces)/target_clips)
    chunks=[" ".join(pieces[i:i+per]) for i in range(0,len(pieces),per)]
    return {"segments":[{"index":i,"text":chunk[:6000],"task":"Host agent must select honest boundaries, verify context and write original hooks; seek source and speaker reuse rights."} for i,chunk in enumerate(chunks)],
            "suggested_formats":["short_reel","carousel","story","podcast_clips"],
            "note":"Text-only rough segmentation, not automatic audio timestamps or generated clips."}


def profile(fields):
    if not isinstance(fields,dict) or set(fields)-{"display_name","handle","bio","link","category","highlight_titles","pinned_topics","avatar_description","content_pillars"}:raise ValueError("Invalid profile fields")
    criteria={"display_name":10,"handle":5,"bio":20,"link":10,"category":5,
              "highlight_titles":10,"pinned_topics":15,"avatar_description":10,"content_pillars":15}
    evaluation=[]
    for key,score in criteria.items():
        v=fields.get(key)
        filled=bool(v and (not isinstance(v,str) or v.strip()))
        evaluation.append({"field":key,"points":score if filled else 0,"maximum":score,
                           "next_action":"Review clarity and relevance with a human" if filled else "Provide this field to complete the profile"})
    return {"completeness_score":sum(e["points"] for e in evaluation),
            "maximum":100,"criteria":evaluation,
            "limitations":"Field completeness only, not real profile quality, reach or conversion. No Instagram connection or scraping occurred."}


def copycheck(text):
    """Minimal transparent, original text lint, without false AI-detection claims."""
    if not isinstance(text,str) or len(text)>MAX_TEXT:raise ValueError("Text too long")
    hidden=[c for c in text if c in ("\u200b","\u200c","\u200d","\ufeff","\u2060")]
    cleaned="".join(ch for ch in text if ch not in ("\u200b","\u200c","\u200d","\ufeff","\u2060"))
    issues=[]
    for expression,note in [
        (r"(?i)\b(delv(e|ing)|revolutionary|game.changing|unleash|in the ever.evolving)\b",
         "Check vague promotional wording against the saved brand voice"),
        (r"[!]{3,}","Reduce repeated emphasis if it is not part of the brand voice"),
        (r"(?i)\bguaranteed (followers|sales|growth|views)\b",
         "Do not promise unverified outcomes")]:
        for m in re.finditer(expression,cleaned):
            issues.append({"start":m.start(),"end":m.end(),"warning":note})
    return {"cleaned_text":cleaned,"removed_invisible_count":len(hidden),
            "issues":issues[:30],"limitations":"Writing and formatting lint, not a claim of AI authorship or watermark detection."}


def caption_review(text,platform="instagram"):
    bounded(text,"caption")
    if platform not in ("instagram","youtube","facebook","tiktok"):raise ValueError("Unsupported platform")
    lines=text.splitlines()
    first=lines[0].strip() if lines else ""
    hashtags=re.findall(r"(?<!\w)#[\w]+",text)
    return {"opening":first,"feed_preview":text[:125],
            "truncated_before_context":len(first)>125,"hashtag_count":len(hashtags),
            "single_call_to_action":len(re.findall(r"(?i)\b(follow|comment|save|share|visit|click|dm)\b",text))==1,
            "quality":copycheck(text),
            "note":"A local preview, not a guarantee of any platform's exact truncation on every device."}


def carousel_outline(topic,points,platform="instagram"):
    bounded(topic,"topic",200)
    if platform not in ("instagram","facebook","multi"):raise ValueError("Unsupported format")
    if not isinstance(points,list) or not 2<=len(points)<=14:raise ValueError("Provide 2-14 points")
    slides=[{"slide":1,"role":"cover","copy":topic,"image_brief":"Original cover visual with topic contrast, brand-approved assets only"}]
    for i,p in enumerate(points,2):
        slides.append({"slide":i,"role":"body","copy":bounded(p,"slide point",350),
                       "image_brief":"Illustrate this particular point; original or rights-cleared material only"})
    slides.append({"slide":len(slides)+1,"role":"call_to_action","copy":"Your next action or question",
                   "image_brief":"Brand-consistent final slide; ask host to tailor CTA to audience"})
    return {"slides":slides,"target_aspect":"4:5","required_review":"Host must create/receive and approve exact images; these are text-only slide specifications."}


def story_sequence(topic,goal,frames):
    bounded(topic,"topic",220)
    if goal not in OBJECTIVES:raise ValueError("Invalid goal")
    if not isinstance(frames,list) or not 2<=len(frames)<=12:raise ValueError("Provide 2-12 frame topics")
    roles=("attention","context","proof","participation","resolution","call_to_action")
    slides=[]
    for i,p in enumerate(frames):
        slides.append({"frame":i+1,"role":roles[min(i,len(roles)-1)],
                       "instruction":bounded(p,"frame topic",500),
                       "media_prompt":"Create an original 9:16 story visual with continuity and accessible legibility",
                       "interactive_suggestion":"Optional question/poll with provider permission" if i==len(frames)-2 else None})
    return {"topic":topic,"goal":goal,"frames":slides,"status":"concept_only",
            "limits":"No story images, live stickers, platform scheduling or posting have occurred."}


def engagement_triage(comments):
    if not isinstance(comments,list) or not 1<=len(comments)<=100:raise ValueError("Provide 1-100 comments")
    result=[]
    for i,c in enumerate(comments):
        c=bounded(c,"comment",1500)
        if re.search(r"(?i)\b(price|how much|where to buy|ship|order|available)\b",c):
            priority="lead";guidance="Answer only verified product details; ask privately before providing sensitive data."
        elif "?" in c or "？" in c:
            priority="question";guidance="Answer concretely and cite verified facts."
        elif re.search(r"(?i)\b(scam|fake|bad|refund|problem)\b",c):
            priority="support";guidance="Acknowledge issue and route privately; don't promise unverified resolutions."
        else:
            priority="community";guidance="Reply if genuine interaction would add value; no unsolicited spam."
        result.append({"index":i,"comment":c,"priority":priority,"reply_instruction":guidance,"draft_status":"host_to_write"})
    result.sort(key=lambda x:{"support":0,"lead":1,"question":2,"community":3}[x["priority"]])
    return {"queue":result,"approval_required":True,
            "note":"Classification is heuristic; it does not send replies or access Instagram DMs."}
