import base64
import concurrent.futures
import json
import tempfile
import unittest
from unittest.mock import patch

from vso.engine import Engine
from vso.store import Store
from vso import tools

PNG = b'\x89PNG\r\n\x1a\n' + b'test image bytes'
MP4 = b'\x00\x00\x00\x18ftypisom' + b'test video bytes'


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)
        self.e = Engine(self.store)
        runtime = patch('vso.flow_runtime.installed', return_value=True)
        runtime.start(); self.addCleanup(runtime.stop)
        self.flow_id = 'a' * 32
        self.store.put('account', self.flow_id, {'id': self.flow_id, 'provider': 'flow', 'status': 'workspace_ready'})
        self.store.put('account', 'youtube', {'id': 'youtube', 'provider': 'youtube', 'status': 'connected'})
        self.channel = self.e.channel_save('Test channel', 'Specific niche', account_ids=['youtube'])
        self.concepts = [{'title': 'A', 'hook': 'Immediate action', 'script': 'Short script',
                          'scenes': [{'image_prompt': 'Exact keyframe', 'video_prompt': 'One movement'}]},
                         {'title': 'B', 'hook': 'Different payoff', 'script': 'Other script',
                          'scenes': [{'image_prompt': 'Different keyframe', 'video_prompt': 'One action'}]}]

    def tearDown(self): self.tmp.cleanup()

    def ready(self, cap=40):
        p = self.e.plan_save(self.channel['id'], self.concepts, 'morning-1')
        self.e.concept_select(p['id'], 0, cap)
        a = self.e.asset_import(base64.b64encode(PNG).decode(), 'image/png')
        self.e.image_attach(p['id'], 0, a['id'])
        return self.e.images_approve(p['id'])

    def final(self):
        p = self.ready()
        a = self.e.asset_import(base64.b64encode(MP4).decode(), 'video/mp4')
        self.e.video_attach(p['id'], a['id'])
        return self.e.publish_prepare(p['id'], 'youtube', 'Title', 'Caption', options={'made_for_kids':False})

    def test_reusable_request_has_same_plan(self):
        a = self.e.plan_save(self.channel['id'], self.concepts, 'same')
        b = self.e.plan_save(self.channel['id'], self.concepts, 'same')
        self.assertEqual(a['id'], b['id'])
        changed = json.loads(json.dumps(self.concepts)); changed[0]['title'] = 'Changed'
        with self.assertRaises(ValueError): self.e.plan_save(self.channel['id'], changed, 'same')

    def test_requires_two_concepts(self):
        with self.assertRaises(ValueError): self.e.plan_save(self.channel['id'], self.concepts[:1], 'bad')

    def test_image_tasks_are_not_generation(self):
        p = self.e.plan_save(self.channel['id'], self.concepts, 'same')
        with self.assertRaises(ValueError): self.e.image_tasks(p['id'])
        self.e.concept_select(p['id'], 1, 10)
        task = self.e.image_tasks(p['id'])
        self.assertEqual(task['provider'], 'chatgpt-native-only')
        self.assertIsNone(task['tasks'][0]['asset_id'])

    def test_requires_every_keyframe(self):
        p = self.e.plan_save(self.channel['id'], self.concepts, 'same')
        self.e.concept_select(p['id'], 0, 20)
        with self.assertRaises(ValueError): self.e.images_approve(p['id'])

    def test_media_signature_and_checksum(self):
        with self.assertRaises(ValueError): self.e.asset_import(base64.b64encode(b'not an image').decode(), 'image/png')
        a = self.e.asset_import(base64.b64encode(PNG).decode(), 'image/png')
        path = self.e.asset_path(a['id']); path.write_bytes(b'changed')
        with self.assertRaises(ValueError): self.e.asset_path(a['id'])

    def test_credit_cap_before_browser_call(self):
        p = self.ready(10)
        with patch.object(self.e, 'flow') as worker:
            with self.assertRaises(ValueError): self.e.video_request(p['id'], 0, self.flow_id, 20, 'expensive', options={'model':'Veo 3.1 - Fast','duration':8,'resolution':'720p','aspect_ratio':'9:16'})
            worker.assert_not_called()

    def test_same_job_does_not_submit_twice(self):
        p = self.ready()
        with patch.object(self.e, 'flow', return_value={'id': 'worker-1'}) as worker:
            a = self.e.video_request(p['id'], 0, self.flow_id, 20, 'job-key', options={'model':'Veo 3.1 - Fast','duration':8,'resolution':'720p','aspect_ratio':'9:16'})
            b = self.e.video_request(p['id'], 0, self.flow_id, 20, 'job-key', options={'model':'Veo 3.1 - Fast','duration':8,'resolution':'720p','aspect_ratio':'9:16'})
            self.assertEqual(a['id'], b['id']); self.assertEqual(worker.call_count, 1)

    def test_unknown_generation_not_retried(self):
        p = self.ready()
        with patch.object(self.e, 'flow', side_effect=ValueError('interrupted')) as worker:
            a = self.e.video_request(p['id'], 0, self.flow_id, 20, 'job-key', options={'model':'Veo 3.1 - Fast','duration':8,'resolution':'720p','aspect_ratio':'9:16'})
            self.assertEqual(a['status'], 'unknown')
            self.e.video_request(p['id'], 0, self.flow_id, 20, 'job-key', options={'model':'Veo 3.1 - Fast','duration':8,'resolution':'720p','aspect_ratio':'9:16'})
            with self.assertRaises(ValueError): self.e.video_request(p['id'], 0, self.flow_id, 20, 'new-key', options={'model':'Veo 3.1 - Fast','duration':8,'resolution':'720p','aspect_ratio':'9:16'})
            self.assertEqual(worker.call_count, 1)

    def test_concurrent_scene_submissions_are_serialized(self):
        p = self.ready()
        def submit(i):
            try: return self.e.video_request(p['id'], 0, self.flow_id, 20, f'job-{i}', options={'model':'Veo 3.1 - Fast','duration':8,'resolution':'720p','aspect_ratio':'9:16'})
            except ValueError: return None
        with patch.object(self.e, 'flow', return_value={'id': 'worker-1'}) as worker:
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(submit, [1, 2]))
            self.assertEqual(sum(x is not None for x in results), 1)
            self.assertEqual(worker.call_count, 1)

    def test_secret_not_in_snapshot_or_sqlite_plaintext(self):
        self.store.secret('youtube', {'access_token': 'sensitive-example-token'})
        self.assertNotIn('sensitive-example-token', json.dumps(self.e.snapshot()))
        with self.store.db() as db:
            encrypted = db.execute('SELECT value FROM secrets WHERE id=?', ('youtube',)).fetchone()[0]
        self.assertNotIn(b'sensitive-example-token', encrypted)
        self.assertEqual(self.store.secret('youtube')['access_token'], 'sensitive-example-token')

    def test_publish_requires_explicit_approval(self):
        p = self.final()
        with self.assertRaises(ValueError): self.e.publish_execute(p['id'])

    def test_publish_unknown_does_not_retry_upload(self):
        p = self.final(); self.e.publish_approve(p['id'])
        with patch.object(self.e.accounts, 'token', side_effect=ValueError('expired')) as token:
            a = self.e.publish_execute(p['id']); b = self.e.publish_execute(p['id'])
            self.assertEqual(a['status'], 'unknown'); self.assertEqual(b['status'], 'unknown')
            self.assertEqual(token.call_count, 1)

    def test_unrelated_destination_is_rejected(self):
        p = self.ready(); a = self.e.asset_import(base64.b64encode(MP4).decode(), 'video/mp4')
        self.e.video_attach(p['id'], a['id'])
        self.store.put('account', 'other', {'id': 'other', 'provider': 'youtube', 'status': 'connected'})
        with self.assertRaises(ValueError): self.e.publish_prepare(p['id'], 'other', 'Title', 'Caption')

    def test_tools_reject_extra_fields_and_wrong_types(self):
        with self.assertRaises(ValueError): tools.call(self.e, 'doctor', {'shell': 'anything'})
        with self.assertRaises(ValueError): tools.call(self.e, 'concept_select', {'plan_id': 'x', 'concept': True, 'max_credits': 1})

    def test_mcp_handshake_and_native_image_constraint(self):
        result = tools.rpc(self.e, {'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18'}})
        self.assertEqual(result['result']['protocolVersion'], '2025-06-18')
        names = {x['name'] for x in tools.definitions(self.e)}
        self.assertIn('image_tasks', names); self.assertNotIn('generate_image_api', names)
        self.assertIsNone(tools.rpc(self.e, {'method': 'notifications/initialized'}))


if __name__ == '__main__': unittest.main()
