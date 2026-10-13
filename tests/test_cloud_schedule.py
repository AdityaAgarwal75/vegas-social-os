import tempfile
import unittest
from unittest.mock import patch

from vso.store import Store
from vso.engine import Engine
from vso.cloud import sync
from vso.schedule import save, tick


class CloudScheduleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.e = Engine(Store(self.tmp.name))
    def tearDown(self): self.tmp.cleanup()

    def test_daily_queue_is_idempotent(self):
        channel = self.e.channel_save('Community channel', 'A defined audience')
        save(self.e, 0, 'UTC', [channel['id']])
        self.assertEqual(tick(self.e), tick(self.e))
        self.assertEqual(tick(self.e)[0]['status'], 'awaiting_chatgpt')

    def test_schedule_rejects_invalid_hour_and_timezone(self):
        with self.assertRaises(ValueError): save(self.e, 24, 'UTC', [])
        with self.assertRaises(ValueError): save(self.e, 5, 'invented-timezone', [])

    def test_cloud_sync_uses_verified_user_and_omits_credentials(self):
        self.e.store.secret('private-account', {'access_token':'secret-example'})
        env = {'SUPABASE_URL':'https://exampleproject.supabase.co', 'SUPABASE_PUBLISHABLE_KEY':'test-publishable', 'SUPABASE_USER_JWT':'test-user-jwt'}
        responses = [({'id':'00000000-0000-0000-0000-000000000001'}, {}), ({}, {})]
        with patch.dict('os.environ', env), patch('vso.cloud.net.request', side_effect=responses) as request:
            result = sync(self.e)
            self.assertEqual(result['status'], 'backed_up')
            sent = request.call_args.kwargs['payload']
            self.assertEqual(sent['owner_id'], responses[0][0]['id'])
            self.assertNotIn('secret-example', str(sent))

    def test_cloud_rejects_arbitrary_host(self):
        with patch.dict('os.environ', {'SUPABASE_URL':'https://attacker.example'}):
            with self.assertRaises(ValueError): sync(self.e)


if __name__ == '__main__': unittest.main()
