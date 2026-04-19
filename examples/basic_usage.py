#!/usr/bin/env python3
"""
StartQ Basic Usage
===================
Run: python examples/basic_usage.py
"""

from startq.brain import BrainManager
from startq.autoq import SessionRecorder
from startq.endq import SessionShutdown


def main():
    print("\n◈ StartQ Basic Usage\n")

    # 1. Init
    brain = BrainManager()
    brain.init_brain()

    # 2. Boot
    session = brain.boot_session()
    print(f"  Session: {session['session_id'][:8]}")
    print(f"  History: {session['sessions_found']} previous sessions")
    if session["recent_context"]:
        print(f"  Context: {session['recent_context'][:80]}")

    # 3. Record (AutoQ)
    recorder = SessionRecorder()
    recorder.record("Connected to production database", category="action")
    recorder.record("Using connection pooling over single connections", category="decision")
    recorder.record("Timeout on large queries > 5s", category="bug")
    recorder.record("Database migration complete", category="milestone")

    records = recorder.read_records(limit=10)
    print(f"\n  Recorded {len(records)} entries:")
    for r in records:
        print(f"    [{r['category'].upper():10s}] {r['message']}")

    # 4. Shutdown (EndQ)
    shutdown = SessionShutdown()
    sid = shutdown.shutdown(
        context="Database migration complete. Connection pooling active. Deploy next.",
        archive=True
    )
    print(f"\n  Receipt: .startq/brain/{sid[:8]}.json")

    # 5. Verify
    brain2 = BrainManager()
    session2 = brain2.boot_session()
    if session2["recent_context"]:
        print(f"  Restored: {session2['recent_context'][:60]}...")

    print("\n◈ Done.\n")


if __name__ == "__main__":
    main()
