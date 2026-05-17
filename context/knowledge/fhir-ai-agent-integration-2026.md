# fhir-ai-agent-integration-2026

*Researched: 2026-04-04 21:21 CDT*

# Agent on FHIR: AI Agents Reading/Writing Clinical Data (2026)

## Key Architecture: FHIR as the OS for Healthcare AI
98% of US hospitals now expose FHIR R4 APIs (ONC 21st Century Cures Act mandate).

## What an Agent Reads from FHIR
- GET /Patient/{id} — demographics
- GET /MedicationRequest?patient={id}&status=active — current meds
- GET /Observation?patient={id}&category=laboratory — lab results
- GET /AllergyIntolerance?patient={id}&clinical-status=active — allergies
- GET /Condition?patient={id}&clinical-status=active — diagnoses
- GET /DocumentReference?patient={id}&type=LOINC|11506-3 — clinical notes

## What an Agent Writes to FHIR
- POST /Communication — alerts to care team
- POST /Task — follow-up tasks
- PUT /Observation — derived clinical insights
- POST /DocumentReference — generated summaries

## Three Integration Patterns
1. **CDS Hooks Agent**: Triggered by clinical workflow events
2. **SMART App Agent**: OAuth2-scoped background agent
3. **Event-Driven Agent**: Subscribed to FHIR Subscriptions

## MCP-FHIR: The Emerging Standard
HL7 is building AI Transparency on FHIR spec. Researchers publishing MCP-FHIR frameworks
that give LLMs structured tool access to clinical data. AWS launched Connect Health with FHIR AI.

## Critical Design Rule
Load ONLY what the agent needs. Selective loading reduces token consumption 40-60%
and enforces HIPAA minimum necessary principle.

## Relevance to SOMA
Our FhirAdapter.ts already maps 45 SNOMED/LOINC/ATC terms. Next step: connect to actual
FHIR server endpoints and implement read operations for patient data display.
MCP-FHIR could give us standardized tool access to any FHIR-compliant EHR.


## Sources

- https://nirmitee.io/blog/agent-on-fhir-building-ai-agents-read-write-clinical-data/
