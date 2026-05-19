# UFO2 Desktop AgentOS

*Researched: 2026-04-05 03:22 CDT*

# UFO2: The Desktop AgentOS (Microsoft Research, April 2025)

**Paper:** arXiv 2504.14603 | **GitHub:** github.com/microsoft/UFO

## Key Innovation
UFO2 is a multiagent **AgentOS** for Windows that moves beyond screenshot-only CUAs into deep OS-level automation. It's not just an agent — it's an OS substrate for agents.

## Architecture
- **HostAgent**: Centralized orchestrator for task decomposition, coordination, and system-level execution control. Uses a finite-state controller and structured output interface.
- **AppAgent**: Application-specialized execution runtimes with native APIs, domain knowledge, and GUI+API action layers. "Everything-as-an-AppAgent" design.
- **Hybrid Control Detection**: Fuses Windows UI Automation (UIA) with vision-based parsing for robust interaction across diverse interface styles. Deduplication pipeline merges both sources.
- **Speculative Multi-Action Execution**: Plans multiple actions per step, reducing per-step LLM overhead significantly.
- **Picture-in-Picture (PiP)**: Virtualized desktop environment allowing agent and user to operate concurrently without interference. Secure cross-session coordination.

## Key Technical Details
- Unified GUI–API Action Orchestrator: Can interact via both visual clicks AND native Windows APIs
- Continuous Knowledge Integration: Bootstraps from documentation, reinforces from experience, runtime RAG
- Automated Task Evaluator for self-assessment
- Comprehensive logging and debugging infrastructure
- Evaluated across 20+ real-world Windows applications

## Relevance to SOMA/Hermes
- **Hybrid control** (vision + structured API) is the right pattern — pure vision is fragile
- **Multiagent decomposition** (HostAgent → AppAgent) mirrors our squad-dev pattern
- **Speculative multi-action** reduces LLM calls — applicable to Hermes agent loop optimization
- **PiP isolation** concept could apply to browser automation tasks
- **Continuous knowledge integration** (docs → experience → RAG) is exactly our knowledge-compiler pipeline

## Performance
Substantial improvements over prior CUAs in robustness and execution accuracy. Model ablation shows GPT-4o backbone. Step count profiling and latency breakdown included.


## Sources

- https://arxiv.org/html/2504.14603v2
- https://www.microsoft.com/en-us/research/publication/ufo2-the-desktop-agentos/
