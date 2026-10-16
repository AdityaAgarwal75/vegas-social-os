"""Fail-closed Instagram published-media deletion contract tests."""
import tempfile
import unittest
from unittest.mock import patch

from vso.engine import Engine
from vso.store import Store
from vso import tools, auth


class InstagramDeletionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.tmp.name)
        self.engine = Engine(self.store)
        self.account = "instagram-own"
        self.media_id = "17988348186076937"
        self.store.put("account", self.account, {
            "id": self.account, "provider": "instagram", "name": "untamedplot",
            "remote_id": "17841425239410984", "status": "connected",
        })
        self.store.put("account", "facebook-page", {
            "id": "facebook-page", "provider": "facebook", "remote_id": "1234567890123456",
            "name": "Utamed Plot", "status": "connected",
            "linked_instagram_id": "17841425239410984",
            "linked_instagram_username": "untamedplot",
            "permissions": ["instagram_manage_contents", "instagram_basic", "pages_show_list"],
        })
        self.store.put("publication", "published-test-reel", {
            "id": "published-test-reel", "kind": "composer", "provider": "instagram",
            "account_id": self.account, "status": "published", "remote_id": self.media_id,
            "caption": "Test reel", "visibility": "public",
        })

    def request(self):
        return tools.call(self.engine, "instagram_delete_prepare", {
            "account_id": self.account, "media_id": self.media_id,
            "request_id": "reel-test-deletion",
        })

    def test_idempotent_prepare_only_owned_media(self):
        first = self.request()
        self.assertEqual(first["status"], "review")
        self.assertEqual(first["id"], self.request()["id"])
        self.assertEqual(first["account_remote_id"], "17841425239410984")
        with self.assertRaises(ValueError):
            tools.call(self.engine, "instagram_delete_prepare", {
                "account_id": self.account, "media_id": "18000000000000000",
                "request_id": "different",
            })
        self.store.put("account", "other", {
            "id": "other", "provider": "instagram", "status": "connected",
            "remote_id": "some-other-id",
        })
        with self.assertRaises(ValueError):
            tools.call(self.engine, "instagram_delete_prepare", {
                "account_id": "other", "media_id": self.media_id,
                "request_id": "other-test",
            })

    def test_requires_exact_repeat_approval_and_no_implicit_delete(self):
        r = self.request()
        with self.assertRaises(ValueError):
            tools.call(self.engine, "instagram_delete_execute", {"deletion_id": r["id"]})
        with self.assertRaises(ValueError):
            tools.call(self.engine, "instagram_delete_approve", {
                "deletion_id": r["id"], "account_id": self.account,
                "media_id": "18000000000000000",
            })
        a = tools.call(self.engine, "instagram_delete_approve", {
            "deletion_id": r["id"], "account_id": self.account,
            "media_id": self.media_id,
        })
        self.assertEqual(a["status"], "approved")
        with patch.object(self.engine.accounts, "token", return_value="fake-page-token"), \
             patch("vso.instagram_delete.net.request") as send:
            send.side_effect = [
                ({"instagram_business_account": {"id":"17841425239410984", "username":"untamedplot"}}, {}),
                ({"id":self.media_id, "username":"untamedplot", "media_product_type":"REELS"}, {}),
                ({"success":True}, {}),
            ]
            result = tools.call(self.engine, "instagram_delete_execute", {"deletion_id":r["id"]})
            self.assertEqual(result["status"], "deleted")
            self.assertTrue(result["provider_confirmed"])
            self.assertEqual(send.call_count, 3)
            self.assertEqual(send.call_args.kwargs["method"], "DELETE")
            self.assertTrue(send.call_args.args[0].endswith("/" + self.media_id))
        self.assertEqual(
            tools.call(self.engine, "instagram_delete_status", {"deletion_id":r["id"]})["status"],
            "deleted",
        )
        with self.assertRaises(ValueError):
            tools.call(self.engine, "instagram_delete_execute", {"deletion_id": r["id"]})

    def test_wrong_account_identity_blocks_execute(self):
        r = self.request()
        tools.call(self.engine, "instagram_delete_approve", {
            "deletion_id": r["id"], "account_id": self.account,
            "media_id": self.media_id,
        })
        a = self.store.get("account", self.account)
        a["remote_id"] = "1234567890123456"
        self.store.put("account", self.account, a)
        with self.assertRaises(ValueError):
            tools.call(self.engine, "instagram_delete_execute", {"deletion_id": r["id"]})

    def test_special_management_scope(self):
        self.assertEqual(auth.tool_scope("instagram_delete_prepare"), "social:manage")
        self.assertEqual(auth.tool_scope("instagram_delete_approve"), "social:manage")
        self.assertEqual(auth.tool_scope("instagram_delete_execute"), "social:manage")
        self.assertEqual(auth.tool_scope("instagram_delete_status"), "social:read")
        specs = {x["name"]: x for x in tools.definitions(self.engine)}
        self.assertIn("instagram_delete_prepare", specs)
        self.assertIn("instagram_delete_execute", specs)
        self.assertEqual(specs["instagram_delete_execute"]["inputSchema"]["required"], ["deletion_id"])


if __name__ == "__main__":
    unittest.main()
