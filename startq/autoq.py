"""
startq.autoq - Session Recorder & Activity Monitor
====================================================
Record everything you do during an AI session.

AutoQ is your session's black box recorder. Every action,
decision, note, and milestone gets logged. Store it anywhere
you want — local JSON files, a database, a cloud API, or
just plain text files. AutoQ doesn't care about the format.
It cares that nothing gets lost.

Usage via CLI:
    startq record "Connected Stripe API, test mode working"
    startq record "Bug: auth tokens expire after 30 min, need refresh logic"
    startq record "Decision: using PostgreSQL over MongoDB for transactions"
    startq log
    startq log --last 5
    startq log --search "stripe"
"""

import json
import os
import uuid
import datetime
from pathlib import Path


class SessionRecorder:
    """Records session activity to local storage.
    
    Default backend is JSON files in .startq/recordings/.
    Override write_record() and read_records() to store
    anywhere — database, cloud API, flat files, whatever.
    """

    def __init__(self, root_dir: str = ".startq"):
        self.root_dir = Path(root_dir)
        self.recordings_dir = self.root_dir / "recordings"
        self._session_file = None

    def _ensure_dir(self):
        """Create recordings directory if it doesn't exist."""
        self.recordings_dir.mkdir(parents=True, exist_ok=True)

    def _get_session_file(self) -> Path:
        """Get or create today's session recording file."""
        self._ensure_dir()
        today = datetime.date.today().isoformat()
        return self.recordings_dir / f"{today}.jsonl"

    def record(self, message: str, category: str = "note", metadata: dict = None):
        """Record a single activity entry.
        
        Args:
            message: What happened. Plain text.
            category: Type of entry — note, decision, bug, milestone, action.
            metadata: Optional dict of extra data to attach.
        """
        entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "message": message,
            "category": category,
        }
        if metadata:
            entry["metadata"] = metadata

        self.write_record(entry)
        return entry

    def write_record(self, entry: dict):
        """Write a record to storage. Override this for custom backends.
        
        Default: appends JSON line to today's .jsonl file.
        
        Override examples:
            - Write to SQLite
            - POST to a REST API
            - Append to a plain text log
            - Store as a cube in a Brain
        """
        session_file = self._get_session_file()
        with open(session_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def read_records(self, limit: int = None, search: str = None, 
                     date: str = None) -> list:
        """Read records from storage. Override this for custom backends.
        
        Default: reads from .jsonl files in recordings directory.
        """
        self._ensure_dir()
        records = []

        if date:
            files = [self.recordings_dir / f"{date}.jsonl"]
        else:
            files = sorted(self.recordings_dir.glob("*.jsonl"), reverse=True)

        for f in files:
            if not f.exists():
                continue
            for line in f.read_text(encoding="utf-8").strip().split("\n"):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                    if search and search.lower() not in json.dumps(record).lower():
                        continue
                    records.append(record)
                except json.JSONDecodeError:
                    continue

        records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)

        if limit:
            records = records[:limit]

        return records

    def get_session_summary(self) -> dict:
        """Get a summary of all recorded sessions."""
        self._ensure_dir()
        files = sorted(self.recordings_dir.glob("*.jsonl"))
        total_records = 0
        dates = []

        for f in files:
            date = f.stem
            dates.append(date)
            lines = [l for l in f.read_text(encoding="utf-8").strip().split("\n") if l.strip()]
            total_records += len(lines)

        return {
            "total_records": total_records,
            "total_sessions": len(files),
            "dates": dates,
            "recordings_dir": str(self.recordings_dir.absolute()),
        }

    def export_session(self, date: str = None, format: str = "json") -> str:
        """Export a session's recordings.
        
        Args:
            date: Date to export (default: today)
            format: Output format — json, text, or jsonl
        
        Returns:
            Formatted string of all records for that date.
        """
        if not date:
            date = datetime.date.today().isoformat()

        records = self.read_records(date=date)

        if format == "text":
            lines = []
            for r in records:
                ts = r.get("timestamp", "?")[:19]
                cat = r.get("category", "note").upper()
                msg = r.get("message", "")
                lines.append(f"[{ts}] [{cat}] {msg}")
            return "\n".join(lines)

        elif format == "jsonl":
            return "\n".join(json.dumps(r) for r in records)

        else:  # json
            return json.dumps(records, indent=2)
