import unittest
import os
import shutil
import json
from pathlib import Path
from startq.brain import BrainManager

class TestBrainManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = ".test_startq"
        self.brain = BrainManager(root_dir=self.test_dir)
        
    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_init_creates_directories(self):
        self.brain.init_brain()
        self.assertTrue(self.brain.brain_dir.exists())
        self.assertTrue(self.brain.state_file.exists())
        self.assertTrue((Path(self.test_dir) / "config.json").exists())

    def test_boot_without_init_fails(self):
        with self.assertRaises(FileNotFoundError):
            self.brain.boot_session()

    def test_end_without_init_fails(self):
        with self.assertRaises(FileNotFoundError):
            self.brain.end_session("context")

    def test_end_session_writes_context(self):
        self.brain.init_brain()
        session_id = self.brain.end_session("Test context payload")
        
        receipt_path = self.brain.brain_dir / f"{session_id}.json"
        self.assertTrue(receipt_path.exists())
        
        data = json.loads(receipt_path.read_text())
        self.assertEqual(data["context"], "Test context payload")

    def test_boot_loads_recent_context(self):
        self.brain.init_brain()
        self.brain.end_session("First context")
        
        result = self.brain.boot_session()
        self.assertEqual(result["recent_context"], "First context")
        self.assertEqual(result["sessions_found"], 1)

    def test_boot_handles_corrupted_session_file(self):
        self.brain.init_brain()
        
        # Write a corrupted JSON file
        bad_file = self.brain.brain_dir / "corrupted.json"
        bad_file.write_text("{ not valid json")
        
        # Should not raise, but should warn internally
        result = self.brain.boot_session()
        self.assertIsNotNone(result["session_id"])
        self.assertIsNone(result["recent_context"])

    def test_secure_boot_tamper_rejection(self):
        self.brain.init_brain()
        session_id = self.brain.end_session("Valid context")
        
        # Tamper with the JSON payload
        receipt_path = self.brain.brain_dir / f"{session_id}.json"
        data = json.loads(receipt_path.read_text())
        data["context"] = "Malicious context injected"
        receipt_path.write_text(json.dumps(data, indent=2))
        
        # Boot should reject it due to signature mismatch and not load the malicious context
        result = self.brain.boot_session()
        self.assertIsNone(result["recent_context"])

    def test_legacy_sha256_receipt_still_loads(self):
        import hashlib

        self.brain.init_brain()
        payload = {
            "session_id": "legacy-session",
            "timestamp": "2026-05-20T00:00:00+00:00",
            "context": "Legacy context",
            "type": "session_receipt",
            "source": "startq",
        }
        serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
        payload["signature"] = hashlib.sha256(serialized).hexdigest()
        (self.brain.brain_dir / "legacy.json").write_text(json.dumps(payload))

        result = self.brain.boot_session(allow_legacy=True)
        self.assertEqual(result["recent_context"], "Legacy context")

    def test_legacy_sha256_receipt_is_blocked_by_default(self):
        import hashlib

        self.brain.init_brain()
        payload = {"context": "Untrusted legacy context", "type": "session_receipt"}
        serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
        payload["signature"] = hashlib.sha256(serialized).hexdigest()
        (self.brain.brain_dir / "legacy-blocked.json").write_text(json.dumps(payload))

        result = self.brain.boot_session()
        self.assertIsNone(result["recent_context"])

    def test_legacy_cloud_key_migrates_out_of_config(self):
        key_file = Path(self.test_dir) / "protected-cloud.key"
        previous = os.environ.get("STARTQ_CLOUD_KEY_FILE")
        os.environ["STARTQ_CLOUD_KEY_FILE"] = str(key_file)
        try:
            self.brain.init_brain()
            config = self.brain.get_config()
            config["cloud"] = {
                "enabled": True,
                "brain_url": "https://brain.example.com",
                "api_key": "legacy-secret",
            }
            self.brain.save_config(config)

            self.assertTrue(self.brain._load_cloud_config())
            migrated = self.brain.get_config()["cloud"]
            self.assertNotIn("api_key", migrated)
            self.assertEqual(key_file.read_text().strip(), "legacy-secret")
        finally:
            if previous is None:
                os.environ.pop("STARTQ_CLOUD_KEY_FILE", None)
            else:
                os.environ["STARTQ_CLOUD_KEY_FILE"] = previous
        
if __name__ == "__main__":
    unittest.main()
