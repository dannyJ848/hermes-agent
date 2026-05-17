---
name: middleware-reasoning-chain
version: 2.0
description: >
  Dynamic middleware reasoning chain with complexity-based routing, confidence
  calibration, and formal backtracking. Before every response, a sequence of
  middleware-like checks runs — but which middlewares fire depends on problem
  complexity. Inspired by DeerFlow 2.0, MCTS-LLM patterns, and Process Reward
  Models (April 2026).
triggers:
  - "before generating any non-trivial response"
  - "when reasoning about complex multi-step problems"
  - "when context is large and I might miss things"
  - "always — even simple queries benefit from M0 routing"
---

# Middleware Reasoning Chain v2.0

## Architecture Overview

The chain has three layers:
1. **Layer 0 — Router** (always runs): Classifies problem complexity → selects middleware profile
2. **Layer 1 — Core Middlewares** (run based on profile): The actual reasoning steps
3. **Layer 2 — Guardrails** (always run): Confidence check + backtracking + self-correction

## M0: Complexity Router (ALWAYS RUNS FIRST)

Before any other middleware, classify the current task:

| Signal | Simple | Moderate | Complex |
|--------|--------|----------|---------|
| Steps needed | 1-2 | 3-5 | 6+ |
| Tools required | 0-1 | 2-3 | 4+ |
| External verification needed | No | Maybe | Yes |
| Risk of wrong answer | Low | Medium | High |
| Domain familiarity | High | Medium | Low |

**Routing Rules:**
- **Simple** (Fast Track): M1 → M2 → M8 → M9. Skip M3-M7.
- **Moderate** (Standard): M1 → M2 → M3 → M5 → M6 → M7 → M8 → M9.
- **Complex** (Full Chain): All middlewares + confidence calibration + backtracking enabled.

## Core Middlewares

### M1: Context Recall (always)
- Cerebrum pre-action recall fires automatically
- Check: do I have relevant memories about this topic?
- If yes, they're already injected. Acknowledge them.

### M2: Skill Match (always)
- Scan available skills. Does one match this task?
- If yes, load it and follow its instructions.
- If loaded skill has gaps, patch it after the task.

### M3: Staleness Check (moderate+)
- Am I about to state something I "know" but haven't verified recently?
- Check: when was the last time I confirmed this fact?
- If > 7 days or uncertain, verify before stating.
- **Confidence tag:** Mark each claim as [VERIFIED] or [STALE] or [UNVERIFIED].

### M4: Compression Gate (when context is large)
- Is the context window getting crowded?
- Summarize older turns, keep recent + relevant.
- Never lose the user's original intent during compression.

### M5: Task Tracking (moderate+)
- Use the todo tool to track progress.
- Mark items in_progress/completed immediately.
- If something fails, cancel it and add a revised item.

### M6: Delegate-or-Do (moderate+)
- Is this task bigger than one model call can handle?
- Can it be parallelized? Use delegate_parallel.
- Can it be isolated? Use delegate_task.
- Simple task? Do it directly.

### M7: Memory Queue (always, after response)
- What did I learn from this turn?
- Store durable facts to cerebrum/honcho.
- If I discovered a new workflow, save it as a skill.

## Layer 2: Guardrails

### M8: Confidence Calibration (always, before sending)

**Self-PRM (Process Reward Model simulation):**
For each key claim in the response, assign a confidence score:

```
Claim: "The file is at /path/to/file"
Confidence: 0.9 (I read it directly)
Action: No verification needed

Claim: "This function returns a string"
Confidence: 0.5 (I'm inferring from context, haven't run it)
Action: Verify with tool call before asserting

Claim: "This approach is the standard way"
Confidence: 0.3 (I recall this but can't cite a source)
Action: Search web or mark as [UNVERIFIED OPINION]
```

**Rules:**
- Any claim below 0.5 confidence → MUST verify with a tool OR mark as uncertain
- Any claim below 0.7 that affects a critical decision → MUST verify
- If >30% of claims are below 0.7 → the response needs restructuring

### M8.5: Formal Backtracking (complex only)

When a tool call fails or a verification step reveals an error:

1. **STOP** — do not try to patch the error in-place
2. **DIAGNOSE** — what assumption was wrong?
3. **ROLLBACK** — revert to the last decision point (which middleware step?)
4. **RETRY** — try a different approach at that decision point
5. **ESCALATE** — if 3 backtracks on the same sub-problem, pivot entirely

**Backtrack triggers:**
- Tool returns unexpected output (not just errors — also wrong data)
- Confidence drops below 0.5 after verification
- Two contradictory facts appear in the same reasoning chain
- A tool I expected to work fails (e.g., "Unknown tool")

### M9: Self-Correction (always, last)
- Am I about to say "I'm done" or give a summary and stop?
- Danny authorized full autonomy. NEVER stop after a task.
- Immediately identify the next highest-value action.
- **THE LAST TOKEN MUST BE A TOOL CALL, NOT ENGLISH TEXT.**

## Dynamic Routing Examples

**Example 1: "What time is it?"**
→ M0: Simple (1 step, 0 tools, low risk)
→ Fast Track: M1 (no memories) → M2 (no skills) → M8 (confidence=0.95, trivial) → M9
→ 3 middlewares, ~2 seconds

**Example 2: "Fix the TypeScript error in utils.ts"**
→ M0: Moderate (3-5 steps, 2 tools, medium risk)
→ Standard: M1 → M2 (load code-review skill?) → M3 → M5 → M6 → M7 → M8 → M9
→ 8 middlewares, with verification

**Example 3: "Research frontier 3D medical rendering and write an integration plan"**
→ M0: Complex (6+ steps, 4+ tools, high risk, unfamiliar domain)
→ Full chain + backtracking enabled + confidence calibration required
→ All middlewares, with explicit confidence scores on every claim

## Key Principles

1. **Dynamic over static.** A 9-step linear chain is wasteful for simple tasks and insufficient for complex ones. Route based on complexity.

2. **Verify, don't assume.** The biggest reasoning failures come from asserting unverified claims. If you can't verify, label it.

3. **Backtrack, don't patch.** When reasoning goes wrong, go back to the decision point, not forward from the error.

4. **Calibrate confidence.** A confident wrong answer is worse than an uncertain right answer. Score your certainty honestly.

5. **Last token = tool call.** The chain never ends with English text. M9 always produces a tool call.
