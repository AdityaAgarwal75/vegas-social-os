// Original, explicit Flow settings control. Never clicks Generate.
const pause=ms=>new Promise(r=>setTimeout(r,ms));
const visible=`e=>!!(e.offsetWidth||e.offsetHeight||e.getClientRects().length)`;
export async function applyVideoSettings(c,options,frames=true){
 const specs={'Omni 1.1 Flash':[[4,6,8,10],['360p','720p']],'Veo 3.1 - Lite':[[4,6,8],['720p']],'Veo 3.1 - Fast':[[4,6,8],['720p']],'Veo 3.1 - Quality':[[4,6,8],['720p']]};
 const spec=specs[options.model];
 if(!spec||!spec[0].includes(options.duration)||!spec[1].includes(options.resolution)||!['9:16','16:9'].includes(options.aspect_ratio))throw Error('Unsupported explicit video settings');
 async function button(label){const ok=await c.eval(`(()=>{const e=[...document.querySelectorAll('button')].filter(${visible}).find(e=>e.getAttribute('aria-label')===${JSON.stringify(label)});if(!e||e.disabled)return false;e.click();return true;})()`);if(!ok)throw Error('Settings button unavailable: '+label);await pause(300);}
 async function open(){if(!await c.eval(`[...document.querySelectorAll('[role="radio"]')].filter(${visible}).some(e=>e.innerText.trim().endsWith('Video'))`))await button('Settings trigger');}
 async function radio(label){await open();const ok=await c.eval(`(()=>{const es=[...document.querySelectorAll('[role="radio"]')].filter(${visible});const e=es.find(e=>{const t=e.cloneNode(true);t.querySelectorAll('i,svg,mat-icon').forEach(x=>x.remove());return t.textContent.trim()===${JSON.stringify(label)};});if(!e||e.getAttribute('aria-disabled')==='true')return false;if(e.getAttribute('aria-checked')!=='true')e.click();return true;})()`);if(!ok){const trigger=await c.eval(`document.querySelector('button[aria-label=\"Settings trigger\"]')?.innerText||''`);if(!/^\d+s$/.test(label)||!new RegExp('\\b'+label+'\\b').test(trigger))throw Error('Requested setting unavailable: '+label);}await pause(250);}
 await c.call('Page.bringToFront');await open();await radio('Video');await radio(frames?'Frames':'Ingredients');
 await button('Select model family');const selected=await c.eval(`(()=>{const e=[...document.querySelectorAll('[role="menuitem"]')].filter(${visible}).find(e=>{const t=e.cloneNode(true);t.querySelectorAll('i,svg,mat-icon').forEach(x=>x.remove());return t.textContent.trim()===${JSON.stringify(options.model)};});if(!e||e.getAttribute('aria-disabled')==='true')return false;e.click();return true;})()`);
 if(!selected)throw Error('Requested model unavailable');await pause(400);await open();
 const model=await c.eval(`document.querySelector('button[aria-label="Select model family"]')?.innerText`);if(!model?.includes(options.model))throw Error('Selected model could not be verified');
 await radio(options.aspect_ratio);if(options.model.startsWith('Omni'))await radio(options.resolution);await radio(options.duration+'s');await radio('x1');
 const trigger=await c.eval(`document.querySelector('button[aria-label="Settings trigger"]')?.innerText`);
 for(const type of ['keyDown','keyUp'])await c.call('Input.dispatchKeyEvent',{type,key:'Escape',code:'Escape',windowsVirtualKeyCode:27});
 return {model:options.model,duration:options.duration,resolution:options.resolution,aspect_ratio:options.aspect_ratio,trigger};
}
