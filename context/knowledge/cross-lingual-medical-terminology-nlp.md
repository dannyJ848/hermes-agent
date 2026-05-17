# cross-lingual-medical-terminology-nlp

*Researched: 2026-04-05 12:49 CDT*

# Cross-Lingual Medical Terminology Alignment for SOMA (EN/ES)

## Key Finding
Cross-lingual medical entity linking to UMLS/SNOMED CT is the dominant approach for bilingual medical NLP. Papers confirm this is the right architecture for SOMA's bilingual terminology layer.

## Techniques Identified

### 1. UMLS-Based Entity Linking (MDTEL Pattern)
- **Source:** Bitton et al. (2020) JAMIA — "Cross-lingual UMLS Entity Linking"
- **Method:** Attention-based encoder-decoder + transliteration normalization → UMLS concept IDs
- **Key insight:** Medical terms in non-English text have high variability (transliteration, partial translation). Linking to UMLS CUIs normalizes them.
- **For SOMA:** Instead of maintaining separate EN/ES term lists, map BOTH languages to UMLS CUIs. One canonical concept per anatomy structure.

### 2. SNOMED CT International Edition
- **Source:** Sciencedirect review of machine translation of standardized medical terminology
- **SNOMED CT is most frequently translated** (39.1% of studies), followed by MeSH (13%), ICD (13%)
- **SNOMED CT Spanish edition exists** — official Spanish translation maintained by SNOMED International
- **For SOMA:** Use SNOMED CT as primary ontology. Its Spanish edition provides authoritative translations.

### 3. Cross-lingual Semantic Annotation
- **Source:** Bioinformatics 2020 — "Cross-lingual semantic annotation of biomedical literature"
- Compares approaches for identifying biomedical terms in Spanish and English text
- **For SOMA:** Can apply similar dual-annotation approach to anatomy descriptions

## Architecture Recommendation for SOMA
```
SOMA Bilingual Term System:
1. Each anatomy structure → UMLS CUI (canonical ID)
2. UMLS CUI → SNOMED CT concept ID (for medical precision)
3. CUI → EN preferred term (from UMLS MRCONSO table)
4. CUI → ES preferred term (from UMLS MRCONSO table, LAT="SPA")
5. Runtime: user language preference → look up CUI → return correct language term
```

## Key Resources
- UMLS Metathesaurus: contains EN + ES terms for ~4M concepts
- SNOMED CT Spanish Edition: authoritative medical translations
- MeSH (Medical Subject Headings): also available in Spanish
- MedlinePlus Health Topics: patient-facing EN/ES health content

## Implementation Priority
- Phase 1: Static bilingual term map (hardcoded EN/ES pairs from UMLS)
- Phase 2: Runtime UMLS lookup via API for dynamic terminology
- Phase 3: NLP-based entity linking for user queries in either language

## Sources
- PMC7566404: Cross-lingual UMLS Entity Linking (Bitton et al., 2020)
- Bioinformatics 36(6):1872 — Cross-lingual semantic annotation
- Sciencedirect — Machine translation of standardized medical terminology


## Sources

- https://pmc.ncbi.nlm.nih.gov/articles/PMC7566404/
- https://academic.oup.com/bioinformatics/article/36/6/1872/5626183
- https://www.sciencedirect.com/science/article/pii/S1871678423000432
