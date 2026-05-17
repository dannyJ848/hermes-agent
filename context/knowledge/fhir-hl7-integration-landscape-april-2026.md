# fhir-hl7-integration-landscape-april-2026

*Researched: 2026-04-03 05:04 CDT*

# FHIR/HL7 Integration Landscape for SOMA — April 2026

## Regulatory Context
- **CMS-0057-F Interoperability and Prior Authorization Final Rule** took effect January 2026 — FHIR is now legally mandated
- Payers must report Patient Access API usage metrics to CMS starting 2026
- 21st Century Cures Act reinforces FHIR as the backbone of healthcare data exchange
- 73% of countries with health data regulations now mandate or recommend FHIR (up from 56% in 2024)
- Over 90% of U.S. hospitals use FHIR-enabled systems

## Open-Source FHIR Platforms

### Medplum (Recommended for SOMA)
- **Headless EHR** — full-stack open-source platform
- React component library (pre-built clinical UI components)
- FHIR datastore with search + GraphQL support
- Terminology services (SNOMED-CT, LOINC, RxNorm)
- Self-hostable on AWS, GCP, Azure, or Docker
- SMART on FHIR support for clinical auth
- HL7 interface engine + FHIRcast for real-time sync
- AI bot framework for automation
- **GitHub:** medplum/medplum (MIT license)

### HAPI FHIR
- Java-based reference FHIR server implementation
- Most mature FHIR server, but heavier than Medplum
- Better suited for enterprise backends than mobile-first apps

## Terminology Binding (Critical for SOMA)

### SNOMED-CT + FHIR
- FHIR `Observation` resource is the primary structure for clinical data
- SNOMED-CT codes bind to `code`, `valueCodeableConcept`, and `bodySite` fields
- LOINC covers lab/clinical observations, RxNorm covers medications
- **eCoach proof-of-concept** (PMC9147872) achieved 0% data loss combining FHIR + SNOMED-CT in a mobile PHR app

### Bilingual Terminology Strategy
- SNOMED-CT Spanish Edition (May 2025 NLM release) provides official ES translations
- FHIR `CodeSystem` and `ValueSet` resources can store bilingual display strings
- SOMA's xMEN-based terminology mapper can feed FHIR terminology services

## Architecture Recommendations for SOMA

1. **FHIR Backend:** Medplum self-hosted (Docker) for development, cloud for production
2. **Auth:** SMART on FHIR (OAuth 2.0) when clinical integration is needed
3. **Mobile Strategy:** Offline-first FHIR client (cache resources locally, sync when online)
4. **Terminology:** SNOMED-CT for anatomy, LOINC for observations, RxNorm for pharmacology
5. **Data Model:**
   - `Patient` → SOMA learner profiles
   - `Observation` → Quiz scores, learning progress, engagement metrics
   - `Condition` → Medical encyclopedia entries (structured)
   - `BodyStructure` → 3D anatomy model references with mesh IDs
6. **React Components:** Medplum's pre-built React components can accelerate SOMA's clinical UI

## Key FHIR Resources for Medical Education
- `BodyStructure` — anatomical locations (maps to SOMA 3D model pins)
- `Condition` — medical conditions (maps to SOMA encyclopedia)
- `Observation` — learner interactions, quiz results
- `Patient` → learner profile
- `Procedure` → simulated procedures in anatomy viewer
- `DiagnosticReport` → assessment summaries
- `ValueSet`/`CodeSystem` — bilingual terminology collections

## Sources
- HL7 Blog: Da Vinci 2026 Use Case Progress — https://blog.hl7.org/driving-change-in-2026
- Dogtown Media FHIR Mobile Guide — https://www.dogtownmedia.com/fhir-api-integration-in-mobile-app-development-the-complete-guide-for-businesses-in-2026/
- Medplum Docs — https://www.medplum.com/docs
- eCoach FHIR+SNOMED PoC (PMC9147872) — https://pmc.ncbi.nlm.nih.gov/articles/PMC9147872/
- LOINC FHIR Terminology Service — https://loinc.org/fhir/


## Sources

- https://blog.hl7.org/driving-change-in-2026-use-case-progress-and-preparing-for-hl7-fhir-adoption
- https://www.dogtownmedia.com/fhir-api-integration-in-mobile-app-development-the-complete-guide-for-businesses-in-2026/
- https://www.medplum.com/docs
- https://pmc.ncbi.nlm.nih.gov/articles/PMC9147872/
- https://loinc.org/fhir/
