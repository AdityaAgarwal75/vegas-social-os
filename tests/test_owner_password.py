"""Regression tests for owner-chosen password authentication."""
import tempfile
import unittest

from vso.store import Store
from vso.owner_auth import configured, password_set, password_check, validate_return

class PasswordTests(unittest.TestCase):
    def test_hash_rotation_and_bad_destinations(self):
        with tempfile.TemporaryDirectory() as d:
            store=Store(d)
            self.assertFalse(configured(store))
            with self.assertRaises(ValueError):password_set(store,"short")
            store.put("session","existing",{"expires":1234})
            sample="this is only a test passphrase"
            password_set(store,sample)
            self.assertTrue(configured(store))
            self.assertTrue(password_check(store,sample,"127.0.0.1"))
            self.assertFalse(password_check(store,"not the passphrase","127.0.0.1"))
            self.assertEqual(store.all("session"),[])
            self.assertNotIn(sample,repr(store.get("owner-auth","password")))
            for destination in ("https://evil.example","//evil.example","/other","/authorize?x=a\\r"):
                with self.assertRaises(ValueError):validate_return(destination)
            self.assertEqual(validate_return("/dashboard"),"/dashboard")

if __name__=="__main__":unittest.main()
