"""
startq.endq - Graceful Session Shutdown
========================================
The mirror of boot. Runs the shutdown sequence:
capture state, snapshot git, archive recordings,
save chat transcript, sign the receipt, sync to cloud.

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


# Default Antigravity IDE brain location (cross-platform)
_ANTIGRAVITY_BRAIN_PATHS = [
    Path.home() / ".gemini" / "antigravity-ide" / "brain",
    Path.home() / ".gemini" / "antigravity" / "brain",
]


class SessionShutdown:
    """Handles graceful session shutdown and state persistence."""

    def __init__(self, root_dir: str = ".startq"):
        self.root_dir = Path(root_dir)
        self.brain_dir = self.root_dir / "brain"
        self.sessions_dir = self.root_dir / "sessions"

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

    # ─── Transcript capture ──────────────────────────────────────────────

    def _find_ide_brain(self) -> Path | None:
        """Find the Antigravity IDE brain directory."""
        for p in _ANTIGRAVITY_BRAIN_PATHS:
            if p.exists():
                return p
        return None

    def _find_current_session(self) -> tuple[Path | None, str | None]:
        """Find the most recently modified IDE conversation directory.
        Returns (session_dir, conversation_id) or (None, None)."""
        brain = self._find_ide_brain()
        if not brain:
            return None, None

        candidates = []
        for d in brain.iterdir():
            if not d.is_dir():
                continue
            # Skip non-UUID directories
            if len(d.name) < 30 or d.name == "tempmediaStorage":
                continue
            candidates.append(d)

        if not candidates:
            return None, None

        candidates.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return candidates[0], candidates[0].name

    def _read_session_content(self, session_dir: Path) -> str | None:
        """Read session content from overview.txt or transcript.jsonl."""

        # Primary: overview.txt
        overview = session_dir / ".system_generated" / "logs" / "overview.txt"
        if overview.exists() and overview.stat().st_size > 0:
            try:
                return overview.read_text(encoding="utf-8", errors="replace")
            except Exception:
                pass

        # Fallback: transcript.jsonl
        transcript = session_dir / ".system_generated" / "logs" / "transcript.jsonl"
        if transcript.exists() and transcript.stat().st_size > 0:
            try:
                lines = []
                for raw in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
                    if not raw.strip():
                        continue
                    try:
                        entry = json.loads(raw)
                        content = entry.get("content", "")
                        if content:
                            source = entry.get("source", "")
                            role = "USER" if "USER" in source else "AGENT"
                            lines.append(f"[{role}] {content}")
                    except json.JSONDecodeError:
                        continue
                if lines:
                    return "\n\n".join(lines)
            except Exception:
                pass

        # Tertiary: artifact markdown files
        artifacts = []
        for name in ["walkthrough.md", "implementation_plan.md", "task.md"]:
            artifact = session_dir / name
            if artifact.exists() and artifact.stat().st_size > 0:
                try:
                    artifacts.append(
                        f"=== {name} ===\n"
                        + artifact.read_text(encoding="utf-8", errors="replace")
                    )
                except Exception:
                    pass
        if artifacts:
            return "\n\n".join(artifacts)

        return None

    def save_transcript(self) -> tuple[str | None, str | None, str | None]:
        """Find and save the current IDE chat session as a .txt file.

        Returns (txt_path, conversation_id, content) or (None, None, None).
        """
        session_dir, conv_id = self._find_current_session()
        if not session_dir:
            return None, None, None

        content = self._read_session_content(session_dir)
        if not content:
            return None, conv_id, None

        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.datetime.now(datetime.timezone.utc)
        date_str = now.strftime("%Y-%m-%d_%H%M%S")
        txt_filename = f"{date_str}_{conv_id[:8]}.txt"
        txt_path = self.sessions_dir / txt_filename

        header = (
            f"Session Transcript\n"
            f"{'=' * 60}\n"
            f"Conversation ID: {conv_id}\n"
            f"Saved at:        {now.isoformat()}\n"
            f"Source:          Antigravity IDE\n"
            f"{'=' * 60}\n\n"
        )

        try:
            txt_path.write_text(header + content, encoding="utf-8")
            return str(txt_path), conv_id, content
        except Exception:
            return None, conv_id, content

    # ─── Receipt creation ────────────────────────────────────────────────

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

        # Save transcript
        transcript_path, conv_id, transcript_content = self.save_transcript()

        receipt = {
            "session_id": session_id,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "context": context,
            "type": "session_receipt",
            "source": "endq",
            "hibernation_state": git_state,
            "records_archived": records_count,
        }

        if transcript_path:
            receipt["transcript_file"] = transcript_path
            receipt["conversation_id"] = conv_id

        if transcript_content:
            # Include a checksum so Brain can deduplicate
            receipt["transcript_checksum"] = hashlib.sha256(
                transcript_content.encode("utf-8")
            ).hexdigest()[:16]

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

                        # Also store transcript as its own cube
                        transcript_content = None
                        if receipt.get("transcript_file"):
                            try:
                                transcript_content = Path(
                                    receipt["transcript_file"]
                                ).read_text(encoding="utf-8")
                            except Exception:
                                pass

                        if transcript_content:
                            max_chars = 500_000
                            cube_content = transcript_content[:max_chars]
                            if len(transcript_content) > max_chars:
                                cube_content += (
                                    f"\n\n[TRUNCATED: {len(transcript_content):,} "
                                    f"total chars]"
                                )
                            client.store_cube({
                                "type": "session_transcript",
                                "conversation_id": receipt.get("conversation_id"),
                                "content": cube_content,
                                "checksum": receipt.get("transcript_checksum"),
                                "source": "endq",
                                "tags": ["session", "transcript", "antigravity"],
                            })
            except Exception:
                pass

        return session_id
