# fhir-r4b-r5-transition-2026

*Researched: 2026-04-02 21:37 CDT*

# FHIR R4B → R5 Transition (2026)

## Timeline
- **R4 (v4.0.1)**: October 2019 — Current production baseline, US federal mandates still on R4
- **R4B (v4.3.0)**: May 2022 — STU, backward-compatible with R4
- **R5 (v5.0.0)**: March 2024 — STU ballot, most significant update since R4, 159 resources
- **R5 normative**: Expected ~2026-2027

## Key Changes for Patient-Facing Apps

### Patient Resource (R5 Additions)
- `genderIdentity` — now first-class CodeableConcept (was extension in R4)
- `pronouns` — now first-class CodeableConcept (was extension in R4)
- `communication.language` — enhanced binding to BCP-47
- `personalRelationship` — new structured relationships element

### Condition Resource (R5 Breaking Changes)
- `bodySite` → **RENAMED** to `bodyStructure`, type changed from CodeableConcept to **CodeableReference(BodyStructure)**
- `evidence` backbone element → **REMOVED** — use ClinicalImpression instead
- `stage.assessment` changed to CodeableReference

### MedicationStatement Resource
- R5 adds `renderedDosageInstruction` for complex dosage display
- Enhanced adherence tracking elements

### Observation Resource
- R5 adds `referenceRange.text` improvements for patient-friendly ranges

## SMART on FHIR v2 Changes
- PKCE required (not optional)
- Token introspection improvements
- Scoped refresh tokens
- Better support for patient-facing apps (standalone launch)

## Multilingual Support in FHIR
- BCP-47 language tags throughout (e.g., `es-MX` for Mexican Spanish)
- `Translation` extension standard for translated display values
- ValueSet expansions can include language-designated displays
- R5 `Narrative` resource improved for multilingual content

## Open-Source TypeScript FHIR Libraries
- **@medplum/core** (Medplum) — Full FHIR client + React components, TypeScript-first
- **fhirclient** (smart-on-fhir) — SMART on FHIR launch framework
- **fhir.js** — Lightweight FHIR REST client
- **@sap/fhir** — Enterprise-grade FHIR server client

## SOMA FHIR Adapter Impact
Our current adapter (`src/anatomy/FhirAdapter.ts`) maps FHIR R4 → BiologicalSelf. Key considerations:
1. `bodySite` → `bodyStructure` rename in Condition will require R5-aware mapping
2. BCP-47 `es-MX` language tags align with SOMA's bilingual mission
3. SMART on FHIR v2 PKCE requirement affects auth flow
4. Medplum React components could replace custom FHIR UI elements


## Sources

- HL7 FHIR R5 specification (hl7.org/fhir/R5)
- FHIR R4B release notes
- SMART on FHIR v2 specification
