import unittest
import os
import shutil
import json
from pathlib import Path
from startq.autoq import SessionRecorder


class TestSessionRecorder(unittest.TestCase):
    def setUp(self):
        self.test_dir = ".test_startq_autoq"
        self.recorder = SessionRecorder(root_dir=self.test_dir)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_record_creates_file(self):
        entry = self.recorder.record("Test message")
        self.assertIn("id", entry)
        self.assertIn("timestamp", entry)
        self.assertEqual(entry["message"], "Test message")
        self.assertEqual(entry["category"], "note")

    def test_record_with_category(self):
        entry = self.recorder.record("Fixed the bug", category="action")
        self.assertEqual(entry["category"], "action")

    def test_record_with_metadata(self):
        entry = self.recorder.record("Test", metadata={"key": "value"})
        self.assertEqual(entry["metadata"], {"key": "value"})

    def test_read_records_returns_recorded_entries(self):
        self.recorder.record("First")
        self.recorder.record("Second")
        self.recorder.record("Third")

        records = self.recorder.read_records()
        messages = [r["message"] for r in records]
        self.assertIn("First", messages)
        self.assertIn("Second", messages)
        self.assertIn("Third", messages)

    def test_read_records_with_limit(self):
        for i in range(10):
            self.recorder.record(f"Entry {i}")

        records = self.recorder.read_records(limit=3)
        self.assertEqual(len(records), 3)

    def test_read_records_with_search(self):
        self.recorder.record("Alpha task done")
        self.recorder.record("Beta task started")
        self.recorder.record("Alpha cleanup")

        records = self.recorder.read_records(search="Alpha")
        self.assertEqual(len(records), 2)
        for r in records:
            self.assertIn("Alpha", r["message"])

    def test_get_session_summary(self):
        self.recorder.record("Test 1")
        self.recorder.record("Test 2")

        summary = self.recorder.get_session_summary()
        self.assertEqual(summary["total_records"], 2)
        self.assertEqual(summary["total_sessions"], 1)

    def test_export_session_json(self):
        self.recorder.record("Export test")
        output = self.recorder.export_session(format="json")
        parsed = json.loads(output)
        self.assertIsInstance(parsed, list)
        self.assertEqual(len(parsed), 1)

    def test_export_session_text(self):
        self.recorder.record("Export text test", category="action")
        output = self.recorder.export_session(format="text")
        self.assertIn("[ACTION]", output)
        self.assertIn("Export text test", output)

    def test_export_session_jsonl(self):
        self.recorder.record("Line 1")
        self.recorder.record("Line 2")
        output = self.recorder.export_session(format="jsonl")
        lines = output.strip().split("\n")
        self.assertEqual(len(lines), 2)
        for line in lines:
            parsed = json.loads(line)
            self.assertIn("message", parsed)

    def test_empty_read_returns_empty_list(self):
        records = self.recorder.read_records()
        self.assertEqual(records, [])

    def test_recordings_are_append_only(self):
        self.recorder.record("First")
        session_file = self.recorder._get_session_file()
        size_after_first = session_file.stat().st_size

        self.recorder.record("Second")
        size_after_second = session_file.stat().st_size

        self.assertGreater(size_after_second, size_after_first)


if __name__ == "__main__":
    unittest.main()
