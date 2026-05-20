<div align="center">

<br>

# StartQ

**Never lose your AI work again.**

[![PyPI](https://img.shields.io/pypi/v/startq?color=0969da&label=PyPI&style=flat-square)](https://pypi.org/project/startq/)
[![Python](https://img.shields.io/pypi/pyversions/startq?color=0969da&style=flat-square)](https://pypi.org/project/startq/)
[![License](https://img.shields.io/badge/License-MIT-0969da?style=flat-square)](LICENSE)
[![Dependencies](https://img.shields.io/badge/Dependencies-Zero-2da44e?style=flat-square)]()

```
pip install startq
```

<br>

</div>

## Your AI Workflow Is a Computer. Boot It Like One.

When you turn on your PC, the BIOS runs, the OS loads your settings, and your last session comes back exactly where you left it. When you shut down, the OS saves your state so tomorrow picks up clean.

Your AI workflow should work the same way.

You have API connections, database credentials, multiple AI models, agent scripts, deployment pipelines, live services. You have context: decisions made yesterday, bugs found last week, architecture from last month. Every time you start a new AI session, all of that is gone.

**StartQ fixes that.**

```
StartQ              AutoQ               EndQ
POWER ON            MONITORING          SHUTDOWN

Health check        Record actions      Save chat session
Load last chat      Track decisions     Convert to JSONL
Verify signatures   Log milestones      Git snapshot
Spawn daemons       Search history      Sign receipt

Ready               Running             Saved
```

Three Python scripts. Zero dependencies. Pure standard library.

---

## Quick Start

```bash
pip install startq

startq init                                    # Create local brain
startq boot                                    # Load previous context

startq record "Connected Stripe API" -t action
startq record "JWT over session cookies" -t decision
startq log                                     # View recordings

startq shutdown -c "Payment API complete."     # Save everything
```

EndQ captures your entire AI chat session, converts it to JSONL, and stores it locally. Tomorrow:

```bash
startq boot
# Context restored: "Payment API complete."
# Full chat transcript from yesterday loaded.
# Zero amnesia.
```

---

## Commands

| Command | Purpose | PC Equivalent |
|:--------|:--------|:-------------|
| `startq init` | Create local brain | Format disk |
| `startq boot` | Load context, spawn daemons | Power on |
| `startq record "msg"` | Log an activity | Write to journal |
| `startq log` | View recorded activities | Read logs |
| `startq end -c "msg"` | Quick session close | Sleep |
| `startq shutdown -c "msg"` | Full graceful shutdown | Hibernate |
| `startq upgrade` | Connect to cloud brain | Mount network drive |
| `startq status` | Show current state | System info |

---

## Recording Categories

```bash
startq record "Fixed the auth bug"                -t action
startq record "Using JWT over session cookies"     -t decision
startq record "Token refresh fails after 30 min"   -t bug
startq record "MVP complete"                       -t milestone
startq record "Maybe add WebSocket support"        -t idea
```

| Category | Flag | Use For |
|:---------|:-----|:--------|
| `note` | *(default)* | General observations |
| `action` | `-t action` | Things you did |
| `decision` | `-t decision` | Choices and rationale |
| `bug` | `-t bug` | Issues found |
| `milestone` | `-t milestone` | Significant completions |
| `idea` | `-t idea` | Future possibilities |

---

## Cloud Sync

```bash
startq upgrade --url https://your-brain.run.app --key sk-xxx

startq boot             # auto-pulls from cloud
startq shutdown -c "..." # auto-pushes to cloud
startq boot --local      # force local-only
```

---

## How It Works

```
.startq/
  brain/                Signed session receipts (JSON)
    a1b2c3d4.json       Session from yesterday
    e5f6g7h8.json       Session from today
  sessions/             Saved chat transcripts (TXT)
    2026-05-19_0830_a1b2.txt
    2026-05-20_2200_c3d4.txt
  recordings/           Activity logs (JSONL)
    2026-05-19.jsonl
    2026-05-20.jsonl
  config.json           Identity + daemons + cloud
  state.json            Init timestamp
```

**Chat sessions are saved automatically.** When you run `startq shutdown`, EndQ finds your current AI chat (Antigravity IDE, Claude Code, or any IDE that stores conversation logs), saves the full transcript as a `.txt` file, and embeds a checksum in the signed receipt. On next `startq boot`, your last session context is restored so you pick up exactly where you left off.

**Session receipts** are SHA-256 signed. On boot, StartQ recalculates the hash. If it does not match, the session was tampered with and its context is rejected.

**Recordings** are append-only JSONL files, one per day. Override `SessionRecorder.write_record()` to store anywhere: database, REST API, flat text, whatever format works for you.

---

## Add to Antigravity IDE Workflows

If you use Antigravity IDE, add StartQ as a workflow so it runs automatically every session. Drop this in `.agent/workflows/startq.py`:

```python
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
```

Even if Antigravity pushes an update mid-session, your state is already persisted locally with cryptographic signatures.

---

## Why This Exists

On May 19, 2026, a major AI IDE pushed an update that wiped environment state for developers mid-session. Workflows deleted. Context gone. Hours of work lost.

The developer who built StartQ did not lose anything. Session state was already persisted locally with cryptographic signatures before the update hit.

> StartQ is insurance for your AI workflow. Your context survives IDE crashes, model swaps, environment resets, and cloud outages.

---

## Architecture

| File | Purpose | Lines |
|:-----|:--------|:------|
| `startq/brain.py` | Local persistence + cloud sync | ~180 |
| `startq/autoq.py` | Session recorder | ~140 |
| `startq/endq.py` | Shutdown + transcript saving | ~280 |
| `startq/cli.py` | Command-line interface | ~280 |
| `startq/cloud_brain.py` | Optional REST client for cloud | ~130 |

Read the source in 10 minutes. Fork and customize in 20. These are just Python scripts.

---

## Works With Everything

StartQ is tool-agnostic:

**Claude Code** / **Cursor** / **Antigravity IDE** / **Gemini CLI** / **Custom scripts**

---

## Contributing

```bash
git clone https://github.com/Phil-Hills/startq.git
cd startq
pip install -e .
python -m pytest tests/
```

Contributions welcome. See `CONTRIBUTING.py` for guidelines.

---

<div align="center">

**License: MIT**

Built in Seattle by [Phil Hills](https://github.com/Phil-Hills)

**Let's make sure no developer ever loses their work again.**

```
pip install startq
```

</div>
