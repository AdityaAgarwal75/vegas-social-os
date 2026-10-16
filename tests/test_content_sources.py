import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from vso.engine import Engine
from vso.store import Store
from vso import content_sources,research_sources,templates

class ContentSourcesTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.e=Engine(Store(self.tmp.name))
 def tearDown(self):self.tmp.cleanup()
 def test_pinned_reference_integrity_and_no_execution(self):
  manifest=json.loads((content_sources.ROOT/'data/content-sources.json').read_text())
  for source in manifest['sources']:
   self.assertEqual(len(source['commit']),40)
   self.assertIn('MIT',(content_sources.ROOT/source['root']/'LICENSE').read_text())
   for name,sha in source['files'].items():self.assertEqual(hashlib.sha256((content_sources.ROOT/source['root']/name).read_bytes()).hexdigest(),sha)
  self.assertEqual(len(content_sources.hooks()['families']),26)
  self.assertIn('adapter_rules',templates.reference('instagram/ig-reel','SKILL.md'))
  for skill,doc in [('instagram/../ig-reel','SKILL.md'),('instagram/ig-reel','../../vso/server.py'),('marketing/social','../LICENSE')]:
   with self.assertRaises(ValueError):content_sources.reference(skill,doc)
 def test_multi_shot_prompts_preserve_edits_and_clip_boundaries(self):
  result=templates.compile_prompt('ugc-unboxing','The supplied blue box')
  self.assertEqual(len(result['scenes']),3)
  edited=[s['video_prompt']+'\nExact owner adjustment '+str(i) for i,s in enumerate(result['shots'])]
  saved=templates.compile_prompt('ugc-unboxing','The supplied blue box',{'video_prompts':edited})
  self.assertEqual([s['video_prompt'] for s in saved['scenes']],edited)
  with self.assertRaises(ValueError):templates.compile_prompt('ugc-unboxing','box',{'video_prompts':['only one']})
 def test_public_search_cache_origin_and_untrusted_metadata(self):
  data={'query':{'search':[{'title':'Black hole','snippet':'<b>Read</b> primary evidence'}]}}
  with patch('vso.research_sources.get',return_value=(200,{},json.dumps(data).encode())) as get:
   first=research_sources.search(self.e,'wikipedia','black hole')
   self.assertTrue(get.call_args.args[0].startswith('https://en.wikipedia.org/w/api.php?'))
   self.assertEqual(first['results'][0]['summary'],'Read primary evidence')
   self.assertIn('Untrusted',first['trust'])
   self.assertTrue(research_sources.search(self.e,'wikipedia','black hole')['cached']);self.assertEqual(get.call_count,1)
  with self.assertRaises(ValueError):research_sources.search(self.e,'https://localhost','x')
 def test_public_search_backoff_and_no_credential_urls(self):
  with patch('vso.research_sources.get',return_value=(429,{'Retry-After':'600'},b'')) as get:
   with self.assertRaises(ValueError):research_sources.search(self.e,'crossref','first')
   with self.assertRaises(ValueError):research_sources.search(self.e,'crossref','second')
   self.assertEqual(get.call_count,1)
  self.assertEqual(research_sources._url('https://user:secret@example.com/'),'')
  self.assertEqual(research_sources._url('http://example.com/'),'')
