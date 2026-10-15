/* Isolated browser acceptance. No provider login, external traffic or spending. */
'use strict';
const {chromium}=require(process.env.VSO_PLAYWRIGHT_MODULE||'playwright');
const {execFileSync}=require('node:child_process');
const assert=require('node:assert/strict');
const base=process.env.VSO_QA_URL||'http://127.0.0.1:8898';
const root=process.env.VSO_QA_DATA||'/tmp/vso-control-qa';
const python=process.env.VSO_QA_PYTHON||'python';
function fixture(code){return JSON.parse(execFileSync(python,['-c',`import sys,json\nfrom vso.store import Store\nfrom vso.owner_auth import password_set\ns=Store(sys.argv[1])\nwith s.db() as db: db.execute("DELETE FROM records WHERE kind='rate-limit'")\n`+code,root],{encoding:'utf8'}));}
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.VSO_QA_CHROME?{executablePath:process.env.VSO_QA_CHROME,chromiumSandbox:true}:{})});
 const page=await browser.newPage({viewport:{width:1440,height:1000},reducedMotion:'reduce'});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 // CDP intercepts every redirect hop; page.route only handles the first URL
 // of a redirected request and could otherwise hit the real host callback.
 const network=await page.context().newCDPSession(page);
 await network.send('Fetch.enable',{patterns:[{urlPattern:'*',requestStage:'Request'}]});
 let closing=false;const networkErrors=[];
 const handleRequest=async request=>{
  const url=new URL(request.request.url),requestId=request.requestId;
  if(url.origin===new URL(base).origin)return network.send('Fetch.continueRequest',{requestId});
  if(url.origin==='https://chatgpt.com'&&url.pathname==='/connector/oauth/test-callback')return network.send('Fetch.fulfillRequest',{requestId,responseCode:200,responseHeaders:[{name:'Content-Type',value:'text/html'}],body:Buffer.from('<h1>Test callback received</h1>').toString('base64')});
  return network.send('Fetch.failRequest',{requestId,errorReason:'Aborted'});
 };
 network.on('Fetch.requestPaused',request=>handleRequest(request).catch(error=>{if(!closing)networkErrors.push(error.message);}));
 const {ticket}=fixture("password_set(s,'private browser fixture password')\nprint(json.dumps({'ticket':s.ticket('owner-reset',{},ttl=600)}))");
 await page.goto(base+'/dashboard');await page.waitForURL(base+'/login');
 await page.getByLabel('Owner password',{exact:true}).fill('incorrect fixture password');await page.locator('button[type=submit]').click();await page.getByRole('alert').waitFor();
 assert.equal(await page.getByLabel('Owner password',{exact:true}).inputValue(),'');
 await page.getByRole('link',{name:'Forgot your password?'}).click();await page.getByRole('heading',{name:'Reset your password',exact:true}).waitFor();
 await page.screenshot({path:'/tmp/vso-recovery-qa.png',fullPage:true});
 await page.goto(base+'/owner-recovery?ticket='+ticket);await page.waitForURL(base+'/password');assert.equal(await page.locator('[name=current]').count(),0);
 await page.locator('[name=password]').fill('updated browser fixture password');await page.locator('[name=confirmation]').fill('does not match fixture');await page.locator('button[type=submit]').click();assert.equal(new URL(page.url()).pathname,'/password');
 await page.locator('[name=confirmation]').fill('updated browser fixture password');await page.locator('button[type=submit]').click();await page.waitForURL(base+'/login');
 await page.getByLabel('Owner password',{exact:true}).fill('updated browser fixture password');await page.getByRole('button',{name:'Show owner password'}).click();assert.equal(await page.locator('#owner-password').getAttribute('type'),'text');await page.getByRole('button',{name:'Hide owner password'}).click();
 for(const width of [360,768,1440]){await page.setViewportSize({width,height:1000});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'login overflow '+width);}
 await page.screenshot({path:'/tmp/vso-login-qa.png',fullPage:true});
 await page.locator('button[type=submit]').click();await page.waitForURL(base+'/dashboard');await page.waitForSelector('#setup-steps .step');
 await page.setViewportSize({width:360,height:900});await page.locator('#mobile-nav').click();assert.equal(await page.locator('#mobile-nav').getAttribute('aria-expanded'),'true');assert(await page.locator('#sidebar').evaluate(e=>e.getBoundingClientRect().x>=-1));await page.locator('nav a[href="#accounts"]').click();await page.waitForFunction(()=>document.querySelector('#mobile-nav').getAttribute('aria-expanded')==='false');await page.waitForFunction(()=>document.querySelector('#sidebar').getBoundingClientRect().right<=1);assert.equal(await page.locator('#mobile-nav').getAttribute('aria-expanded'),'false');assert(await page.locator('#sidebar').evaluate(e=>e.getBoundingClientRect().right<=1));
 await page.goto(base+'/help');for(const width of [360,768,1440]){await page.setViewportSize({width,height:1000});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'help overflow '+width);}await page.screenshot({path:'/tmp/vso-help-qa.png',fullPage:true});
 const client=await page.evaluate(async()=>{const response=await fetch('/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({client_name:'Browser fixture',redirect_uris:['https://chatgpt.com/connector/oauth/test-callback']})});return response.json();});
 const verifier='v'.repeat(43);const challenge=require('node:crypto').createHash('sha256').update(verifier).digest('base64url');
 const params=new URLSearchParams({client_id:client.client_id,redirect_uri:'https://chatgpt.com/connector/oauth/test-callback',response_type:'code',scope:'social:read',code_challenge:challenge,code_challenge_method:'S256',resource:base+'/mcp',state:'browser-fixture'});
 await page.goto(base+'/authorize?'+params);await page.getByRole('button',{name:'Authorize Vegas Social OS'}).click();await page.waitForURL('https://chatgpt.com/connector/oauth/test-callback?**');await page.getByRole('heading',{name:'Test callback received'}).waitFor();
 const code=new URL(page.url()).searchParams.get('code');assert(code);
 const exchange=await page.request.post(base+'/token',{form:{grant_type:'authorization_code',client_id:client.client_id,redirect_uri:'https://chatgpt.com/connector/oauth/test-callback',code,code_verifier:verifier,resource:base+'/mcp'}});assert.equal(exchange.status(),200);const tokens=await exchange.json();assert(tokens.access_token);
 await page.goto(base+'/dashboard');await page.locator('#logout').click();await page.waitForURL(base+'/login');
 await page.waitForLoadState('networkidle');assert.deepEqual(errors,[]);assert.deepEqual(networkErrors,[]);closing=true;await network.send('Fetch.disable');await network.detach();await browser.close();console.log('PASS: login/error/recovery/save/login, callback CSP + PKCE exchange, mobile navigation, logout and 360/768/1440 layouts. Disposable test state only; no real host acceptance claimed.');
})().catch(e=>{console.error(e);process.exit(1);});
