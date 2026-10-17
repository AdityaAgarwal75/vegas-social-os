"""Conservative account-day Flow credit admission, no provider I/O."""
import json
import os
import tempfile
import time
import unittest
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from vso.flow_controller import assert_daily_budget, daily_reserved
from vso.store import Store


class DailyFlowCreditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(self.temp.name)
        self.now = datetime(2026, 10, 17, 13, 0, tzinfo=ZoneInfo('Asia/Kolkata')).timestamp()

    def tearDown(self):
        self.temp.cleanup()

    def job(self, ident, account, ceiling, age=0, kind='video-job', status='processing'):
        self.store.put(kind, ident, {'account_id': account, 'created_at': self.now - age,
                                      'max_credits': ceiling, 'status': status})

    def test_jobs_across_kinds_share_one_account_daily_limit(self):
        self.job('one', 'a', 18, kind='image-job')
        self.job('two', 'a', 25, kind='video-job')
        self.job('other', 'b', 50)
        with patch('vso.flow_controller.time.time', return_value=self.now):
            with self.store.db() as db:
                self.assertEqual(daily_reserved(db, 'a'), 43)
                self.assertEqual(assert_daily_budget(db, 'a', 7), 0)
                with self.assertRaisesRegex(ValueError, 'ceiling'): assert_daily_budget(db, 'a', 8)

    def test_daily_counter_rolls_over_at_local_midnight(self):
        self.job('yesterday', 'a', 50, age=86400)
        with patch('vso.flow_controller.time.time', return_value=self.now):
            with self.store.db() as db:
                self.assertEqual(daily_reserved(db, 'a'), 0)
                self.assertEqual(assert_daily_budget(db, 'a', 50), 0)

    def test_cancelled_reservations_excluded_and_unknown_conserved(self):
        self.job('cancel', 'a', 40, status='cancelled')
        self.job('unknown', 'a', 45, status='unknown')
        with patch('vso.flow_controller.time.time', return_value=self.now):
            with self.store.db() as db:
                self.assertEqual(assert_daily_budget(db, 'a', 5), 0)
                with self.assertRaisesRegex(ValueError, 'ceiling'): assert_daily_budget(db, 'a', 6)

    def test_operator_ceiling_and_boolean_validation(self):
        with patch.dict(os.environ, {'VSO_FLOW_DAILY_CREDIT_LIMIT': '20'}), patch('vso.flow_controller.time.time', return_value=self.now):
            with self.store.db() as db:
                self.assertEqual(assert_daily_budget(db, 'a', 20), 0)
                with self.assertRaisesRegex(ValueError, 'ceiling'): assert_daily_budget(db, 'a', 21)
                with self.assertRaisesRegex(ValueError, 'Invalid'): assert_daily_budget(db, 'a', True)


if __name__ == '__main__':
    unittest.main()
