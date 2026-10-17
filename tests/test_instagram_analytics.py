"""Mocked provider contract tests: no Meta network or token leakage."""
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from vso import auth, tools
from vso.engine import Engine
from vso.store import Store


class InstagramMediaAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.engine = Engine(Store(self.tmp.name))
        self.ig = "ig-own"
        self.first = "17900000000000001"
        self.second = "17900000000000002"
        self.engine.store.put("account", self.ig, {
            "id": self.ig, "provider": "instagram", "status": "connected",
            "remote_id": "17841425239410984", "name": "untamedplot",
        })
        self.page = {
            "id": "page-own", "provider": "facebook", "status": "connected",
            "remote_id": "1255341171004088", "linked_instagram_id": "17841425239410984",
            "linked_instagram_username": "untamedplot",
            "permissions": ["instagram_basic", "instagram_manage_insights",
                            "pages_read_engagement", "pages_show_list"],
        }
        self.engine.store.put("account", "page-own", self.page)
        self.engine.accounts.token = lambda account_id: "fixture-only-token"
        self.engine.accounts.config.version = lambda provider: "v25.0"
        self.fail_view_for = set()
        self.calls = []

    def fake_request(self, url, *, token=None, **kwargs):
        self.assertEqual(token, "fixture-only-token")
        u = urlsplit(url)
        self.assertEqual(u.scheme, "https")
        self.assertEqual(u.hostname, "graph.facebook.com")
        query = parse_qs(u.query)
        self.calls.append((u.path, query))
        if u.path == "/v25.0/1255341171004088":
            return {"instagram_business_account": {
                "id": "17841425239410984", "username": "untamedplot"
            }}, {}
        if u.path == "/v25.0/17841425239410984/media":
            if "after" not in query:
                return {"data": [
                    {"id": self.first, "media_product_type": "REELS",
                     "media_type": "VIDEO", "caption": "First Reel",
                     "permalink": "https://www.instagram.com/reel/A/", "like_count": 8},
                    {"id": "17900000000000003", "media_product_type": "FEED",
                     "media_type": "IMAGE", "caption": "Not a Reel"},
                ], "paging": {"next": "provider-next-url-containing-private-token",
                              "cursors": {"after": "opaque-page-2"}}}, {}
            self.assertEqual(query["after"], ["opaque-page-2"])
            return {"data": [
                {"id": self.second, "media_product_type": "REELS",
                 "media_type": "VIDEO", "caption": "Second Reel",
                 "permalink": "https://www.instagram.com/reel/B/", "like_count": 12},
            ]}, {}
        if u.path in ("/v25.0/" + self.first + "/insights",
                      "/v25.0/" + self.second + "/insights"):
            mid = u.path.split("/")[2]
            metric = query["metric"][0]
            if metric == "views" and mid in self.fail_view_for:
                raise ValueError("Provider rejected request (HTTP 400)")
            views = {self.first: 100, self.second: 900}
            if metric != "views":
                return {"data": []}, {}
            return {"data": [{"name": metric, "total_value": {"value": views[mid]}}]}, {}
        self.fail("Unexpected API call " + u.path)

    def test_reels_ranked_by_real_views_only_and_read_scope(self):
        self.assertEqual(auth.tool_scope("instagram_media_list"), "social:read")
        self.assertEqual(auth.tool_scope("instagram_media_insights"), "social:read")
        with patch("vso.instagram_analytics.net.request", self.fake_request):
            result = tools.call(self.engine, "instagram_media_list", {"account_id": self.ig})
            detail = tools.call(self.engine, "instagram_media_insights", {
                "account_id": self.ig, "media_id": self.second,
            })
        self.assertEqual(result["scanned_media"], 3)
        self.assertEqual(result["reels_found"], 2)
        self.assertTrue(result["ranking_complete"])
        self.assertEqual(result["top_reel"]["id"], self.second)
        self.assertEqual(result["top_reel"]["views"], 900)
        self.assertEqual(detail["views"], 900)
        self.assertIn("reach", detail["unavailable_metrics"])
        # Ignore potentially token-bearing provider paging next URL.
        self.assertFalse(any("provider-next-url" in path for path, _ in self.calls))

    def test_missing_views_are_unknown_not_zero(self):
        self.fail_view_for.add(self.second)
        with patch("vso.instagram_analytics.net.request", self.fake_request):
            result = tools.call(self.engine, "instagram_media_list", {"account_id": self.ig})
        self.assertFalse(result["ranking_complete"])
        self.assertIsNone(result["top_reel"])
        self.assertIsNone(result["reels"][-1]["views"])

    def test_wrong_page_and_missing_grant_fail_closed(self):
        self.page["linked_instagram_id"] = "17840000000000000"
        self.engine.store.put("account", "page-own", self.page)
        with patch("vso.instagram_analytics.net.request", self.fake_request):
            with self.assertRaises(ValueError):
                tools.call(self.engine, "instagram_media_list", {"account_id": self.ig})
        self.page["linked_instagram_id"] = "17841425239410984"
        self.page["permissions"].remove("instagram_manage_insights")
        self.engine.store.put("account", "page-own", self.page)
        with self.assertRaises(ValueError):
            tools.call(self.engine, "instagram_media_list", {"account_id": self.ig})

    def test_rejects_other_media_and_unbounded_limit(self):
        with patch("vso.instagram_analytics.net.request", self.fake_request):
            with self.assertRaises(ValueError):
                tools.call(self.engine, "instagram_media_insights", {
                    "account_id": self.ig, "media_id": "17900000000000003",
                })
        with self.assertRaises(ValueError):
            tools.call(self.engine, "instagram_media_list", {
                "account_id": self.ig, "limit": 9999,
            })


if __name__ == "__main__":
    unittest.main()
