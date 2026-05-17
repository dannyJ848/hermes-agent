# tool-optimization-autotool-and-selection-at-scale

*Researched: 2026-04-11 23:19 CDT*

# Tool Optimization: AutoTool and Selection at Scale

## AutoTool (AAAI 2026) — arXiv:2511.14650

**Key insight:** Tool usage inertia — tool invocations follow predictable sequential patterns in agent trajectories.

**Method:**
- Constructs a directed graph from historical agent trajectories
- Nodes = tools, edges = transition probabilities
- Models "inertia" in tool selection
- Integrates parameter-level information to refine tool input generation
- Traverses the graph to select tools with minimal LLM inference

**Results:** Reduces inference costs by up to 30% while maintaining competitive task completion rates.

**Implication for Hermes:** Build a transition graph from tool call logs. When the model calls `read_file`, the next call is likely `patch` or `search_files`. Pre-rank tools by transition probability to reduce selection errors.

## The Tool Selection Problem at Scale (Tian Pan, Apr 2026)

**Core finding:** Accuracy drops from 43% → 2% when tools go from 4 → 51 (Berkeley Function Calling Leaderboard).

**Three failure modes:**
1. **Token explosion** — 58 tool definitions ≈ 55,000 tokens baseline per turn
2. **Selection accuracy degradation** — model picks plausible but wrong tools, combines incorrectly
3. **Documentation quality variance** — overlapping descriptions confuse models

**Solutions explored:**
- Static retrieval (RAG-based tool selection): better than dumping all tools, but pure embedding retrieval fails on behavioral differences
- Need layered routing: coarse retrieval → fine-grained selection → parameter generation

**Implication for Hermes:** Hermes has 50+ tools across toolsets. The current approach of filtering by enabled toolsets is a first-level routing. Adding transition-graph-based prediction (AutoTool style) as a second level could reduce both token usage and selection errors.


## Sources

- https://arxiv.org/abs/2511.14650
- https://tianpan.co/blog/2026-04-09-tool-selection-problem-agent-tool-routing-at-scale
