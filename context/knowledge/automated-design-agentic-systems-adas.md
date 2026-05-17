# automated-design-agentic-systems-adas

*Researched: 2026-04-14 22:20 CDT*

# Automated Design of Agentic Systems (ADAS)

**Paper:** arXiv:2408.08435 | Authors: Shengran Hu, Cong Lu, Jeff Clune | Revised Mar 2025

## Core Thesis
Hand-designed agent architectures will eventually be replaced by learned/discovered ones, following the ML pattern (hand-crafted features → learned features).

## Key Method: Meta Agent Search
- A **meta agent** iteratively programs new agents in code
- Uses an ever-growing archive of previous discoveries
- Code-based search space (Turing Complete) enables discovering ANY possible agentic system
- Discovers novel prompts, tool use patterns, workflows, and combinations

## Results
- Outperforms state-of-the-art hand-designed agents across coding, science, and math
- **Cross-domain transfer:** Agents discovered in one domain perform well in others
- **Cross-model transfer:** Works across different LLM backbones
- Demonstrates generality and robustness

## Relevance to Hermes Agent
- Our distillation/tip system is a primitive form of ADAS (meta-learning agent behaviors)
- The `subconscious` modules (meta_loop, domain_certainty, tool_planner) are hand-designed meta-components
- ADAS suggests these could be auto-designed via code search
- The skill-factory skill partially implements this pattern (auto-generating skills from workflows)

## Future Direction
- Replace manual tip/skill creation with automated agent-design search
- Use code-level search to discover new tool combinations and workflows
- Cross-domain transfer validates that meta-learned agent strategies generalize


## Sources

- https://arxiv.org/abs/2408.08435
