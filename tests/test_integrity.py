import os
import shutil
import tempfile
import unittest
from pathlib import Path

from startq.credentials import cloud_api_key_path, load_cloud_api_key, write_cloud_api_key
from startq.integrity import sign_receipt, signing_key_path, verify_receipt


class TestIntegrity(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(".test_startq_integrity")
        self.key_dir = tempfile.TemporaryDirectory(dir="/tmp" if os.name == "posix" else None)
        self.original_key_file = os.environ.get("STARTQ_SIGNING_KEY_FILE")
        self.original_cloud_key_file = os.environ.get("STARTQ_CLOUD_KEY_FILE")
        os.environ["STARTQ_SIGNING_KEY_FILE"] = str(Path(self.key_dir.name) / "signing.key")
        os.environ["STARTQ_CLOUD_KEY_FILE"] = str(Path(self.key_dir.name) / "cloud.key")

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        if self.original_key_file is None:
            os.environ.pop("STARTQ_SIGNING_KEY_FILE", None)
        else:
            os.environ["STARTQ_SIGNING_KEY_FILE"] = self.original_key_file
        if self.original_cloud_key_file is None:
            os.environ.pop("STARTQ_CLOUD_KEY_FILE", None)
        else:
            os.environ["STARTQ_CLOUD_KEY_FILE"] = self.original_cloud_key_file
        self.key_dir.cleanup()

    def test_hmac_receipt_verifies(self):
        receipt = sign_receipt({"context": "test"}, self.test_dir)
        self.assertEqual(verify_receipt(receipt, self.test_dir), (True, "hmac-sha256"))

    def test_hmac_receipt_rejects_tampering(self):
        receipt = sign_receipt({"context": "original"}, self.test_dir)
        receipt["context"] = "changed"
        self.assertEqual(verify_receipt(receipt, self.test_dir), (False, "hmac-sha256"))

    def test_hmac_receipt_rejects_missing_key(self):
        receipt = sign_receipt({"context": "original"}, self.test_dir)
        signing_key_path(self.test_dir).unlink()
        self.assertEqual(verify_receipt(receipt, self.test_dir), (False, "missing-signing-key"))

    def test_signing_key_is_not_world_readable_on_posix(self):
        sign_receipt({"context": "test"}, self.test_dir)
        if os.name == "posix":
            mode = signing_key_path(self.test_dir).stat().st_mode & 0o777
            self.assertEqual(mode, 0o600)

    def test_cloud_key_uses_separate_protected_file(self):
        path = write_cloud_api_key(self.test_dir, "secret-value")
        self.assertIsNotNone(path)
        self.assertEqual(path, cloud_api_key_path(self.test_dir))
        self.assertEqual(load_cloud_api_key(self.test_dir, {}), "secret-value")


if __name__ == "__main__":
    unittest.main()
