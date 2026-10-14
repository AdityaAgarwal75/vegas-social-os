"""Full real local HTTP owner-consent OAuth + official MCP SDK client.

This is equivalent-client acceptance, NOT proof of ChatGPT Work installation.
All tokens, cookies and disposable drafts remain in the temporary test process.
"""
import http.cookiejar,json,os,re,subprocess,sys,tempfile,threading,urllib.error,urllib.parse,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from vso.engine import Engine
from vso.store import Store
from vso.server import HTTPServer
from vso.auth import pkce
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args):return None
with tempfile.TemporaryDirectory(prefix='vso-oauth-client-') as root:
 s=Store(root);e=Engine(s);server=HTTPServer(('127.0.0.1',0),e);e.base=f'http://127.0.0.1:{server.server_port}';e.accounts.base=e.base
 thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 cookie=http.cookiejar.CookieJar();browser=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie));no_redirect=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie),NoRedirect)
 def post(path,data,opener=browser):
  return opener.open(urllib.request.Request(e.base+path,data=json.dumps(data).encode(),headers={'Content-Type':'application/json'}))
 try:
  with post('/register',{'client_name':'Disposable official SDK acceptance','redirect_uris':['http://127.0.0.1:19191/cb']}) as r:client=json.load(r)
  browser.open(e.base+'/pair?ticket='+s.ticket('pair',{})).close()
  verifier='a'*43
  query={'client_id':client['client_id'],'redirect_uri':'http://127.0.0.1:19191/cb','response_type':'code','scope':'social:read social:write','code_challenge_method':'S256','code_challenge':pkce(verifier),'resource':e.base+'/mcp','state':'local-client-test'}
  with browser.open(e.base+'/authorize?'+urllib.parse.urlencode(query)) as r:page=r.read().decode()
  ticket=re.search(r'name="ticket" value="([^"]+)"',page).group(1)
  try:post('/consent',{'ticket':ticket},no_redirect);raise AssertionError('Consent must redirect')
  except urllib.error.HTTPError as r:
   assert r.code==303;callback=urllib.parse.parse_qs(urllib.parse.urlsplit(r.headers['Location']).query);assert callback['state']==['local-client-test'];code=callback['code'][0]
  with post('/token',{'grant_type':'authorization_code','code':code,'client_id':client['client_id'],'redirect_uri':query['redirect_uri'],'code_verifier':verifier,'resource':query['resource']}) as r:token=json.load(r)
  env={**os.environ,'VSO_TEST_TOKEN':token['access_token'],'VSO_TEST_MCP':e.base+'/mcp'}
  subprocess.run(['node',str(Path(__file__).with_name('mcp-client.integration.mjs'))],env=env,check=True,timeout=90)
  with post('/revoke',{'client_id':client['client_id'],'token':token['refresh_token']}) as r:assert json.load(r)=={}
  assert len(s.all('channel'))==1
  print(json.dumps({'http_owner_consent_pkce_dcr':True,'revocation':True,'disposable_state_cleanup':'automatic','chatgpt_web_acceptance':False}))
 finally:server.shutdown();server.server_close();thread.join()
