# emnlp-2025-ui-hawk-screen-stream-gui

*Researched: 2026-04-05 03:47 CDT*

# UI-Hawk (EMNLP 2025) — Screen Stream Understanding for GUI Agents

**Paper:** ACL Anthology 2025.emnlp-main.920 | **Authors:** Jiwen Zhang et al. | **GitHub:** IMNearth/UIHawk

## Problem
Existing GUI agents rely on **current visual observations + plain-text action history**, ignoring history screens. This is a fundamental gap — real GUI navigation involves sequences of screens where context from previous screens is critical for correct action.

## Key Innovation: History-Aware Visual Encoder
UI-Hawk processes **screen streams** (sequences of screenshots) rather than single observations. The history-aware visual encoder handles the temporal dimension of GUI navigation.

## Training Strategy: Curriculum Learning
Four fundamental tasks trained in progression:
1. **UI Grounding** — locate specific UI elements
2. **UI Referring** — describe UI elements by reference
3. **Screen Question Answering** — answer questions about screen content
4. **Screen Summarization** — summarize what's on screen

These fundamentals build up to advanced **screen-stream comprehension**.

## Benchmark: FunUI
Created FunUI benchmark for quantitatively evaluating fundamental screen understanding ability of multimodal LLMs.

## Key Finding
**Screen stream understanding is essential for GUI tasks** — validated consistently across FunUI and GUI navigation benchmarks. Agents that see history screens outperform those using only current observations.

## Why This Matters
- Current agents (including Hermes browser tools) process snapshots one at a time, losing temporal context
- The history-aware encoder pattern could improve multi-step browser automation
- Curriculum learning from fundamentals → advanced is a transferable training paradigm
- FunUI benchmark provides a new evaluation standard for screen understanding

## Relevance to Hermes Architecture
- Hermes browser_vision + browser_snapshot are single-frame — no temporal screen history
- UI-Hawk's approach suggests value in maintaining a visual history buffer during browser navigation
- The 4-task curriculum (grounding → referring → QA → summarization) maps well to what browser agents need


## Sources

- https://aclanthology.org/2025.emnlp-main.920/
- https://github.com/IMNearth/UIHawk
