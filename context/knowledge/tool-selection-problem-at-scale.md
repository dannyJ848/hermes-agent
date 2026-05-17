# tool-selection-problem-at-scale

*Researched: 2026-04-12 09:38 CDT*

# The Tool Selection Problem at Scale

**Source:** TianPan.co (April 9, 2026) + Statsig + Berkeley Function Calling Leaderboard

## Key Findings

### Accuracy Collapse at Scale
- Berkeley Function Calling Leaderboard: accuracy drops from 43% to 2% on calendar scheduling when tools expand from 4 to 51 across multiple domains
- This is NOT graceful degradation — it's a cliff

### Token Explosion
- Anthropic internal testing: 58 tool definitions = ~55,000 tokens baseline per turn
- Every agent turn carries overhead equivalent to summarizing a short novel BEFORE user query
- Makes unit economics unworkable at production scale

### Failure Modes at Scale
1. **Wrong tool selection**: Model picks plausible-sounding but semantically incorrect tool
2. **Cross-parameter confusion**: Calls tool with params matching a different tool's schema
3. **Documentation variance**: Vague/overlapping descriptions across 50+ tools confuse models
4. **Silent errors**: Response format often valid but semantically incorrect — hard to detect

### Solutions (Layered)
1. **RAG-based tool selection**: Embed tool descriptions + query, pass top-k to model. Better than static but insufficient alone.
2. **Layered routing**: Semantic classifier → domain gate → tool schema subset
3. **Documentation quality**: Precise, well-scoped descriptions with explicit behavioral differences
4. **Tool grouping/clustering**: Organize into semantic namespaces to reduce selection space

### Relevance to Hermes
- Hermes has 50+ tools across multiple toolsets — squarely in the problem zone
- Current `toolsets.py` grouping is a partial solution (enabling/disabling by category)
- `model_tools.py` `_discover_tools()` already filters by availability
- Opportunity: implement semantic tool routing using embeddings of tool descriptions


## Sources

- https://tianpan.co/blog/2026-04-09-tool-selection-problem-agent-tool-routing-at-scale
- https://www.statsig.com/perspectives/tool-calling-optimization
