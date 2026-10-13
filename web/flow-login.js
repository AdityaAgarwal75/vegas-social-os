import RFB from '/novnc/core/rfb.js';
const status=document.querySelector('#browser-status');
const info=await fetch('/flow/session').then(async r=>{const x=await r.json();if(!r.ok)throw Error(x.error);return x;});
if(info.existing_service){document.querySelector('h1').textContent=info.label+' · Google browser';document.querySelector('.muted').textContent=info.shared_desktop?'Your existing private workstation is shown here. These accounts share its display; the selected browser is focused.':'Your existing account browser is shown here. No session has been copied.';}
const url=new URL('/flow/socket/'+info.account_id,location.href);url.protocol=location.protocol==='https:'?'wss:':'ws:';
const rfb=new RFB(document.querySelector('#browser-screen'),url.href,{shared:true});
rfb.scaleViewport=true;rfb.resizeSession=false;
rfb.addEventListener('connect',()=>status.textContent=info.existing_service?'Existing account browser connected.':'Browser connected. Sign in directly with Google.');
rfb.addEventListener('disconnect',()=>status.textContent='Browser connection ended. Request a fresh account-login link.');
document.querySelector('#verify-flow').onclick=async()=>{try{const r=await fetch('/flow/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({})});const x=await r.json();if(!r.ok)throw Error(x.error);status.textContent=x.workspace_ready?'Flow workspace verified. You can return to ChatGPT.':'Sign-in/project setup is incomplete. Open one Flow project, then verify again.';}catch(e){status.textContent=e.message;}};
