# fhir-r4-typescript-ecosystem

*Researched: 2026-04-02 17:42 CDT*

# FHIR R4 TypeScript Ecosystem (Solara Health)

**Source:** github.com/SolaraHealthAU/fhir (MIT license)
**Relevance:** Direct replacement/enhancement for SOMA's FhirAdapter.ts

## What It Provides
Two packages:
- `@solarahealth/fhir-r4` -- Types, validation, and utilities for FHIR R4
- `@solarahealth/fhir-r4-server` -- Full FHIR R4 server implementation

## Key Features
- Bulletproof TypeScript type safety for all FHIR R4 resources
- Runtime validation (not just compile-time)
- Monorepo with Lerna
- MIT license (compatible with SOMA)
- 77 commits, actively maintained

## Integration Opportunity
SOMA's current `FhirAdapter.ts` manually maps SNOMED, LOINC, ATC codes. This library could:
1. Replace manual type definitions with validated FHIR R4 types
2. Add proper FHIR server capability for local data storage
3. Enable FHIR-compliant API endpoints for EHR integration

## Action Items
1. `npm install @solarahealth/fhir-r4`
2. Refactor FhirAdapter.ts to use their types instead of manual interfaces
3. Evaluate fhir-r4-server for local FHIR data persistence


## Sources

- https://github.com/SolaraHealthAU/fhir
