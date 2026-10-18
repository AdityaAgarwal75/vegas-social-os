"""Security and result-provenance tests for the Meta-owned Reel adapter."""
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from vso import intelligence
from vso import intelligence_owned as own
from tests.test_intelligence import EngineStub


class OwnedReelTests(unittest.TestCase):
    def test_meta_download_must_be_cdn(self):
        for url in (
            "http://scontent.cdninstagram.com/a.mp4",
            "https://cdninstagram.com/a.mp4",
            "https://evilcdninstagram.com/a.mp4",
            "https://127.0.0.1/a.mp4",
            "https://user:pass@scontent.cdninstagram.com/a.mp4",
            "https://x.fbcdn.net:4443/a.mp4",
            "https://x.fbcdn.net/a.mp4#fragment",
            "https://scontent.cdninstagram.com.evil.test/a.mp4",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                own._cdn_download(url, Path("/tmp/should-not-exist.mp4"))

    def test_owner_video_identity_checks_before_media_url(self):
        with patch.object(own.ig, "_context", return_value=(
            {"remote_id": "123", "name": "untamedplot"}, "https://graph.facebook.com/v23.0", "private-token")), \
             patch.object(own.ig, "_pages", return_value=(
                 [{"id": "17927711046446006", "media_product_type": "REELS"}], True)), \
             patch.object(own.net, "request", return_value=({
                 "id": "17927711046446006", "media_product_type": "REELS",
                 "media_url": "https://scontent.cdninstagram.com/vid.mp4"}, {})):
            row, url = own._owned_media(object(), "account", "17927711046446006")
            self.assertEqual(row["id"], "17927711046446006")
            self.assertTrue(url.startswith("https://scontent."))

    def test_rank_is_sample_relative_not_guaranteed_viral(self):
        rows = [{"id": str(i), "views": n, "permalink": f"https://instagram.com/reel/{i}",
                 "caption": "hello", "timestamp": "", "likes": 0, "comments": 0}
                for i, n in enumerate([100, 200, 1000], start=1)]
        with patch.object(own.ig, "media_list", return_value={
            "username": "untamedplot", "reels": rows, "ranking_complete": True
        }):
            result = own.performance(None, "fake_id")
        self.assertEqual(result["median_views"], 200)
        self.assertEqual(result["ranked"][2]["views_relative_to_sample_median"], 5)
        self.assertIn("not causal", result["method"])

    def test_request_id_idempotent_and_owner_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = EngineStub(tmp)
            intelligence._ACTIVE = threading.BoundedSemaphore(1)
            with patch.object(own.threading.Thread, "start", return_value=None):
                job = own.analyze_owned(engine, "a"*32, "17927711046446006", "same-request")
                self.assertEqual(job["status"], "running")
                self.assertEqual(own.analyze_owned(engine, "a"*32, "17927711046446006", "same-request")["id"], job["id"])
                with self.assertRaisesRegex(ValueError, "different Reel"):
                    own.analyze_owned(engine, "b"*32, "17927711046446006", "same-request")
            intelligence._ACTIVE.release()

    def test_short_video_probe(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp)/"test.mp4"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error",
                            "-f", "lavfi", "-i", "color=black:size=160x160:rate=2",
                            "-t", "2", "-c:v", "mpeg4", str(video)], timeout=25, check=True)
            self.assertGreater(own._duration(video), 1)


if __name__ == "__main__":
    unittest.main()
