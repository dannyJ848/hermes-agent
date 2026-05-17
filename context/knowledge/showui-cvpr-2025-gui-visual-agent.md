# ShowUI CVPR 2025 GUI Visual Agent

*Researched: 2026-04-05 02:37 CDT*

# ShowUI: Vision-Language-Action Model for GUI Visual Agent (CVPR 2025)

**Authors:** Kevin Qinghong Lin, Linjie Li, Difei Gao, Zhengyuan Yang, et al. (Show Lab / NUS + Microsoft)
**Paper:** arXiv:2411.17465 (Nov 2024, accepted CVPR 2025)
**Code:** github.com/showlab/ShowUI (1.8k stars, Apache-2.0)
**Model:** 2B parameters on HuggingFace

## Key Innovations

### 1. UI-Guided Visual Token Selection
- Formulates screenshots as a **UI connected graph**
- Adaptively identifies redundant visual relationships
- Uses graph structure as criteria for token selection during self-attention blocks
- **Result:** Reduces 33% of redundant visual tokens, 1.4x training speedup
- This is a novel approach to the "screenshot tokens are expensive" problem — treats UI layout as a graph rather than just spatial grid

### 2. Interleaved Vision-Language-Action Streaming
- Unifies diverse GUI task needs in a single stream
- Manages visual-action history during navigation
- Pairs multi-turn query-action sequences per screenshot to improve training efficiency
- Key insight: GUI tasks need both grounding (where to click) AND navigation (what happened after)

### 3. Small-scale High-quality Data Curation
- Only 256K training samples (vs millions in competing approaches)
- Resampling strategy to address data type imbalances
- Careful curation over raw volume
- **Result:** 75.1% zero-shot screenshot grounding accuracy

## Benchmarks
- **Mind2Web** (web navigation)
- **AITW** (mobile Android navigation)
- **MiniWob** (online web tasks)
- Zero-shot screenshot grounding: 75.1%

## Relevance to SOMA / Agent Systems
- **Graph-based token selection** is applicable to any vision-heavy agent (medical imaging, anatomy viewers)
- **Interleaved streaming** pattern useful for multi-step GUI automation in Hermes
- The 2B lightweight model can run locally — potential for on-device GUI understanding
- Data curation strategy (quality over quantity, resampling for balance) is applicable to medical training data

## Compared to Related Work
- vs UIPro (20.6M samples): ShowUI achieves comparable results with 80x less data
- vs OmniParser (pipeline approach): ShowUI is end-to-end, single model
- vs closed-source (GPT-4o computer use): Open-source, 2B params, runs locally


## Sources

- https://arxiv.org/abs/2411.17465
- https://github.com/showlab/ShowUI
