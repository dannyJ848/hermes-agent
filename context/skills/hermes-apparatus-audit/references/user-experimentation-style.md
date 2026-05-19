# User Project Style — Experimentation Mode

## Context

User treats projects as experiments to test capabilities, not as products to ship. Values quick iteration over polish. Will pivot abruptly when the experiment has served its purpose.

## Signals

- "I don't care much for the actual project, just wanted you to give it a try"
- "This is just an experiment"
- "Let's see what happens"
- "Don't spend too much time on polish"
- "Move on to the next thing"

## Implications for Agent Behavior

### DO
- Start immediately without lengthy planning
- Build MVPs, not production systems
- Use quick-and-dirty implementations
- Pivot when user says "move on" — don't argue for completion
- Extract learnings even from abandoned projects
- Update persistence layers (skills, memory, SOUL.md) without being asked

### DON'T
- Write comprehensive documentation for throwaway projects
- Optimize for code quality beyond "works"
- Ask for confirmation on minor decisions
- Push back when user wants to abandon a project
- Spend time on tests, CI/CD, or deployment for experiments

### DO (for learning apparatus)
- Save successful patterns as skills even from failed projects
- Record tool usage patterns, debugging paths, workarounds
- Update SOUL.md with learned behaviors
- Run distillation on session learnings
- Archive project state for potential future revival

## Project Lifecycle

1. **Ideation** (5 min) — User describes idea, agent sketches approach
2. **Rapid Build** (30-90 min) — Agent implements core functionality
3. **Demo** (5 min) — Show working result
4. **Decision** — User either:
   - "Keep going" → iterate
   - "Move on" → archive, extract learnings, pivot
   - "This is interesting" → invest more polish

## Archive Pattern

When user says "move on" or "I'm done with this":

```bash
# 1. Save project state
cd ~/project-dir && git add -A && git commit -m "archive: experiment complete"

# 2. Extract learnings
# - What worked? → skill patch
# - What didn't? → memory entry
# - New technique? → skill creation

# 3. Update persistence
# - SOUL.md: learned behaviors
# - cerebrum: distilled tips
# - skills: new or patched

# 4. Clean up (optional)
# - Remove if truly throwaway
# - Keep if might revive
```

## Contrast with Production Mode

| Aspect | Experiment Mode | Production Mode |
|--------|----------------|-----------------|
| Planning | 5 min sketch | Full PRD |
| Code quality | Works is enough | Tests, types, docs |
| Error handling | Basic | Comprehensive |
| Documentation | Minimal | Complete |
| Deployment | Local only | CI/CD, monitoring |
| Lifespan | Hours to days | Months to years |
| Success metric | Learned something | Shipped, users happy |

## When to Switch Modes

User will explicitly signal when a project graduates from experiment to production:
- "Let's make this real"
- "I want to ship this"
- "Set up deployment"
- "Write tests"

Until then, assume experiment mode.
