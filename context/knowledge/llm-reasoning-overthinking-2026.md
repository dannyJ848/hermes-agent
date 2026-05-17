# llm-reasoning-overthinking-2026

*Researched: 2026-04-20 10:33 CDT*

# LLM Reasoning: Overthinking & Test-Time Compute Scaling (2025-2026)

## Key Finding: Diminishing Returns in Extended Reasoning
Extended chain-of-thought follows the law of diminishing marginal returns. Beyond certain token thresholds, additional "thinking" causes models to **abandon correct answers** for incorrect ones — a phenomenon called "overthinking."

### The Crossover Point (DeepSeek-R1-32B on AIME)
- **2K tokens**: 37.8% accuracy, flip ratio 0.32 (healthy)
- **4K tokens**: 46.5% accuracy, flip ratio 0.60 (still positive)
- **8K tokens**: 53.8% accuracy, flip ratio 1.42 (negative flips exceed positive)
- **12K tokens**: 55.8% accuracy, flip ratio 3.29 (peak accuracy)
- **16K tokens**: 54.9% accuracy, flip ratio 7.55 (accuracy DROPS)

### Overthinking Indicators (76.3% precision at 80% recall)
1. **Answer Oscillation** (r=0.78) — strongest signal
2. **Hesitation Markers** — "actually," "let me reconsider"
3. **Confidence Drop** — decreasing log-probabilities

### Why Models Overthink (audit of 80 negative flips)
- 67.5% Genuine Overthinking — explicitly reconsiders and rejects correct answer
- 20.0% Exploration Divergence — tries valid alternative but makes execution error
- 12.5% Degradation Artifacts — reasoning becomes repetitive/unfocused

## Broader Context: State of LLMs 2025 (Raschka)
- **Year of Reasoning**: RLVR + GRPO replaced RLHF as the dominant training paradigm
- **DeepSeek R1**: Training reasoning layer cost only $294K on top of base model
- **Architecture convergence**: MoE + GQA standard; diffusion models emerging for low-latency
- **Benchmaxxing crisis**: Public benchmarks no longer trustworthy — use as thresholds not rankings
- **2026 predictions**: Agentic open-weight models, RLVR expansion to chemistry/biology, inference > training for intelligence gains

## Agent Implications
1. **Adaptive stopping** is critical — don't use fixed token budgets
2. **Difficulty-based routing**: simple queries get 1-2K tokens, hard ones get 8K+
3. **Monitor answer oscillation** as an early warning signal for reasoning degradation
4. **For autonomous agents**: implement cost-aware evaluation that balances accuracy vs compute cost


## Sources

- https://arxiv.org/html/2604.10739v1
- https://magazine.sebastianraschka.com/p/state-of-llms-2025
