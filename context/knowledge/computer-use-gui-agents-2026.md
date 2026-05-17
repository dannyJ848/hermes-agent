# computer-use-gui-agents-2026

*Researched: 2026-04-04 20:03 CDT*

# Computer Use & GUI Agents: State of the Art (2026)

## Key Findings

### Commercial Products
- **Anthropic Computer Use**: Claude API with computer/mouse/keyboard control. 466-499 extra tokens in system prompt. Recommends VM/container isolation.
- **OpenAI Operator → ChatGPT Agent**: CUA model (GPT-4o + RL). 87% success on complex JS sites. 58% WebArena, 38% OSWorld.
- **Google Project Mariner**: Gemini 2.0. 84% ScreenSpot, 83.5% WebVoyager. Handles 10 simultaneous tasks. "Teach & Repeat" workflow learning.
- **Microsoft UFO³ Galaxy**: Multi-device orchestration. Hybrid UI Automation + vision parsing. Picture-in-Picture isolated desktop.
- **Apple Intelligence**: On-device Siri with multi-step cross-app actions. Formal verification for irreversible steps.

### Open-Source Leaders
- **Mobile-Agent-v3 + GUI-Owl**: SOTA open-source. AndroidWorld 73.3%.
- **OmniParser V2** (24.6K stars): YOLOv8 detection + BLIP-2 captioning. 39.5% ScreenSpot Pro.
- **ShowUI** (1.8K stars, CVPR 2025): 2B VLA model, 75.1% zero-shot grounding. UI-guided token selection.

### Key Architecture Patterns
1. **Hybrid Detection**: Accessibility API (fast, free) + Vision model (handles anything)
2. **Set-of-Mark**: Number overlays on detected elements for precise LLM coordinate reference
3. **Dual Resolution**: High-res for OCR/text, low-res for semantic understanding
4. **Multi-Agent Decomposition**: Host agent coordinates, specialized sub-agents per app/domain
5. **Teach & Repeat**: Record workflows, replay them autonomously

### What We Should Implement Next
1. **Set-of-Mark annotation**: Draw numbered boxes on screenshots before sending to vision model
2. **Hybrid AX+Vision**: We already have AXUIElement for discovery. Add SoM overlay for coords.
3. **Workflow Recording**: Capture click sequences, replay them (like Mariner's Teach & Repeat)
4. **Dual Resolution**: Capture at full res for OCR, downscale for semantic analysis
5. **Multi-step Verification**: After each action, capture and verify the result

### Performance Benchmarks
- Best overall: OpenAI CUA at 58% WebArena / 38% OSWorld
- Open-source best: ~73% on domain-specific tasks
- The gap between commercial and open-source is narrowing fast
- Scrolling, dragging, zooming remain hard for all agents


## Sources

- https://zylos.ai/research/2026-02-08-computer-use-gui-agents
- https://github.com/microsoft/omniparser
- https://github.com/showlab/ShowUI
