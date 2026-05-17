# snomed-ct-spanish-edition-2025-soma

*Researched: 2026-04-07 13:03 CDT*

# SNOMED CT Spanish Edition (May 2025) - SOMA Bilingual Terminology

## Key Finding
NLM released the **May 2025 SNOMED CT Spanish Edition** — official Spanish translations of the full SNOMED CT clinical terminology.

## Access
- Download: Requires UMLS Metathesaurus License + UMLS Terminology Services login
- License info: https://www.nlm.nih.gov/healthit/snomedct/us.html
- This is FREE for non-commercial use (covers SOMA)

## SOMA Integration Path
1. **soma-bilingual-medical-terms skill** can use SNOMED CT Spanish Edition as authoritative source
2. Map anatomy terms (EN) → SNOMED CT concept ID → Spanish translation
3. Creates a standardized, medically-accurate bilingual dictionary
4. Covers: body structures, clinical findings, procedures, organisms, substances

## Why This Matters
- Previously SOMA relied on manual EN/ES translations from medical dictionaries
- SNOMED CT Spanish Edition provides **standardized, peer-reviewed** Spanish medical terms
- ~350,000+ concepts with Spanish translations
- Updates twice yearly (May/November releases)

## Next Steps
1. Apply for UMLS license (free for research/non-commercial)
2. Download SNOMED CT Spanish Edition RF2 release files
3. Extract anatomy-relevant concepts (body structure hierarchy)
4. Build EN→SNOMED→ES mapping table for SOMA


## Sources

- https://www.nlm.nih.gov/pubs/techbull/mj25/brief/mj25_snomed_spanish_may.html
- https://www.snomed.org/maps
