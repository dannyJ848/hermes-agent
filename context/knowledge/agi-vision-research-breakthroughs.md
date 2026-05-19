# agi-vision-research-breakthroughs

*Researched: 2026-04-04 19:43 CDT*

# AGI Vision Research Breakthroughs (April 2026)

## Screen Parsing State of the Art

### OmniParser V2 (Microsoft) — 24.6K stars
- Converts UI screenshots into structured interactable elements
- Uses YOLOv8 for object detection + BLIP-2 for captioning
- V2: Fine-grained small icon detection, interactability prediction
- Screen Spot Pro benchmark: 39.5% (SOTA)
- OmniTool: Controls Windows 11 VM with any VLM (GPT-4o, DeepSeek R1, Qwen 2.5VL)
- Key insight: Separate detection from understanding — detect elements first, then describe

### ShowUI (CVPR 2025, NUS + Microsoft) — 1.8K stars
- End-to-end Vision-Language-Action model for GUI agents
- UI-guided token selection (efficiency trick)
- ShowUI-Aloha: Human demonstration workflow (recorder → learner → planner → actor)
- Supports Qwen2.5-VL as base, vLLM inference, int8 quantization
- Key insight: Token selection — don't process whole screenshot, focus on UI regions

### Set-of-Mark (Microsoft)
- Overlay numbered marks on image regions
- LLM then references marks by number for grounding
- Solves the coordinate precision problem — instead of guessing pixels, mark and reference
- This is what I should use with vision_analyze annotate=true

### CogAgent (Tsinghua, CVPR 2024)
- 18B parameter VLM specializing in GUI understanding
- Processes 1120x1120 resolution efficiently via cross-attention module
- Key: Dual-visual encoder (high-res for OCR, low-res for semantics)
- Outperforms GPT-4V on GUI tasks despite being smaller

## Apple Accessibility API Approach
- AXUIElement from ApplicationServices framework (Python via pyobjc)
- Can enumerate ALL UI elements: position, size, label, role, value
- Returns element tree (window → group → button/text/field)
- Works WITHOUT accessibility permissions for reading (only needs it for actions)
- Key insight: Can get precise coordinates and labels FOR FREE, no vision model needed
- Appium uses XCUITest under the hood but is heavy — direct AXUIElement is lightweight

## Memory State of the Art (Mem0 Benchmark, ECAI 2025)
- LOCOMO benchmark: standardized memory evaluation
- Best approaches by accuracy: Full-context (72.9%) > Mem0g graph-enhanced (68.4%) > Mem0 (66.9%) > RAG (61.0%)
- But latency: Mem0g at 1.09s vs Full-context at 9.87s
- Token efficiency: ~1800 tokens (Mem0) vs ~26000 (full-context)
- Key insight for Evey: Graph-enhanced memory with selective retrieval is the sweet spot

## AGI Self-Improvement Pathways
- US approach: Recursive Self-Improvement (RSI) — AI building AI
- China approach: Embodied AGI through physical-world interaction
- Both agree: self-improvement loop is the path
- For Evey: The iteration cycle IS the AGI training. Each cycle:
  1. Perceive (see the world)
  2. Reason (understand what to improve)
  3. Research (find knowledge)
  4. Implement (make changes)
  5. Verify (test results)
  6. Remember (store what worked)


## Sources

- https://github.com/microsoft/omniparser
- https://github.com/showlab/ShowUI
- https://arxiv.org/abs/2310.11441
- https://arxiv.org/abs/2312.08914
- https://mem0.ai/blog/state-of-ai-agent-memory-2026
- https://research.macpaw.com/publications/how-to-parse-macos-app-ui
- https://www.chinatalk.media/p/how-china-hopes-to-build-agi-through
