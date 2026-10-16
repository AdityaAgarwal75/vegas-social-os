'use strict';
for(const button of document.querySelectorAll('[data-password]')){
 button.addEventListener('click',()=>{const input=document.getElementById(button.dataset.password);const show=input.type==='password';input.type=show?'text':'password';button.textContent=show?'Hide':'Show';button.setAttribute('aria-pressed',String(show));button.setAttribute('aria-label',(show?'Hide':'Show')+' owner password');});
}
for(const form of document.querySelectorAll('form')){
 form.addEventListener('submit',event=>{if(form.getAttribute('aria-busy')==='true'){event.preventDefault();return;}const password=form.querySelector('[name=password]'),confirmation=form.querySelector('[name=confirmation]');if(confirmation){confirmation.setCustomValidity(confirmation.value===password.value?'':'Enter the same password in both fields.');if(!confirmation.reportValidity()){event.preventDefault();return;}}form.setAttribute('aria-busy','true');const button=form.querySelector('[type=submit]');if(button){button.disabled=true;button.textContent=button.dataset.pending||'Saving…';}});
 for(const input of form.querySelectorAll('[name=password],[name=confirmation]'))input.addEventListener('input',()=>form.querySelector('[name=confirmation]')?.setCustomValidity(''));
}
window.addEventListener('pageshow',event=>{if(event.persisted)location.reload();});

for(const button of document.querySelectorAll('[data-theme-toggle]'))button.addEventListener('click',()=>{const value=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=value;try{localStorage.setItem('vso-theme',value);}catch{}});
