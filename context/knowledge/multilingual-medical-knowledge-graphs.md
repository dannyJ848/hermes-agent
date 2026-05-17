# multilingual-medical-knowledge-graphs

*Researched: 2026-03-31 23:07 CDT*

# Multilingual Medical Knowledge Graphs: EN/ES for SOMA

## Key Resources for SOMA
1. **UMLS** (NLM): ~4.4M concepts, 1.2M+ have Spanish strings. CUI = language-agnostic linking key. Filter MRCONSO.RRF by LAT=SPA.
2. **ICD-11** (WHO): Natively multilingual. Spanish built into core. Easiest win.
3. **MeSH/DeCS** (BIREME/PAHO): ~33K Spanish descriptors, curated for Latin American/Caribbean health. Annual updates.
4. **SNOMED CT Spanish**: ~340K translated descriptions. Spain is a member nation = free access.

## Recommended SOMA Stack
- **Concept Embeddings**: SapBERT-XLM (fine-tuned on UMLS)
- **Sentence/Document**: mE5-large (fine-tuned on medical parallel text)
- **KG Structure**: RotatE on UMLS/SNOMED graph
- **Linking Layer**: CUI as universal anchor (language-agnostic)

## Cross-Lingual Entity Linking Pipeline (Practical Hybrid)
1. Dictionary lookup: exact match against UMLS Spanish strings -> CUI (catches ~60-70%)
2. Fuzzy/similarity: SapBERT/XLM-R semantic similarity -> CUI (catches ~20% more)
3. LLM fallback: multilingual medical LLM for the tail ~10%

## Key Insight
The CUI (Concept Unique Identifier) is the universal anchor. One CUI maps to "hypertension" (EN) and "hipertension" (ES). Build everything around CUIs, not around language-specific strings.

## Active Groups to Follow
- NLM/NIH (UMLS research)
- BIREME/PAHO (DeCS, Latin American medical informatics)
- BIGG Barcelona (Spanish biomedical NLP)
- LINNAEUS group DCU Ireland (multilingual biomedical text mining)

## Research Directions
- "multilingual medical knowledge graph"
- "cross-lingual biomedical entity linking"
- "UMLS multilingual embeddings"
- "health equity NLP Spanish"
- "DeCS knowledge graph"


## Sources

- https://www.nlm.nih.gov/research/umls/
- https://www.snomed.org/
- https://icd.who.int/en
- https://decs.bvsalud.org/
