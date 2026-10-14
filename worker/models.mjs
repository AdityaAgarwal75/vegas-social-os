// Original model-menu discovery. No generation, tokens or cookie access.
import {CDP} from './flow.mjs';
const pause=ms=>new Promise(r=>setTimeout(r,ms));
export async function discover(port){
 if(!Number.isInteger(port)||port<1024||port>65535)throw Error('Invalid private browser port');
 const tabs=await fetch(`http://127.0.0.1:${port}/json/list`,{signal:AbortSignal.timeout(3000)}).then(r=>r.json());
 const matching=tabs.filter(t=>t.type==='page'&&/^https:\/\/(flow\.google\.com|labs\.google)\/.*project\//.test(t.url));
 if(matching.length!==1)throw Error('Keep one Flow project tab');
 const c=await CDP.connect(matching[0].webSocketDebuggerUrl);
 const visible=`e=>!!(e.offsetWidth||e.offsetHeight||e.getClientRects().length)`;
 const escape=async()=>{for(const type of ['keyDown','keyUp'])await c.call('Input.dispatchKeyEvent',{type,key:'Escape',code:'Escape',windowsVirtualKeyCode:27});await pause(150);};
 async function clickButton(label){
  const clicked=await c.eval(`(()=>{const e=[...document.querySelectorAll('button')].filter(${visible}).find(e=>e.getAttribute('aria-label')===${JSON.stringify(label)});if(!e||e.disabled)return false;e.click();return true;})()`);
  if(!clicked)throw Error('Model control unavailable: '+label);await pause(300);
 }
 async function openSettings(){
  if(!await c.eval(`[...document.querySelectorAll('[role="radio"]')].filter(${visible}).some(e=>/(Image|Video)$/.test(e.innerText.trim()))`))await clickButton('Settings trigger');
 }
 async function mode(kind){
  await openSettings();
  const clicked=await c.eval(`(()=>{const e=[...document.querySelectorAll('[role="radio"]')].filter(${visible}).find(e=>e.innerText.trim().endsWith(${JSON.stringify(kind)}));if(!e)return false;if(e.getAttribute('aria-checked')!=='true')e.click();return true;})()`);
  if(!clicked)throw Error('Mode unavailable');
  for(let i=0;i<10;i++){await pause(150);if(await c.eval(`[...document.querySelectorAll('[role="radio"]')].filter(${visible}).some(e=>e.innerText.trim().endsWith(${JSON.stringify(kind)})&&e.getAttribute('aria-checked')==='true')`))return;}
  throw Error('Mode change could not be verified');
 }
 let original;const out={image:[],video:[],video_settings:{}};const originalModels={};
 async function currentModel(){return c.eval(`(()=>{const e=document.querySelector('button[aria-label=\"Select model family\"]');if(!e)return null;const t=e.cloneNode(true);t.querySelectorAll('i,svg,mat-icon').forEach(x=>x.remove());return t.textContent.trim().replace(/^🍌\\s*/, '');})()`);}
 async function chooseModel(name){await openSettings();await clickButton('Select model family');const ok=await c.eval(`(()=>{const e=[...document.querySelectorAll('[role=\"menuitem\"]')].filter(${visible}).find(e=>e.textContent.includes(${JSON.stringify(name)}));if(!e||e.getAttribute('aria-disabled')==='true')return false;e.click();return true;})()`);if(!ok)throw Error('Model unavailable');await pause(350);await openSettings();if(!(await currentModel())?.includes(name))throw Error('Model selection unverified');}
 try{
  await c.call('Page.bringToFront');await openSettings();
  original=await c.eval(`(()=>{const e=[...document.querySelectorAll('[role="radio"]')].filter(${visible}).find(e=>e.getAttribute('aria-checked')==='true'&&/(Image|Video)$/.test(e.innerText.trim()));return e?.innerText.trim().endsWith('Video')?'Video':e?'Image':null;})()`);
  if(!original)throw Error('Current mode unavailable');
  for(const kind of ['Image','Video']){
   await mode(kind);originalModels[kind]=await currentModel();await clickButton('Select model family');
   const labels=await c.eval(`(()=>[...document.querySelectorAll('[role="menuitem"]')].filter(${visible}).map(e=>{const clone=e.cloneNode(true);clone.querySelectorAll('i,svg,mat-icon,[class*="material-symbol"]').forEach(x=>x.remove());return clone.textContent.replace(/\\s+/g,' ').trim().replace(/^volume_up/,'').replace(/^🍌\\s*/, '');}))()`);
   if(!labels.length)throw Error('Model menu empty');out[kind.toLowerCase()]=[...new Set(labels)];await escape();
   if(kind==='Video'){for(const name of out.video){await chooseModel(name);out.video_settings[name]=await c.eval(`(()=>{const ts=[...document.querySelectorAll('[role=\"radio\"]')].filter(${visible}).map(e=>{const t=e.cloneNode(true);t.querySelectorAll('i,svg,mat-icon').forEach(x=>x.remove());return t.textContent.trim();});const trigger=document.querySelector('button[aria-label=\"Settings trigger\"]')?.innerText||'';const durations=ts.filter(t=>/^\\d+s$/.test(t)).map(t=>Number(t.slice(0,-1)));const resolutions=ts.filter(t=>/^(360|720)p$/.test(t));return {durations:durations.length?durations:[...trigger.matchAll(/\\b(\\d+)s\\b/g)].map(m=>Number(m[1])),resolutions:resolutions.length?resolutions:[...trigger.matchAll(/\\b(360|720)p\\b/g)].map(m=>m[1]+'p')};})()`);}if(originalModels[kind])await chooseModel(originalModels[kind]);await escape();}
  }
 }finally{try{await escape();if(original)await mode(original);await escape();}finally{c.close();}}
 return out;
}
if(process.argv[1]?.endsWith('/models.mjs')){try{console.log(JSON.stringify(await discover(Number(process.argv[2]))));}catch(e){console.log(JSON.stringify({error:e.message}));process.exitCode=1;}}
