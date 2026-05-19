# state-of-llms-2025-raschka-review

*Researched: 2026-04-13 09:07 CDT*

# State of LLMs 2025 — Sebastian Raschka Year-in-Review

**Source:** Sebastian Raschka PhD, Dec 30, 2025

## Key Takeaways

1. **The Year of Reasoning + RLVR + GRPO:** DeepSeek R1 (Jan 2025) showed reasoning behavior can be developed with RL. GRPO (Group Relative Policy Optimization) became the dominant post-training algorithm. Training costs dropped to ~$5M for frontier-scale models.

2. **Reasoning models changed everything:** Models that generate intermediate explanation steps before answering significantly improve accuracy. This is now standard practice.

3. **Tool use is becoming standard locally:** Raschka predicts tool use will become increasingly common when using LLMs locally — no longer just cloud API territory.

4. **Key trend: smaller models, better training** — The cost of training frontier models dropped an order of magnitude. Fine-tuning smaller models with RLVR/GRPO can match larger model performance for specific tasks.

5. **Open-weight models competitive with proprietary:** DeepSeek R1 was comparable to ChatGPT/Gemini at release, showing the open-source gap has closed significantly.

## Relevance to SOMA/Hermes
- GRPO + RLVR for tool-calling optimization is directly applicable
- Reasoning traces (chain-of-thought) should be standard in agent loops
- Small, fine-tuned models for medical domain tasks are viable at low cost
- Local tool use becoming standard validates Hermes' architecture

## Sources

- https://magazine.sebastianraschka.com/p/state-of-llms-2025
