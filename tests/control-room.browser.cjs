/* Real browser against disposable state; blocks all provider network requests. */
const {chromium}=require(process.env.VSO_PLAYWRIGHT_MODULE||'playwright');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict');
const base=process.env.VSO_QA_URL||'http://127.0.0.1:8898';
const root=process.env.VSO_QA_DATA||'/tmp/vso-control-qa';
const python=process.env.VSO_QA_PYTHON||'python';
(async()=>{
 const fixture=execFileSync(python,['-c',`import sys,json,base64
from vso.store import Store
from vso.engine import Engine
s=Store(sys.argv[1]);e=Engine(s)
with s.db() as db: db.execute("DELETE FROM records WHERE kind!='installation'")
s.put('account','qa-facebook',{'id':'qa-facebook','provider':'facebook','remote_id':'qa-only','name':'Simulated test Page','status':'connected'})
c=e.channel_save('Furniture stories','Small apartment buyers',account_ids=['qa-facebook'])
concepts=[{'title':t,'hook':'Measure before you buy','script':'Measure the doorway and leave room to move.','scenes':[{'image_prompt':'A small room with a sofa','video_prompt':'Camera reveals the doorway'}]} for t in ['Make room for living','The doorway test']]
p=e.plan_save(c['id'],concepts,'browser-review');e.concept_select(p['id'],0,0)
a=e.asset_import('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl6N7sAAAAASUVORK5CYII=','image/png');e.image_attach(p['id'],0,a['id'])
print(json.dumps({'ticket':s.ticket('pair',{}),'plan_id':p['id']}))`,root],{encoding:'utf8'});
 const {ticket,plan_id}=JSON.parse(fixture);
 const browser=await chromium.launch({headless:true,...(process.env.VSO_QA_CHROME?{executablePath:process.env.VSO_QA_CHROME,chromiumSandbox:true}:{})});
 const page=await browser.newPage({viewport:{width:1440,height:960},reducedMotion:'reduce'});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',r=>new URL(r.request().url()).origin===new URL(base).origin?r.continue():r.abort());
 await page.goto(base+'/pair?ticket='+ticket);await page.waitForSelector('#setup-steps .step',{state:'attached'});
 await page.locator('a.settings-link').click();await page.locator('#profile-form [name="name"]').fill('Independent operator');await page.locator('#profile-form [name="goals"]').fill('Original furniture content');await page.locator('#profile-form button').click();await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('Profile saved'));
 await page.locator('nav a[href="#accounts"]').click();assert.equal(await page.locator('#accounts input[type=password]').count(),0);
 await page.locator('#provider-cards button').filter({hasText:'Connect YouTube'}).click();await page.locator('#connect-dialog').waitFor({state:'visible'});assert(await page.locator('#dialog-content').textContent().then(t=>t.includes('Connection service needs setup')));await page.locator('#dialog-close').click();
 await page.locator('nav a[href="#productions"]').click();await page.locator('#production-cards button').filter({hasText:'Approve storyboard'}).click();await page.waitForFunction(()=>document.querySelector('#production-cards').textContent.includes('ChatGPT directs production'));
 const dialogHandler=d=>d.accept('Use a calmer opening');page.once('dialog',dialogHandler);
 await page.locator('#production-cards button').filter({hasText:'Request storyboard changes'}).click();await page.waitForFunction(()=>document.querySelector('#production-cards').textContent.includes('Waiting for ChatGPT: Use a calmer opening'));
 const state=await page.evaluate(()=>fetch('/api/state').then(r=>r.json()));assert.equal(state['review-request'].length,1);assert.equal(state['review-request'][0].plan_id,plan_id);assert.equal(state.job.length,0);assert.equal(state.publication.length,0);assert.equal(state.plan[0].revision_requested,true);
 for(const width of [360,768,1440]){await page.setViewportSize({width,height:900});for(const id of ['home','setup','accounts','flow','productions','media','publishing']){await page.evaluate(id=>location.hash=id,id);await page.locator('#'+id).waitFor({state:'visible'});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Overflow '+width+' '+id);}await page.evaluate(()=>location.hash='composer');await page.locator('#home').waitFor({state:'visible'});}
 await page.evaluate(()=>location.hash='flow');assert.equal(await page.locator('#flow-image-form').isVisible(),false);assert.equal(await page.locator('#flow-video-form').isVisible(),false);assert.equal(await page.locator('#open-flow-browser').isVisible(),true);assert.equal(await page.locator('nav a[href="#automation"]').count(),0);
 await page.screenshot({path:'/tmp/vso-video-workspace-qa.png',fullPage:true});await page.evaluate(()=>location.hash='productions');await page.screenshot({path:'/tmp/vso-content-manager-qa.png',fullPage:true});await page.evaluate(()=>location.hash='home');await page.screenshot({path:'/tmp/vso-desktop-qa.png',fullPage:true});await page.setViewportSize({width:360,height:900});await page.screenshot({path:'/tmp/vso-mobile-qa.png',fullPage:true});await page.goto(base+'/admin');await page.locator('#admin-form').waitFor({state:'visible'});assert.equal(await page.locator('#admin-id').getAttribute('readonly'),'');assert.equal(await page.locator('#admin-code').getAttribute('type'),'password');assert.deepEqual(errors,[]);await browser.close();console.log('Browser QA passed: owner setup, provider consent gate, storyboard approval and revision queue, no render/upload, hidden manual production, seven review routes and 360/768/1440 layouts.');
})().catch(e=>{console.error(e);process.exit(1);});
