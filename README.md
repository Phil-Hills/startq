# StartQ

> A minimal CLI for persisting session context across AI agent runs.

Every time you start a new AI agent session, you repeat yourself. You re-explain the project. You re-paste the context. You hope the agent remembers what happened yesterday. It usually doesn't.

StartQ fixes that.

It is a lightweight command-line utility that persists session summaries locally. When a session boots, StartQ loads prior context from its local memory (the Brain).

## 60-Second Install

```bash
pip install startq
```

Initialize your local memory (Brain) in your project directory:

```bash
startq init
```

Boot your agent workflow:

```bash
startq boot
```

When you are finished with your session, sync the persistent memory:

```bash
startq end -c "Finished refactoring the database schemas."
```

## Features

- **Local First**: Your Brain is a local JSON object directory (`.startq/brain/`). No cloud dependencies, no lock-in.
- **Universal Agnosticism**: Point any agent (Claude Code, Cursor, Antigravity, or custom scripts) to the `.startq/` directory to share context across sessions.
- **Daemons (Systemd for AI)**: Add scripts to `.startq/config.json` under `"daemons"`, and StartQ will spawn them as detached background runners on boot.
- **Zero Dependencies**: Pure python standard library.

## License
MIT License. Built in Seattle.
