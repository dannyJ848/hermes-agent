# smart-fhir-cds-hooks-soma-integration-2026

*Researched: 2026-04-04 22:09 CDT*

# SMART on FHIR + CDS Hooks: SOMA Hospital Integration Path (April 2026)

## Executive Summary
SMART on FHIR and CDS Hooks form the **authorization and clinical decision support layer** that SOMA needs for real hospital EHR integration. All US-certified EHRs have been required to support SMART on FHIR APIs since end of 2022. This finding maps the integration path from standalone app → EHR-embedded clinical tool.

## SMART on FHIR v2.2.0 (Current Standard)
- **What**: Combines FHIR data standard with OAuth2 authorization and OpenID Connect authentication
- **Goal**: "Write once, run unmodified across different healthcare IT systems"
- **Mandate**: Required for all certified US EHRs (21st Century Cures Act)
- **Supported by**: Epic, Oracle Health/Cerner, Allscripts, Apple, Google, Microsoft
- **Architecture**: Substitutable app model — apps register with EHR, launch via OAuth2 flow, access FHIR resources via scoped tokens
- **Best Practices (v2.2)**:
  - Use refresh tokens only once (OAuth 2.1 §6.1)
  - Bind tokens to asymmetric secrets in hardware (DPOP spec)
  - Use wildcard + fine-grained SMART 2.0 scopes for least privilege
  - Transparent consent: short + long scope descriptions in user's language

## CDS Hooks (HL7 Standard)
- **What**: EHR invokes external CDS services at key workflow moments via HTTPS/JSON
- **How it works**: EHR (CDS client) sends JSON payload → CDS service returns "cards" (guidance, actions, or SMART app launch links)
- **Key hooks for SOMA**:
  - `patient-view`: Triggers when clinician opens patient record → launch SOMA anatomy viewer
  - `order-select`: Triggers when selecting a procedure → show relevant anatomy
  - `order-sign`: Before finalizing orders → verify anatomical context
- **Integration pattern**: CDS Hooks card → launches SMART on FHIR app (SOMA) → receives FHIR patient context
- **Evidence**: University of Utah ED trial showed CDS Hooks prompts doubled SMART app (MDCalc) utilization from 2.6% → 6.0% (OR≈2.45, p=0.02)

## FDA 2026 CDS Guidance Update (Key for SOMA)
- **Criterion 3 relaxed**: Enforcement discretion for single-recommendation outputs if only one clinically appropriate option exists
- **LLM considerations**: New examples address AI/LLM summarization use cases
- **Implication**: SOMA's anatomy recommendations could qualify as non-device CDS if they meet 4 criteria (display/analyze medical info, support HCP decisions, HCP can independently review basis)
- **Risk classification**: If SOMA goes beyond display (e.g., AI-driven diagnosis suggestions), it enters medical device territory → need 510(k) pathway

## SOMA Integration Architecture

```
EHR (Epic/Cerner)
    │
    ├── patient-view hook fires
    │   └── CDS Service receives patient context (FHIR Patient resource)
    │       └── Returns Card: "View 3D Anatomy → Launch SOMA"
    │           └── SMART on FHIR launch with OAuth2
    │               └── SOMA app receives:
    │                   ├── Patient demographics
    │                   ├── Condition/Diagnosis resources
    │                   ├── Procedure resources (surgical history)
    │                   └── ImagingStudy references (DICOM links)
    │
    └── SOMA renders anatomy based on patient context
        ├── Highlight affected regions from Conditions
        ├── Show surgical sites from Procedures
        └── Link to DICOM viewer via ImagingStudy
```

## FHIR Coverage Resource (Insurance Integration)
- Standardized structure for patient insurance/payment data
- Used for prior authorizations, eligibility checks, cost lookups
- **Da Vinci Coverage Requirements Discovery IG**: Payer-side coverage exposure at point of care
- **Relevance**: SOMA could verify coverage for anatomy-guided procedures

## Action Items for SOMA
1. **Phase 1**: Implement SMART on FHIR standalone launch (OAuth2 + FHIR scopes)
2. **Phase 2**: Register as CDS Hooks service → embed in EHR workflow
3. **Phase 3**: Add patient-context rendering (condition → anatomy highlighting)
4. **Phase 4**: FDA CDS compliance assessment (stay in non-device CDS zone)

## Key Standards References
- SMART App Launch v2.2.0: https://build.fhir.org/ig/HL7/smart-app-launch/
- CDS Hooks: https://cds-hooks.hl7.org/
- FDA CDS Guidance 2026: https://www.hardianhealth.com/insights/fda-2026-clinical-decision-support-c-guidance-update
- Da Vinci IGs: https://www.hl7.org/fhir/us/davinci/


## Sources

- https://intuitionlabs.ai/articles/smart-on-fhir-cds-hooks-coverage-guide
- https://www.hardianhealth.com/insights/fda-2026-clinical-decision-support-c-guidance-update
- https://build.fhir.org/ig/HL7/smart-app-launch/best-practices.html
- https://www.researchgate.net/publication/384042934_AI_Integration_in_Clinical_Decision_Support_Systems
