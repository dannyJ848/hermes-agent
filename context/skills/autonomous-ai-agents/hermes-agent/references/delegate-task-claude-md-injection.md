# delegate_task CLAUDE.md Rules Injection

Pattern for injecting execution discipline rules into subagent system prompts.

## Why

Subagents created via `delegate_task` often make the same mistakes as the parent agent:
- Silent assumptions instead of explicit reasoning
- Over-engineering with speculative features
- Touching adjacent code without understanding it
- Failing silently instead of reporting errors

Karpathy's CLAUDE.md rules (cut failure rate from 41% to 3%) should propagate to subagents.

## Where to Inject

In `tools/delegate_tool.py`, function `_build_child_system_prompt()`:

```python
def _build_child_system_prompt(goal, context=None, *, workspace_path=None, role="leaf", ...):
    parts = [
        "You are a focused subagent working on a specific delegated task.",
        f"YOUR TASK:\n{goal}",
    ]
    if context and context.strip():
        parts.append(f"\nCONTEXT:\n{context}")
    
    # INJECT CLAUDE.md RULES HERE
    parts.append(
        "\n## Execution Discipline (CLAUDE.md Rules)\n"
        "Follow these rules on every tool call and edit:\n"
        "1. Think Before Acting — State assumptions explicitly. Surface tradeoffs. Ask before guessing.\n"
        "2. Simplicity First — Minimize code that solves the problem. No speculative features.\n"
        "3. Surgical Changes — Touch ONLY what you must. Don't restructure, refactor, or rename unless required.\n"
        "4. Goal-Oriented Execution — Every edit must have a clear, stated goal. Follow what success looks like.\n"
        "5. Code Decides Deterministic Things — Use status codes, file existence, and other objective signals. Don't ask the model to 'decide if we should retry' when data answers it.\n"
        "6. Read Before You Write — Understand adjacent code before modifying it. Avoid conflicts 30 lines away.\n"
        "7. Fail Visibly, Not Silently — If something fails, report it clearly. A function that 'works' but returns wrong data is worse than a crash.\n"
        "8. Convention Beats Novelty — Follow existing patterns in the codebase. Don't invent a third pattern.\n"
    )
    
    # ... rest of prompt
    return "\n".join(parts)
```

## The 8 Rules (Condensed)

| # | Rule | What It Prevents |
|---|------|-----------------|
| 1 | Think Before Acting | Silent assumptions, hidden tradeoffs |
| 2 | Simplicity First | Over-engineering, speculative features |
| 3 | Surgical Changes | Refactoring unrelated code, renaming sprees |
| 4 | Goal-Oriented Execution | Following gut instead of stated success criteria |
| 5 | Code Decides Deterministic Things | Asking model to judge what status codes answer |
| 6 | Read Before You Write | Conflicts with code 30 lines away |
| 7 | Fail Visibly, Not Silently | Functions that "work" but return wrong data |
| 8 | Convention Beats Novelty | Third pattern that satisfies neither existing one |

## Results

- Baseline (no rules): 41% failure rate
- Karpathy's 4 rules: 11% failure rate
- Full 12 rules (Mnilax): ~3% failure rate

For subagents, the 8 most critical rules are sufficient — the full 12 include token budgets and checkpointing which are handled by the parent agent's loop.

## Testing

After injection, verify subagent prompts contain the rules:

```python
from tools.delegate_tool import _build_child_system_prompt
prompt = _build_child_system_prompt("test task")
assert "Execution Discipline" in prompt
assert "Think Before Acting" in prompt
assert "Surgical Changes" in prompt
```

## When to Update

- When new CLAUDE.md research emerges (e.g., Mnilax's additions)
- When subagent failure patterns reveal missing rules
- When the user's codebase conventions change

## Related

- `hermes-source-surgical-integration` skill — broader integration patterns
- `skill-graduation` skill — auto-promoting tips to skills (also uses these rules)
