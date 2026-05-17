---
name: multi-agent-collaboration
title: Multi-Agent Collaboration and Profile Management
description: |
  Set up and manage multiple Hermes Agent instances for parallel autonomous work.
  Covers profile-based teams, twin agents for long-running collaboration, tmux
  coordination, and shared filesystem communication patterns.
triggers:
  - When setting up multiple Hermes agents for parallel work
  - When spawning a twin agent for extended collaboration
  - When coordinating agent teams with different specializations
  - When the user says "multi-agent", "twin", "parallel agents", "agent team"
category: software-development
---

# Multi-Agent Collaboration

## Overview

Hermes supports running multiple agent instances simultaneously — either as specialized
profiles with distinct roles, or as twin agents sharing the same environment for
extended collaborative work.

---

## Section 1: Profile-Based Agent Teams

### Overview

Use `hermes profile create` to spawn multiple independent Hermes agents, each with a
specialized role. They run in parallel in tmux sessions, coordinated by a central
orchestrator (the default profile running the gateway).

### Creating Profiles

```bash
# Create specialized profiles (cloned from default for shared API keys)
hermes profile create soma-coder --description "SOMA frontend/backend developer"
hermes profile create soma-researcher --description "Medical content researcher"
hermes profile create soma-tester --description "QA and testing specialist"
```

### Profile Configuration

Each profile gets its own directory under `~/.hermes/profiles/`:
```
~/.hermes/profiles/
├── default/          # Original profile
├── soma-coder/       # Frontend/backend dev
│   ├── SOUL.md
│   ├── config.yaml
│   └── skills/
├── soma-researcher/  # Medical content
│   ├── SOUL.md
│   ├── config.yaml
│   └── skills/
└── soma-tester/      # QA specialist
    ├── SOUL.md
    ├── config.yaml
    └── skills/
```

### Running in tmux

```bash
# Start each agent in a tmux window
tmux new-session -d -s hermes-team -n gateway "hermes gateway run"
tmux new-window -t hermes-team -n coder "hermes profile use soma-coder && hermes agent run"
tmux new-window -t hermes-team -n researcher "hermes profile use soma-researcher && hermes agent run"
tmux new-window -t hermes-team -n tester "hermes profile use soma-tester && hermes agent run"

# Attach to monitor
tmux attach -t hermes-team
```

### Communication Patterns

Agents communicate through:
- **Shared filesystem** — `/tmp/hermes-shared/` for data exchange
- **Gateway API** — REST endpoints for status and results
- **Database** — Shared SQLite/Postgres for state synchronization

---

## Section 2: Twin Agent Collaboration

### Overview

Spawn a second Hermes Agent as an autonomous twin for extended collaborative work.
Both agents share the same environment (API keys, config, filesystem) but run in
separate processes with isolated conversation contexts.

### When to Use

- Long debugging sessions where the user needs to step away
- Parallel workstreams (one agent researches, one implements)
- Tasks requiring days of autonomous effort
- Complex problems benefiting from two perspectives

### Spawning a Twin

```bash
# In a new terminal/tmux window
tmux new-window -t hermes-team -n twin "hermes agent run --twin"

# Or via script
hermes twin spawn --role "debugging partner" --focus "backend API issues"
```

### Communication

Twins communicate through shared `/tmp/` files:
```python
# Agent A writes status
with open('/tmp/twin_status.json', 'w') as f:
    json.dump({'task': 'debugging', 'progress': 0.5, 'findings': [...]}, f)

# Agent B reads and responds
with open('/tmp/twin_status.json') as f:
    status = json.load(f)
```

### Isolation vs Sharing

| Aspect | Shared | Isolated |
|--------|--------|----------|
| API keys | ✅ Same config | — |
| Filesystem | ✅ Same files | — |
| Conversation | ❌ Separate | ✅ Independent context |
| Memory | ❌ Separate SOUL.md | ✅ Independent learning |
| Tools | ✅ Same toolset | — |

---

## Section 3: Coordination Patterns

### Leader-Follower

One agent (leader) coordinates, others execute:
```
Leader: "Research X, implement Y, test Z"
Researcher: Finds information → writes to /tmp/
Coder: Reads findings → implements → commits
Tester: Tests → reports results → leader decides next steps
```

### Peer Collaboration

Two agents work on the same problem from different angles:
```
Twin A: Debugs from frontend perspective
Twin B: Debugs from backend perspective
Both: Share findings, cross-validate solutions
```

### Pipeline

Agents process data in sequence:
```
Raw Data → Researcher (analysis) → Coder (implementation) → Tester (validation) → Output
```

## Pitfalls

- **Resource contention**: Multiple agents hitting the same API can trigger rate limits
- **File conflicts**: Concurrent writes to the same file require locking
- **Database locks**: SQLite WAL mode has issues with concurrent writes — use Postgres for multi-agent setups
- **Context pollution**: Don't share conversation history between agents — keep contexts isolated
- **Gateway bottleneck**: One gateway serving many agents can become a bottleneck — consider multiple gateway instances

## References

- `references/tmux-session-templates.md` — Ready-to-use tmux session configurations
- `references/shared-filesystem-protocol.md` — File-based communication patterns
- `references/profile-specialization-guide.md` — How to specialize profiles for different roles
