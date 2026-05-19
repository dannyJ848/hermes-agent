# active-inference-multi-llm-agents

*Researched: 2026-04-06 18:58 CDT*

# Active Inference for Self-Organizing Multi-LLM Systems

**Paper:** arXiv 2412.10425v2 (November 2024)
**Author:** Rithvik Prakki (UNC)

## Key Insight
Integrates active inference (Free Energy Principle) as a **cognitive layer above LLM agents**, dynamically adjusting prompts and search strategies through principled information-seeking behavior.

## Architecture
- **3 state factors:** prompt state, search state, information state
- **7 observation modalities:** accuracy, relevance, comprehensiveness, info relevance, info usefulness, source quality, info state
- **Agent alternates** between prompt-changing and searching states
- Belief updating follows thermodynamic constraints (Jarzynski equality)

## How It Works
1. Active inference agent acts as a "brain" that dynamically adjusts prompts to LLMs
2. LLMs generate research outputs → quality metrics become observations
3. Agent updates beliefs about which prompt/strategy combinations work best
4. Exploration-exploitation naturally emerges: initial broad exploration → targeted prompt testing
5. Observation matrices develop emergent structure as agent learns environment dynamics

## Key Results
- Agent develops accurate models of environment dynamics
- Sophisticated exploration-exploitation behavior emerges without explicit programming
- Thermodynamic framing provides principled cost-benefit for information gathering

## Relevance to Hermes Agent
- **Direct application:** Could wrap Hermes' delegation system with active inference to auto-optimize prompt selection per task type
- **Exploration-exploitation:** Currently my curiosity engine uses heuristic scoring; active inference would provide principled math for balancing exploration vs. exploitation
- **Multi-LLM coordination:** The multi-model delegation (delegate_parallel, council_decide) could benefit from active inference-driven model selection
- **Self-improvement loop:** The belief-updating mechanism maps naturally to Hermes' skill/delegation quality tracking

## Implementation Path
1. Model task selection as state factors (domain, task_type, model_choice)
2. Observations = delegation quality scores, execution time, token cost
3. Free energy minimization → optimal policy selection for next task
4. Transition from static scoring to dynamic belief-updating


## Sources

- https://arxiv.org/html/2412.10425v2
