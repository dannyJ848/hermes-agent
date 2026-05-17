# UI-Hawk screen stream understanding GUI agents

*Researched: 2026-04-05 04:13 CDT*

# UI-Hawk: Unleashing Screen Stream Understanding for Mobile GUI Agents

**Paper:** Zhang et al., EMNLP 2025 (Suzhou, China)
**URL:** https://aclanthology.org/2025.emnlp-main.920/
**Code:** https://github.com/IMNearth/UIHawk

## Key Innovation
UI-Hawk is a multi-modal GUI agent designed to process **screen streams** (sequential screenshots) during GUI navigation, rather than just the current screenshot. This addresses a critical gap: existing GUI agents only use current visual observations + text action history, ignoring history screens.

## Architecture
- **History-aware visual encoder**: Processes screen sequences, not just individual frames
- **4 fundamental tasks** for screen stream understanding:
  1. UI grounding (locate elements)
  2. UI referring (describe elements)
  3. Screen question answering
  4. Screen summarization
- **Curriculum learning**: Guides model from fundamental tasks → advanced screen-stream comprehension

## Benchmark
- **FunUI**: New benchmark for evaluating fundamental screen understanding of MLLMs
- Validated on FunUI + existing GUI navigation benchmarks
- Key finding: screen stream understanding is essential for GUI tasks

## Also Noted: V2P (Valley-to-Peak) Visual Attention Calibration
- arXiv:2601.06899 (Jan 2026, withdrawn — replaced by arXiv:2508.13634)
- Addresses GUI grounding via background suppression + center peaking
- Uses Fitts' Law-inspired 2D Gaussian heatmaps for click precision
- Achieved 92.4% on ScreenSpot-v2, 52.5% on ScreenSpot-Pro
- Two key insights: (1) background attention drift hurts grounding, (2) uniform element modeling fails to distinguish center from edges

## Relevance to Agent Vision
- UI-Hawk's history-aware encoding is directly applicable to browser automation agents (like Hermes)
- Screen stream understanding could improve web navigation by maintaining visual context across page transitions
- The 4 fundamental tasks (grounding, referring, QA, summarization) map well to agent visual perception needs
- Curriculum learning pattern could train specialized vision models for agent UI interaction


## Sources

- https://aclanthology.org/2025.emnlp-main.920/
- https://github.com/IMNearth/UIHawk
- https://arxiv.org/abs/2601.06899
