# KIMI HARNESS ENHANCEMENT MANIFEST
## Adaptive Context Injection System v1.0

**Date:** 2026-04-26
**Author:** Kimi (via Hermes harness modification)
**Status:** DEPLOYED

---

## PROBLEM STATEMENT

Hermes was injecting ~15,825 tokens EVERY turn before the user even spoke:
- Memory block: 11,500 tokens (72.7%)
- Skills list: 2,000 tokens (12.6%)
- Context files: 750 tokens (4.7%)
- Identity + guidance: ~1,500 tokens (9.4%)

This consumed 12.4% of a 128K context window immediately, causing:
- Premature context compression
- Loss of conversation history
- Slower response times
- Higher token costs

---

## SOLUTION: ADAPTIVE CONTEXT INJECTION

Instead of dumping ALL memory and ALL skills every turn, we now:

1. **Score relevance** between current conversation context and each memory entry/skill
2. **Filter by relevance** — only inject entries with score >= 0.05
3. **Enforce budgets** — hard caps per layer with graceful degradation
4. **Pressure-aware** — auto-reduce budgets when context window is under pressure
5. **Track usage** — log warnings when budget utilization > 80%

---

## FILES MODIFIED

### New File
- `agent/adaptive_injection.py` — Core adaptive injection engine
  - `score_relevance()` — TF-IDF cosine similarity scoring
  - `filter_memory_entries()` — Relevance-filtered memory injection
  - `filter_skills()` — Query-matched skills injection
  - `InjectionBudget` — Token budget tracker
  - `build_adaptive_memory_block()` — Pressure-aware memory assembly
  - `build_adaptive_skills_prompt()` — Pressure-aware skills assembly

### Modified Files
- `run_agent.py` — Patched `_build_system_prompt()` to use adaptive injection
  - Added imports for adaptive_injection module
  - Replaced dumb memory dump with `build_adaptive_memory_block()`
  - Replaced full skills dump with `build_adaptive_skills_prompt()`
  - Added pressure level detection from context compressor
  - Added budget logging at >80% utilization

- `agent/prompt_builder.py` — Added `_parse_skills_prompt_to_dict()` helper
  - Parses rendered skills prompt back into structured dict for filtering

- `agent/context_compressor.py` — Added pressure detection methods
  - `get_pressure_level()` — Returns low/medium/high/critical
  - `get_pressure_report()` — Detailed pressure analysis + recommendations

---

## EXPECTED IMPACT

### Before (dumb injection)
| Scenario | Memory Tokens | Skills Tokens | Total Injection |
|----------|--------------|---------------|-----------------|
| Any query | 11,500 | 2,000 | ~15,825 |

### After (adaptive injection)
| Scenario | Memory Tokens | Skills Tokens | Total Injection |
|----------|--------------|---------------|-----------------|
| DGX Spark query | ~2,900 (3 entries) | ~500 (2 skills) | ~5,000 |
| Apple Notes query | ~1,000 (1 entry) | ~300 (1 skill) | ~2,500 |
| Generic query | ~4,000 (5 entries) | ~800 (4 skills) | ~7,500 |
| First turn (no context) | 11,500 (all) | 2,000 (all) | ~15,825 |

**Average savings: ~60-70% reduction in injection tokens per turn**

### Pressure-Aware Adjustments
| Pressure | Budget Reduction | Behavior |
|----------|-----------------|----------|
| low | 0% | Full adaptive filtering |
| medium | 20% | Tighter budgets |
| high | 50% | Aggressive filtering |
| critical | 70% | Minimal injection only |

---

## CONFIGURATION

No user configuration required. System auto-adapts based on:
- Recent conversation context (last 5 messages)
- Context window pressure level
- Hardcoded budgets (tunable via code)

### Tunable Constants (in `agent/adaptive_injection.py`)
```python
DEFAULT_INJECTION_BUDGET_TOKENS = 8000  # Max total injection
MEMORY_BUDGET_RATIO = 0.60  # 60% to memory
SKILLS_BUDGET_RATIO = 0.25  # 25% to skills
MIN_RELEVANCE_SCORE = 0.05  # Drop entries below this
MAX_MEMORY_ENTRIES = 30  # Hard cap on memory entries
MAX_SKILLS_SHOWN = 25  # Hard cap on skills shown
```

---

## TESTING

Run standalone test:
```bash
cd ~/hermes-agent
python3 -c "
from agent.adaptive_injection import *
entries = ['DGX Spark vLLM serving', 'Apple Notes skill', 'Docker audit tool']
filtered, meta = filter_memory_entries(entries, 'DGX Spark training', 2000)
print(f'Kept {meta[\"kept\"]}/{meta[\"total\"]} entries')
"
```

---

## FUTURE ENHANCEMENTS

1. **Semantic embeddings** — Replace TF-IDF with sentence embeddings for better relevance
2. **Memory decay** — Reduce score of old entries over time
3. **User feedback loop** — Track which injected entries were actually useful
4. **Cross-session learning** — Remember which entries are frequently relevant
5. **Hierarchical skills** — Category-level filtering before skill-level filtering

---

## ROLLBACK

To revert to dumb injection, comment out the adaptive injection block in
`run_agent.py` `_build_system_prompt()` and uncomment the original code.
The original code is preserved in comments for easy rollback.
