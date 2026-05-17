# gui-grounding-2026-sota

*Researched: 2026-04-05 03:19 CDT*

# GUI Grounding State-of-the-Art (Feb 2026)

## 1. POINTS-GUI-G-8B (Tencent, Feb 2026)
- **Paper:** arXiv 2602.06391
- **Model:** POINTS-GUI-G-8B on HuggingFace
- **Key idea:** Start from base model with minimal grounding ability (POINTS-1.5), master full pipeline via:
  1. **Refined Data Engineering** — unified open-source datasets, augmentation, filtering, difficulty grading
  2. **Improved Training Strategies** — continuous vision encoder fine-tuning, resolution consistency between train/inference
  3. **RL with Verifiable Rewards** — RL traditionally boosts reasoning, but here significantly improves perception-intensive GUI grounding. Rewards are easily verifiable (click accuracy).
- **Benchmarks:** ScreenSpot-Pro 59.9, OSWorld-G 66.0, ScreenSpot-v2 95.7, UI-Vision 49.9 (SOTA)
- **Key insight for agents:** RL with verifiable rewards works for perception tasks, not just reasoning. GUI grounding provides natural reward signals (did you click the right element?).

## 2. GUI-Actor (Microsoft Research, 2025)
- **Key idea:** Coordinate-free visual grounding — humans don't calculate pixel coordinates, they perceive elements and interact directly. GUI-Actor uses **action attention** to ground targets by attending to relevant visual regions instead of generating x,y coordinates.
- **Problems with coordinate generation identified:**
  1. Weak spatial-semantic alignment
  2. Ambiguous supervision signals
  3. Granularity mismatch between vision and action space
- **Results:** GUI-Actor-3B/7B reaches 42.2/44.6 on ScreenSpot-Pro (without verifier) with Qwen2.5-VL backbone
- **Significance:** Moving away from coordinate generation toward attention-based grounding is a paradigm shift — potentially more robust for real-world agent deployment.

## Implications for SOMA / Agent Systems
- GUI grounding is the bottleneck for autonomous agent interaction with software
- RL with verifiable rewards is a generalizable technique — applicable whenever you can verify output correctness
- Coordinate-free approaches (attention-based) may be more robust for diverse screen sizes/resolutions
- Both approaches emphasize that vision encoder adaptation to the GUI domain is critical (not just LLM fine-tuning)

## Sources

- https://arxiv.org/html/2602.06391v1
- https://www.microsoft.com/en-us/research/project/gui-actor-coordinate-free-visual-grounding-for-gui-agents/
