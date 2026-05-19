# soma-intelligence-architecture-synthesis-april-2026

*Researched: 2026-04-03 13:03 CDT*

# SOMA Intelligence Architecture: Cross-Domain Synthesis (April 2026)

**Synthesized from:** 8 research findings across memory systems, FHIR standards, bilingual NLP, GEPA optimization, MCP ecosystem, and 3D anatomy rendering.

**Date:** April 3, 2026

## The Convergence Thesis

Five independently researched domains converge into a unified intelligence architecture for SOMA:

1. **Agent Memory** (LOCOMO benchmark) → How SOMA stores and retrieves what users know
2. **FHIR/HL7 Standards** (CMS mandates) → How SOMA structures medical data
3. **Bilingual NLP** (SNOMED-CT ES + xMEN) → How SOMA bridges EN/ES medical terminology
4. **GEPA Prompt Evolution** (ICLR 2026) → How SOMA optimizes its educational explanations
5. **MCP Ecosystem** (healthcare-mcp-public, mcp-slicer) → How SOMA accesses external medical knowledge

The key insight: **These are not separate systems to bolt together — they are facets of a single dataflow from medical knowledge → structured storage → bilingual presentation → adaptive learning.**

---

## Unified Data Flow

```
[SNOMED-CT/LOINC/RxNorm] ──→ FHIR Resources ──→ Bilingual Term Mapper (xMEN)
                                      │                        │
                                      ▼                        ▼
                              [BodyStructure] ──→ 3D Model Mesh IDs
                              [Condition]     ──→ Encyclopedia Entries
                              [Observation]   ──→ Quiz Progress
                                      │
                                      ▼
                           MCP Client Layer (healthcare-mcp-public)
                                      │
                                      ▼
                           SOMA Memory Stack (4 tiers)
                                      │
                                      ▼
                           GEPA-Optimized Explanation Prompts
                                      │
                                      ▼
                           Adaptive Learning Path (spaced repetition)
```

---

## Layer 1: Knowledge Ingestion (FHIR + Terminology)

**Purpose:** Get authoritative medical data into SOMA's structured format.

### Data Sources
| Source | Coverage | SOMA Use |
|--------|----------|----------|
| SNOMED-CT (EN) | 350K+ concepts | Anatomy facts, conditions |
| SNOMED-CT Spanish Edition (May 2025) | Official ES translations | Bilingual term pairs |
| LOINC | Lab/clinical observations | Quiz content |
| RxNorm | Medications | Pharmacology module |
| BodyParts3D/Z-Anatomy | 3D meshes | Visual anatomy models |

### Ingestion Pipeline
1. **FHIR Resources** store medical data with standard codes (`BodyStructure`, `Condition`, `ValueSet`)
2. **xMEN normalizes** free-text descriptions to SNOMED concept IDs across languages
3. **Lookup table** built: `SNOMED_ID → {en_label, es_label, en_desc, es_desc, en_friendly, es_friendly, mesh_id}`
4. **FHIR bodySite → 3D mesh mapping** using SNOMED anatomy codes (already documented in soma-fhir-to-3d-mapping-architecture.md)

### Key Design Decision
Use **Medplum** as FHIR backend (self-hosted Docker for dev, cloud for production). Its React component library + terminology services + SMART on FHIR auth covers SOMA's needs. The eCoach PoC (PMC9147872) proves 0% data loss with FHIR + SNOMED-CT on mobile.

---

## Layer 2: External Knowledge Access (MCP)

**Purpose:** Access dynamic medical data that changes faster than static builds.

### MCP Server Stack
| Server | Role | Priority |
|--------|------|----------|
| healthcare-mcp-public (104★) | FDA, PubMed, ICD-10, clinical trials, DICOM | P0 — primary |
| mcp-slicer (27★) | 3D Slicer integration, mesh processing | P1 — asset pipeline |
| medadapt-content-server | Educational content generation | P2 — enrichment |

### Integration Pattern
```typescript
// SOMA MCP Client (offline-first)
class SomaMCPClient {
  private cache: SQLite;  // Offline cache
  private server: MCPServer;

  async queryMedicalTerm(snomedId: string, lang: 'en' | 'es') {
    // 1. Check local cache first
    const cached = await this.cache.get(snomedId, lang);
    if (cached && !isStale(cached)) return cached;

    // 2. Query MCP server
    const result = await this.server.call('search_term', { snomedId, lang });

    // 3. Cache for offline use
    await this.cache.set(snomedId, lang, result);
    return result;
  }
}
```

### Offline Strategy
- **Core anatomy facts:** Bundled at build time (always available)
- **Clinical enrichment:** Cached from MCP, stale-after-7-days policy
- **Quiz content:** Generated offline from bundled data, enriched when online
- **Token budget:** ~1,800 tokens per query (per LOCOMO benchmark)

---

## Layer 3: Memory Architecture (4 Tiers)

Based on the LOCOMO benchmark results and arXiv:2512.13564 taxonomy:

| Tier | Type | Storage | Token Budget | Example |
|------|------|---------|-------------|---------|
| **Factual** | What SOMA knows | SQLite + bundled JSON | ~800/interaction | "El corazón tiene 4 cámaras" |
| **Experiential** | What the user learned | SQLite (synced) | ~500/interaction | "User struggled with heart anatomy quiz" |
| **Working** | Current interaction | In-memory + snapshots | ~300/interaction | "Selected: Left Ventricle, mode: dissection" |
| **External** | MCP queries | MCP cache | ~200/interaction | Drug interaction for metformin" |

**Total per interaction: ~1,800 tokens** — matching Mem0g's sweet spot from LOCOMO.

### Graph-Enhanced Retrieval
Pure vector search (like Honcho's pgvector) misses relational context. SOMA should use:
- **Entity-relationship graph:** Anatomy structure A connects to system B, relates to condition C
- **Graph traversal for "explore related":** Click heart → graph shows cardiovascular system, related conditions, adjacent structures
- **Mem0g's approach (68.4% accuracy) > Mem0's pure vector (66.9%)** at nearly identical latency

---

## Layer 4: Adaptive Explanation Engine (GEPA)

**Purpose:** Optimize how SOMA explains medical concepts to different audiences.

### GEPA Application to SOMA
GEPA (ICLR 2026 Oral) outperforms RL approaches with 35x fewer rollouts. For SOMA:

1. **Sample trajectories:** Collect quiz results + explanation ratings across audience tiers
2. **Reflect in natural language:** "The Professional-tier explanation for 'myocardial infarction' had 90% quiz pass rate, but the Layman-tier only 60%"
3. **Propose prompt updates:** Modify the layman explanation template to include analogy-based descriptions
4. **Pareto frontier:** Keep prompts that perform well across multiple metrics (accuracy, engagement, retention)
5. **Iterate monthly** with accumulated learning data

### Tier System (already designed)
| Tier | Audience | Explanation Style | Spanish |
|------|----------|-------------------|---------|
| Layman | General public | Analogy-based, jargon-free | Lenguaje cotidiano |
| Student | Medical students | Technical terms + context | Terminología técnica |
| Professional | Doctors/researchers | Full clinical detail | Detalle clínico completo |

### Cost Efficiency
GEPA's 35x reduction in rollouts means SOMA can optimize prompts for **$0.03 per prompt** vs **$1.05 with GRPO** — affordable for a bootstrapped project.

---

## Layer 5: Adaptive Learning (Spaced Repetition)

**Purpose:** Use experiential memory to personalize the learning path.

### Algorithm
1. Track user interactions per anatomy structure (time spent, quiz scores, return visits)
2. Calculate **retention score** per topic using Ebbinghaus forgetting curve
3. When retention drops below threshold, surface review material
4. Use GEPA to optimize the review prompt based on past performance
5. Sync progress to FHIR `Observation` resources for portability

### FHIR Integration for Learning Data
```json
{
  "resourceType": "Observation",
  "code": { "coding": [{ "system": "http://soma.health/learning", "code": "quiz-score" }] },
  "bodySite": { "coding": [{ "system": "http://snomed.info/sct", "code": "80248007" }] },
  "valueQuantity": { "value": 85, "unit": "%", "system": "http://unitsofmeasure.org" },
  "interpretation": [{ "coding": [{ "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", "code": "N" }] }]
}
```
This maps quiz scores to specific anatomy structures using SNOMED bodySite codes — enabling portable learning records.

---

## Implementation Priority Matrix

| Phase | Component | Dependencies | Impact | Effort |
|-------|-----------|-------------|--------|--------|
| **P0** | Bilingual term lookup (SNOMED ES) | SNOMED Spanish Edition | High | Low |
| **P0** | FHIR data model (Medplum) | Docker + Medplum | High | Medium |
| **P1** | SQLite memory + offline cache | React Native/WebView | High | Medium |
| **P1** | MCP client (healthcare-mcp-public) | MCP SDK | Medium | Medium |
| **P2** | Graph-enhanced retrieval | SQLite schema | Medium | High |
| **P2** | GEPA prompt optimization | Learning data collected | High | High |
| **P3** | Spaced repetition engine | Experiential memory | Medium | Medium |
| **P3** | FHIR learning records export | FHIR + memory | Low | Low |

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| MCP servers go down | Medium | Medium | Offline cache + bundled data |
| SNOMED ES coverage gaps | Medium | Medium | BioMistral 2 fallback for missing terms |
| Mobile performance (graph queries) | Low | High | Pre-compute graph edges at build time |
| GEPA overfitting on small data | Medium | Low | Require 50+ samples before optimization |
| FHIR compliance complexity | Low | Medium | Start with education-only resources |

---

## Knowledge Gaps (Future Research)

1. **3D mesh → SNOMED mapping at scale:** Need automated pipeline for BodyParts3D/Z-Anatomy meshes to SNOMED bodySite codes
2. **Spanish medical education prompt benchmark:** No existing benchmark for ES medical explanation quality
3. **Mobile SQLite graph performance:** Need benchmarks for graph traversal on iOS/Android
4. **GEPA + multilingual:** GEPA paper only tested English — unknown if reflection works across languages
5. **MCP security:** No auth standard for MCP servers — need research on secure medical data access

## Sources
- arXiv:2512.13564 — Agent Memory Architectures Survey
- arXiv:2504.19413 — LOCOMO Benchmark (Mem0)
- arXiv:2507.19457 — GEPA Prompt Evolution (ICLR 2026)
- PMC9147872 — eCoach FHIR+SNOMED PoC
- https://github.com/Cicatriiz/healthcare-mcp-public
- https://github.com/hpi-dhc/xmen
- https://www.nlm.nih.gov/pubs/techbull/mj25/brief/mj25_snomed_spanish_may.html
- https://www.medplum.com/docs


## Sources

- https://arxiv.org/abs/2512.13564
- https://arxiv.org/abs/2504.19413
- https://arxiv.org/abs/2507.19457
- https://github.com/Cicatriiz/healthcare-mcp-public
- https://github.com/hpi-dhc/xmen
- https://www.medplum.com/docs
