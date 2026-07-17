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
        from startq.integrity import verify_receipt
        receipt = self.shutdown.create_receipt("Signed session")
        valid, profile = verify_receipt(receipt, self.test_dir)
        self.assertTrue(valid)
        self.assertEqual(profile, "hmac-sha256")
        self.assertEqual(receipt["signature_algorithm"], "hmac-sha256")

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

    def test_save_transcript_no_ide_returns_none(self):
        result = self.shutdown.save_transcript()
        # Returns (None, None, None) if no IDE brain exists
        self.assertEqual(len(result), 3)

    def test_sessions_dir_created_on_transcript(self):
        # Create a fake IDE brain directory
        fake_brain = Path(self.test_dir) / "fake_brain"
        fake_conv = fake_brain / "aaaa1111-bbbb-cccc-dddd-eeeeffffaaaa"
        logs_dir = fake_conv / ".system_generated" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        overview = logs_dir / "overview.txt"
        overview.write_text("USER: Hello\nAGENT: Hi there", encoding="utf-8")

        # Monkey-patch the brain paths
        import startq.endq as endq_mod
        original = endq_mod._ANTIGRAVITY_BRAIN_PATHS
        endq_mod._ANTIGRAVITY_BRAIN_PATHS = [fake_brain]

        try:
            txt_path, conv_id, content = self.shutdown.save_transcript()
            self.assertIsNotNone(txt_path)
            self.assertIn("aaaa1111", conv_id)
            self.assertIn("Hello", content)
            self.assertTrue(Path(txt_path).exists())
            saved = Path(txt_path).read_text(encoding="utf-8")
            self.assertIn("Session Transcript", saved)
            self.assertIn("Hello", saved)
        finally:
            endq_mod._ANTIGRAVITY_BRAIN_PATHS = original

    def test_read_session_content_overview(self):
        fake_dir = Path(self.test_dir) / "session_test"
        logs = fake_dir / ".system_generated" / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        (logs / "overview.txt").write_text("This is the full session.", encoding="utf-8")
        content = self.shutdown._read_session_content(fake_dir)
        self.assertEqual(content, "This is the full session.")

    def test_read_session_content_fallback_transcript(self):
        fake_dir = Path(self.test_dir) / "session_test2"
        logs = fake_dir / ".system_generated" / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        entries = [
            json.dumps({"source": "USER_EXPLICIT", "content": "What is 2+2?"}),
            json.dumps({"source": "MODEL", "content": "4"}),
        ]
        (logs / "transcript.jsonl").write_text("\n".join(entries), encoding="utf-8")
        content = self.shutdown._read_session_content(fake_dir)
        self.assertIn("[USER]", content)
        self.assertIn("[AGENT]", content)
        self.assertIn("2+2", content)

    def test_receipt_includes_transcript_path(self):
        fake_brain = Path(self.test_dir) / "fake_brain2"
        fake_conv = fake_brain / "bbbb2222-cccc-dddd-eeee-ffffaaaabbbb"
        logs_dir = fake_conv / ".system_generated" / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        (logs_dir / "overview.txt").write_text("Full session content here.", encoding="utf-8")

        import startq.endq as endq_mod
        original = endq_mod._ANTIGRAVITY_BRAIN_PATHS
        endq_mod._ANTIGRAVITY_BRAIN_PATHS = [fake_brain]

        try:
            receipt = self.shutdown.create_receipt("Test with transcript")
            self.assertIn("transcript_file", receipt)
            self.assertIn("transcript_checksum", receipt)
            self.assertIn("conversation_id", receipt)
        finally:
            endq_mod._ANTIGRAVITY_BRAIN_PATHS = original


if __name__ == "__main__":
    unittest.main()
