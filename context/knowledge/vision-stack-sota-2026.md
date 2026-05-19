# vision-stack-sota-2026

*Researched: 2026-04-05 02:08 CDT*

# Vision Stack State (Apr 2026)

## Current Approach: SoM via Browser JS
- `browser_vision` with `annotate=true` overlays numbered labels on interactive elements
- For Safari/native apps: `screencapture` + vision_analyze for OCR
- Safari JS `getBoundingClientRect()` provides OmniParser-level precision for free (no model needed)
- 219 elements detected on Hacker News, tested on BioDigital anatomy

## SOTA Comparison (April 2026)
1. **OmniParser** (Microsoft): Uses detectron2 + BLIP for icon detection + description. Our browser_vision annotation achieves similar results without a local model.
2. **Complete Screen Parsing** (arXiv 2602.14276): Goes beyond sparse grounding to full screen understanding. Uses complete supervision.
3. **CUA (Computer Use Agents)**: Open-source framework for visual computer control.
4. **Set-of-Mark (SoM)** (Microsoft/Yang et al.): Our current approach. Proven effective.

## Gap Analysis
- **Native app parsing**: We rely on OCR for non-browser apps. Could benefit from OmniParser's icon detection model.
- **Multi-monitor**: Not tested.
- **Scroll understanding**: We capture current viewport only. No persistent spatial map of scrolled content.
- **State tracking**: No differential detection (what changed between screenshots).

## Recommendations
1. Keep SoM for web (free, precise)
2. Consider OmniParser for native app icon detection
3. Add visual diff detection for state tracking
4. Build spatial memory for scroll-based navigation


## Sources

- https://www.microsoft.com/en-us/research/articles/omniparser-for-pure-vision-based-gui-agent/
- https://github.com/microsoft/omniparser
- https://arxiv.org/abs/2602.14276
