// Exercise the complete engine's real settings function. No Generate click.
// Operator must serialize with all other account/browser jobs.
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
const root=process.env.VSO_FLOW_ENGINE_ROOT;
if(!root||process.env.VSO_FLOW_ATTACH_ONLY!=='1')throw Error('Managed attach-only engine required');
const {getFlowPage,getFlowState}=await import(pathToFileURL(resolve(root,'dist/flow.js'))).then(async f=>({...f,...await import(pathToFileURL(resolve(root,'dist/chrome.js')))}));
const {applySettings}=await import(pathToFileURL(resolve(root,'dist/flow.js')));
const input=JSON.parse(process.argv[2]);
const state=await getFlowState(false);
if(!state.signedIn||!state.inProject)throw Error('Signed-in project required');
const page=await getFlowPage();
const out=[];
const trigger=page.getByRole('button',{name:'Settings trigger'});
await trigger.click();
const original=await page.evaluate(()=>{
 const visible=e=>!!(e.offsetWidth||e.offsetHeight||e.getClientRects().length);
 const text=e=>{const c=e.cloneNode(true);c.querySelectorAll('i,svg,mat-icon').forEach(x=>x.remove());return c.textContent.trim().replace(/^🍌\s*/,'');};
 const checked=[...document.querySelectorAll('[role="radio"]')].filter(e=>visible(e)&&e.getAttribute('aria-checked')==='true').map(text);
 const model=text(document.querySelector('button[aria-label="Select model family"]'));
 const t=document.querySelector('button[aria-label="Settings trigger"]').innerText;
 return {type:checked.includes('Video')?'video':'image',model,aspect_ratio:checked.find(t=>/^(9:16|16:9|1:1|4:3|3:4)$/.test(t)),
  duration:Number((checked.find(t=>/^\d+s$/.test(t))||t.match(/\b\d+s\b/)?.[0]||'8s').slice(0,-1)),
  resolution:checked.find(t=>/^(360|720)p$/.test(t)),variants:Number((checked.find(t=>/^x\d$/.test(t))||'x1').slice(1)),
  reference_images:checked.includes('Ingredients')?['asset:probe-mode-only']:[]};
});
await page.keyboard.press('Escape');
try{for(const options of input){
 try{
  const quote=await applySettings(page,{params:{type:'video',variants:1,...options}});
  out.push({options,quote,status:'controls_applied',trigger:await page.getByRole('button',{name:'Settings trigger'}).innerText()});
 }catch(e){await page.keyboard.press('Escape');out.push({options,status:'unsupported_or_failed',error:e.message});}
}}finally{
 if(original.type==='image'){delete original.duration;delete original.resolution;}
 if(!original.model.startsWith('Omni'))delete original.resolution;
 await applySettings(page,{params:original});
 await page.keyboard.press('Escape');
}
console.log(JSON.stringify({rendered:false,spent:0,restored:true,results:out}));
process.exit(0);
