# self-corrective agent architecture patterns

*Researched: 2026-04-05 11:37 CDT*

# Self-Corrective Agent Architecture Patterns (2025 Survey)

## Canonical Two-Layer Pattern
1. **Primary (Task) Layer**: Encodes the plan–act loop. State = {Goal, Active Plan, Execution History}
2. **Secondary (Metacognitive) Layer**: Monitors primary layer, evaluates failure-risk signals at each step

## Failure Detection Triggers
- **Action repetition** — agent repeating the same action
- **Excessive latency** — taking too long on a step
- **Plan complexity** — overly complex plans that likely won't execute well
- **Rule-based and statistical triggers** — both approaches used

## When Failure Detected
1. Metacognitive layer interrupts primary execution
2. Triggers either: **recovery protocol** or **human handoff**
3. Provides **explainability trace** — reasoning + cause of failure

## Domain Validations
- Low-code/no-code agents
- Autonomous scientific coding
- Robotics
- Multi-agent collaborations
- Neuro-symbolic planning stacks

## Mapping to Evey's Architecture
| Survey Pattern | Evey Implementation |
|---|---|
| Primary (Task) Layer | Main agent loop (run_agent.py) |
| Secondary (Metacognitive) Layer | self_awareness.py + middleware-reasoning-chain |
| Action repetition detection | stop_detection_log (tracks text-only responses) |
| Excessive latency | watchdog_heartbeat (monitors silence) |
| Plan complexity | autonomous_plan (estimates complexity) |
| Recovery protocol | aggressive_continue (Layer 1 anti-stop) |
| Human handoff | proactive_nudge / telegram_card |
| Explainability trace | session_checkpoint + learn_from_interaction |

## Key Gap Identified
Our system has most components but the **metacognitive layer is not truly monitoring at each decision step** — it fires reactively (after failures) rather than proactively (predicting failures before they happen). The survey suggests evaluating failure indicators at EVERY action proposal, not just after errors.

**Improvement opportunity:** Add pre-action monitoring that evaluates proposed tool calls against historical failure patterns BEFORE execution.

**Source:** Emergent Mind survey aggregating Xu et al. (Sep 2025) and related work on self-corrective agent architectures.


## Sources

- https://www.emergentmind.com/topics/self-corrective-agent-architecture
