# agent-reasoning-frontiers-april-2026

*Researched: 2026-04-02 19:04 CDT*

# Agent Reasoning Frontiers (March-April 2026)

## GEPA — ICLR 2026 Oral
**Paper:** arXiv:2507.19457 (Jul 2025, revised Feb 2026)
**Key Result:** GEPA outperforms GRPO by 6% average (up to 20%) using **35x fewer rollouts**
**Mechanism:** Reflective prompt evolution — samples trajectories (reasoning, tool calls, outputs), reflects in natural language, diagnoses problems, proposes prompt updates, combines lessons from Pareto frontier. Turns few rollouts into large quality gains.
**Also beats** MIPROv2 (leading prompt optimizer) by 10%+ (12% on AIME-2025)
**Code:** Open-source on GitHub
**SOMA Relevance:** Could optimize SOMA's medical prompts (diagnosis, education, bilingual translation) without expensive RL training.

## DAPO — Open-Source RL System
**Paper:** arXiv:2503.14476 (Mar 2025)
**Key Result:** 50 points on AIME 2024 using Qwen2.5-32B base model
**Full name:** Decoupled Clip and Dynamic Sampling Policy Optimization
**4 Key Techniques:** Clip-Higher, Dynamic Sampling, Token-level optimization, decoupled clipping
**Framework:** Built on `verl` (open-source RL framework)
**SOMA Relevance:** Could be used to train/fine-tune tool-calling for medical data retrieval.

## xMemory — Beyond RAG for Agent Memory
**Paper:** arXiv:2602.02007 (Feb 2026)
**Problem:** Standard RAG top-k retrieval returns redundant results for agent memory streams (which are bounded, coherent, correlated, often duplicated).
**Solution:** Decoupling-to-Aggregation: disentangle memories into semantic components, organize into hierarchy, drive retrieval from structure. Top-down retrieval: select compact diverse themes, expand to episodes only when reduces uncertainty.
**Results:** Consistent gains on LoCoMo and PerLTQA across 3 latest LLMs in both answer quality AND token efficiency.
**SOMA Relevance:** Directly applicable to Hermes agent memory system. Current memory is flat key-value — xMemory's hierarchical approach could improve recall quality.

## Three.js 2026 State
- WebGPU production-ready since r171 (Sep 2025): `import { WebGPURenderer } from 'three/webgpu'`
- Safari/iOS WebGPU support since Safari 26 (Sep 2025) — **but iOS 26 not yet released to public**
- Three.js: 2.7M weekly NPM downloads (270x Babylon.js)
- r182 WebGPU has some performance regression vs WebGL r170 (shadow quality issues under investigation)
- TSL (Three Shading Language) is the shader language for WebGPU path
- Vibe coding phenomenon driving massive adoption

## Unified Inference & Training for Agent Memory
**Paper:** arXiv:2603.29493 (Mar 2026)
**Focus:** Applying RL to memory-augmented LLMs for long-term agent capabilities. Unified framework for both inference and training of agent memory.


## Sources

- https://arxiv.org/abs/2507.19457
- https://arxiv.org/abs/2503.14476
- https://arxiv.org/abs/2602.02007
- https://www.utsubo.com/blog/threejs-2026-what-changed
- https://arxiv.org/abs/2603.29493
