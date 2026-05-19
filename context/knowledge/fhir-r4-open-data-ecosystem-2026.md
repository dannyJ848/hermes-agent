# fhir-r4-open-data-ecosystem-2026

*Researched: 2026-04-02 19:03 CDT*

# FHIR R4 Open Data Ecosystem for SOMA

## Key Open-Source FHIR Servers
- **HAPI FHIR** (Java, Apache 2.0): https://github.com/hapifhir/hapi-fhir — Public R4 test server at `https://hapi.fhir.org/baseR4`
- **Microsoft FHIR Server** (MIT): https://github.com/microsoft/fhir-server
- **IBM/FHIR** (Apache 2.0): https://github.com/IBM/FHIR
- **Firely Server** (.NET): https://fire.ly/products/firely-server/

## Test Data Sources
- **Synthea** (gold standard synthetic patient generator): https://github.com/synthetichealth/synthea — Generates FHIR R4 bundles
- **SMART Health IT Launcher**: https://launch.smarthealthit.org/ — Full OAuth simulation
- **MIMIC-IV FHIR**: https://physionet.org/content/mimic-iv-fhir/2.0/
- **Synthea Pre-Generated (1000 patients)**: https://github.com/synthetichealth/synthea-sample-data

## SMART on FHIR Auth Flow (Patient-Facing Apps)
1. Discover OAuth endpoints via `/.well-known/smart-configuration`
2. Redirect to authorization URL with `launch/patient patient/*.read openid fhirUser` scopes
3. User authenticates → authorization code
4. Exchange code for access token (includes `patient` ID in response)
5. Use Bearer token for FHIR API calls

## Key FHIR Resources for Anatomy Education
- **Patient**: Demographics + preferred language (bilingual EN/ES via `communication` field)
- **Condition**: Diagnoses with SNOMED CT body sites → maps to 3D anatomy regions
- **Observation**: Vitals, labs, measurements (LOINC codes)
- **BodyStructure**: Most relevant for anatomy — links morphologies to SNOMED CT locations
- **Procedure**: Surgeries/interventions with body sites
- **MedicationRequest/Statement**: Medications with ATC → target body regions
- **ImagingStudy**: DICOM references for visualization

## SOMA Integration Notes
- `FhirAdapter.ts` already has SNOMED_TO_REGION, LOINC_TO_ORGAN, ATC_TO_TARGETS maps
- BodyStructure resource is the key bridge from FHIR → 3D anatomy visualization
- Bilingual support: `text` fields can contain "English / Español" format
- SMART on FHIR standalone patient access is the correct auth pattern for consumer health apps
- Synthea can generate bilingual test patients for QA

## Code Patterns
```python
# Bilingual patient with FHIR communication field
"communication": [{
    "language": {"coding": [{"system": "urn:ietf:bcp:47", "code": "es"}]},
    "preferred": true
}]
```

```python
# Condition with bilingual text + body site mapping
"code": {"text": "Mitral Valve Regurgitation / Regurgitación de la válvula mitral"},
"bodySite": [{"coding": [{"system": "http://snomed.info/sct", "code": "74262004"}]}]
```


## Sources

- https://github.com/hapifhir/hapi-fhir
- https://github.com/synthetichealth/synthea
- https://launch.smarthealthit.org/
- https://hl7.org/fhir/smart-app-launch/
- https://hl7.org/fhir/R4/bodystructure.html
