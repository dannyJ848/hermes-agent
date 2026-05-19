# Memory-Cortex Wiring Gap — Discovery Log (2026-05-06)

## Problem
User asked: "fix memory offloading into cortex". Assumption: there was an existing offloading pipeline that had broken.

## Discovery
After exhaustive codebase search, NO offloading system exists. The three memory tiers are completely disconnected:

| Tier | System | Capacity | Content | Offload Target |
|------|--------|----------|---------|----------------|
| Hot | `memory` tool (JSON) | 2,500 chars | User prefs, corrections | **NONE** — rejects new entries when full |
| Warm | `cerebrum_memory.db` (SQLite) | ~8MB | Distilled tips, patterns | **NONE** — manual consolidation only |
| Cold | `cortex` (PostgreSQL) | Unlimited | Elo-rated tips, full history | **NONE** — no automatic intake |

## Search Performed
- Searched all Python files for: `memory.*offload`, `offload.*memory`, `memory.*cortex`, `cortex.*memory`, `memory_decay`, `memory_score`, `tiered.*memory`, `episodic`, `semantic`
- Checked: `hermes_cli/`, `agent/`, `subconscious/`, `skills/`, `tools/`
- Found ZERO wiring code. Only references are in skill documentation (this file now) and user memory entries.

## Systems Found (with NO connections)
1. **`memory` tool**: Simple key-value JSON at `~/.hermes/memory.json`. Hard 2,500 char limit enforced by the tool itself.
2. **`cerebrum_memory.db`**: SQLite with tables `semantic_facts`, `experiences`, `distilled_tips`, `reasoning_traces`. Updated by `cortex_learning.py` but only for tip usage tracking — no memory intake.
3. **`cortex_access.py`**: PostgreSQL/SQLite wrapper for `cortex_nodes`, `cortex_edges`, `cortex_flywheel`, `cortex_eval_history`. Used by flywheel for Elo evaluation — no memory ingestion path.
4. **`unified_context.db`**: CLI state (tool intelligence, errors, sessions) — unrelated to memory.

## What Would Need Building
To create a tiered memory system, these components would need to be built:

### 1. Memory → Cerebrum Distiller
- Trigger: `memory` hits 80% (2,000 chars)
- Action: Extract oldest entries, distill into tip format (condition/recommendation/rationale)
- Destination: `cerebrum_memory.db.distilled_tips`
- Need: A distillation function that converts raw memory entries into structured tips

### 2. Cerebrum → Cortex Evaluator
- Trigger: `distilled_tips` accumulates 50+ unrated tips
- Action: Batch evaluate via LLM judge (DeepSeek V4 Pro), assign Elo
- Destination: `cortex.cortex_nodes` with `node_type='tip'`
- Need: Integration with existing `cortex_flywheel.py` evaluation pipeline

### 3. Cortex → Memory Promoter
- Trigger: Cortex tips with Elo > 1300 and high access frequency
- Action: Promote back to `memory` as "golden rules"
- Need: A promotion gate that prevents memory bloat while keeping top tips hot

### 4. Cerebrum Cleanup
- Trigger: Tips with trust < 0.3 and access_count < 2 after 30 days
- Action: Move to cortex as `node_type='archived_tip'` then purge from cerebrum
- Need: A cleanup job integrated with `cerebrum-consolidation` skill

## Why This Matters
Without this wiring, the learning pipeline is broken:
- Raw experiences in `memory` die when memory fills (no archive)
- Distilled tips in `cerebrum` never get evaluated (no Elo)
- Cortex has no intake path for new knowledge (stale corpus)
- The agent effectively "forgets" everything beyond the 2,500-char window

## Recommendation
Build the tiered system explicitly. Do not assume any automatic offloading exists — it doesn't. The three systems are islands.
