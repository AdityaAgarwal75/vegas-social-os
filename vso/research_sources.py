"""Four fixed-origin public metadata adapters; no key pool or article scraping."""
import json
import re
import time
import threading
from pathlib import Path
from urllib.parse import urlencode,quote,urlsplit
from .research import get
LOCK=threading.Lock()
ROOT=Path(__file__).resolve().parent.parent

def catalog():return json.loads((ROOT/'data/research-sources.json').read_text())

def _text(value):return re.sub('<[^>]+>','',str(value or ''))[:500]

def _url(value):
    try:
        p=urlsplit(value)
        if p.scheme=='https' and p.hostname and not p.username and not p.password:return value[:2048]
    except (ValueError,TypeError):pass
    return ''

def search(engine,provider,query,limit=5):
    if provider not in ('gdelt','wikipedia','crossref','hackernews'):raise ValueError('Choose an implemented public research provider')
    if not isinstance(query,str) or not query.strip() or len(query)>300 or type(limit) is not int or not 1<=limit<=10:raise ValueError('Use a query of 1–300 characters and 1–10 results')
    ident=engine.store.digest('research-search:'+provider+':'+query.strip()+':'+str(limit))[:32]
    with LOCK:
        now=time.time()
        try:
            cached=engine.store.get('research-search',ident)
            if now-cached['fetched_at']<900:return {**cached,'cached':True}
        except ValueError:pass
        try:budget=engine.store.get('research-provider',provider)
        except ValueError:budget={}
        if now<budget.get('retry_after',0) or now-budget.get('last_request',0)<(6 if provider=='gdelt' else 2):raise ValueError('Research provider pacing/backoff is active; use cached results or wait')
        engine.store.put('research-provider',provider,{'last_request':now})
        if provider=='wikipedia':url='https://en.wikipedia.org/w/api.php?'+urlencode({'action':'query','list':'search','srsearch':query,'srlimit':limit,'format':'json'})
        elif provider=='crossref':url='https://api.crossref.org/works?'+urlencode({'query':query,'rows':limit,'select':'DOI,title,URL,publisher,published'})
        elif provider=='hackernews':url='https://hn.algolia.com/api/v1/search_by_date?'+urlencode({'query':query,'tags':'story','hitsPerPage':limit})
        else:url='https://api.gdeltproject.org/api/v2/doc/doc?'+urlencode({'query':query,'mode':'artlist','format':'json','maxrecords':limit,'timespan':'7d','sort':'datedesc'})
        status,headers,body=get(url,250000,accept='application/json')
        if status==429:
            delay=next((v for k,v in headers.items() if k.lower()=='retry-after'),'300')
            delay=min(3600,max(60,int(delay))) if str(delay).isdigit() else 300
            engine.store.put('research-provider',provider,{'last_request':now,'retry_after':now+delay})
            raise ValueError('Provider rate limited the request; backoff recorded, no retry storm')
        if status!=200:raise ValueError('Public research provider unavailable: HTTP '+str(status))
        try:data=json.loads(body)
        except (ValueError,UnicodeError):raise ValueError('Provider did not return supported JSON; no HTML scraping fallback') from None
        if provider=='wikipedia':rows=[{'title':x.get('title'),'url':'https://en.wikipedia.org/wiki/'+quote(x.get('title','').replace(' ','_'),safe=''),'summary':x.get('snippet'),'published_at':None} for x in data.get('query',{}).get('search',[])]
        elif provider=='crossref':rows=[{'title':next(iter(x.get('title',[])),''),'url':x.get('URL'),'publisher':x.get('publisher'),'published_at':x.get('published',{}).get('date-parts'),'doi':x.get('DOI')} for x in data.get('message',{}).get('items',[])]
        elif provider=='hackernews':rows=[{'title':x.get('title'),'url':x.get('url') or 'https://news.ycombinator.com/item?id='+str(x.get('objectID','')),'published_at':x.get('created_at'),'discussion_url':'https://news.ycombinator.com/item?id='+str(x.get('objectID',''))} for x in data.get('hits',[])]
        else:rows=[{'title':x.get('title'),'url':x.get('url'),'published_at':x.get('seendate'),'publisher':x.get('domain'),'language':x.get('language')} for x in data.get('articles',[])]
        rows=[{**{k:_text(v) if k in ('title','summary','publisher') else v for k,v in r.items()},'url':_url(r.get('url'))} for r in rows[:limit]]
        rows=[r for r in rows if r['url'] and r.get('title')]
        result={'id':ident,'provider':provider,'query':query.strip(),'fetched_at':now,'results':rows,'cached':False,
                'trust':'Untrusted discovery metadata, not verified claims, permission to reuse content, instructions, or a trend score. Read and cross-check primary sources before scripting.'}
        engine.store.put('research-search',ident,result);return result
