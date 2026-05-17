# reflection-tuning-llm-self-improvement-2025

*Researched: 2026-04-05 10:13 CDT*

# Reflection Tuning for Self-Improving LLMs (July 2025)

**Source:** Galileo AI Blog — "Reflection Tuning Explained: Self-Improving LLMs 101"

## Core Concept
Reflection tuning creates a feedback loop where the model critiques and rewrites its own responses before delivering them. Instead of generating one answer, the model reviews → identifies problems → rewrites → learns from the improved version.

## 3-Step Process
1. **Generate:** Prompt model with question, record initial answer
2. **Critique:** Same model (or oracle like GPT-4) examines response for factual/logical/stylistic errors
3. **Refine:** Generate improved answer; incorporate (original, improved) pair into training data

## Key Results
- Reflection-tuned WizardLM 7B: 81.25% win rate on Vicuna test set
- Llama 3.1 70B climbed leaderboards after adopting reflection
- Doubles computational cost (multiple forward passes)

## When Reflection Works vs Doesn't
- **Works best:** Knowledge-intensive, reasoning-heavy tasks where hallucinations matter
- **Overkill:** High-volume chatbots, embedding systems where speed matters more than perfection

## Comparison to Other Methods
| Method | Mechanism | Cost |
|--------|-----------|------|
| Standard instruction tuning | Fixed human examples | Low |
| RLHF | Separate reward model + human eval | High |
| Self-consistency | Multiple answers, no feedback | Medium |
| **Reflection** | Integrated critique in data pipeline | Medium-High |

## Relevance to Hermes Agent
- Our `self-evaluation-loop` skill already implements Self-Refine + Reflexion pattern
- **Enhancement:** After delegation, we could run a reflection pass on poor-quality results (score < 6) — ask the same model to critique its own output, then save the improved version
- **Calibration link:** Reflection passes generate (original_score, reflected_score) pairs that directly feed ECE/Brier calibration tracking
- **Cost consideration:** Only worth running reflection on tasks where quality matters (code changes, research synthesis) — skip for simple lookups


## Sources

- https://galileo.ai/blog/reflection-tuning-llms
