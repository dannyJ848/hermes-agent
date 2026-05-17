# context-reservoir-demand-paging-2026

*Researched: 2026-04-05 12:15 CDT*

# Context Reservoir: Demand Paging for Evey (Apr 2026)

## Architecture (Based on Pichay arXiv 2603.09023 + Danny's Vision)

### Memory Hierarchy
- **L1 (Context Window)**: Active working memory, keep lean <35%. This is NOT memory -- it's L1 cache.
- **L2 (Eviction Buffer)**: Recent evictions, verbatim, fast recall. Auto-pruned at 100 entries.
- **L3 (Reservoir)**: Full chronological archive, verbatim, searchable. NEVER deleted.
- **L4 (Honcho/Cerebrum)**: Consolidated semantic memory (existing system).

### Key Operations
1. **evict(role, content)**: Move from L1 to L2+L3. Returns retrieval handle (small anchor).
2. **fault_in(handle_id)**: Bring content back from L3 on demand. Like a page fault.
3. **search_reservoir(query)**: Find relevant archived content.
4. **get_handles_for_context()**: Get small anchors to inject into L1.

### Key Principle
NEVER lose data. Move verbatim, don't summarize. The retrieval handle is the only thing that stays in context -- a tiny pointer.

### Pichay Results (Validation)
- 93% context reduction (5,038KB -> 339KB)
- 0.0254% page fault rate (almost never needs to bring back)
- 21.8% of context is structural waste (tool defs, system prompts, stale results)

### Implementation
- DB: ~/.hermes/context_reservoir.db (SQLite)
- Module: ~/subconscious/context_reservoir.py
- Tables: eviction_buffer (L2), reservoir (L3), retrieval_handles, page_faults
- Wire into Hermes compression pipeline: intercept before summarize -> evict instead

### Next Steps
1. Wire into Hermes on_pre_compression hook
2. Inject retrieval handles into context on session start
3. Wire fault_in as a tool the model can call
4. Monitor fault rates and adjust eviction policy


## Sources

- https://arxiv.org/abs/2603.09023
- https://www.letta.com/blog/letta-v1-agent
