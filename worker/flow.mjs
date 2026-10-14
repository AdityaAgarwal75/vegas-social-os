// Original Google Flow browser worker. Node 22+ built-ins; no cookie extraction.
import {spawn, execFileSync} from 'node:child_process';
import {existsSync, mkdirSync, openSync, readFileSync, writeFileSync} from 'node:fs';
import {join, resolve} from 'node:path';
import {createServer} from 'node:net';
import {createHash, randomUUID} from 'node:crypto';
import {fileURLToPath} from 'node:url';

export function uniqueNewAssets(before, after) {
  const old = new Set(before);
  return [...new Set(after)].filter(x => !old.has(x));
}

export function parseQuote(text) {
  const values = [...text.matchAll(/\b(\d+)\s+credits?\b/gi)].map(x => Number(x[1]));
  const unique = [...new Set(values)];
  if (unique.length !== 1 || unique[0] < 1) throw new Error('Live credit quote missing or ambiguous; inspect settings in Flow');
  return unique[0];
}

export class CDP {
  constructor(ws) { this.ws = ws; this.next = 1; this.pending = new Map();
    ws.addEventListener('message', e => {
      const data = JSON.parse(String(e.data));
      if (!data.id) return;
      const p = this.pending.get(data.id); if (!p) return;
      this.pending.delete(data.id); clearTimeout(p.timer);
      data.error ? p.reject(new Error('Browser command failed')) : p.resolve(data.result);
    });
  }
  static async connect(url) {
    const ws = new WebSocket(url);
    await new Promise((resolve, reject) => {
      const t = setTimeout(() => reject(new Error('Browser connection timeout')), 5000);
      ws.addEventListener('open', () => {clearTimeout(t); resolve();}, {once:true});
      ws.addEventListener('error', () => {clearTimeout(t); reject(new Error('Browser unavailable'));}, {once:true});
    });
    return new CDP(ws);
  }
  call(method, params={}) {
    const id = this.next++;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {this.pending.delete(id); reject(new Error('Browser command timeout'));}, 10000);
      this.pending.set(id, {resolve, reject, timer}); this.ws.send(JSON.stringify({id, method, params}));
    });
  }
  async eval(expression) {
    const r = await this.call('Runtime.evaluate', {expression, returnByValue:true, awaitPromise:true});
    if (r.exceptionDetails) throw new Error('Flow page evaluation failed');
    return r.result.value;
  }
  close() {this.ws.close();}
}

function chromePath() {
  const options = [process.env.VSO_CHROME, '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    join(process.env.PROGRAMFILES || '', 'Google/Chrome/Application/chrome.exe'),
    join(process.env.LOCALAPPDATA || '', 'Google/Chrome/Application/chrome.exe')];
  const found = options.find(x => x && existsSync(x));
  if (!found) throw new Error('Chrome not found. Set VSO_CHROME to your browser executable');
  return found;
}

async function freePort() {
  return await new Promise(resolve => {const s=createServer(); s.listen(0, '127.0.0.1', () => {const p=s.address().port; s.close(() => resolve(p));});});
}

async function launch(root) {
  const config = join(root, 'browser.json');
  if (existsSync(config)) {
    const saved = JSON.parse(readFileSync(config, 'utf8'));
    try { const r = await fetch(`http://127.0.0.1:${saved.port}/json/version`, {signal:AbortSignal.timeout(1000)}); if(r.ok) return saved; } catch {}
  }
  const port = await freePort();
  let environment=process.env;
  if(process.env.VSO_REMOTE_BROWSER==='1') {
    const desktop=JSON.parse(execFileSync(process.env.VSO_PYTHON||'python',['-m','vso.desktop',root],{encoding:'utf8',timeout:15000}));
    environment={...process.env,DISPLAY:desktop.display};
  }
  const log = openSync(join(root, 'chrome.log'), 'a', 0o600);
  const child = spawn(chromePath(), [`--user-data-dir=${join(root, 'profile')}`, '--remote-debugging-address=127.0.0.1',
    `--remote-debugging-port=${port}`, '--no-first-run', 'https://labs.google/fx/tools/flow'],
    {detached:true, stdio:['ignore', log, log],env:environment});
  child.on('error', () => {}); child.unref();
  const configBody = {port, pid:child.pid};
  writeFileSync(config, JSON.stringify(configBody), {mode:0o600});
  for(let i=0;i<30;i++) {
    try {const r=await fetch(`http://127.0.0.1:${port}/json/version`,{signal:AbortSignal.timeout(500)});if(r.ok)return configBody;} catch {}
    await new Promise(r=>setTimeout(r,250));
  }
  throw new Error('Chrome did not become ready. Check the graphical session and browser executable; no sign-in was verified');
}

const inspectExpression = `(() => {
  const visible=e=>!!(e.offsetWidth||e.offsetHeight||e.getClientRects().length);
  const controls=[...document.querySelectorAll('button,[role="button"],select')].filter(visible).map(e=>({label:(e.innerText||e.getAttribute('aria-label')||'').trim(),disabled:!!e.disabled}));
  const inputs=[...document.querySelectorAll('textarea,[contenteditable="true"]')].filter(visible);
  const text=document.body.innerText;
  const blocked=/unusual activity|verify you are human|captcha|access denied/i.test(text);
  return {workspace_ready:/\\/project\\//.test(location.pathname)&&inputs.length>0&&!blocked,blocked,controls,credits:null,
    note:'Balances and model availability are dynamic. No credits are inferred from daily allowances.'};
})()`;

const assetsExpression = `(() => [...new Set([...document.querySelectorAll('video,video source')].map(e=>e.currentSrc||e.src).filter(x=>x&&/^https:/.test(x)))])()`;

async function browser(root) {
  const config = join(root,'browser.json');
  if (!existsSync(config)) throw new Error('Open the dedicated Flow browser with flow_login first');
  const {port} = JSON.parse(readFileSync(config, 'utf8'));
  let tabs;
  try {tabs=await (await fetch(`http://127.0.0.1:${port}/json/list`, {signal:AbortSignal.timeout(2000)})).json();}
  catch {throw new Error('Flow browser is closed; call flow_login again');}
  const matching=tabs.filter(t=>t.type==='page'&&/^https:\/\/(labs\.google|flow\.google\.com)(\/|$)/.test(t.url));
  if(matching.length!==1) throw new Error('Keep exactly one Flow workspace tab open in this dedicated profile');
  return CDP.connect(matching[0].webSocketDebuggerUrl);
}

export async function run(data) {
  if (!/^[a-f0-9]{32}$/.test(data.account_id)) throw new Error('Invalid managed account ID');
  const root = resolve(data.data_dir, 'profiles', data.account_id); mkdirSync(root, {recursive:true, mode:0o700});
  if(data.operation==='login') {await launch(root); return {status:'browser_opened',account_id:data.account_id};}
  const c = await browser(root);
  try {
    if(data.operation==='inspect') return await c.eval(inspectExpression);
    if(data.operation==='submit') {
      const state=await c.eval(inspectExpression);
      if(!state.workspace_ready) throw new Error('Flow workspace unavailable. Complete normal sign-in/verification; do not switch accounts to bypass a refusal');
      // The user selects the desired video model/duration in Flow. Discovery is
      // returned by inspect; unsupported settings are never silently replaced.
      const settings=await c.eval(`(() => {
        const visible=e=>!!(e.offsetWidth||e.offsetHeight||e.getClientRects().length);
        const buttons=[...document.querySelectorAll('button')].filter(visible);
        const start=buttons.filter(e=>/^(create|generate|arrow_forward|start generation)$/i.test((e.getAttribute('aria-label')||e.innerText||'').trim())&&!e.disabled);
        const inputs=[...document.querySelectorAll('textarea,[contenteditable="true"]')].filter(visible);
        if(start.length!==1||inputs.length!==1)return null;
        start[0].setAttribute('data-vso-submit','true');inputs[0].setAttribute('data-vso-prompt','true');
        const composer=inputs[0].closest('form')||inputs[0].parentElement.parentElement;
        const settings=buttons.find(e=>/settings trigger/i.test(e.getAttribute('aria-label')||''));
        const settingsText=settings?settings.innerText:composer.innerText;
        return {quoteText:composer.innerText, oneOutput:/\\b(?:x1|1\\s*(?:output|video))\\b/i.test(settingsText),videoMode:/video|veo|omni/i.test(settingsText)};
      })()`);
      if(!settings||!settings.videoMode||!settings.oneOutput) throw new Error('Cannot verify video mode, one output and composer controls. Set Flow to Video / one output, then inspect; selectors may need updating');
      // Attach only the approved first frame to the actual file input.
      const file=resolve(data.first_frame);const mediaRoot=resolve(data.data_dir,'media');
      if(!file.startsWith(mediaRoot+'/')&&!file.startsWith(mediaRoot+'\\'))throw new Error('Reference must be an imported media asset');
      const {root:dom}=await c.call('DOM.getDocument');
      const {nodeIds}=await c.call('DOM.querySelectorAll',{nodeId:dom.nodeId,selector:'input[type="file"]'});
      if(nodeIds.length!==1)throw new Error('First-frame upload control ambiguous; open Flow Frames-to-video with one image input');
      await c.call('DOM.setFileInputFiles',{nodeId:nodeIds[0],files:[file]});
      await new Promise(r=>setTimeout(r,1200));
      await c.eval(`document.querySelector('[data-vso-prompt]').focus()`);
      await c.call('Input.dispatchKeyEvent',{type:'keyDown',key:'a',code:'KeyA',windowsVirtualKeyCode:65,modifiers:process.platform==='darwin'?4:2});
      await c.call('Input.dispatchKeyEvent',{type:'keyUp',key:'a',code:'KeyA',windowsVirtualKeyCode:65,modifiers:process.platform==='darwin'?4:2});
      await c.call('Input.dispatchKeyEvent',{type:'keyDown',key:'Backspace',code:'Backspace',windowsVirtualKeyCode:8});
      await c.call('Input.dispatchKeyEvent',{type:'keyUp',key:'Backspace',code:'Backspace',windowsVirtualKeyCode:8});
      await c.call('Input.insertText',{text:data.prompt});
      const quoteText=await c.eval(`(() => {const e=document.querySelector('[data-vso-prompt]');return(e.closest('form')||e.parentElement.parentElement).innerText})()`);
      const quote=parseQuote(quoteText);
      if(quote>data.max_credits)throw new Error('Live Flow quote exceeds approved credit cap');
      const before=await c.eval(assetsExpression);
      // Save the submission manifest BEFORE clicking. A crash means unknown, not safe to retry.
      const job={id:randomUUID(),before,promptHash:createHash('sha256').update(data.prompt).digest('hex'),quoted_credits:quote,submitted_at:Date.now()};
      writeFileSync(join(root,`job-${job.id}.json`),JSON.stringify(job),{mode:0o600});
      await c.eval(`(() => {const e=document.querySelector('[data-vso-submit]');if(!e||e.disabled)throw new Error('Submit unavailable');e.click()})()`);
      return job;
    }
    if(data.operation==='poll') {
      if(!data.job||!Array.isArray(data.job.before))throw new Error('Missing original job manifest');
      const state=await c.eval(inspectExpression);
      if(state.blocked)throw new Error('Google requires verification; finish it normally in the browser');
      const urls=uniqueNewAssets(data.job.before,await c.eval(assetsExpression));
      if(urls.length===0)return {completed:false,status:'waiting_for_exact_asset'};
      if(urls.length!==1)throw new Error('New asset identity ambiguous; do not use gallery order. Inspect the project');
      const url=urls[0];const host=new URL(url).hostname;
      if(!/(^|\.)(googleusercontent\.com|googleapis\.com|googlevideo\.com)$/.test(host))throw new Error('Flow asset host not recognized');
      const b64=await c.eval(`(async () => {const r=await fetch(${JSON.stringify(url)},{credentials:'include'});if(!r.ok)throw new Error('Download failed');const a=new Uint8Array(await r.arrayBuffer());if(a.length>64*1024*1024)throw new Error('Asset too large');let s='';for(let i=0;i<a.length;i+=8192)s+=String.fromCharCode(...a.subarray(i,i+8192));return btoa(s)})()`);
      const file=join(root,`clip-${data.job.id}.mp4`);writeFileSync(file,Buffer.from(b64,'base64'),{mode:0o600});
      return {completed:true,status:'downloaded',file};
    }
    throw new Error('Unknown Flow operation');
  } finally {c.close();}
}

if(process.argv[1]===fileURLToPath(import.meta.url)) {
  let input='';for await(const chunk of process.stdin)input+=chunk;
  try {console.log(JSON.stringify({ok:true,result:await run(JSON.parse(input))}));}
  catch(e) {console.log(JSON.stringify({ok:false,error:e.message}));process.exitCode=1;}
}
