# testing-gym-validation-injection-pipeline

*Researched: 2026-04-15 20:43 CDT*

# Testing Gym Validation: Injection Pipeline is the Bottleneck

## Date: 2026-04-15

## Executive Summary
The distillation pipeline (Experience→Distill→Store→Retrieve→Inject→Perform) has a broken Retrieve→Inject step. 92.1% of active tips (466/506) are NEVER injected into agent context. R34-R113 modules produce tips that sit dormant in Cortex.

## Key Metrics
- Active tips: 506
- Tips ever accessed: 40 (7.9%)
- Tips never accessed: 466 (92.1%)
- Module variables live: 220/235
- Modules with build_injection: 11/237 (4.7%)
- LLM eval success rate: 0%
- Self-improvement tips in P2: 0 (domain mismatch)
- P1 exploration pool: 437 tips with low access

## Bugs Fixed
1. P2 domain query: `self-improvement` → `training` + `meta` (canonical domains)
2. P1.5 exploration: ε-greedy injection of 2 random under-accessed tips
3. Metacog insertion domain: `self_improvement` → `training`
4. 9 high-quality self_improvement tips reactivated as training domain

## Root Cause
hybrid_search + entity extraction returns the same high-confidence tips every turn. _MAX_INJECT=8 caps injection space, leaving no room for new tips. Popularity bias means well-matched tips always win, new tips never get exposure.

## Next Steps
1. Increase _MAX_INJECT from 8 to 12-15
2. Add exploration ratio metric to track diversity
3. Fix LLM evaluation pipeline (0% success → tips lose elo → get deactivated)
4. Test injection diversity with live agent tasks
5. Consider Thompson Sampling for tip selection instead of pure exploitation

## Sources

- internal://cortex_db
- internal://testing_gym.py
- internal://distillation_plugin
