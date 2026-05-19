---
name: multi-agent-profiles
description: Set up a team of specialized Hermes Agent profiles using hermes profiles. Each profile gets its own SOUL.md, memory, sessions, and skills but shares API keys. Spawn them in tmux for parallel autonomous work.
version: 1.0
---

# Multi-Agent Profile Setup

## Overview
Use `hermes profile create` to spawn multiple independent Hermes agents, each with a specialized role. They run in parallel in tmux sessions, coordinated by a central orchestrator (the default profile running the gateway).

## Step-by-Step

### 1. Create profiles (cloned from default for shared API keys)
```bash
cd ~/hermes-agent && source venv/bin/activate
hermes profile create agent-name --clone
```
Repeat for each agent. `--clone` copies config.yaml, .env, SOUL.md. Use `--clone-all` for full state including memory/sessions.

### 2. Copy custom skills to each profile
Bundled skills are synced automatically, but custom skills (in `~/.hermes/skills/software-development/`) are NOT. Copy them:
```bash
SRC=~/.hermes/skills/software-development
for profile in agent1 agent2 agent3; do
  DEST=~/.hermes/profiles/$profile/skills/software-development
  mkdir -p "$DEST"
  for skill in custom-skill-1 custom-skill-2; do
    [ -d "$SRC/$skill" ] && [ ! -d "$DEST/$skill" ] && cp -r "$SRC/$skill" "$DEST/"
  done
done
```

### 3. Write SOUL.md with shared foundation + role specialization
Each SOUL.md should start with the same base identity, then add a role-specific section. Pattern:
```
[Base Hermes identity paragraph — same for all agents]

---

## Your Role: [Role Name]

You are part of a multi-agent team building [project]. 

**Your specialty:** [what this agent does best]

**Your teammates:**
- agent1 — [role]
- agent2 — [role]
- default (orchestrator) — coordinates the team

**Key context:**
- [project-specific details]

Write progress/bugs/research to /tmp/[agent-name]-status.md
```

### 4. Set matching config values
```bash
for profile in agent1 agent2 agent3; do
  CFG=~/.hermes/profiles/$profile/config.yaml
  # Set memory limit to match default
  sed -i '' 's/memory_char_limit: .*/memory_char_limit: 4400/' "$CFG"
done
```

### 5. Spawn agents in tmux
```bash
tmux new-session -d -s agent1 "cd ~/hermes-agent && source venv/bin/activate && agent1 chat"
tmux new-session -d -s agent2 "cd ~/hermes-agent && source venv/bin/activate && agent2 chat"
tmux new-session -d -s agent3 "cd ~/hermes-agent && source venv/bin/activate && agent3 chat"
```
Note: profile name becomes a command alias at `~/.local/bin/<name>`.

### 6. Send initial tasks
```bash
sleep 5  # wait for startup
tmux send-keys -t agent1 "Your first task: [description]. Work autonomously." Enter
tmux send-keys -t agent2 "Your first task: [description]. Work autonomously." Enter
tmux send-keys -t agent3 "Your first task: [description]. Work autonomously." Enter
```

### 7. Monitor agents
```bash
tmux list-sessions                    # see all running
tmux capture-pane -t agent1 -p | tail -20  # peek at an agent
tmux attach -t agent1                 # watch live
```

### 8. Communication between agents
- Shared files in `/tmp/` (e.g., `/tmp/agent1-status.md`, `/tmp/soma-bugs/`)
- Orchestrator reads status files and sends new tasks via `tmux send-keys`
- Agents can also use `/tmp/` to hand off work items

## Example Team Layout
```
◆default          (orchestrator — runs gateway, coordinates team)
  soma-coder      (coding specialist — builds features, fixes bugs)
  soma-researcher (research specialist — competitor analysis, content)
  soma-tester     (QA specialist — browser testing, bug reports)
```

## Switching a Profile's Model (Hot-Swap)
```bash
# Edit the profile's config.yaml
sed -i '' 's/default: OLD_MODEL/default: NEW_MODEL/' ~/.hermes/profiles/PROFILE/config.yaml

# Kill the old session and relaunch
tmux send-keys -t SESSION C-c; sleep 1; tmux send-keys -t SESSION C-c; sleep 1
tmux send-keys -t SESSION "cd ~/hermes-agent && source venv/bin/activate && PROFILE chat" Enter

# Verify the new model shows in the status bar
sleep 5 && tmux capture-pane -t SESSION -p | tail -5
```

IMPORTANT: Test that the new model is available on your plan BEFORE switching a live agent. Do a quick API call first:
```bash
curl -s https://api.z.ai/api/coding/paas/v4/chat/completions \
  -H "Authorization: Bearer $GLM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"NEW_MODEL","messages":[{"role":"user","content":"ping"}],"max_tokens":5}' | head -5
```
If you get HTTP 429 / error 1311 ("subscription plan does not yet include access"), the model is gated behind a higher tier.

## Pitfalls
- Cloned profiles do NOT get custom skills — must copy manually (step 2)
- Each profile has INDEPENDENT memory — shared context must be in SOUL.md or /tmp/ files
- tmux sessions survive terminal disconnect but NOT machine restart
- Agent command aliases use the profile name directly: `soma-coder chat` not `hermes -p soma-coder chat`
- If an agent's tmux session dies, respawn: `tmux new-session -d -s agent1 "agent1 chat"`
- Sending tasks via `tmux send-keys` is fire-and-forget — no response back. Check status files.
- Model availability varies by subscription tier — GLM-5V-Turbo requires higher Z.AI plan (error 1311 on standard tier as of Apr 2026). Always test before switching.
