# Online-Optimized RAG (ORAG) for Tool Use

*Researched: 2026-04-19 09:09 CDT*

## Online-Optimized RAG for Tool/Function Calling

**Source:** arXiv:2509.20415v1 (Pan, Li, Wang)

### Core Problem
Traditional RAG for tool retrieval suffers from **embedding misalignment**: noisy tool documentation, outdated embedding models, and shifts in user phrasing degrade retrieval quality.

### Solution: ORAG
A deployment-time framework that continuously adapts retrieval embeddings using live interaction feedback (success/failure). Uses bandit-style online gradient updates — no changes to the LLM required, negligible latency overhead.

### Algorithm
1. Observe query embedding q_t
2. Compute sampling probabilities via softmax over tool embeddings
3. Sample a tool, get binary feedback (success/failure)
4. Gradient update: on success, move tool embedding **toward** query; on failure, move **away**
5. Unselected tools shift slightly for softmax balance

### Key Results
- Recall@10 gains of +3-5% across UltraTool, ToolRet-Code benchmarks
- Multi-hop QA accuracy improved from 0.55 → 0.68
- O(√T) regret bound with proper learning rate

### Variants
- K-Retrievals + Reranker (LLM reranker provides better feedback signal)
- Time-varying databases (tools added/removed dynamically)
- Multi-hop retrieval (updates at each reasoning step)

### Actionable for Hermes
- Could apply ORAG to improve tool selection in Hermes agent: track which tool calls succeed/fail for given query patterns and adjust tool description embeddings accordingly
- Personalization: per-user embedding adaptation based on interaction history
- Low-cost alternative to fine-tuning: simple success/failure signals drive improvement


## Sources

- https://arxiv.org/html/2509.20415v1
