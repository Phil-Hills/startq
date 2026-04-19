import unittest
import os
import shutil
import json
from pathlib import Path
from startq.endq import SessionShutdown
from startq.autoq import SessionRecorder


class TestSessionShutdown(unittest.TestCase):
    def setUp(self):
        self.test_dir = ".test_startq_endq"
        self.shutdown = SessionShutdown(root_dir=self.test_dir)
        # Create brain directory
        brain_dir = Path(self.test_dir) / "brain"
        brain_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_create_receipt_returns_valid_receipt(self):
        receipt = self.shutdown.create_receipt("Test session complete")
        self.assertIn("session_id", receipt)
        self.assertIn("timestamp", receipt)
        self.assertIn("context", receipt)
        self.assertIn("signature", receipt)
        self.assertEqual(receipt["context"], "Test session complete")
        self.assertEqual(receipt["type"], "session_receipt")
        self.assertEqual(receipt["source"], "endq")

    def test_receipt_signature_is_valid(self):
        import hashlib
        receipt = self.shutdown.create_receipt("Signed session")

        # Remove signature and recompute
        sig = receipt.pop("signature")
        serialized = json.dumps(receipt, sort_keys=True).encode("utf-8")
        expected = hashlib.sha256(serialized).hexdigest()
        self.assertEqual(sig, expected)

    def test_shutdown_writes_receipt_file(self):
        session_id = self.shutdown.shutdown(context="Shutdown test")
        receipt_path = Path(self.test_dir) / "brain" / f"{session_id}.json"
        self.assertTrue(receipt_path.exists())

        data = json.loads(receipt_path.read_text())
        self.assertEqual(data["context"], "Shutdown test")

    def test_shutdown_with_archive_embeds_recordings(self):
        # Create a recording first
        recorder = SessionRecorder(root_dir=self.test_dir)
        recorder.record("Test activity", category="action")

        session_id = self.shutdown.shutdown(
            context="Archive test",
            archive=True
        )
        receipt_path = Path(self.test_dir) / "brain" / f"{session_id}.json"
        data = json.loads(receipt_path.read_text())

        self.assertIn("recordings", data)
        self.assertEqual(len(data["recordings"]), 1)
        self.assertEqual(data["recordings"][0]["message"], "Test activity")

    def test_archive_recordings_counts_correctly(self):
        recorder = SessionRecorder(root_dir=self.test_dir)
        recorder.record("Entry 1")
        recorder.record("Entry 2")
        recorder.record("Entry 3")

        count = self.shutdown.archive_recordings()
        self.assertEqual(count, 3)

    def test_archive_recordings_empty_returns_zero(self):
        count = self.shutdown.archive_recordings()
        self.assertEqual(count, 0)

    def test_capture_git_state_returns_dict_or_none(self):
        result = self.shutdown.capture_git_state()
        # In a git repo it returns a dict, outside it returns None
        if result is not None:
            self.assertIn("branch", result)
            self.assertIn("modified_files", result)

    def test_shutdown_returns_valid_uuid(self):
        import uuid
        session_id = self.shutdown.shutdown(context="UUID test")
        # Should not raise
        uuid.UUID(session_id)

    def test_multiple_shutdowns_create_separate_receipts(self):
        id1 = self.shutdown.shutdown(context="Session 1")
        id2 = self.shutdown.shutdown(context="Session 2")
        self.assertNotEqual(id1, id2)

        brain_dir = Path(self.test_dir) / "brain"
        receipts = list(brain_dir.glob("*.json"))
        self.assertEqual(len(receipts), 2)


if __name__ == "__main__":
    unittest.main()
