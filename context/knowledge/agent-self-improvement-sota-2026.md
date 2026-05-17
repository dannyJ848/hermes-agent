# agent-self-improvement-sota-2026

*Researched: 2026-04-05 22:41 CDT*

# AI Agent Self-Improvement SOTA 2025-2026

## Key Breakthroughs

### 1. Self-Modifying Agents
- **ADAS (Automated Design of Agentic Systems)**: Meta-agent writes code to create agent architectures, evaluates on task, reads traceback, rewrites code
- **Open-Ended Multi-Agent Systems (OMAS)**: Agent accesses own Python base code, writes new modules, tests in sandbox, compiles into runtime
- **Self-Diagnostic Trace**: Before altering code, agent generates explicit metacognitive trace of WHY current behavior failed

### 2. Unsupervised Continuous Learning
- **SPIN (Self-Play Fine-Tuning)**: Actor-Critic self-play against past versions
- **Autonomous Environment Design (UED)**: Agent generates own training curriculum for weak areas
- **Uncertainty-Directed Exploration**: Calibrated confidence → auto-switch to "learning mode" when prediction failure rate is high

### 3. Dynamic Tool Creation & Optimization
- **CRAFT (Creation and Retrieval of Tools)**: Agent writes custom scripts, tests, saves to local "Toolbox"
- **Tool Retrieval Routing (TRR)**: Dense vector embeddings to search API databases, cost-benefit of tool vs internal memory
- **Tool Abandonment**: Agent recognizes when tool is hallucinating/broken, cross-references with world model

### 4. Process Reward Models (PRMs)
- Chain of Thought with per-step reward scoring
- Backtracking when step reward drops
- Integration into agentic loops for "System 2" routing

### Integration into Evey
Already implemented:
- Dynamic Tool Creation (flow_graph, auto_test_gen, etc.)
- Self-Diagnostic Traces (iteration engine, self_awareness.py)
- Tool Abandonment (circuit breaker)

To implement:
- SPIN-style self-play for strategy evaluation
- UED for autonomous training curriculum generation
- PRM-style per-step reward scoring
- ADAS meta-agent for architecture optimization


## Sources

- research delegation
- ADAS paper
- SPIN paper
- CRAFT paper
