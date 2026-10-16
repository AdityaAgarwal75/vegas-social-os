/* Real browser against disposable state. All provider requests blocked. */
'use strict';
const {chromium}=require(process.env.VSO_PLAYWRIGHT_MODULE||'playwright');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict');
const base=process.env.VSO_QA_URL||'http://127.0.0.1:8898';
const root=process.env.VSO_QA_DATA||'/tmp/vso-control-qa';
const python=process.env.VSO_QA_PYTHON||'python';
(async()=>{
 const fixture=execFileSync(python,['-c',`import sys,json,base64,time,zlib,struct
from datetime import datetime,timezone
from vso.store import Store
from vso.engine import Engine
from vso import projects,activity
s=Store(sys.argv[1]);e=Engine(s)
with s.db() as db: db.execute("DELETE FROM records WHERE kind!='installation'")
s.put('account','qa-facebook',{'id':'qa-facebook','provider':'facebook','remote_id':'qa-only','name':'Simulated test Page','status':'connected'})
for key,credits in [('qa-one',80),('qa-two',0),('qa-unknown',None)]:s.put('account',key,{'id':key,'provider':'flow','label':'Test profile '+key[-3:],'status':'login_required','credits':credits,'verified_at':time.time()-120})
c=e.channel_save('Furniture stories · test','Small apartment buyers',account_ids=['qa-facebook'])
concepts=[{'title':t,'hook':'Measure before you buy','script':'Measure the doorway and leave room to move.','scenes':[{'image_prompt':'A small room with a sofa','video_prompt':'Camera reveals the doorway'}]} for t in ['Make room for living','The doorway test']]
p=e.plan_save(c['id'],concepts,'browser-review');e.concept_select(p['id'],0,0)
def chunk(t,b):return struct.pack('>I',len(b))+t+b+struct.pack('>I',zlib.crc32(t+b)&0xffffffff)
png=b'\\x89PNG\\r\\n\\x1a\\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',400,240,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(b'\\0'+bytes([int(162+y/5),190,169])*400 for y in range(240))))+chunk(b'IEND',b'')
a=e.asset_import(base64.b64encode(png).decode(),'image/png');e.image_attach(p['id'],0,a['id'])
projects.collect(e)
second=projects.create(e,'The next chapter · test','second',planned_for=datetime.fromtimestamp(time.time()+86400,timezone.utc).isoformat())
b=e.asset_import(base64.b64encode(b'\\x89PNG\\r\\n\\x1a\\nfixture').decode(),'image/png')
s.put('publication','qa-release',{'id':'qa-release','provider':'facebook','account_id':'qa-facebook','status':'scheduled','scheduled_at':time.time()+90000,'title':'Scheduled test release','asset_ids':[]})
activity.report(e,'caption','Synthetic browser test task','browser-caption')
print(json.dumps({'ticket':s.ticket('pair',{}),'plan_id':p['id'],'second_id':second['id'],'asset_id':b['id']}))`,root],{encoding:'utf8'});
 const {ticket,plan_id,second_id,asset_id}=JSON.parse(fixture);
 const browser=await chromium.launch({headless:true,...(process.env.VSO_QA_CHROME?{executablePath:process.env.VSO_QA_CHROME,chromiumSandbox:true}:{})});
 const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>new URL(r.request().url()).origin===new URL(base).origin?r.continue():r.abort());
 await page.goto(base+'/pair?ticket='+ticket);await page.waitForSelector('#profile-form');
 await page.locator('#profile-form [name="name"]').fill('Independent operator');await page.locator('#profile-form [name="goals"]').fill('Original furniture content');await page.locator('#profile-form button').click();await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('Profile saved'));
 async function go(route){await page.evaluate(r=>location.hash=r,route);await page.waitForFunction(r=>location.hash==='#'+r,route);await page.waitForTimeout(80);}
 await go('home');await page.locator('.metrics').waitFor();assert.equal(await page.locator('.metric strong').first().textContent(),'80');assert((await page.locator('.role-card').allTextContents()).some(t=>t.includes('running')));assert((await page.locator('#page-root').textContent()).includes('Scheduled test release'));
 await page.evaluate(()=>document.fonts.ready);assert.equal(await page.title(),'Vegas Studio · Control panel');assert((await page.locator('#sidebar').textContent()).includes('VEGAS'));assert(await page.evaluate(()=>document.fonts.check('16px "DM Sans"')));assert.equal((await page.request.get(base+'/fonts/dm-sans.ttf')).status(),200);assert.equal((await page.request.get(base+'/horizon.css')).status(),200);
 assert.equal(await page.locator('.metrics .metric').count(),6);assert.equal(await page.locator('.horizon-source-row').count(),3);assert.equal(await page.locator('.horizon-source-pair').count(),2);const geometry=await page.locator('.horizon-source-row').first().locator(':scope > section').evaluateAll(nodes=>nodes.map(n=>{const r=n.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width};}));assert(Math.abs(geometry[0].y-geometry[1].y)<2);assert(geometry[1].x>geometry[0].x+geometry[0].width);const calendarTitle=await page.locator('.horizon-mini-calendar').locator('..').locator('h2').textContent();await page.getByRole('button',{name:'Next month',exact:true}).click();assert.notEqual(await page.locator('.horizon-mini-calendar').locator('..').locator('h2').textContent(),calendarTitle);await page.getByRole('button',{name:'Previous month',exact:true}).click();assert.equal(await page.locator('.horizon-mini-calendar').locator('..').locator('h2').textContent(),calendarTitle);
 await page.screenshot({path:'/tmp/vso-desktop-qa.png',fullPage:true});
 await page.getByRole('button',{name:'Switch to dark theme'}).click();assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');await page.reload();await page.locator('.metrics').waitFor();assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');await page.screenshot({path:'/tmp/vso-dark-qa.png',fullPage:true});await page.getByRole('button',{name:'Switch to light theme'}).click();
 await go('accounts');await page.getByRole('button',{name:'Connect account',exact:true}).click();await page.getByRole('button',{name:'YouTube',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#dialog-content').textContent.includes('setup agent must configure'));await page.getByRole('button',{name:'Close dialog'}).click();
 await go('project/'+plan_id);await page.getByRole('button',{name:'Approve storyboard',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('Storyboard approved'));
 page.once('dialog',d=>d.accept('Use a calmer opening'));await page.getByRole('button',{name:'Request storyboard changes'}).click();await page.waitForFunction(()=>document.querySelector('#page-root').textContent.includes('Waiting for ChatGPT: Use a calmer opening'));await page.screenshot({path:'/tmp/vso-content-manager-qa.png',fullPage:true});
 await go('unassigned');await page.getByRole('button',{name:'Assign to project'}).click();await page.locator('[name=project_id]').selectOption(second_id);await page.locator('[name=scene]').fill('1');await page.getByRole('button',{name:'Assign asset',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#page-root').textContent.includes('Everything has a home'));
 await go('project/'+second_id);assert((await page.locator('#page-root').textContent()).includes('Scene 1'));await page.screenshot({path:'/tmp/vso-video-workspace-qa.png',fullPage:true});
 await go('projects');await page.getByRole('button',{name:'New project',exact:true}).first().click();await page.locator('[name=name]').fill('Browser-created production');await page.getByRole('button',{name:'Create project',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#page-title').textContent==='Browser-created production');
 await page.locator('#global-search').fill('Browser-created');await page.waitForFunction(()=>location.hash==='#projects');assert.equal(await page.locator('.project-card').count(),1);await page.locator('#global-search').fill('');
 const result=await page.evaluate(()=>fetch('/api/control').then(r=>r.json()));assert.equal(result.credits.total_observed,80);assert.equal(result.schedules.filter(s=>s.kind==='scheduled').length,1);assert.equal(result.schedules.filter(s=>s.kind==='planned').length,1);assert.equal(result.projects.find(p=>p.id===second_id).assets[0].scene,0);assert.equal(result.unassigned.length,0);
 const legacy=await page.evaluate(()=>fetch('/api/state').then(r=>r.json()));assert.equal(legacy['review-request'][0].plan_id,plan_id);assert.equal(legacy.job.length,0);assert.equal(legacy.publication.length,1);assert.equal(legacy.plan[0].revision_requested,true);
 for(const theme of ['light','dark']){await page.evaluate(t=>{document.documentElement.dataset.theme=t;localStorage.setItem('vso-theme',t);},theme);for(const width of [360,768,1440,1920]){await page.setViewportSize({width,height:1000});for(const id of ['home','projects','project/'+plan_id,'unassigned','planning','schedule','agents','activity','analytics','setup','accounts','flow','system','publishing']){await go(id);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Overflow '+theme+' '+width+' '+id);assert(!(await page.locator('#page-root').textContent()).includes('undefined'),'Undefined '+id);}}}
 await page.setViewportSize({width:360,height:1000});await go('home');await page.screenshot({path:'/tmp/vso-mobile-qa.png',fullPage:true});await page.getByRole('button',{name:'Open navigation'}).click();assert.equal(await page.locator('#mobile-nav').getAttribute('aria-expanded'),'true');await page.locator('nav a[href="#projects"]').click();await page.waitForFunction(()=>document.querySelector('#mobile-nav').getAttribute('aria-expanded')==='false');await go('projects');await page.getByRole('button',{name:'Open navigation'}).click();await page.locator('nav a[href="#projects"]').click();assert.equal(await page.locator('#mobile-nav').getAttribute('aria-expanded'),'false');
 await page.goto(base+'/admin');await page.locator('#admin-form').waitFor();assert.equal(await page.locator('#admin-id').getAttribute('readonly'),'');assert.equal(await page.locator('#admin-code').getAttribute('type'),'password');assert.deepEqual(errors,[]);await browser.close();console.log('PASS: real credit totals, live specialist status, light/dark persistence, project create/assignment, scene indexing, storyboard review, provider setup gate, schedule distinctions, search, fourteen routes at 360/768/1440/1920. No provider writes.');
})().catch(e=>{console.error(e);process.exit(1);});
