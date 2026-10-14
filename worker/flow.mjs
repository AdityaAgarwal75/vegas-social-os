// Original Google Flow browser worker. Node 22+ built-ins; no cookie extraction.
import {spawn, execFileSync} from 'node:child_process';
import {existsSync, mkdirSync, openSync, readFileSync, writeFileSync} from 'node:fs';
import {join, resolve} from 'node:path';
import {createServer} from 'node:net';
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
    let up=false;
    try {up=(await fetch(`http://127.0.0.1:${saved.port}/json/version`, {signal:AbortSignal.timeout(1000)})).ok;} catch {}
    if(up){
      let owns=false;
      if(process.platform==='linux'){
        try {const args=readFileSync(`/proc/${saved.pid}/cmdline`,'utf8').split('\0');owns=args.includes(`--user-data-dir=${join(root,'profile')}`)&&args.includes(`--remote-debugging-port=${saved.port}`);}catch{}
      }
      if(!owns)throw Error('Saved browser port belongs to another process/profile; inspect it before reopening');
      return saved;
    }
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
    if(['submit','poll'].includes(data.operation)) throw new Error('Use the complete managed Flow engine; legacy generation is disabled');
    throw new Error('Unknown Flow operation');
  } finally {c.close();}
}

if(process.argv[1]===fileURLToPath(import.meta.url)) {
  let input='';for await(const chunk of process.stdin)input+=chunk;
  try {console.log(JSON.stringify({ok:true,result:await run(JSON.parse(input))}));}
  catch(e) {console.log(JSON.stringify({ok:false,error:e.message}));process.exitCode=1;}
}
