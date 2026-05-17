# human-memory-neuroscience-for-ai-architecture

*Researched: 2026-04-02 23:51 CDT*

# Human Memory Systems → AI Architecture Mapping

## The Biological Hierarchy

### Layer 0: Sensory Memory (milliseconds → seconds)
- Iconic (visual, 250-500ms), Echoic (auditory, 2-4s)
- Very high capacity, extremely brief
- **AI analog:** Raw tool outputs, web scrape results, unfiltered API responses
- **Design:** Input buffer that auto-decays unless attended to

### Layer 1: Working Memory (10-30 seconds, 4±1 chunks)
- Baddeley's model: Central Executive + Phonological Loop + Visuospatial Sketchpad + Episodic Buffer
- Cowan: 4±1 chunks, not 7±2 (Miller was about absolute judgment, not WM)
- **AI analog:** Current context window — the active conversation
- **Key insight:** Active rehearsal needed to maintain. Without it, decay is inevitable.
- **Design:** Priority queue with decay timer. Items rehearsed (accessed) get boosted.

### Layer 2: Short-Term Memory (minutes → hours)
- Intermediate buffer between working and long-term
- Sensitive to interference (proactive = old blocks new, retroactive = new blocks old)
- **AI analog:** Session-scoped facts, recent conversation summaries
- **Design:** Turn-scoped buffer with interference-aware scoring

### Layer 3: Long-Term Memory (days → lifetime)
#### Declarative (Explicit)
- **Episodic:** Autobiographical events with temporal/spatial context. "What happened"
  - AI analog: Session logs, conversation histories, task outcomes
- **Semantic:** Facts, concepts, meanings detached from specific events. "What is true"
  - AI analog: Knowledge base, entity facts, user preferences

#### Non-Declarative (Implicit)
- **Procedural:** Skills, how to do things. "How to act"
  - AI analog: Skills, learned behaviors, SOPs
- **Priming:** Exposure to stimulus affects response to later stimulus
  - AI analog: Context-dependent behavior shifts

### Memory Consolidation (The Transfer Pipeline)
1. **Encoding:** Attention + depth of processing → strength of initial trace
2. **Synaptic consolidation:** Hours, protein synthesis stabilizes the trace
3. **Systems consolidation:** Weeks-months, hippocampus → neocortex transfer via replay during SWS
4. **Reconsolidation:** Each retrieval modifies the memory (memory is reconstructive, not reproductive)

### Key Mechanisms
- **Ebbinghaus Forgetting Curve:** Retention = e^(-t/S), where S = memory strength
- **Spreading Activation:** Semantic networks, activation decays with distance
- **Emotional Salience:** Amygdala modulates hippocampal encoding (flashbulb memories)
- **Sleep Replay:** SWS for declarative, REM for emotional/procedural
- **Ribot's Law:** Recent memories are most vulnerable, remote memories are resilient (consolidation creates resilience)

## Disorder Lessons for AI Design
| Disorder | Lesson | AI Design Principle |
|----------|--------|-------------------|
| HM (no hippocampus) | Separate encoding vs retrieval vs skills | Modular memory with independent subsystems |
| Clive Wearing | Skills survive context loss | Capabilities in weights/SOPs, not context |
| Korsakoff | Confabulation without source verification | Mandatory provenance + trust scoring |
| ADHD | Fast decay in working memory | Active maintenance + priority routing |
| Alzheimer's | Recent lost first, remote preserved | Tiered consolidation creates resilience |
| PTSD | Overconsolidation of salient events | Regulated emotional weighting |
| Childhood amnesia | No encoding without schemas | Scaffolded encoding (semantic before episodic) |
| Normal aging | Recall fails, recognition works | Multi-modal indexing + associative retrieval |

## Computational Models
- **ACT-R:** Base-level activation Ai = Bi + Σ(Wj × Sji). Memory competition via recency, frequency, context.
- **CLS (Complementary Learning Systems):** Hippocampus (fast episodic) + Neocortex (slow semantic). Prevents catastrophic forgetting.
- **MemGPT/Letta:** 3-tier: core (always context), archival (searchable external), recall (recent conversation). Virtual context management.
- **HRR (Holographic Reduced Representations):** Circular convolution for binding, circular correlation for unbinding. Fixed-width compositional vectors.
- **Ebbinghaus in AI:** Retention = e^(-t/S), spaced repetition scheduling (SM-2 algorithm).


## Sources

- Baddeley (2000) Working Memory Model
- McClelland et al. (1995) Complementary Learning Systems
- Anderson (1996) ACT-R
- Plate (1995) Holographic Reduced Representations
- MemGPT (Packer et al., 2023)
