# MUSE-metacognitive-agents

*Researched: 2026-04-05 11:52 CDT*

# MUSE: Metacognition for Unknown Situations and Environments

**Source:** Valiente & Pilly, HRL Laboratories (arXiv 2411.13537v2)

## Key Framework
MUSE integrates metacognitive **self-assessment** and **self-regulation** into autonomous agents. Two implementations:
1. **World-model based** (decoder-based world model for competence prediction)
2. **LLM-based** (extends ReAct + Reflexion with metacognitive loops)

## Core Mechanisms
- **Self-Assessment**: Agent continually learns to predict its own competence on a given task before acting
- **Self-Regulation**: Uses competence prediction to guide iterative strategy selection cycles
- **Competence-aware action selection**: Key advantage over Reflexion — agent knows when it doesn't know

## Results
- MUSE agents show high competence awareness (accurate prediction of success/failure)
- Significant improvement in solving novel, out-of-distribution tasks
- Outperforms both model-based RL and prompt-based LLM agent approaches (ReAct, Reflexion)
- Reduces failure rate and time to completion in unknown environments

## Relevance to Hermes/Evey
- Our `aggressive_continue` + `self_awareness.py` is a primitive form of MUSE's self-regulation
- Our domain confidence tracking (epistemic uncertainty scores per domain) parallels MUSE's competence awareness
- **Gap**: We lack formal self-assessment — predicting success probability BEFORE attempting a task
- **Actionable**: Could implement a pre-task competence scorer that logs predicted vs actual success per task type, then use that signal for task selection (our `autonomous_decide` equivalent)

## Citation
Valiente, R. & Pilly, P. (2024). "Competence-Aware AI Agents with Metacognition for Unknown Situations and Environments (MUSE)." arXiv:2411.13537v2. HRL Laboratories, Malibu, CA.

## Sources

- https://arxiv.org/html/2411.13537v2
