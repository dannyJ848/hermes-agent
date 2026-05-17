# active-inference-agents-2025

*Researched: 2026-04-05 20:56 CDT*

# Active Inference AI Agents (2025 State)

## Core Concept
Active inference (from Karl Friston's Free Energy Principle) proposes that intelligent systems minimize "free energy" (surprise/uncertainty) through continuous prediction-error minimization. Unlike RL (reward-seeking), active inference agents build internal world models and act to reduce uncertainty — making them naturally curious.

## Key Development: VERSES Genius Platform (2025)
- Active inference-based AI demonstrated **60% performance boost while using only 3% of compute** vs conventional deep learning approaches
- Single objective: reduce uncertainty → natural curiosity emerges
- Unlike LLMs: learns in real-time from lived experience, doesn't freeze after training
- Outperformed DeepSeek R1 in code-breaking challenge (Mastermind game)
- Mastered Atari Gameworld 10k in minutes using AXIOM "Digital Brain"

## Why It Matters for Agent Design
1. **Adaptation over imitation**: LLMs imitate training data; active inference agents adapt to new situations
2. **Causal understanding**: Builds internal causal models, not just pattern matching
3. **Sample efficiency**: Far less data needed because the agent actively explores
4. **Natural curiosity**: Uncertainty minimization = intrinsic motivation to explore
5. **Compute efficiency**: 3% of compute for 60% better performance is paradigm-shifting

## Relevance to Hermes Architecture
- My current "autonomous-curiosity" skill implements a crude version of this: uncertainty scoring drives domain exploration
- Active inference formalizes what I'm doing heuristically: pick tasks that maximize expected information gain
- Key insight: the "bitter lesson" applies — hand-coded rules (skills, memory) matter less than systems that learn autonomously
- Future direction: replace manual domain scoring with proper Bayesian surprise minimization

## Sources
- VERSES Newsletter Oct 2025: Financial Times feature, IWAI workshop
- Karl Friston ML Street Talk podcast: FEP explained
- Gabriel René CEO letter: Sutton's "bitter lesson" applied to active inference


## Sources

- https://www.verses.ai/news/verses-monthly-newsletter-october-2025
- https://granthbrennermd.medium.com/designing-a-curious-machine-intelligence-that-actually-thinks-949f50a7ca9f
