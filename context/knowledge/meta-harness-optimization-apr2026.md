# Meta-Harness: Optimizing Agent Runtime Without Retraining

## Summary
The Meta-Harness approach (Lee et al. 2026, arXiv:2603.28052, Finn+Khattab) and its open-source implementations:
- **canvas-org/meta-agent**: General framework, 67% → 87% on tau-bench v3
- **howdymary/hermes-agent-metaharness**: Hermes-specific outer loop

## Key Results
- **tau-bench v3 airline**: 67% → 87% holdout accuracy (canvas-org/meta-agent)
- **TerminalBench-2**: 27.5% → 35.5% (Meta-Harness paper, hand-engineered)

## Hermes-Specific Architecture (howdymary/hermes-agent-metaharness)

### Two-Layer Split
- **hermes-agent** (inner): candidate protocol, benchmark integration, loop hooks, archive writing
- **hermes-agent-metaharness** (outer): candidate evaluation, archive analysis, baseline reuse, frontier tracking, mutation/search

### Built-in Mutations (from mutation.py)
1. **plan_briefly**: Prepend planning reminder ("Start with a short plan, then act")
2. **verify_before_finish**: Prepend verification reminder ("run the smallest relevant verification step")
3. **terminal_first**: Prioritize terminal/shell tools earlier in tool list
4. **no_todo**: Hide todo-style tools to reduce overhead on short tasks
5. **shorter_loop**: Cap rollout to fewer turns (delta=-6, cap=24)

### Mutation Dimensions
- `prompt_prelude`: Text prepended to user prompt
- `prioritize_tools`: Reorder tool list
- `exclude_tools`: Remove specific tools
- `max_turns_delta`: Adjust turn limit (+/-)
- `max_turns_cap`: Hard cap on turns

### Frontier Store (from frontier.py)
- JSON-backed with cross-platform file locking (filelock)
- Atomic saves via temp file + rename
- `upsert_from_summary()`: Insert or update from run summary
- `best_for_benchmark()`: Return best entry by pass rate
- `top_for_benchmark()`: Ranked entries with filter by status + task_selection_hash

### Search Loop (from search.py)
1. Generate variant candidates from seed + mutations
2. Resolve baseline (fresh run or reuse from frontier)
3. For each mutation variant:
   - Run benchmark through Hermes
   - Build comparison report (baseline vs candidate)
   - Upsert to frontier with pass_rate_delta + net_task_gain
4. Return SearchSummary with all trial results

## Key Principles
1. **One change per iteration** — enables attribution
2. **Holdout validation** — prevents overfitting
3. **Filesystem memory** — persistent candidate archive
4. **Smallest effective fix** — prefer minimal changes
5. **Deterministic mutations** — reproducible experiments

## Relevance to Our Distillation System
Our distillation plugin is Level 1 (tip injection). The meta-harness shows:
- Level 1: Tip injection (current) — behavioral nudges via pre_llm_call
- Level 2: Config optimization — prompt additions, tool ordering, stop heuristics
- Level 3: Code-level harness modification — hooks, error handling, subagents

### Directly Applicable Ideas
1. The 5 built-in mutations map to things our distillation COULD optimize
2. Frontier store pattern → our distilled_tips table is similar but lacks versioning/comparison
3. Baseline reuse → we should compare tip sets before/after changes
4. Comparison reports with pass_rate_delta → we need per-tip impact metrics

## Distilled Tips (4 added to cerebrum)
1. Optimize harness before model (conf: 0.88)
2. Use holdout validation for changes (conf: 0.86)
3. Make one targeted change per iteration (conf: 0.84)
4. Preserve structure of failure feedback (conf: 0.85)

## Sources
- Paper: https://arxiv.org/abs/2603.28052
- General repo: https://github.com/canvas-org/meta-agent
- Hermes-specific: https://github.com/howdymary/hermes-agent-metaharness
- Mary's thread: https://x.com/howdymerry/status/2041616469084270917
- Teknium endorsement: https://x.com/teknium/status/2041732470996136236
