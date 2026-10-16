/* Real UI + local persistence. Disposable state only; all external requests blocked. */
'use strict';
const {chromium}=require(process.env.VSO_PLAYWRIGHT_MODULE||'playwright');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict');
const base=process.env.VSO_QA_URL||'http://127.0.0.1:8898';
const root=process.env.VSO_QA_DATA||'/tmp/vso-control-qa';
const python=process.env.VSO_QA_PYTHON||'python';
(async()=>{
 const fixture=JSON.parse(execFileSync(python,['-c',`import sys,json,base64,time,subprocess
from pathlib import Path
from vso.store import Store
from vso.engine import Engine
from vso import projects
assert Path(sys.argv[1]).resolve().is_relative_to('/tmp'), 'Use disposable QA state'
s=Store(sys.argv[1]);e=Engine(s)
with s.db() as db: db.execute("DELETE FROM records WHERE kind!='installation'")
s.put('profile','owner',{'name':'Alex','brand':'Sample studio','timezone':'UTC'})
for ident,provider,name in [('demo-youtube','youtube','Sample channel'),('demo-facebook','facebook','Sample Page')]:s.put('account',ident,{'id':ident,'provider':provider,'remote_id':ident,'name':name,'status':'connected','verified_at':time.time()})
s.put('account','demo-flow',{'id':'demo-flow','provider':'flow','label':'Production profile','credits':80,'verified_at':time.time()-600,'status':'workspace_ready'})
p=projects.create(e,'Objects in motion','demo-project')
image=e.asset_import(base64.b64encode(Path('web/template-previews/product.png').read_bytes()).decode(),'image/png',p['id'],'storyboard',0)
landscape=e.asset_import(base64.b64encode(Path('web/template-previews/landscape.png').read_bytes()).decode(),'image/png')
second=projects.create(e,'A moment outdoors','demo-landscape');projects.attach(e,second['id'],landscape['id'],'image',0)
clip=Path(sys.argv[1])/'qa-clip.mp4'
subprocess.run(['ffmpeg','-v','error','-y','-loop','1','-i','web/template-previews/product.png','-t','1','-vf','scale=320:212','-r','10','-pix_fmt','yuv420p',str(clip)],check=True)
video=e.asset_import(base64.b64encode(clip.read_bytes()).decode(),'video/mp4',p['id'],'clip',0)
projects.attach(e,p['id'],video['id'],'final',0)
print(json.dumps({'ticket':s.ticket('pair',{}),'project':p['id'],'image':image['id'],'video':video['id']}))`,root],{encoding:'utf8'}));
 const browser=await chromium.launch({headless:true,...(process.env.VSO_QA_CHROME?{executablePath:process.env.VSO_QA_CHROME,chromiumSandbox:true}:{})});
 const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>new URL(r.request().url()).origin===new URL(base).origin?r.continue():r.abort());
 await page.goto(base+'/pair?ticket='+fixture.ticket);await page.locator('#page-root .panel').first().waitFor();
 const go=async hash=>{await page.evaluate(h=>location.hash=h,hash);await page.waitForTimeout(80);};
 await go('project/'+fixture.project);await page.getByRole('heading',{name:/^Images/}).waitFor();assert.equal(await page.locator('.media-group').count(),3);assert.equal(await page.getByRole('heading',{name:/^Scene clips/}).count(),1);assert.equal(await page.getByRole('heading',{name:/^Final exports/}).count(),1);
 await page.getByRole('button',{name:'Preview Scene 1 · storyboard',exact:true}).click();await page.locator('.lightbox-image').waitFor();assert(await page.locator('.lightbox-image').evaluate(i=>i.complete&&i.naturalWidth>0));await page.getByRole('button',{name:'Close dialog'}).click();
 await go('media');await page.getByRole('button',{name:'Images',exact:true}).click();assert.equal(await page.locator('.media-group').count(),2);assert.equal(await page.locator('video').count(),0);await page.getByRole('button',{name:'Scene clips',exact:true}).click();assert.equal(await page.locator('.asset-card').count(),1);await page.getByRole('button',{name:'Final exports',exact:true}).click();assert.equal(await page.locator('.asset-card').count(),1);
 await go('publishing');await page.getByRole('button',{name:'Prepare a post',exact:true}).first().click();await page.locator('[name=account_id]').selectOption('demo-youtube');await page.locator('[name=title]').fill('Sample reviewed release');await page.locator('[name=asset][value="'+fixture.video+'"]').check();await page.locator('[name=caption]').fill('An original sample video for private UI verification.');await page.locator('[name=thumbnail_id]').selectOption(fixture.image);await page.locator('[name=audience]').selectOption('general');await page.locator('[name=tags]').fill('studio, sample');const when=new Date(Date.now()+2*86400000);when.setSeconds(0,0);const local=new Date(when-when.getTimezoneOffset()*60000).toISOString().slice(0,16);await page.locator('[name=schedule_at]').fill(local);await page.getByRole('button',{name:'Prepare for review',exact:true}).click();await page.waitForFunction(()=>!document.querySelector('#connect-dialog').open);assert((await page.locator('#page-root').textContent()).includes('Sample reviewed release'));let state=await page.evaluate(()=>fetch('/api/state').then(r=>r.json()));assert.equal(state.publication.length,1);const post=state.publication[0];assert.equal(post.status,'review');assert.equal(post.visibility,'private');assert.equal(post.options.thumbnail_id,fixture.image);assert.equal(post.options.made_for_kids,false);assert.deepEqual(post.options.tags,['studio','sample']);assert.equal(Date.parse(post.options.schedule_at),when.getTime());
 page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Approve exact release',exact:true}).click();await page.getByRole('button',{name:'Schedule approved release',exact:true}).waitFor();page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Schedule approved release',exact:true}).click();await page.getByRole('button',{name:/^Scheduled · 1$/}).click();assert.equal(await page.locator('.release-card').count(),1);await page.screenshot({path:'/tmp/vso-publishing-qa.png',fullPage:true});
 await go('schedule');await page.getByRole('button',{name:'Scheduled uploads',exact:true}).click();assert((await page.locator('.schedule-item').textContent()).includes('Sample reviewed release'));const day=new Date(when).toDateString();await page.locator('.calendar-cell.has-schedule').click();assert.equal(await page.locator('.calendar-cell.selected').count(),1);assert.equal(await page.locator('.schedule-item').count(),1);
 await go('publishing');page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'Cancel release',exact:true}).click();state=await page.evaluate(()=>fetch('/api/state').then(r=>r.json()));assert.equal(state.publication[0].status,'cancelled');assert.equal(state.publication[0].remote_id,null);assert.equal(state.job.length,0);
 // Ordered Facebook media: choose in reverse order, verify the frozen server payload.
 await page.getByRole('button',{name:'Prepare a post',exact:true}).first().click();await page.locator('[name=account_id]').selectOption('demo-facebook');const ids=await page.locator('.composer-assets [name=asset]').evaluateAll(nodes=>nodes.filter(n=>n.closest('label').querySelector('img')).map(n=>n.value));await page.locator('[name=asset][value="'+ids[1]+'"]').check();await page.locator('[name=asset][value="'+ids[0]+'"]').check();await page.locator('[name=caption]').fill('An ordered photo set for review.');await page.getByRole('button',{name:'Prepare for review',exact:true}).click();await page.waitForFunction(()=>!document.querySelector('#connect-dialog').open);state=await page.evaluate(()=>fetch('/api/state').then(r=>r.json()));assert.deepEqual(state.publication.find(p=>p.provider==='facebook').asset_ids,[ids[1],ids[0]]);
 // Independent optional library failure must not take down projects or overview.
 await page.route('**/api/tool',async route=>{const body=route.request().postDataJSON();if(body.name==='template_catalog')return route.fulfill({status:503,json:{error_description:'Sample library unavailable'}});return route.continue();});await page.reload();await page.locator('.release-card').first().waitFor();await go('home');await page.locator('.metrics').waitFor();await go('templates');await page.getByRole('heading',{name:'Video recipes could not load'}).waitFor();await page.unroute('**/api/tool');await page.reload();await page.locator('.template-card').first().waitFor();
 // Public landing never displays private state; actual screenshot assets load.
 for(const hash of ['home','project/'+fixture.project,'schedule']){await go(hash);await page.evaluate(()=>document.fonts.ready);await page.screenshot({path:'/tmp/vso-demo-'+hash.split('/')[0]+'.png',fullPage:false});}
 await page.goto(base+'/about');for(const theme of ['light','dark']){await page.evaluate(t=>document.documentElement.dataset.theme=t,theme);for(const width of [360,768,1440,1920]){await page.setViewportSize({width,height:1000});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'landing overflow '+theme+' '+width);}}
 await page.setViewportSize({width:1440,height:1000});await page.evaluate(()=>document.documentElement.dataset.theme='light');await page.screenshot({path:'/tmp/vso-landing-qa.png',fullPage:true});assert(!((await page.locator('body').textContent()).includes('Sample reviewed release')));
 assert.deepEqual(errors,[]);await browser.close();console.log('PASS: grouped images/clips/exports, image preview, reviewed composer, cover/audience/tags, frozen schedule, approval/schedule/cancel, media ordering, optional catalog failure, public landing layouts. No provider requests.');
})().catch(e=>{console.error(e);process.exit(1);});
