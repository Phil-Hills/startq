#!/usr/bin/env python3
"""
StartQ - The Operational Layer for AI
======================================
Never lose your AI chats or work again.

pip install startq

Your AI Workflow Is a Computer. Boot It Like One.
--------------------------------------------------

Think about what happens when you turn on your PC.

The BIOS runs. It checks the hardware. The OS loads drivers,
mounts disks, reads your settings, restores your last session.
Everything comes back exactly where you left it. Then you work.
Then you shut down - the OS saves your state so tomorrow picks
up clean.

Now think about your AI development workflow.

You have API connections. Database credentials. Multiple AI models.
Agent scripts, deployment pipelines, live services, project configs.
You have context - decisions made yesterday, bugs found last week,
architecture from last month.

Every time you start a new AI session, all of that is gone.

StartQ treats your AI workflow like a computer.

    StartQ              AutoQ               EndQ
    POWER ON            MONITORING          SHUTDOWN
    |                   |                   |
    +- Health check     +- Record actions   +- Capture state
    +- Load context     +- Track decisions  +- Git snapshot
    +- Verify sigs      +- Log milestones   +- Sign receipt
    +- Spawn daemons    +- Search history   +- Sync to cloud
    |                   |                   |
    v                   v                   v
    Ready               Running             Saved

Three Python scripts. Zero dependencies. Pure standard library.

Quick Start
-----------

    pip install startq

    startq init                                  # Create local brain
    startq boot                                  # Load previous context
    startq record "Connected Stripe API" -t action
    startq record "JWT over session cookies" -t decision
    startq log                                   # View recordings
    startq shutdown -c "Payment API complete."   # Save everything

Tomorrow:

    startq boot
    # Context restored: "Payment API complete."
    # Zero amnesia.

Commands
--------

    startq init          Create local brain            (Format disk)
    startq boot          Load context, spawn daemons   (Power on)
    startq record "msg"  Log an activity               (Write to journal)
    startq log           View recorded activities       (Read logs)
    startq end -c "msg"  Quick session close            (Sleep)
    startq shutdown      Full graceful shutdown          (Hibernate)
    startq upgrade       Connect to cloud brain         (Mount network drive)
    startq status        Show current state              (System info)

Recording Categories
--------------------

    startq record "Fixed the auth bug"                -t action
    startq record "Using JWT over session cookies"    -t decision
    startq record "Token refresh fails after 30 min"  -t bug
    startq record "MVP complete"                      -t milestone
    startq record "Maybe add WebSocket support"       -t idea

Cloud Sync (v0.3.0)
--------------------

    startq upgrade --url https://your-brain.run.app --key sk-xxx
    startq boot          # auto-pulls from cloud
    startq shutdown -c "..." # auto-pushes to cloud
    startq boot --local  # force local-only

How It Works
------------

    .startq/
    +-- brain/              Signed session receipts (JSON)
    |   +-- a1b2c3d4.json   Session from yesterday
    |   +-- e5f6g7h8.json   Session from today
    +-- recordings/         Activity logs (JSONL)
    |   +-- 2026-05-19.jsonl
    |   +-- 2026-05-20.jsonl
    +-- config.json         Identity + daemons + cloud
    +-- state.json          Init timestamp

Session receipts are SHA-256 signed. On boot, StartQ recalculates
the hash. If it doesn't match, the session was tampered with and
its context is rejected.

Recordings are append-only JSONL files. Override write_record()
and read_records() in SessionRecorder to store anywhere you want:
database, REST API, flat text, whatever format works for you.

Why This Exists
---------------

On May 19, 2026, a major AI IDE pushed an update that wiped
environment state for developers mid-session. Workflows deleted.
Context gone. Hours of work lost.

The developer who built StartQ didn't lose anything. Because
session state was already persisted locally with cryptographic
signatures before the update hit.

StartQ is insurance for your AI workflow.

Architecture
------------

    startq/brain.py       Local persistence + cloud sync       ~180 lines
    startq/autoq.py       Session recorder                     ~140 lines
    startq/endq.py        Graceful shutdown with signing        ~120 lines
    startq/cli.py         Command-line interface                ~250 lines
    startq/cloud_brain.py Optional REST client for cloud brains ~130 lines

Read the source in 10 minutes. Fork and customize in 20.

Works With Everything
---------------------

    Claude Code, Cursor, Antigravity, Gemini CLI, custom scripts.
    StartQ is tool-agnostic. Use it with anything.

Add to Antigravity IDE Workflows
---------------------------------

If you use Antigravity IDE, add StartQ as a workflow so it runs
automatically at the start and end of every session. Create a
workflow file at .agent/workflows/startq.py in your project:

    # .agent/workflows/startq.py
    #
    # Before starting any session:
    #   1. pip install startq (if not installed)
    #   2. startq init (first time only)
    #   3. startq boot
    #
    # Before ending any session:
    #   1. startq shutdown -c "summary of what happened"
    #
    # To record important decisions mid-session:
    #   startq record "your note here" -t decision

This way your agent automatically loads previous context on boot
and saves everything on shutdown. No manual steps. No lost work.
Even if Antigravity pushes an update mid-session, your state is
already persisted locally with cryptographic signatures.

Contributing
------------

    git clone https://github.com/Phil-Hills/startq.git
    cd startq
    pip install -e .
    python -m pytest tests/

Contributions welcome. Run CONTRIBUTING.py for guidelines.

License: MIT
Built in Seattle by Phil Hills
https://github.com/Phil-Hills/startq

Let's make sure no developer ever loses their work again.
"""


def main():
    print(__doc__)
    print("Install:  pip install startq")
    print("Docs:     python README.py")
    print("Source:   https://github.com/Phil-Hills/startq")
    print()


if __name__ == "__main__":
    main()
