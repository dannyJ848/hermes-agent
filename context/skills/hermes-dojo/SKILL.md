---
name: hermes-dojo
version: 1.0
description: |
  Hermes Dojo — continuous self-improvement system. Analyzes past sessions,
  identifies improvement opportunities, and generates actionable training tips.
  Integrates with the Cerebrum/Cortex knowledge base for persistent learning.
trigger: |
  When the user asks for dojo analysis, session review, or improvement suggestions.
  When running daily autonomous cognitive optimization.
---

# Hermes Dojo

## Overview
The Dojo is a self-improvement engine that reviews past sessions, identifies patterns,
and generates actionable tips for the agent's learning apparatus.

## Key Functions
1. **Session Analysis**: Review past sessions for errors, inefficiencies, missed opportunities
2. **Tip Generation**: Convert insights into Cerebrum-compatible tips
3. **Skill Audit**: Check skill ecosystem health and suggest updates
4. **Performance Tracking**: Monitor tool success rates and delegation quality

## Usage
```bash
# Run dojo analysis on recent sessions
hermes dojo analyze --days=7

# Generate improvement tips
hermes dojo distill --target=tool_efficiency

# Audit skill health
hermes dojo skills --report
```

## Integration
- Reads from `~/.hermes/memory/` for session logs
- Writes to `~/.hermes/cerebrum_memory.db` for tips
- Updates `~/.hermes/skills/` when new patterns emerge

## Metrics Tracked
- Tool success/failure rates per tool
- Delegation quality scores per model
- Session completion rates
- Error pattern frequency
- Tip survival rates (upvotes/downvotes)
