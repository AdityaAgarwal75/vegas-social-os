"""Dependency-free owner onboarding screens. No credentials or private state."""
import html


def login(next_url='/dashboard', error=None):
    warning = '<div class="form-error" role="alert">' + html.escape(error) + '</div>' if error else ''
    return ("<p class=\"auth-intro\">Sign in to your own installation. Your accounts, projects and media stay on your server.</p>" + warning +
        '<form action="/login" method="post" class="auth-form">'
        '<label for="owner-password">Owner password</label><div class="password-field">'
        '<input id="owner-password" name="password" type="password" required minlength="14" maxlength="256" autocomplete="current-password" aria-describedby="password-hint">'
        '<button type="button" class="password-toggle" data-password="owner-password" aria-label="Show owner password" aria-pressed="false">Show</button></div>'
        '<p id="password-hint" class="field-hint">Use the password you chose for this installation.</p>'
        '<input type="hidden" name="next" value="' + html.escape(next_url, quote=True) + '">'
        '<button type="submit" class="primary auth-submit" data-pending="Signing in…">Sign in <span aria-hidden="true">→</span></button>'
        '<a class="forgot-link" href="/forgot-password">Forgot your password?</a></form>'
        '<div class="auth-note"><b>Connecting ChatGPT?</b><p>Sign-in opens your workspace. You will review and approve the plugin’s permissions separately.</p></div>'
        '<p class="auth-bottom">First time here? <a href="/help">Read the setup guide</a></p>')


def forgot():
    return '''<p class="auth-intro">Get a private recovery link from the administrator or ChatGPT agent that manages your server.</p>
<ol class="guide-steps"><li><b>Ask your connected agent</b><p>“Generate a new Vegas Studio password recovery link on my own installation. Keep it private.”</p></li>
<li><b>Open the fresh link once</b><p>It expires in 10 minutes and opens the new-password form directly. Use the same browser throughout.</p></li>
<li><b>Choose a new password</b><p>Use 14–256 characters. Sign in again after saving. Your accounts, projects and media stay in place.</p></li></ol>
<details class="operator-details"><summary>For server administrators</summary><p>Run through your existing authorized server connection:</p><code>sudo bash /opt/vegas-social-os/scripts/new-setup-link.sh --reset-password</code><p>Return the link privately to the owner. Do not open it on their behalf or post it in a public issue.</p></details>
<div class="auth-note"><b>No reset email?</b><p>This self-hosted installation does not require an email service. Recovery uses verified administrator access to your server.</p></div>
<a class="primary auth-submit" href="/login">Back to sign in <span aria-hidden="true">→</span></a>'''


def guide(base):
    endpoint = html.escape(base + '/mcp')
    return '''<p class="auth-intro">One owner. One server. Your production workspace inside ChatGPT.</p>
<ol class="guide-steps"><li><b>Install on your own server</b><p>Give the repository to a ChatGPT Work agent with authorized VPS or AWS access. It checks requirements, installs the system and verifies HTTPS. Each user needs an independent installation.</p></li>
<li><b>Open your private setup link</b><p>Your agent provides a one-use link after setup. Open it within 10 minutes. Never bookmark or share it.</p></li>
<li><b>Set your owner password</b><p>In the paired browser, open <a href="/password">Set owner password</a>. Choose 14–256 characters, then sign in. Bookmark the permanent login page.</p></li>
<li><b>Connect ChatGPT</b><p>Add this installation’s remote MCP endpoint through a supported custom-plugin workflow:</p><code>''' + endpoint + '''</code><p>Sign in and click Authorize once. Return to ChatGPT and ask it to run guide, doctor and account_list. A healthy server alone does not prove the plugin is connected.</p></li>
<li><b>Connect your own accounts</b><p>Open Connections. Sign into each Google profile in the private VPS browser and open Flow, then verify access. Official YouTube, Instagram and Facebook publishing require separate app configuration and consent.</p></li>
<li><b>Make one reviewed production</b><p>Ask ChatGPT for two ideas. Choose a concept, review the actual storyboard images, approve a credit limit, watch the clips and approve the exact publishing destination.</p></li></ol>
<div class="auth-note"><b>Know the current limits</b><p>Provider eligibility and credits vary. Scheduled briefs do not prove unattended ChatGPT generation. Complete a real capped production and posting trial before relying on automation.</p></div>
<div class="help-links"><a href="/login">Sign in →</a><a href="/forgot-password">Password recovery →</a><a href="https://github.com/AdityaAgarwal75/vegas-social-os" target="_blank" rel="noopener noreferrer">Source & installation docs ↗</a></div>'''


def shell(title, body, status=200):
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="theme-color" content="#f4f7fe"><meta name="robots" content="noindex,nofollow"><link rel="icon" href="/logo.svg" type="image/svg+xml"><script src="/theme.js"></script><link rel="stylesheet" href="/control.css"><link rel="stylesheet" href="/horizon.css"><link rel="stylesheet" href="/auth.css"><script defer src="/auth.js"></script><title>''' + html.escape(title) + ''' · Vegas Studio</title></head><body class="owner-page"><a class="skip-link" href="#owner-content">Skip to content</a><header class="owner-header"><a href="/login" class="owner-brand" aria-label="Vegas Studio sign in"><img src="/logo.svg" alt="" width="36" height="36"><span>VEGAS <strong>STUDIO</strong></span></a><div class="owner-header-actions"><a href="/help" class="help-link">Setup guide ↗</a><button class="icon-button" type="button" data-theme-toggle aria-label="Switch theme">◐</button></div></header><div class="owner-layout"><main id="owner-content" class="owner-card" tabindex="-1"><p class="eyebrow">YOUR PRIVATE WORKSPACE</p><h1>''' + html.escape(title) + '''</h1>''' + ('<p class="error-caption" role="status">Action needed · '+str(status)+'</p>' if status>=400 else '') + body + '''</main><aside class="owner-story" aria-label="About your workspace"><div class="auth-brand-display"><img src="/logo.svg" alt="" width="96" height="96"><p>VEGAS <strong>STUDIO</strong></p></div><h2>Ideas in chat.<br>Production under control.</h2><p class="story-copy">A private home for your accounts, storyboards and the work you approve.</p><div class="story-pipeline"><div><span>01</span><b>Plan in ChatGPT</b><small>Research · concepts · direction</small></div><div><span>02</span><b>Review the work</b><small>Storyboards · clips · revisions</small></div><div><span>03</span><b>Publish with intent</b><small>Your accounts · your approval</small></div></div><p class="story-foot">Independently hosted. Open source.</p></aside></div><footer class="owner-footer"><span>Vegas Studio · Your installation, your data.</span><nav aria-label="Legal and help"><a href="/help">Help</a><a href="/privacy">Privacy</a><a href="/data-deletion">Data deletion</a></nav></footer></body></html>'''
