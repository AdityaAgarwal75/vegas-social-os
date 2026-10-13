import base64
import tempfile
import unittest
from unittest.mock import patch

from vso.engine import Engine
from vso.store import Store
from vso.drive import archive, reconcile


class DriveArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.e=Engine(Store(self.tmp.name))
        self.e.store.put('account','drive',{'id':'drive','provider':'drive','status':'connected'})
        self.asset=self.e.asset_import(base64.b64encode(b'\x89PNG\r\n\x1a\nexample').decode(),'image/png')
    def tearDown(self):self.tmp.cleanup()

    def test_same_asset_is_uploaded_once_without_public_sharing(self):
        with patch.object(self.e.accounts,'token',return_value='test-token'), patch('vso.drive.net.request',return_value=({'id':'file-1','webViewLink':'https://drive.google.com/file/d/file-1/view'},{})) as net:
            a=archive(self.e,self.asset['id'],'drive');b=archive(self.e,self.asset['id'],'drive')
            self.assertEqual(a['status'],'archived');self.assertEqual(a['id'],b['id']);self.assertEqual(net.call_count,1)
            self.assertNotIn(b'"permissions"',net.call_args.kwargs['raw'])
            self.assertIn(b'vegasSocialAsset',net.call_args.kwargs['raw'])

    def test_unknown_upload_reconciles_without_resubmitting(self):
        with patch.object(self.e.accounts,'token',return_value='test-token'), patch('vso.drive.net.request',side_effect=ValueError('interrupted')) as net:
            a=archive(self.e,self.asset['id'],'drive');self.assertEqual(a['status'],'unknown')
            archive(self.e,self.asset['id'],'drive');self.assertEqual(net.call_count,1)
        with patch.object(self.e.accounts,'token',return_value='test-token'), patch('vso.drive.net.request',return_value=({'files':[{'id':'existing-file','webViewLink':'https://drive.google.com/file/d/existing-file/view'}]},{})) as net:
            r=reconcile(self.e,a['id']);self.assertEqual(r['file_id'],'existing-file')
            self.assertNotIn('method',net.call_args.kwargs)

    def test_drive_is_not_a_publishing_destination(self):
        with self.assertRaises(ValueError):self.e.channel_save('Channel','Niche',account_ids=['drive'])


if __name__=='__main__':unittest.main()
