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
        
        # Test that it triggers without error
        session_id = self.brain.boot_session()
        self.assertIsNotNone(session_id)

if __name__ == "__main__":
    unittest.main()
