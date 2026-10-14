// Original read-only model-menu discovery. No generation, token or cookie access.
import {CDP} from './flow.mjs';
const pause=ms=>new Promise(r=>setTimeout(r,ms));
export async function discover(port){
 if(!Number.isInteger(port)||port<1024||port>65535)throw Error('Invalid private browser port');
 const tabs=await fetch(`http://127.0.0.1:${port}/json/list`,{signal:AbortSignal.timeout(3000)}).then(r=>r.json());
 const matching=tabs.filter(t=>t.type==='page'&&/^https:\/\/(flow\.google\.com|labs\.google)\/.*project\//.test(t.url));
 if(matching.length!==1)throw Error('Keep one Flow project tab');
 const c=await CDP.connect(matching[0].webSocketDebuggerUrl);
 const escape=()=>c.call('Input.dispatchKeyEvent',{type:'keyDown',key:'Escape',code:'Escape',windowsVirtualKeyCode:27}).then(()=>c.call('Input.dispatchKeyEvent',{type:'keyUp',key:'Escape',code:'Escape',windowsVirtualKeyCode:27}));
 async function click(role,label){let box=await c.eval(`(()=>{const es=[...document.querySelectorAll(${JSON.stringify(role==='button'?'button':'[role="'+role+'"]')})].filter(e=>e.getBoundingClientRect().width>0);const e=es.find(e=>(e.getAttribute('aria-label')||'')===${JSON.stringify(label)}||(e.innerText||'').replace(/\\s+/g,' ').trim()===${JSON.stringify(label)}||(e.getAttribute('data-value')||'')===${JSON.stringify(label)});if(!e)return null;const b=e.getBoundingClientRect();return {x:b.x+b.width/2,y:b.y+b.height/2};})()`);if(!box&&label==='Select model family'){await click('button','Settings trigger');await pause(400);box=await c.eval(`(()=>{const e=document.querySelector('button[aria-label="Select model family"]');if(!e||!e.getBoundingClientRect().width)return null;const b=e.getBoundingClientRect();return {x:b.x+b.width/2,y:b.y+b.height/2};})()`);}if(!box)throw Error('Model control unavailable: '+label);await c.call('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...box});await c.call('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...box});await pause(250);}
 let original='Image';const out={image:[],video:[]};
 try{
  await click('button','Settings trigger');original=await c.eval(`(()=>{const e=[...document.querySelectorAll('[role="radio"]')].find(e=>e.getAttribute('aria-checked')==='true'&&/Image|Video/.test(e.innerText));return e?.innerText.includes('Video')?'Video':'Image';})()`);
  for(const kind of ['Image','Video']){
   // Icons contribute text; use accessible label through aria or final text suffix.
   const radio=await c.eval(`(()=>{const e=[...document.querySelectorAll('[role="radio"]')].find(e=>e.getBoundingClientRect().width>0&&(e.innerText||'').endsWith(${JSON.stringify(kind)}));if(!e)return null;const b=e.getBoundingClientRect();return {x:b.x+b.width/2,y:b.y+b.height/2,checked:e.getAttribute('aria-checked')==='true'};})()`);if(!radio)throw Error('Mode unavailable');
   if(!radio.checked){await c.call('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,x:radio.x,y:radio.y});await c.call('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,x:radio.x,y:radio.y});}await pause(300);await click('button','Select model family');
   out[kind.toLowerCase()]=await c.eval(`(()=>[...document.querySelectorAll('[role="menuitem"]')].filter(e=>e.getBoundingClientRect().width>0).map(e=>{const clone=e.cloneNode(true);clone.querySelectorAll('i,svg,mat-icon,[class*="material-symbol"]').forEach(x=>x.remove());return clone.textContent.replace(/\\s+/g,' ').trim().replace(/^volume_up/,'').replace(/^🍌\\s*/, '');}))()`);await escape();await pause(100);
  }
 }finally{try{const pos=await c.eval(`(()=>{const e=[...document.querySelectorAll('[role="radio"]')].find(e=>(e.innerText||'').endsWith(${JSON.stringify(original)}));if(!e||!e.getBoundingClientRect().width)return null;const b=e.getBoundingClientRect();return {x:b.x+b.width/2,y:b.y+b.height/2};})()`);if(pos){await c.call('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...pos});await c.call('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...pos});}await escape();}finally{c.close();}}
 return out;
}
if(process.argv[1]?.endsWith('/models.mjs')){try{console.log(JSON.stringify(await discover(Number(process.argv[2]))));}catch(e){console.log(JSON.stringify({error:e.message}));process.exitCode=1;}}
