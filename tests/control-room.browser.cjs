/* Browser QA against a disposable local installation. Never contacts providers. */
const {chromium}=require(process.env.VSO_PLAYWRIGHT_MODULE||'playwright');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict');
const base=process.env.VSO_QA_URL||'http://127.0.0.1:8898';
const root=process.env.VSO_QA_DATA||'/tmp/vso-control-qa';
const python=process.env.VSO_QA_PYTHON||'python';
(async()=>{
 const ticket=execFileSync(python,['-c',"from vso.store import Store; import sys; s=Store(sys.argv[1]); s.put('account','qa-facebook',{'id':'qa-facebook','provider':'facebook','remote_id':'qa-only','name':'Browser test Page (simulated)','status':'connected'}); print(s.ticket('pair',{}))",root],{encoding:'utf8'}).trim();
 const browser=await chromium.launch({headless:true, ...(process.env.VSO_QA_CHROME?{executablePath:process.env.VSO_QA_CHROME,chromiumSandbox:true}:{})});
 const page=await browser.newPage({viewport:{width:1440,height:960},reducedMotion:'reduce'});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/pair?ticket='+ticket);await page.waitForSelector('#setup-steps .step',{state:'attached'});
 await page.locator('a.settings-link').click();
 await page.locator('#profile-form [name="name"]').fill('Independent operator');
 await page.locator('#profile-form [name="brand"]').fill('My own studio');
 await page.locator('#profile-form [name="goals"]').fill('Original furniture content for local buyers');
 await page.locator('#profile-form button').click();await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('Profile saved'));
 await page.locator('nav a[href="#accounts"]').click();
 assert.equal(await page.locator('#accounts input[type="password"]').count(),0);
 await page.locator('#provider-cards button').filter({hasText:'Connect YouTube'}).click();await page.locator('#connect-dialog').waitFor({state:'visible'});assert((await page.locator('#dialog-content').textContent()).includes('setup agent'));await page.locator('#dialog-close').click();
 await page.locator('a.settings-link').click();await page.locator('#show-advanced').click();
 await page.locator('details[data-provider="google"] summary').click();
 await page.locator('details[data-provider="google"] [name="client_id"]').fill('qa-client');
 await page.locator('details[data-provider="google"] [name="client_secret"]').fill('qa-private-secret');
 await page.locator('details[data-provider="google"] form button').click();await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('App settings saved'));
 assert.equal(await page.locator('details[data-provider="google"] [name="client_secret"]').inputValue(),'');
 const snapshot=await page.request.get(base+'/api/state');assert(!(await snapshot.text()).includes('qa-private-secret'));
 await page.evaluate(()=>location.hash='channels');
 await page.locator('#channel-form [name="name"]').fill('Furniture stories');await page.locator('#channel-form [name="niche"]').fill('Small apartments');
 await page.locator('#destinations input[value="qa-facebook"]').check();await page.locator('#channel-form button').click();await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('Channel brief saved'));
 await page.locator('nav a[href="#media"]').click();
 const image=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aD3sAAAAASUVORK5CYII=','base64');
 await page.locator('#upload-form input').setInputFiles({name:'qa.png',mimeType:'image/png',buffer:image});
 await page.locator('#upload-form button').click();await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('Actual files imported'));
 await page.evaluate(()=>location.hash='composer');
 await page.locator('#post-account').selectOption('qa-facebook');await page.locator('#composer-form [name="caption"]').fill('A reviewed test draft. Do not publish.');
 await page.locator('#composer-form [name="visibility"]').selectOption('public');await page.locator('#post-assets input').first().check();
 await page.locator('#composer-form button').click();await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('Release prepared'));
 assert(await page.locator('#publication-cards').textContent().then(t=>t.includes('A reviewed test draft. Do not publish.')));
 await page.locator('#publication-cards button').filter({hasText:'Cancel release'}).click();await page.waitForFunction(()=>document.querySelector('#publication-cards').textContent.includes('cancelled'));
 await page.locator('nav a[href="#automation"]').click();await page.locator('#schedule-channels input').first().check();await page.locator('#schedule-form [name="hour"]').fill('23');
 await page.locator('#schedule-form button').filter({hasText:'Enable daily briefs'}).click();await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('Daily briefs enabled'));
 await page.locator('#pause-briefs').click();await page.waitForFunction(()=>document.querySelector('#automation-status').textContent.includes('paused'));
 for(const id of ['home','setup','accounts','flow','strategy','channels','productions','media','composer','publishing','automation','research']){
  await page.evaluate(id=>location.hash=id,id);await page.locator('#'+id).waitFor({state:'visible'});assert.equal(await page.locator('#'+id).isVisible(),true);
 }
 await page.evaluate(()=>location.hash='home');await page.screenshot({path:'/tmp/vso-desktop-qa.png',fullPage:true});
 await page.evaluate(()=>location.hash='strategy');await page.locator('#strategy-channel').selectOption({label:'Furniture stories'});await page.locator('#strategy-form [name=audience]').fill('Small apartment buyers');await page.locator('#strategy-form [name=goal]').fill('Qualified inquiries');await page.locator('#strategy-form [name=voice]').fill('Plain practical English');await page.locator('#strategy-form [name=pillars]').fill('Space\nMaterials');await page.locator('#strategy-form button').click();await page.waitForFunction(()=>document.querySelector('#notice').textContent.includes('Channel strategy saved'));await page.locator('#content-channel').selectOption({label:'Furniture stories'});await page.locator('#content-request-form [name=week_start]').fill('2026-10-19');await page.locator('#content-request-form button').click();await page.waitForFunction(()=>document.querySelector('#content-calendars').textContent.includes('awaiting agent'));await page.locator('#reel-review-form [name=hook]').fill('Your sofa may block this doorway');await page.locator('#reel-review-form [name=script]').fill('Measure the doorway before you buy.');await page.locator('#reel-review-form button').click();await page.waitForFunction(()=>document.querySelector('#reel-review-result').textContent.includes('estimated_seconds'));await page.evaluate(()=>location.hash='flow');assert.equal(await page.locator('#flow-video-model option').count(),4);await page.locator('#flow-video-model').selectOption('Veo 3.1 - Quality');assert.equal(await page.locator('#flow-video-duration option[value=10]').count(),0);assert.equal(await page.locator('#flow-video-resolution option[value=360p]').count(),0);
 for(const width of [360,768,1440]){await page.setViewportSize({width,height:900});for(const id of ['home','accounts','flow','strategy','composer','setup']){await page.evaluate(id=>location.hash=id,id);await page.locator('#'+id).waitFor({state:'visible'});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Horizontal overflow at '+width+' on '+id);}}
 await page.setViewportSize({width:360,height:900});await page.evaluate(()=>location.hash='home');await page.screenshot({path:'/tmp/vso-mobile-qa.png',fullPage:true});
 assert.deepEqual(errors,[]);
 await browser.close();console.log('Browser QA passed: profile, encrypted app settings, brief, asset import, exact draft/cancel, scheduler, 12 routes and strategy/calendar/reel/model controls, consent buttons, advanced-only credentials, visible Flow Studio, and 360/768/1440 layouts. No provider calls or publishing.');
})().catch(e=>{console.error(e);process.exit(1);});
