import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vso.engine import Engine
from vso.store import Store
from vso.tools import call, definitions
from vso import auth, templates, higgsfield


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.engine=Engine(Store(self.temp.name))
        self.project=call(self.engine,'project_create',{'name':'Bangle reveal','request_id':'test-project'})

    def tearDown(self):self.temp.cleanup()

    def test_catalog_preview_and_upstream_integrity(self):
        result=call(self.engine,'template_catalog',{})
        self.assertEqual(len(result['templates']),35)
        self.assertEqual(len({c['id'] for c in result['templates']}),35)
        self.assertEqual(len(call(self.engine,'template_catalog',{'category':'Product'})['templates']),4)
        self.assertEqual(len(call(self.engine,'template_catalog',{'query':'bullet'})['templates']),1)
        for card in result['templates']:
            self.assertIsNone(card['preview_url'])
            self.assertTrue(card['reference_requirements'])
            self.assertGreater(len(card['video_prompt']),300)
            self.assertTrue(card['shots'])
        self.assertEqual(sum(len(c['shots']) for c in result['templates']),65)
        source=templates.ROOT/'third_party/higgsfield-skills'
        manifest=json.loads((source/'PROVENANCE.json').read_text())
        for name,checksum in manifest['files'].items():
            self.assertEqual(hashlib.sha256((source/name).read_bytes()).hexdigest(),checksum,name)
        self.assertIn('Higgsfield AI',(source/'LICENSE').read_text())

    def test_selection_is_immutable_idempotent_and_spends_nothing(self):
        args={'project_id':self.project['id'],'template_id':'product-hero','subject':'Exactly two supplied bangles',
              'request_id':'same','settings':{'lens':'100mm macro'},'continuity':'Preserve plain–stones pattern and exact count of two.'}
        a=call(self.engine,'template_select',args)
        self.assertEqual(a,call(self.engine,'template_select',args))
        self.assertIn('exact count of two',a['video_prompt'])
        self.assertEqual(a['settings']['lens'],'100mm macro')
        self.assertFalse(a['spend_authorized'])
        with self.assertRaises(ValueError):call(self.engine,'template_select',{**args,'subject':'Different object'})
        self.assertEqual(self.engine.store.all('job'),[])
        self.assertEqual(self.engine.store.all('publication'),[])
        self.assertEqual(self.engine.store.all('plan'),[])
        with self.assertRaises(ValueError):call(self.engine,'template_select',{**args,'project_id':'unknown'})

    def test_compiled_scene_survives_existing_plan_contract(self):
        compiled=call(self.engine,'template_compile',{'template_id':'fashion-walk','subject':'A model wearing the exact supplied garment'})
        channel=self.engine.channel_save('Fashion','Fashion')
        concepts=[{'title':name,'hook':'Look at the embroidery','script':'Inspect the stitching.',
                   'scenes':[compiled['scene']]} for name in ['Walk','Detail']]
        result=call(self.engine,'plan_save',{'channel_id':channel['id'],'concepts':concepts,'request_id':'compiled','project_id':self.project['id']})
        self.assertEqual(result['concepts'][0]['scenes'][0]['continuity']['template_id'],'editorial-walk')
        for settings in ({'lens':'bad'},{'lighting':'invented'},{'motion':'explode'},{'aspect_ratio':'7:9'},{'command':'rm'}):
            with self.assertRaises(ValueError):templates.compile_prompt('product-hero','bottle',settings)
        with self.assertRaises(ValueError):templates.compile_prompt('missing','bottle')

    def test_exact_reference_lookup_and_tool_scopes(self):
        ref=call(self.engine,'skill_reference',{'document':'references/workflows.md'})
        self.assertIn('reframe',ref['text'])
        for skill,doc in [('..','LICENSE'),('higgsfield-generate','../../vso/server.py'),('higgsfield-generate','unknown.md')]:
            with self.assertRaises(ValueError):templates.reference(skill,doc)
        for name in ['template_catalog','template_compile','skill_reference','higgsfield_status','higgsfield_discover']:
            self.assertEqual(auth.tool_scope(name),'social:read')
        self.assertEqual(auth.tool_scope('template_select'),'social:write')
        names={t['name'] for t in definitions(self.engine)}
        self.assertTrue({'template_catalog','template_compile','template_select','skill_reference','higgsfield_status','higgsfield_discover'}<=names)

    def test_optional_provider_fails_closed_and_redacts_metadata(self):
        with patch.dict(os.environ,{'VSO_HIGGSFIELD_ENABLED':'0'}):
            result=call(self.engine,'higgsfield_status',{})
            self.assertEqual(result['authenticated'],'not_checked')
            with self.assertRaises(ValueError):call(self.engine,'higgsfield_discover',{})
        with patch('vso.higgsfield._run',return_value={'data':[{'id':'soul','access_token':'private','thumbnail':'https://example.com/?token=secret'}]}) as run:
            result=higgsfield.discover(self.engine,'presets','soul-v2')
            self.assertNotIn('access_token',result['data']['data'][0])
            self.assertNotIn('secret',json.dumps(result))
            self.assertEqual(run.call_args.args[1],['preset','list','soul-v2'])
        with patch('vso.higgsfield._run') as run:
            for kind,name in [('generate','create'),('models','bad; shell'),('presets','unknown')]:
                with self.assertRaises(ValueError):higgsfield.discover(self.engine,kind,name)
            run.assert_not_called()

    def test_real_cli_wrapper_is_read_only_and_uses_private_home(self):
        binary=Path(self.temp.name)/'fake-higgsfield'
        binary.write_text('#!/usr/bin/env python3\nimport json,os,sys\nprint(json.dumps({"argv":sys.argv[1:],"home":os.environ["HOME"]}))\n')
        binary.chmod(0o700)
        with patch.dict(os.environ,{'VSO_HIGGSFIELD_ENABLED':'1','VSO_HIGGSFIELD_BIN':str(binary)}):
            value=higgsfield.discover(self.engine,'workflows')
            self.assertEqual(value['data']['argv'],['workflow','list','--json'])
            self.assertEqual(value['data']['home'],str(self.engine.store.root/'higgsfield'))
        self.assertEqual(self.engine.store.all('job'),[])


if __name__=='__main__':unittest.main()
