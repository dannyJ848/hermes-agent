# Upstream Cherry-Pick Analysis
## Date: 2026-05-18
## Source: NousResearch/hermes-agent main (457fa913b)
## Target: Our custom cognitive apparatus (bf0c4337f)

## Files Cherry-Picked

### 1. background_review.py
- **Purpose**: Fork agent after each turn for memory/skill evaluation
- **Relevance**: TIER S — Could replace our custom post-turn hooks
- **Integration**: Add as subsystem #22 or enhance training_gym/self_audit
- **Key Pattern**: Isolated fork with tool whitelist, prefix cache optimization

### 2. agent_runtime_helpers.py
- **Purpose**: Trajectory format, JSON repair, think block stripping
- **Relevance**: TIER S — trajectory_format for training_gym, strip_think_blocks for distillation
- **Integration**: Extract functions into existing subsystems
- **Key Pattern**: Standardized data formats for training export

### 3. conversation_compression.py
- **Purpose**: Compression with feasibility checking
- **Relevance**: TIER A — Enhance context_sculptor
- **Integration**: Replace or augment existing compression logic
- **Key Pattern**: Proactive feasibility probes before compression

### 4. iteration_budget.py
- **Purpose**: Thread-safe iteration counter
- **Relevance**: TIER A — Add to unified_intelligence
- **Integration**: Track cognitive subsystem iteration costs
- **Key Pattern**: Budget consume/refund with locking

### 5. async_utils.py
- **Purpose**: Safe async scheduling
- **Relevance**: TIER B — Use in brain subsystem
- **Integration**: Replace raw ThreadPoolExecutor scheduling
- **Key Pattern**: Coroutine cleanup on scheduling failure

### 6. conversation_loop.py
- **Purpose**: Extracted conversation loop from run_agent.py
- **Relevance**: TIER A — Study structure for our hook placement
- **Integration**: Reference for where to inject cognitive hooks
- **Key Pattern**: Clean separation of conversation logic

## Integration Strategy

Since upstream architecture is incompatible (no hook system), we adapt
patterns rather than code:

1. **Background Review Pattern** → Enhance training_gym:
   - After each turn, fork a lightweight agent
   - Tool-whitelist: only memory/skill tools
   - Evaluate: "Should this turn be distilled?"
   - Write to cerebrum_memory.db

2. **Trajectory Format Pattern** → Enhance distillation_bridge:
   - Export successful tool sequences as training trajectories
   - Include tool_name, args, result, reasoning
   - Store in training_gym for later replay

3. **Iteration Budget Pattern** → Enhance unified_intelligence:
   - Track per-subsystem iteration costs
   - Cap expensive subsystems (brain, training_gym)
   - Refund budget on successful outcomes

4. **Memory Isolation Pattern** → Enhance memory_bridge:
   - Isolate background processes from external plugins
   - Prevent plugin interference with cognitive operations
   - Use whitelist approach for cognitive tool access

## Next Steps

1. Study each cherry-picked file in detail
2. Identify specific functions/patterns to adapt
3. Create integration plan per subsystem
4. Implement as enhancements (not replacements)
5. Test with cognitive orchestrator active
