"""
startq.endq - Graceful Session Shutdown
========================================
The mirror of boot. Runs the shutdown sequence:
capture state, snapshot git, archive recordings,
sign the receipt, sync to cloud.

Usage via CLI:
    startq shutdown -c "Summary of what happened"
    startq shutdown -c "Summary" --archive
"""

import json
import os
import uuid
import datetime
import hashlib
import subprocess
from pathlib import Path


class SessionShutdown:
    """Handles graceful session shutdown and state persistence."""

    def __init__(self, root_dir: str = ".startq"):
        self.root_dir = Path(root_dir)
        self.brain_dir = self.root_dir / "brain"

    def capture_git_state(self) -> dict | None:
        """Snapshot current git branch and uncommitted changes."""
        try:
            branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            status_lines = subprocess.check_output(
                ["git", "status", "--porcelain"],
                stderr=subprocess.DEVNULL
            ).decode().splitlines()

            diff_stat = subprocess.check_output(
                ["git", "diff", "--stat"],
                stderr=subprocess.DEVNULL
            ).decode().strip()

            return {
                "branch": branch,
                "modified_files": status_lines,
                "diff_summary": diff_stat[:500] if diff_stat else None,
            }
        except Exception:
            return None

    def archive_recordings(self) -> int:
        """Move today's recordings into the session receipt.
        
        Returns the number of records archived.
        """
        recordings_dir = self.root_dir / "recordings"
        if not recordings_dir.exists():
            return 0

        today = datetime.date.today().isoformat()
        today_file = recordings_dir / f"{today}.jsonl"
        if not today_file.exists():
            return 0

        lines = [l for l in today_file.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
        return len(lines)

    def get_todays_recordings(self) -> list:
        """Load all recordings from today."""
        recordings_dir = self.root_dir / "recordings"
        today = datetime.date.today().isoformat()
        today_file = recordings_dir / f"{today}.jsonl"

        if not today_file.exists():
            return []

        records = []
        for line in today_file.read_text(encoding="utf-8").strip().split("\n"):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records

    def create_receipt(self, context: str, archive: bool = False) -> dict:
        """Create a signed session receipt.
        
        Args:
            context: Summary of what was accomplished.
            archive: If True, embed today's recordings in the receipt.
        
        Returns:
            The complete receipt dict.
        """
        session_id = str(uuid.uuid4())
        git_state = self.capture_git_state()
        records_count = self.archive_recordings()
        
        receipt = {
            "session_id": session_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "context": context,
            "type": "session_receipt",
            "source": "endq",
            "hibernation_state": git_state,
            "records_archived": records_count,
        }

        if archive:
            receipt["recordings"] = self.get_todays_recordings()

        # Sign the receipt
        serialized = json.dumps(receipt, sort_keys=True).encode("utf-8")
        receipt["signature"] = hashlib.sha256(serialized).hexdigest()

        return receipt

    def shutdown(self, context: str, archive: bool = False, 
                 use_cloud: bool = False) -> str:
        """Run the full shutdown sequence.
        
        Returns the session ID.
        """
        receipt = self.create_receipt(context, archive=archive)
        session_id = receipt["session_id"]

        # Write locally
        self.brain_dir.mkdir(parents=True, exist_ok=True)
        receipt_path = self.brain_dir / f"{session_id}.json"
        receipt_path.write_text(json.dumps(receipt, indent=2))

        # Cloud sync if configured
        if use_cloud:
            try:
                config_file = self.root_dir / "config.json"
                if config_file.exists():
                    config = json.loads(config_file.read_text())
                    cloud_cfg = config.get("cloud", {})
                    if cloud_cfg.get("enabled") and cloud_cfg.get("brain_url"):
                        from .cloud_brain import CloudBrainClient
                        client = CloudBrainClient(
                            brain_url=cloud_cfg["brain_url"],
                            api_key=cloud_cfg.get("api_key"),
                        )
                        result = client.sync_session(receipt)
                        receipt["cloud_sync"] = result
            except Exception:
                pass

        return session_id
