#!/usr/bin/env python3
"""
StartQ — Instructions
=====================
Run this file to see how StartQ works:

    python3 examples/quickstart.py

Or just read it. Every section is a working code example.
"""

import subprocess
import sys
import os


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def run(cmd):
    """Run a shell command and print the output."""
    print(f"  $ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        for line in result.stdout.strip().split("\n"):
            print(f"    {line}")
    if result.returncode != 0 and result.stderr.strip():
        for line in result.stderr.strip().split("\n"):
            print(f"    [!] {line}")
    print()
    return result.returncode


# ─────────────────────────────────────────────────────────────
# STEP 1: INSTALL
# ─────────────────────────────────────────────────────────────

section("STEP 1: Install StartQ")

print("  StartQ is a pip package with zero dependencies.")
print("  It uses only Python's standard library.")
print()
print("  Install it:")
print()
print("    pip install startq")
print()
print("  That's it. No API keys. No accounts. No cloud setup.")
print()


# ─────────────────────────────────────────────────────────────
# STEP 2: INITIALIZE
# ─────────────────────────────────────────────────────────────

section("STEP 2: Initialize Your Project")

print("  Navigate to your project directory and run:")
print()
print("    startq init")
print()
print("  This creates a .startq/ directory:")
print()
print("    .startq/")
print("    ├── brain/          # Session memory storage")
print("    ├── config.json     # Your identity + daemon config")
print("    └── state.json      # Initialization timestamp")
print()
print("  The brain/ folder is where StartQ stores your session")
print("  context as signed JSON files.")
print()
print("  Optional: Edit .startq/config.json to set your identity:")
print()
print('    {')
print('      "identity": "your-name",')
print('      "role": "ai-operator",')
print('      "daemons": {}')
print('    }')
print()


# ─────────────────────────────────────────────────────────────
# STEP 3: BOOT A SESSION
# ─────────────────────────────────────────────────────────────

section("STEP 3: Boot a Session")

print("  At the start of every AI work session, run:")
print()
print("    startq boot")
print()
print("  What happens:")
print("    1. Health check — verifies .startq/brain/ exists and is writable")
print("    2. Config load  — reads your identity from config.json")
print("    3. Context load — finds the most recent session receipt")
print("    4. Signature verify — SHA-256 hash check on the receipt")
print("    5. Session ID   — generates a new UUID for this session")
print("    6. Daemon spawn — starts any background scripts from config")
print()
print("  If a previous session exists, its context is loaded and")
print("  available to your AI agent. No re-explaining needed.")
print()
print("  If the signature check fails (file was tampered with),")
print("  StartQ will warn you and skip that session's context.")
print()


# ─────────────────────────────────────────────────────────────
# STEP 4: WORK
# ─────────────────────────────────────────────────────────────

section("STEP 4: Do Your Work")

print("  Work normally with your AI agent. Use Claude, Cursor,")
print("  Antigravity, Gemini CLI, or any tool you want.")
print()
print("  StartQ is not running in the background during this step.")
print("  It only activates on boot and end.")
print()


# ─────────────────────────────────────────────────────────────
# STEP 5: END THE SESSION
# ─────────────────────────────────────────────────────────────

section("STEP 5: End the Session")

print("  When you're done working, save your session context:")
print()
print('    startq end -c "Refactored the auth module. Added JWT validation."')
print()
print("  What happens:")
print("    1. Your summary is captured as the session context")
print("    2. Git state is snapshotted (current branch + dirty files)")
print("    3. Everything is bundled into a session receipt")
print("    4. The receipt is SHA-256 signed for integrity")
print("    5. Written to .startq/brain/<session-uuid>.json")
print()
print("  The next time you run 'startq boot', this context")
print("  is loaded automatically. Your agent picks up where")
print("  you left off.")
print()


# ─────────────────────────────────────────────────────────────
# STEP 6: DAEMONS (OPTIONAL)
# ─────────────────────────────────────────────────────────────

section("STEP 6: Daemons (Optional)")

print("  Daemons are background scripts that launch on boot.")
print("  Think of them as systemd for your AI workflow.")
print()
print("  Edit .startq/config.json:")
print()
print('    {')
print('      "identity": "phil",')
print('      "role": "ai-operator",')
print('      "daemons": {')
print('        "file-watcher": "python3 watch_files.py",')
print('        "local-server": "python3 -m http.server 8080"')
print('      }')
print('    }')
print()
print("  On 'startq boot', each daemon command is spawned as")
print("  a detached background process. They run until you")
print("  kill them or end the session.")
print()


# ─────────────────────────────────────────────────────────────
# EXAMPLE: FULL WORKFLOW
# ─────────────────────────────────────────────────────────────

section("EXAMPLE: Full Workflow")

print("  Day 1:")
print("    $ cd my-project")
print("    $ startq init")
print("    $ startq boot")
print("    ... work with AI agent all day ...")
print('    $ startq end -c "Built the API routes. Need to add auth tomorrow."')
print()
print("  Day 2:")
print("    $ cd my-project")
print("    $ startq boot")
print("    --> Previous context loaded: 'Built the API routes. Need to add auth tomorrow.'")
print("    --> Agent has full context. No re-explaining.")
print("    ... work with AI agent ...")
print('    $ startq end -c "Auth complete. JWT + refresh tokens. Deploy next."')
print()
print("  Day 3:")
print("    $ cd my-project")
print("    $ startq boot")
print("    --> Previous context loaded: 'Auth complete. JWT + refresh tokens. Deploy next.'")
print("    --> Zero amnesia. Agent knows exactly where you are.")
print()


# ─────────────────────────────────────────────────────────────
# EXAMPLE: USING WITH DIFFERENT AI TOOLS
# ─────────────────────────────────────────────────────────────

section("USING WITH DIFFERENT AI TOOLS")

print("  StartQ works with any AI agent or tool.")
print("  Point your agent to .startq/brain/ for shared context.")
print()
print("  Claude Code:")
print("    Just run 'startq boot' before starting Claude Code.")
print("    Run 'startq end -c \"summary\"' when done.")
print()
print("  Cursor:")
print("    Same pattern. Boot, work, end.")
print("    Add .startq/ to your project so Cursor can see it.")
print()
print("  Antigravity:")
print("    Same pattern. StartQ saved my work when Antigravity")
print("    pushed an update that wiped other developers' state.")
print()
print("  Custom scripts:")
print("    Read .startq/brain/*.json in your Python scripts:")
print()
print("    import json")
print("    from pathlib import Path")
print("    sessions = sorted(Path('.startq/brain').glob('*.json'))")
print("    if sessions:")
print("        latest = json.loads(sessions[-1].read_text())")
print("        print(latest['context'])")
print()


# ─────────────────────────────────────────────────────────────
# HOW THE BRAIN WORKS
# ─────────────────────────────────────────────────────────────

section("HOW THE BRAIN WORKS")

print("  Each session receipt is a JSON file in .startq/brain/:")
print()
print('    {')
print('      "session_id": "a1b2c3d4-...",')
print('      "timestamp": "2026-05-19T03:00:00+00:00",')
print('      "context": "Your session summary goes here.",')
print('      "hibernation_state": {')
print('        "branch": "main",')
print('        "modified_files": ["M src/auth.py", "A tests/test_auth.py"]')
print('      },')
print('      "signature": "sha256-hash-of-the-above-fields"')
print('    }')
print()
print("  The signature is computed by:")
print("    1. Serialize the payload (without signature) as sorted JSON")
print("    2. SHA-256 hash the bytes")
print("    3. Store the hex digest as 'signature'")
print()
print("  On boot, StartQ recalculates the hash and compares.")
print("  If they don't match, the file was tampered with and")
print("  its context is rejected.")
print()


# ─────────────────────────────────────────────────────────────
# FAQ
# ─────────────────────────────────────────────────────────────

section("FAQ")

print("  Q: Does StartQ need an internet connection?")
print("  A: No. Everything is local. No cloud, no API keys.")
print()
print("  Q: Does it work on Windows?")
print("  A: Yes. Python 3.8+ on any OS.")
print()
print("  Q: Can I use it with multiple projects?")
print("  A: Yes. Run 'startq init' in each project directory.")
print("     Each project gets its own .startq/brain/.")
print()
print("  Q: Should I commit .startq/ to git?")
print("  A: Your choice. It contains no secrets by default.")
print("     Committing it means your team shares context.")
print("     Adding it to .gitignore keeps it personal.")
print()
print("  Q: How much disk space does it use?")
print("  A: Each session receipt is ~1KB. Even 1000 sessions")
print("     would be about 1MB.")
print()
print("  Q: Can multiple AI tools share the same brain?")
print("  A: Yes. That's the point. Any tool that can read")
print("     JSON files can access .startq/brain/.")
print()


if __name__ == "__main__":
    print("\n  StartQ — The Operational Layer for AI")
    print("  Built in Seattle by Phil Hills")
    print("  https://github.com/Phil-Hills/startq")
    print()
