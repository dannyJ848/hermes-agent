# hierarchical-cot-reasoning

*Researched: 2026-04-20 05:47 CDT*

# Hierarchical Chain-of-Thought (Hi-CoT) Prompting

**Source:** arXiv:2604.00130v1 (April 2026)

Hi-CoT alternates between `<|instruction|>` (high-level planning) and `<|execution|>` (concrete operations) blocks. This structured format acts as a compression bottleneck.

## Key Results
- Accuracy: up to 61.4% improvement, 100% on AMC/MATH500 with strict format compliance
- Efficiency: 13.9% average trace reduction, up to 75% in format-compliant cases
- Particularly effective for small models (0.6B-4B) as scaffolding

## Agent Relevance
Plan-execute alternation maps directly to agent tool-use loops. Could improve Hermes agent task planning by enforcing structured plan→execute→plan rhythm instead of free-form reasoning.

## Sources

- https://arxiv.org/html/2604.00130v1
