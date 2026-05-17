---
name: adaptive-cortex-v2
version: 1.0
description: |
  Adaptive Cortex v2 — real-time personalized learning system.
  Makes the agent smarter with every interaction by adapting to user patterns,
  optimizing tool selection, and refining reasoning strategies.
trigger: |
  When the user asks for cortex optimization, adaptive learning setup,
  or real-time personalization configuration.
---

# Adaptive Cortex v2

## Overview
The Adaptive Cortex is a real-time learning layer that sits between the agent's
core loop and its knowledge base. It personalizes behavior based on:
- User communication patterns
- Task type preferences
- Tool success history
- Error recovery patterns

## Components
1. **Pattern Recognizer**: Identifies recurring user behaviors
2. **Strategy Optimizer**: Selects best approach per task type
3. **Error Predictor**: Anticipates failures before they happen
4. **Context Sculptor**: Adapts context injection per domain

## Integration Points
- Hooks into `pre_llm_call` for context adaptation
- Hooks into `post_tool_call` for outcome learning
- Reads from `cortex.db` and `cerebrum_memory.db`
- Writes to `adaptive_eval.db` for metrics

## Activation
```python
from agent.adaptive_cortex import get_instance
 cortex = get_instance(session_id)
 hint = cortex.build_injection(context)
```

## Key Files
- `~/hermes-agent/agent/adaptive_cortex.py` — Core implementation
- `~/.hermes/adaptive_eval.db` — Evaluation metrics
- `~/.hermes/cortex.db` — Cortex state
