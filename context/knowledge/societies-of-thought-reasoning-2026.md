# societies-of-thought-reasoning-2026

*Researched: 2026-04-05 02:36 CDT*

# Societies of Thought: Reasoning Models as Implicit Multi-Agent Systems (Google, Jan 2026)

## Paper: arXiv 2601.10825

## Key Insight
Enhanced reasoning in models like DeepSeek-R1 and QwQ-32B emerges NOT from extended computation alone, but from **implicit simulation of multi-agent-like interactions** — a "society of thought". The model internally simulates diverse perspectives with different personality traits and domain expertise.

## Findings
1. Reasoning models exhibit greater **perspective diversity** than baseline instruction-tuned models
2. They activate broader conflict between **heterogeneous personality- and expertise-related features** during reasoning
3. This manifests as: question-answering sequences, perspective shifts, reconciliation of conflicting views
4. **Conversational scaffolding** accelerates reasoning improvement vs monologue-like reasoning
5. Base models spontaneously increase conversational behaviors when rewarded for reasoning accuracy

## Implications for Evey
- Our `council_decide` and `mixture_of_agents` tools are doing explicitly what these models do implicitly
- We should encourage **perspective diversity** in our own reasoning traces
- The MARS reflection pattern (principle + procedural) should include **multiple perspectives**
- We can train our reasoning by explicitly generating diverse viewpoints before deciding

## Action Items
1. Add "perspective diversity" to the fluid reasoning engine — track how many distinct viewpoints we consider
2. In distillation tips, classify whether a tip came from single-perspective or multi-perspective reasoning
3. Experiment with "conversational scaffolding" in the AGI cycles — have the agent argue with itself before deciding


## Sources

- https://arxiv.org/html/2601.10825v1
