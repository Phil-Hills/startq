# StartQ

> Your AI agents shouldn't boot from scratch.

Every time you start a new AI agent session, you repeat yourself. You re-explain the project. You re-paste the context. You hope the agent remembers what happened yesterday. It usually doesn't.

StartQ fixes that.

It is an operational layer that sits between you and your AI agents. When a session boots, StartQ verifies state, loads prior context from its persistent memory (the Brain), and enforces continuity. 

Think of it as **systemd for AI**.

## 60-Second Install

```bash
pip install startq
```

Initialize your persistent memory (Brain) in your project directory:

```bash
startq init
```

Boot your agent with context verification:

```bash
startq boot
```

When you are finished with your session, sync the persistent memory:

```bash
startq end
```

## Features

- **Local First**: Your Brain is a local JSON/SQLite object directory (`.startq/brain/`). No cloud dependencies.
- **Universal Agnosticism**: Compatible with Claude Code, Cursor, Antigravity, or custom agent networks. 
- **Zero Amnesia**: Cryptographic enforcement guarantees that state is preserved cleanly across sessions.

## License
MIT License. Built in Seattle.
