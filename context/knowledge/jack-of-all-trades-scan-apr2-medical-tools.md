# jack-of-all-trades-scan-apr2-medical-tools

*Researched: 2026-04-02 21:06 CDT*

# Jack of All Trades Scan — Medical & Agent Tools (Apr 2, 2026)

## Top 5 Tools Discovered

### 1. Medplum (★2,240) — Score: 86/100
- **What:** Full-stack open-source FHIR platform (TypeScript/React)
- **Why SOMA:** React FHIR components, SMART-on-FHIR auth, self-hostable with Docker, Apache-2.0
- **Key insight:** Has 50+ React components for displaying FHIR resources (PatientSummary, MedicationTable, etc.) — could replace SOMA's custom FHIR rendering
- **Integration path:** `npm install @medplum/core @medplum/react` → wire into existing FhirAdapter.ts

### 2. DICOM-MCP (★88) — Score: 82/100
- **What:** MCP server for querying/retrieving DICOM data from PACS/VNA systems
- **Why SOMA:** Enables AI-agent-driven medical imaging access, connects to TCIA for educational content
- **Key insight:** C-FIND/C-MOVE/C-GET operations via MCP protocol — AI agents can query imaging directly
- **Integration path:** pip install → add to Hermes MCP config → use with soma-asset-pipeline

### 3. DWV-React (★129) — Score: 74/100
- **What:** DICOM Web Viewer as React components (zero-footprint, JavaScript/HTML5)
- **Why SOMA:** React-based medical image viewer for future radiology viewing in SOMA
- **Key insight:** Zero-footprint = no server-side rendering needed, runs entirely in browser

### 4. IBM Granite Speech 3.3 (★34) — Score: 73/100
- **What:** Open-source STT models (2B and 8B variants), Apache-2.0
- **Why SOMA:** Bilingual EN/ES speech recognition critical for SOMA's Spanish-speaking communities
- **Key insight:** Granite Speech 3.3 8B is one of the best open-source STT models in 2026; 2B variant runs on edge devices

### 5. FHIR-React (1uphealth) (★106) — Score: 72/100
- **What:** React component library for displaying FHIR data
- **Why SOMA:** Lightweight alternative to Medplum for just the display layer
- **Key insight:** Simpler than Medplum — good if SOMA only needs FHIR rendering, not a full backend

## Cross-Domain Patterns

1. **MCP for Healthcare is exploding:** awesome-medical-mcp-servers (★64) lists 12+ medical MCP servers including PubMed, DICOM, FHIR, NICE guidelines, and 3D Slicer integration
2. **AgentCare-MCP:** FHIR-to-EMR bridge (Epic/Cerner) — shows MCP can connect to real clinical systems
3. **DICOM + MCP convergence:** dicom-mcp enables AI agents to query PACS directly — this is the future of AI-assisted radiology
4. **Bilingual STT maturing:** Canary Qwen 2.5B, Granite Speech 3.3, and Speechmatics all pushing bilingual boundaries — SOMA's EN/ES voice interface is increasingly feasible

## Skills Created
- `mcp/medplum-fhir` — Full Medplum integration guide
- `mcp/dicom-mcp` — DICOM MCP server setup for Hermes

## Recommended Next Actions
1. Install Medplum SDK and test FHIR component rendering in SOMA
2. Add dicom-mcp to Hermes MCP config for TCIA dataset access
3. Evaluate Granite Speech 3.3 2B for on-device EN/ES STT
4. Create awesome-medical-mcp-servers bookmark for ongoing monitoring


## Sources

- https://github.com/medplum/medplum
- https://github.com/ChristianHinge/dicom-mcp
- https://github.com/ivmartel/dwv-react
- https://github.com/ibm-granite/granite-speech-models
- https://github.com/1uphealth/fhir-react
- https://github.com/sunanhe/awesome-medical-mcp-servers
- https://github.com/Kartha-AI/agentcare-mcp
