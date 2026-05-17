# curiosity-driven-exploration-agents-2025

*Researched: 2026-04-04 20:50 CDT*

# Curiosity-Driven Exploration & Intrinsic Motivation in AI Agents

## Key Techniques

### 1. Intrinsic Curiosity Module (ICM) — Pathak et al. 2017
- Generates intrinsic reward from prediction error about environment dynamics
- Uses inverse dynamics model to learn features the agent can influence (avoids TV noise problem)
- Forward model: predict φ(s_{t+1}) from (φ(s_t), a_t); reward = prediction error
- Inverse model: predict action from (φ(s_t), φ(s_{t+1})) — trains encoder
- Naturally decays as agent masters environment ("gets bored")
- **Paper**: Pathak et al. "Curiosity-driven Exploration by Self-supervised Prediction" ICML 2017
- **Repo**: github.com/pathak22/noreward-rl

### 2. Random Network Distillation (RND) — Burda et al. 2019
- Fixed random target network + trained predictor; novelty = prediction error
- Captures epistemic uncertainty (lack of data), not aleatoric (noise)
- Key tricks: observation normalization, non-episodic intrinsic returns
- More robust than ICM in stochastic environments
- First non-trivial performance on Montezuma's Revenge without extrinsic reward
- **Paper**: Burda et al. "Exploration by Random Network Distillation" ICLR 2019
- **Repo**: github.com/openai/random-network-distillation

### 3. Active Inference — Friston
- Agents minimize variational free energy = expected surprise
- Expected Free Energy has two terms: epistemic (info gain = exploration) + pragmatic (goal alignment)
- Curiosity emerges naturally from epistemic drive
- Selects actions that resolve uncertainty about hidden states
- Deep Active Inference: amortized inference + learned transitions + imagined rollouts

### Application to LLM Agents (Non-RL)
- **Prediction error as novelty**: Track what topics/tools the agent hasn't explored; prioritize those
- **RND-like novelty scoring**: Hash task descriptions → if predictor disagrees with random hash, topic is novel → explore
- **Active inference for task selection**: Score tasks by information gain (how much would this teach?) + pragmatic value (how useful?)
- **Epistemic drive**: Maintain uncertainty estimates per domain; select tasks that reduce highest uncertainty
- **Intrinsic motivation signal**: Log prediction accuracy per task type; prioritize types where predictions are worst

## Sources

- Pathak et al. ICML 2017
- Burda et al. ICLR 2019
- Friston Free Energy Principle
- Delegated research via GLM-5.1
