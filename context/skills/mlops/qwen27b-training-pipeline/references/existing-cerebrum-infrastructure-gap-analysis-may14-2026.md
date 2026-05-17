# Existing Cerebrum Infrastructure vs Qwen Training Gap Analysis

**Date:** May 14, 2026
**Context:** DGX Spark GB10 with full Hermes Agent deployment

## What Exists

### Cerebrum Database (`~/.hermes/cerebrum_memory.db`)
- **244 experiences** in `experiences` table
- **2 staging tips** in `staging_tips` table
- **15+ tables** for cognitive actions, error patterns, tool predictions, etc.

### Active Learning Modules
1. **iteration_engine.py** — Sub-millisecond pattern matching before/after every tool call
2. **distillation_bridge.py** — Converts tool outcomes → tips → context injection
3. **adaptive_cortex.py** — Real-time personalized learning from mistakes

### Experience Breakdown (244 total)
| Action Type | Result | Count |
|-------------|--------|-------|
| patch | success | 154 |
| write_file | success | 38 |
| terminal | success | 4 |
| terminal | regression | 1 |
| skill_view | regression | 1 |
| evey_goals | regression | 1 |
| web_extract | regression | 1 |
| browser_* | success | 5 |
| autonomous_plan | success | 1 |

### Staging Tips (2 total)
1. "DGX Spark GB10: Use direct PEFT + transformers.Trainer instead of axolotl..." (tier1)
2. "SSH background process: terminal(background=true) backgrounds locally not remotely..." (tier1)

## The Gap

**Conversion rate: 0.8%** (2 tips from 244 experiences)

**Missing link:** Distilled tips go back to Hermes context injection, but NEVER become training data for the Qwen LoRA.

```
My Actions → Iteration Engine → Cerebrum DB → Distilled Tips → My Context
                                              ↓
                                         (Missing Link)
                                              ↓
                                         Qwen Training Data
```

## Why the Pipeline is Redundant

The `export_sessions_to_training.py` script we built scans raw session files (`~/.hermes/sessions/session_*.json`) independently. This is parallel to the existing infrastructure that already captures every action in `experiences`.

**Wrong approach:**
- Scan raw session JSON files
- Quality-score conversations independently
- Export to ShareGPT format
- Merge with training data

**Right approach:**
- Query `cerebrum_memory.db` `experiences` table
- Filter for high-confidence experiences (confidence > 0.7, result != "regression")
- Convert to ShareGPT format
- Merge with training data

## SQL Queries for Extraction

```sql
-- High-quality experiences (successful actions with lessons)
SELECT action_type, result, lesson, timestamp 
FROM experiences 
WHERE result = 'success' 
  AND lesson IS NOT NULL 
  AND lesson != ''
ORDER BY timestamp DESC;

-- Error patterns (regression results)
SELECT action_type, result, lesson, timestamp 
FROM experiences 
WHERE result = 'regression'
ORDER BY timestamp DESC;

-- Staging tips ready for training
SELECT content, source_tier, priority, tags 
FROM staging_tips 
WHERE evaluated = 1 
  AND sent_to_cortex = 1;
```

## Recommended Integration

Instead of building parallel infrastructure:

1. **Export from existing experiences table** — 244 rows already there
2. **Fix distillation bridge conversion rate** — Why only 2 tips from 244 experiences?
3. **Add training data export to distillation pipeline** — Tips should flow to BOTH context injection AND Qwen training

## Files on DGX
- `/data/SpecForge/hermes-agent/agent/iteration_engine.py`
- `/data/SpecForge/hermes-agent/agent/distillation_bridge.py`
- `/data/SpecForge/hermes-agent/agent/adaptive_cortex.py`
- `~/.hermes/cerebrum_memory.db`
