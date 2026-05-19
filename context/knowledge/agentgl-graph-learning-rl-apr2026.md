# agentgl-graph-learning-rl-apr2026

*Researched: 2026-04-08 11:38 CDT*

# AgentGL: Agentic Graph Learning with RL
**Paper**: arXiv:2604.05846 (April 2026, ACL 2026 Main Conference)
**Authors**: Yuanfu Sun, Kang Li, Dongzhe Fan, Jiajin Liu, Qiaoyu Tan

## Key Innovation
First RL-driven framework for agentic graph learning. Equips LLM with graph-native tools for multi-scale exploration.

## Techniques
1. **Search-constrained thinking**: Regulate tool usage by constraining search space before calls
2. **Graph-conditioned curriculum RL**: Start with simpler subgraphs, increase complexity gradually
3. **Multi-scale exploration tools**: Local neighborhood, community-level, global patterns

## Results
- +17.5% node classification
- +28.4% link prediction over GraphLLM/GraphRAG baselines
- Stabilizes long-horizon policy learning without step-wise supervision

## Applications to Evey
- Search-constrained thinking → pre-filter tips by domain before injection
- Curriculum RL → start training with single-tool tasks, progress to multi-tool chains
- Multi-scale exploration → local (current tip), community (domain cluster), global (cross-domain patterns)


## Sources

- https://arxiv.org/abs/2604.05846
