/* A consent ticket is consumed once; prevent accidental double-submit. */
(() => {
  const form = document.querySelector('form[action="/consent"]');
  if (!form) return;
  let sent = false;
  form.addEventListener('submit', event => {
    if (sent) { event.preventDefault(); return; }
    sent = true;
    const button = form.querySelector('button[type="submit"]');
    if (button) { button.disabled = true; button.textContent = 'Redirecting to ChatGPT…'; }
  });
  window.addEventListener('pageshow', event => {
    if (event.persisted) {
      sent = false;
      const button = form.querySelector('button[type="submit"]');
      if (button) { button.disabled = false; button.textContent = 'Authorize Vegas Social OS'; }
    }
  });
})();
