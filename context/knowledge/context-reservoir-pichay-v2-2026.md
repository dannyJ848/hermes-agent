# context-reservoir-pichay-v2-2026

*Researched: 2026-04-05 12:45 CDT*

# Context Reservoir v2: Full Pichay Architecture (arXiv 2603.09023)

## Complete Feature Set (10 systems)

### 1. L1-L4 Memory Hierarchy
- L1 = Context window (keep <35%)
- L2 = Working cache with SLRU (probationary + protected segments)
- L3 = Verbatim reservoir (NEVER deleted, chronological archive)
- L4 = Honcho/Cerebrum (consolidated semantic memory)

### 2. Segmented LRU (SLRU) Eviction Policy
- Probationary segment: new entries, first to evict
- Protected segment: frequently accessed, last to evict
- Promote on second access

### 3. Garbage Collection vs Paging
- GC: permanently removes dead tool output (26.5% waste)
- Paging: moves content to L3 with retrieval handles (preserves data)
- Dead = not referenced in 20+ turns

### 4. Page Fault Detection + Fault-Driven Pinning
- fault_in() brings content back on demand
- After 3+ faults: pinned in L2
- After 5+ faults: promoted to protected segment

### 5. Retrieval Handles as Anchors
- Model-readable format: "[Paged out: description (N tokens). Re-read if needed.]"
- Models understand without instruction (per Pichay)

### 6. Dead Tool Output Detection
- Tracks tool results by (tool_name, output_hash)
- Counts turns since last reference
- Marks as dead after 20 turns, removes from L2

### 7. Tool Definition Stubbing
- Replace full JSON schema with short stub when tool not recently called
- Full schema loaded on-demand when tool is actually called
- Saves 20.2% of context per Pichay

### 8. Content Deduplication
- Hash-based dedup index
- Tracks reference count per content hash
- Detects repeated content across turns (2.2% waste)

### 9. Graduated Pressure Zones
- NORMAL (<50%): no action
- PRESSURE (50-75%): proactive eviction, consider tool stubbing
- CRITICAL (75%+): aggressive eviction, force GC, stub infrequent tools

### 10. Cooperative Memory Management
- Model can voluntarily release context via cooperative_release()
- LLM-in-the-loop approach from Section 3.7

## Pichay Results (Validation)
- 93% context reduction (5,038KB -> 339KB)
- 0.0254% fault rate
- 21.8% structural waste (26.5% dead output + 20.2% tool defs + 11.0% system + 2.9% skill + 2.2% dedup)

## Integration
- Module: ~/subconscious/context_reservoir.py
- DB: ~/.hermes/context_reservoir.db (8 tables, 8 indexes)
- Hook: plugins/memory/cerebrum/provider.py on_pre_compress()
- Fires automatically when compression threshold (40%) is hit


## Sources

- https://arxiv.org/abs/2603.09023
