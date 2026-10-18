"""Tests for private, bounded content intelligence."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from vso import intelligence as v
from vso.store import Store


class EngineStub:
    def __init__(self, folder):
        self.store = Store(folder)

    def _load(self, db, kind, ident):
        row = db.execute("SELECT body FROM records WHERE kind=? AND id=?",
                         (kind, ident)).fetchone()
        if not row:
            raise ValueError("Record not found")
        return json.loads(row[0])


class VideoIntelligenceTests(unittest.TestCase):
    def test_supported_urls(self):
        for url in (
            "https://www.youtube.com/shorts/aBcD1234_5x",
            "https://youtu.be/aBcD1234_5x",
            "https://www.instagram.com/reel/ABC123xyz/",
            "https://www.youtube.com/watch?v=aBcD1234_5x",
        ):
            self.assertEqual(v.validate_url(url), url)

    def test_reject_private_hosts_and_junk(self):
        for url in (
            "http://www.youtube.com/watch?v=test",
            "https://youtube.com.evil.com/shorts/abc",
            "https://127.0.0.1/shorts/foo",
            "https://user:pass@youtube.com/watch?v=123",
            "https://instagram.com/accounts/login",
            "https://youtube.com:8443/watch?v=abc",
            "https://youtube.com/watch?v=abc\nabc",
            "https://youtu.be/one/two",
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                v.validate_url(url)

    def test_job_creation_and_idempotent_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = EngineStub(tmp)
            v._ACTIVE = threading.BoundedSemaphore(1)
            with patch.object(v.threading.Thread, "start", return_value=None):
                record = v.analyze(engine, "https://youtu.be/aBcD1234_5x", "first")
                self.assertEqual(record["status"], "running")
                self.assertEqual(v.analyze(engine, record["url"], "first")["id"], record["id"])
                with self.assertRaisesRegex(ValueError, "another video"):
                    v.analyze(engine, "https://youtu.be/anOther1111", "first")
                self.assertEqual(v.status(engine, record["id"])["id"], record["id"])
            v._ACTIVE.release()

    def test_interrupted_worker_honestly_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = EngineStub(tmp)
            job_id = "a" * 32
            engine.store.put("intelligence-job", job_id, {
                "id": job_id, "status": "running", "updated_at": time.time()-400
            })
            result = v.status(engine, job_id)
            self.assertEqual(result["status"], "interrupted")
            self.assertIn("no automatic retry", result["error"])

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "FFmpeg unavailable")
    def test_extract_contact_sheet_from_synthetic_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            engine = EngineStub(Path(tmp)/"state")
            job_id = "b" * 32
            engine.store.put("intelligence-job", job_id, {
                "id": job_id, "status": "running", "updated_at": time.time()
            })
            folder = Path(tmp)/"frames"
            folder.mkdir()
            source = folder/"sample.mp4"
            cmd = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error",
                   "-f", "lavfi", "-i", "testsrc2=size=320x240:rate=5",
                   "-t", "4", "-c:v", "mpeg4", "-y", str(source)]
            subprocess.run(cmd, check=True, timeout=20)
            asset, cuts = v._visual(engine, job_id, folder, source)
            self.assertEqual(len(asset), 64)
            self.assertIsInstance(cuts, list)
            stored = engine.store.get("asset", asset)
            self.assertEqual(stored["media_type"], "image/jpeg")
            self.assertTrue((engine.store.root/"media"/stored["file"]).exists())


if __name__ == "__main__":
    unittest.main()
