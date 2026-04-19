#!/usr/bin/env python3
"""
StartQ Custom Storage Backend
===============================
Override SessionRecorder to store anywhere.
StartQ doesn't care about the format.
"""

import json
from startq.autoq import SessionRecorder


class SQLiteRecorder(SessionRecorder):
    """Store recordings in SQLite."""

    def __init__(self, db_path="recordings.db"):
        super().__init__()
        import sqlite3
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS recordings (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                message TEXT,
                category TEXT
            )
        """)
        self.conn.commit()

    def write_record(self, entry):
        self.conn.execute(
            "INSERT INTO recordings VALUES (?, ?, ?, ?)",
            (entry["id"], entry["timestamp"], entry["message"],
             entry.get("category", "note"))
        )
        self.conn.commit()

    def read_records(self, limit=None, search=None, date=None):
        q = "SELECT * FROM recordings ORDER BY timestamp DESC"
        params = []
        if search:
            q = "SELECT * FROM recordings WHERE message LIKE ? ORDER BY timestamp DESC"
            params = [f"%{search}%"]
        if limit:
            q += " LIMIT ?"
            params.append(limit)
        rows = self.conn.execute(q, params).fetchall()
        return [{"id": r[0], "timestamp": r[1], "message": r[2], "category": r[3]} for r in rows]


class PlainTextRecorder(SessionRecorder):
    """Store recordings as plain text lines."""

    def __init__(self, log_file="session.log"):
        super().__init__()
        self.log_file = log_file

    def write_record(self, entry):
        ts = entry["timestamp"][:19]
        cat = entry.get("category", "note").upper()
        with open(self.log_file, "a") as f:
            f.write(f"[{ts}] [{cat}] {entry['message']}\n")

    def read_records(self, limit=None, search=None, date=None):
        try:
            lines = open(self.log_file).readlines()
        except FileNotFoundError:
            return []
        records = [{"message": l.strip()} for l in reversed(lines) if l.strip()]
        if search:
            records = [r for r in records if search.lower() in r["message"].lower()]
        return records[:limit] if limit else records


def main():
    print("\n◈ Custom Backend Examples\n")

    db = SQLiteRecorder(":memory:")
    db.record("Deployed to staging", category="action")
    db.record("Redis for caching", category="decision")
    for r in db.read_records():
        print(f"  SQLite: [{r['category']}] {r['message']}")

    print()
    import tempfile, os
    tmp = os.path.join(tempfile.gettempdir(), "demo.log")
    txt = PlainTextRecorder(tmp)
    txt.record("Migration complete", category="milestone")
    for r in txt.read_records():
        print(f"  Text:   {r['message']}")
    os.unlink(tmp)

    print("\n◈ Override write_record() and read_records() to store anywhere.\n")


if __name__ == "__main__":
    main()
