# StartQ

StartQ is a local-first session journal for AI-assisted development. It saves concise session context, records decisions and actions, captures useful Git state, and verifies receipt integrity when the next session starts.

[![PyPI](https://img.shields.io/pypi/v/startq?color=0969da&label=PyPI&style=flat-square)](https://pypi.org/project/startq/)
[![Python](https://img.shields.io/pypi/pyversions/startq?color=0969da&style=flat-square)](https://pypi.org/project/startq/)
[![License](https://img.shields.io/badge/License-MIT-0969da?style=flat-square)](LICENSE)

```bash
pip install startq
```

StartQ uses only the Python standard library at runtime.

## The workflow

```text
StartQ              AutoQ               EndQ
BOOT                 JOURNAL             SHUTDOWN

Verify receipts      Record actions      Save context
Load last summary    Track decisions     Capture Git state
Check local state    Search history      Capture transcript
Start daemons        Export records      Sign receipt
```

StartQ does not replace your model, IDE, or agent framework. It creates a small durable record around those tools so a fresh session has a trustworthy place to resume.

## Quick start

```bash
startq init
startq boot

startq record "Connected the payment API" -t action
startq record "Use JWT instead of session cookies" -t decision
startq log

startq shutdown -c "Payment API complete; integration tests remain."
```

The next `startq boot` verifies the newest receipt and restores its context summary.

## Commands

| Command | Purpose |
|---|---|
| `startq init` | Create `.startq/` and a local signing key |
| `startq boot` | Verify recent state and load the last context summary |
| `startq record "message"` | Append an activity to the session journal |
| `startq log` | Read, search, summarize, or export journal entries |
| `startq end -c "summary"` | Save a lightweight session receipt |
| `startq shutdown -c "summary"` | Save a full receipt with Git and available transcript metadata |
| `startq upgrade` | Configure an optional cloud Brain endpoint |
| `startq status` | Show local session and cloud configuration status |

Recording categories are `note`, `action`, `decision`, `bug`, `milestone`, and `idea`.

## Local storage

```text
.startq/
  brain/             Session receipts
  recordings/        Append-only daily JSONL journals
  sessions/          Captured chat transcripts, when available
  config.json        Non-secret configuration
  state.json         Initialization state
```

Add `.startq/` to your project's ignore rules. It can contain private prompts, decisions, source context, and credentials.

## Receipt integrity

StartQ 0.5 receipts use HMAC-SHA256 with a randomly generated 256-bit key stored in the current user's config directory, outside the workspace. On Linux and WSL this defaults to `~/.config/startq/keys/`; on Windows it uses `%LOCALAPPDATA%\\StartQ\\keys`. On boot, StartQ verifies the receipt before restoring its context. A modified receipt is rejected.

Receipts from StartQ 0.4 and earlier used an unkeyed SHA-256 digest. They are blocked by default because accepting one silently would permit a downgrade attack. To migrate a receipt you trust, run `startq boot --allow-legacy`, review the warning and restored summary, then close the session to create a new HMAC receipt. An unkeyed digest can detect accidental changes, but it does not authenticate the writer.

The HMAC design protects against receipt edits by a process that cannot read the signing key. It does not protect against an administrator or compromised process that can read both the receipts and key. Set `STARTQ_SIGNING_KEY_FILE` to an explicitly managed key path when moving a brain between machines or accessing one workspace from both Windows and WSL. Losing the key makes new-format receipts unverifiable.

## Transcript capture

`startq shutdown` can capture the most recent Antigravity IDE session when a supported local transcript is available. It stores a local text copy and includes its checksum and path in the receipt. StartQ boot restores the context summary; it does not inject the entire transcript into another model automatically.

Transcript capture reads local IDE state and may include sensitive prompts or source material. Review `.startq/sessions/` before sharing or syncing it.

## Optional cloud sync

```bash
startq upgrade --url https://your-brain.example.com
startq boot --cloud
startq shutdown -c "Session complete" --cloud
```

The API-key prompt does not echo. Keys are stored in the current user's config directory, not `config.json` or the workspace. Managed environments can set `STARTQ_CLOUD_API_KEY` instead. Set `STARTQ_CLOUD_KEY_FILE` to choose an explicit credential file. Passing `--key` remains supported for automation, but can expose the key in shell history or process listings.

The cloud endpoint is expected to implement the JSON operations documented by `startq/cloud_brain.py`. Cloud transport and server-side retention are controlled by that endpoint, not by StartQ.

## Use as a library

```python
from startq.autoq import SessionRecorder
from startq.brain import BrainManager

brain = BrainManager(".startq")
brain.init_brain()

recorder = SessionRecorder(".startq")
recorder.record("Selected PostgreSQL", category="decision")

brain.end_session("Database decision recorded")
```

See [examples](examples/) for custom storage and workflow patterns.

## Development

```bash
python -m unittest discover -v
python -m build
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

StartQ is MIT licensed. Built by [Phil Hills](https://github.com/Phil-Hills).
