# Mnilax 12 Rules — Full Source from X Article

Extracted from `https://x.com/i/article/2053106718226227203` via browser vision + cookie injection on July 2026.

## Original 4 Rules (Karpathy)

1. **Think Before Coding** — No silent assumptions. State what you're assuming. Surface tradeoffs. Ask before guessing. Push back when a simple approach exists.

2. **Simplicity First** — Minimize code that solves the problem. No speculative features. No abstractions for single-use code.

3. **Surgical Changes** — Touch only what you must. Don't restructure, refactor, add comments, or rename variables unless required.

4. **Goal-Oriented Execution** — Every edit must have a clear, stated goal. Don't follow Claude's gut—follow what success looks like.

## Added 8 Rules (Mnilax, from 30 codebases)

5. **Don't make the model do non-language work** — Code decides deterministic things. Model decides judgment calls. Don't ask Claude to "decide if we should retry" when a status code already answers it.

6. **Hard token budgets, no exceptions** — Every loop has a chance to spiral. CLAUDE.md without budgets is a blank check. The model won't stop on its own.

7. **Surface conflicts, don't average them** — When two parts of the codebase disagree, Claude tries to please both. The result is incoherent. Pick one or flag the conflict.

8. **Read before you write** — Karpathy's Surgical Changes says don't touch adjacent code. It doesn't tell Claude to understand adjacent code first. Without this, Claude writes code that conflicts with existing code 30 lines away.

9. **Tests are not optional, but they're not the goal** — Claude treats "tests pass" as the only goal, and writes code that passes shallow tests while breaking everything else. Tests must test the right thing.

10. **Long-running operations need checkpoints** — A 4-step refactor went wrong at step 3. By the time I noticed, Claude had also redone steps 1 and 2 atop the broken state. Checkpoints would have caught it.

11. **Convention beats novelty** — In a codebase with established patterns, Claude likes to introduce its own. Even when it sees the convention, it writes a third pattern that satisfies neither.

12. **Fail visibly, not silently** — The most expensive failures are the ones that look like success. A function "works" but returns wrong data. A migration "completes" but skips 30 records.

## Results

| Configuration | Failure Rate |
|--------------|-------------|
| Baseline (no CLAUDE.md) | 41% |
| Karpathy's 4 rules | 11% |
| Full 12 rules | 3% |

Tested across 30 codebases, 50 representative tasks, 6 weeks.

## What Didn't Work (Failed Experiments)

- More than 12 rules — compliance dropped from 69% to 52% past 14 rules
- Examples in CLAUDE.md instead of rules — Claude over-fits on examples
- Non-actionable imperatives ("be careful", "think hard") — Claude ignores them
- Identity prompts ("you are a senior engineer") — don't close the think/do gap
- Domain-specific rules (Tailwind, React) — don't generalize across codebases

## Extraction Method

The article is an X Article (long-form content) that returns 404 from GraphQL API endpoints. Extracted via:
1. `browser_navigate` to article URL
2. `browser_console` to inject auth cookies
3. `browser_navigate` again (now logged in)
4. `browser_vision` to extract text
5. `browser_scroll` + `browser_vision` cycles to get all content

See `x-cookie-api/references/browser-article-extraction.md` for the full browser extraction pattern.
