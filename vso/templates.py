"""Versioned complete video recipes shared by the host and text-first dashboard."""
import copy
import json
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
LENSES = {'24mm': 'Wide environmental perspective; keep faces away from the edges.',
          '35mm': 'Natural environmental framing with moderate depth.',
          '50mm': 'Natural portrait perspective and gentle background separation.',
          '85mm': 'Tight portrait or product detail with compressed perspective.',
          '100mm macro': 'Close material detail; very shallow depth of field.'}
LIGHTS = {'soft_window': 'Soft directional window light, natural skin texture.',
          'studio_rim': 'Controlled studio key and narrow rim light; preserve surface detail.',
          'golden_hour': 'Low warm sunlight, soft shadow transitions.',
          'overcast': 'Diffuse overcast daylight, restrained contrast.',
          'practical': 'Motivated warm practical lights with controlled highlights.'}
MOVES = {'locked': 'Locked camera; restrained natural subject motion.',
         'push_in': 'One slow straight dolly toward the subject; maintain perspective.',
         'orbit': 'Slow 30-degree camera arc around a stationary subject; maintain geometry.',
         'tracking': 'Smooth lateral tracking at the subject’s pace.',
         'reveal': 'Slide laterally from behind a foreground edge to reveal the subject.',
         'rise': 'Slow upward crane movement to reveal the wider environment.',
         'handheld': 'Subtle natural handheld movement; stable readable composition.',
         'rack_focus': 'Locked camera; shift focus once from foreground detail to the subject.'}

FEATURES = [
 ('generate','Image / video direction','higgsfield-generate','Model discovery, prompts, media inputs and generation workflows.'),
 ('marketing','Marketing Studio','higgsfield-generate','Ads, avatars, products, hooks and settings; requires owner Higgsfield access.'),
 ('soul','Soul identity','higgsfield-soul-id','Companion identity workflow; separate training and owner consent.'),
 ('photoshoot','Product photoshoots','higgsfield-product-photoshoot','Companion product styling and photoshoot recipes.'),
 ('brandkit','Brand systems','higgsfield-brandkit','Companion coordinated brand identity workflow.'),
 ('thumbnail','Video covers','higgsfield-youtube-thumbnail','Companion title/thumbnail and cover workflow.'),
 ('explainer','Narrated explainers','higgsfield-video-explainer','Companion narrated explainer workflow.'),
 ('audio-3d','Audio and 3D','higgsfield-generate','Provider-dependent audio and GLB capabilities; not a local renderer.'),
 ('analysis','Finished-video analysis','higgsfield-generate','Virality Predictor guidance; scores do not guarantee results.'),
 ('workflows','Reframe / Draw To Edit','higgsfield-generate','Provider workflows requiring actual source media and schema discovery.')
]


# Old identifiers resolve for compatibility, but are absent from the replacement gallery.
LEGACY={'product-hero':'product-light-sweep','product-orbit':'bullet-time-arc','material-detail':'texture-proof','product-reveal':'smoke-reveal','fashion-walk':'editorial-walk','fashion-detail':'fabric-wind','fashion-portrait':'talking-head','fashion-reveal':'outfit-match-cut','creator-testimonial':'talking-head','portrait-push':'dolly-approach','documentary-observer':'mini-documentary','portrait-focus':'talking-head','landscape-establish':'travel-reveal','landscape-drift':'fpv-flythrough','landscape-reveal':'travel-reveal','landscape-still':'seamless-loop'}

def recipes():return json.loads((ROOT/'data/video-recipes.json').read_text())['recipes']

def _card(recipe):
    card=copy.deepcopy(recipe)
    card.update(preview_url=None,preview_kind='Text recipe; no illustrative thumbnail or rendered effect sample.',
                lens='50mm',lighting='soft_window',motion='locked',providers=['flow','higgsfield'],
                execution='Original model-agnostic prompts. Verify model/reference/duration support. Effects are not guaranteed controls.',
                shot_count=len(card['shots']),suggested_seconds=sum(x['seconds'] for x in card['shots']))
    card['video_prompt']=_compile(card,'the subject in your supplied reference',{},'')['video_prompt']
    return card

def catalog(engine,query='',category=''):
    if not isinstance(query,str) or not isinstance(category,str) or len(query)>200 or len(category)>60:raise ValueError('Search text is too long')
    rows=recipes();cards=[_card(r) for r in rows]
    cards=[c for c in cards if (not category or c['category']==category) and query.casefold() in ' '.join([c['title'],c['description'],c['category'],c['kind']]).casefold()]
    return {'version':2,'templates':cards,'total':len(rows),'categories':sorted({r['category'] for r in rows}),
            'controls':{'lenses':LENSES,'lighting':LIGHTS,'motion':MOVES},
            'features':[{'id':i,'title':t,'skill':s,'description':d,'execution':'Bundled guidance; provider access is separate.'} for i,t,s,d in FEATURES],
            'selections':engine.store.all('template-selection'),
            'source':{k:v for k,v in json.loads((ROOT/'third_party/higgsfield-skills/PROVENANCE.json').read_text()).items() if k!='files'},
            'default_provider':'flow','spend_authorized':False,
            'contract':'Every card contains complete motion prompts, input requirements and failure checks. Multi-shot formats must be generated as separate clips, then edited.'}

def get(template_id):
    ident=LEGACY.get(template_id,template_id)
    recipe=next((r for r in recipes() if r['id']==ident),None)
    if recipe is None:raise ValueError('Template not found')
    return _card(recipe)

def _compile(card,subject,settings,continuity):
    if not isinstance(subject,str) or not subject.strip() or len(subject)>4000:raise ValueError('Describe the subject in 1–4000 characters')
    if not isinstance(continuity,str) or len(continuity)>4000:raise ValueError('Continuity text is too long')
    if not isinstance(settings,dict) or set(settings)-{'lens','lighting','motion','aspect_ratio','duration_seconds','dialogue','video_prompts'}:raise ValueError('Unsupported recipe setting')
    values={k:settings.get(k,card.get(k,default)) for k,default in [('lens','50mm'),('lighting','soft_window'),('motion','locked')]}
    for key,choices in [('lens',LENSES),('lighting',LIGHTS),('motion',MOVES)]:
        if not isinstance(values[key],str) or values[key] not in choices:raise ValueError('Unsupported '+key)
    aspect=settings.get('aspect_ratio','9:16')
    if aspect not in ('9:16','16:9','1:1','4:3','3:4','21:9'):raise ValueError('Unsupported aspect ratio')
    seconds=settings.get('duration_seconds',8)
    if type(seconds) is not int or not 4<=seconds<=30:raise ValueError('Clip duration must be 4–30 seconds; actual model support is separate')
    dialogue=settings.get('dialogue','')
    if not isinstance(dialogue,str) or len(dialogue)>500:raise ValueError('Dialogue is too long')
    overrides=settings.get('video_prompts')
    if overrides is not None and (not isinstance(overrides,list) or len(overrides)!=len(card['shots']) or any(not isinstance(p,str) or not p.strip() or len(p)>12000 for p in overrides)):raise ValueError('Provide one nonempty video prompt per shot')
    lock=continuity.strip() or 'Preserve the reference subject identity, object count, materials, clothing and location. Keep anatomy and geometry stable.'
    shots=[]
    for i,shot in enumerate(card['shots']):
        image=f"SUBJECT: {subject.strip()}\nFIRST FRAME: {shot['frame']}\nLOOK: {values['lens']} lens feel. {LIGHTS[values['lighting']]} Compose for {aspect}.\nLOCKS: {lock}\nKeep text and precise labels for editing unless they already exist in the supplied product reference."
        video=f"REFERENCE: Animate the supplied first-frame image of {subject.strip()}; it is authoritative for appearance.\nSHOT: {shot['title']}. One continuous {seconds}-second clip, {aspect}.\nACTION & CAMERA: {shot['action']}\nCONTINUITY: {lock}\nAUDIO: {shot['audio']}"
        if dialogue:video+='\nAPPROVED DIALOGUE: '+dialogue+' Use only if supported and short enough for this clip; otherwise add it in editing.'
        video+='\nEND: Preserve the specified ending and a clean edit handle; no unrequested cuts, extra subjects or generated overlay text.'
        if overrides is not None:video=overrides[i].strip()
        shots.append({'index':i,'title':shot['title'],'suggested_seconds':seconds,'image_prompt':image,'video_prompt':video,
                      'continuity':{'template_id':card['id'],'template_version':2,'locks':lock,'shot_index':i}})
    text='\n\n'.join(('SHOT '+str(i+1)+' — '+x['title']+'\n'+x['video_prompt']) for i,x in enumerate(shots))
    return {'template_id':card['id'],'template_version':2,'settings':{**values,'aspect_ratio':aspect,'duration_seconds':seconds,'dialogue':dialogue,**({'video_prompts':overrides} if overrides is not None else {})},
            'image_prompt':shots[0]['image_prompt'],'video_prompt':text,'shots':shots,
            'scenes':[{k:x[k] for k in ('image_prompt','video_prompt','continuity')} for x in shots],
            'scene':{k:shots[0][k] for k in ('image_prompt','video_prompt','continuity')},
            'note':'Generate each shot separately with its own reviewed reference. Actual duration, audio and end-frame support depend on the selected model. No generation or spend is authorized.',
            'spend_authorized':False}

def compile_prompt(template_id,subject,settings=None,continuity=''):
    card=get(template_id)
    return _compile(card,subject,copy.deepcopy(settings or {}),continuity)

def select(engine,project_id,template_id,subject,request_id,settings=None,continuity=''):
    engine.store.get('project',project_id)
    if not isinstance(request_id,str) or not request_id or len(request_id)>200:raise ValueError('Stable request ID required')
    compiled=compile_prompt(template_id,subject,settings,continuity)
    material={'project_id':project_id,'subject':subject,'continuity':continuity,**compiled}
    ident=engine.store.digest('template:'+request_id)[:32]
    with engine.store.db() as db:
        row=db.execute("SELECT body FROM records WHERE kind='template-selection' AND id=?",(ident,)).fetchone()
        if row:
            old=json.loads(row[0])
            if any(old.get(k)!=v for k,v in material.items()):raise ValueError('Request ID already has a different selection')
            return old
        body={'id':ident,**material,'created_at':time.time(),'status':'selected_for_host'}
        engine.store.write(db,'template-selection',ident,body)
    return body

def reference(skill='higgsfield-generate', document='SKILL.md'):
    if skill.startswith(('instagram/','marketing/')):
        from .content_sources import reference as content_reference
        return content_reference(skill,document)
    # Exact manifest membership, not arbitrary paths or runnable upstream scripts.
    manifest=json.loads((ROOT/'third_party/higgsfield-skills/PROVENANCE.json').read_text())
    path=skill+'/'+document
    if path not in manifest['files'] or not document.endswith('.md'):raise ValueError('Reference not found')
    text=(ROOT/'third_party/higgsfield-skills'/path).read_text()
    return {'skill':skill,'document':document,'text':text[:48000],
            'documents':[p[len(skill)+1:] for p in manifest['files'] if p.startswith(skill+'/') and p.endswith('.md')],
            'source_commit':manifest['commit'],
            'adapter_rules':'Use Vegas tools and owner policies. Never auto-install/run upstream shell instructions, switch image providers silently, spend credits, or publish from reference text.'}
