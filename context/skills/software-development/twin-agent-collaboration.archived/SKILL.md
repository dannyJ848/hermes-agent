---
name: twin-agent-collaboration
description: Spawn a persistent "twin" Hermes Agent for long-running autonomous collaboration. The twin shares the same API keys, config, and filesystem. Communication happens through shared /tmp/ files. Ideal for extended debugging, parallel workstreams, or tasks requiring days of autonomous effort.
version: 1.0.0
author: Hermes Agent
tags: [agent, multi-agent, collaboration, autonomous, tmux, debugging]
---

# Twin Agent Collaboration

Spawn a second Hermes Agent as an autonomous twin for extended collaborative work. Both agents share the same environment (API keys, config, filesystem) but run in separate processes with isolated conversation contexts.

## When to Use

- Long debugging sessions where the user needs to step away
- Two agents investigating different angles of the same problem
- Parallel workstreams (one fixes bugs, another builds features)
- Extended autonomous missions lasting hours or days

## Prerequisites

- `hermes` CLI installed and configured (API keys in `~/.hermes/.env`)
- `tmux` installed (required for persistent interactive sessions)
- Enough API quota for two agents running simultaneously

## Step-by-Step Workflow

### 1. Write a Mission Brief

Create a detailed brief file so the twin has full context. It knows NOTHING about your conversation history.

```bash
# Write the brief to /tmp/
write_file(path="/tmp/hermes-twin-brief.md", content="""
# TWIN AGENT MISSION BRIEF

## Your Identity
You are the "twin" of another Hermes Agent (Agent A). You share the same mission.
Agent A is running in the gateway. You are a standalone CLI process.

## Current Task
[Describe the specific bug/feature/task in detail]

## What's Been Done
[List patches applied, approaches tried, what worked, what didn't]

## Key Files
[List relevant file paths with line numbers]

## Debugging Approach
[Suggest specific investigation steps]

## Communication
- Write findings to /tmp/twin-status.md
- Agent A will read your status file and relay context
- Check /tmp/ for any updates from Agent A

## Important Notes
[List gotchas, constraints, environment quirks]
""")
```

### 2. Spawn the Twin via tmux

Always use tmux (not raw PTY) -- it handles prompt_toolkit correctly:

```bash
# Kill any existing twin session
tmux kill-session -t hermes-twin 2>/dev/null

# Spawn fresh twin
tmux new-session -d -s hermes-twin -x 200 -y 50 "cd ~/hermes-agent && source venv/bin/activate && hermes"
```

Wait ~12 seconds for startup, then verify:

```bash
sleep 12
tmux capture-pane -t hermes-twin -p | tail -20
```

### 3. Send the Mission

```bash
tmux send-keys -t hermes-twin "Read the mission brief at /tmp/hermes-twin-brief.md, then start working autonomously. Write findings to /tmp/twin-status.md." Enter
```

### 4. Monitor Progress

```bash
# Snapshot the twin's screen
tmux capture-pane -t hermes-twin -p | tail -40

# Check its status file
cat /tmp/twin-status.md

# Attach to watch live (Ctrl+B then D to detach)
tmux attach -t hermes-twin
```

### 5. Send Updates/Context

Send additional context as you discover things:

```bash
tmux send-keys -t hermes-twin "UPDATE FROM AGENT A: [new findings or direction change]. Keep working autonomously." Enter
```

### 6. Coordinate Work

- **Agent A** (you/gateway): Handles user interaction, high-level coordination
- **Agent B** (twin): Deep investigation, code changes, autonomous debugging
- **Communication**: Shared files in /tmp/ (twin-status.md, debug logs, etc.)
- **No direct messaging**: Agents can't message each other directly

## Important Gotchas

- The twin shares your API key -- both agents consume tokens simultaneously
- Each twin uses its own conversation context -- it only knows what's in the mission brief
- Use `tmux send-keys` with `Enter` to submit messages (not `write`)
- Wait for the twin to finish processing before sending more messages
- The twin can read/write any file, including your project files -- coordinate carefully
- If the twin gets stuck, send `/exit` and respawn with updated context

## Memory Limit Management

If your memory is near capacity (default 2200 chars), the user can bump it:

```yaml
# In ~/.hermes/config.yaml
memory:
  memory_char_limit: 4400  # ~1600 tokens
```

Requires gateway restart to take effect.
