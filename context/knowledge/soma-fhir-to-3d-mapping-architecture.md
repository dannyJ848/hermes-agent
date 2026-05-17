# soma-fhir-to-3d-mapping-architecture

*Researched: 2026-04-02 16:07 CDT*

# SOMA FHIR R4 → 3D Body Model Mapping Architecture

## Resource-to-Region Mapping

| FHIR Resource | bodySite Element | Visual Mapping |
|---|---|---|
| BodyStructure | location (CodeableConcept) | Primary spatial anchor |
| Observation | bodySite | Visual indicator overlay |
| Condition | bodySite | Highlighted/diseased region |
| Procedure | bodySite | Intervention site marker |
| MedicationStatement | Indirect: reasonReference→Condition | Pharmacological system overlay |
| ImagingStudy | series.bodySite | Volume/render overlay |

## Key SNOMED CT Codes for 3D Mapping

- Heart: 80248007, Left Ventricle: 87878005, Right Atrium: 73829007
- Liver: 10200004, Spleen: 78961009, Kidney: 64033007
- Pancreas: 15776009, Lung: 181216001 (Left: 72410000, Right: 76848001)
- Brain: 12738006, Bone: 272673000, Knee: 62106008
- Cardiovascular: 51185008, Respiratory: 31078005

## Laterality Codes
Left: 7771000, Right: 24028007, Bilateral: 51440002

## Lab-to-Region Inference (Systemic)
- BNP → Heart (80248007)
- eGFR → Kidney (64033007)
- ALT/ALP → Liver (10200004)
- Glucose → Pancreas (15776009)
- Hemoglobin → Brain+Lungs (12738006, 72410000)

## Medication-to-Region Inference (ATC)
- ACE Inhibitors (C09A) → Heart, Kidney
- Beta Blockers (C07) → Heart
- Statins (C10AA) → Brain, Heart, Coronary arteries
- NSAIDs (M01A) → Kidney, Liver, GI (risk overlay)
- Metformin → Pancreas, Kidney, Liver
- Anticoagulants (B01) → Cardiovascular, Brain

## Visual Indicators by Severity
- Normal: #4CAF50, opacity 0.0
- Monitor: #2196F3, opacity 0.15
- Moderate: #FFC107, opacity 0.3, pulse 2000ms
- Warning: #FF9800, opacity 0.45, pulse 1500ms
- Critical: #F44336, opacity 0.6, pulse 800ms

## Recommended FHIR Client
`fhirclient` (SMART on FHIR, HL7 official, TypeScript defs included)
Plus `@types/fhir` for R4 type definitions.

## FHIR Compartment Search Pattern
```
Patient/{id}/Condition?clinical-status=active
Patient/{id}/Observation?category=vital-signs,laboratory&_count=200
Patient/{id}/MedicationStatement?status=active
Patient/{id}/BodyStructure
```


## Sources

- https://hl7.org/fhir/R4/bodystructure.html
- https://www.snomed.org/
- https://github.com/smart-on-fhir/client-js
