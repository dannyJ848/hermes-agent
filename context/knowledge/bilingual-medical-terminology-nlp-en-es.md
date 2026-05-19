# bilingual-medical-terminology-nlp-en-es

*Researched: 2026-04-05 12:28 CDT*

# Bilingual Medical Terminology NLP (EN/ES) — Open Source Resources

## MedLexSp — Unified Medical Lexicon for Spanish NLP (2023)
- **Paper:** Campillos-Llanos, Journal of Biomedical Semantics, 2023
- **URL:** https://link.springer.com/article/10.1186/s13326-022-00281-5
- **Scale:** 100,887 lemmas, 302,543 inflected forms (conjugated verbs, gender/number variants), 42,958 UMLS CUIs
- **Sources aggregated:** UMLS, MeSH, SNOMED-CT, MedDRA, ICD-10, ATC, NCI Dictionary, OMIM, OrphaData, Spanish Royal Academy of Medicine Dictionary
- **COVID-19 terms** extracted via word embeddings similarity approach
- **Integration:** SpaCy lemmatizer module, Stanza lemmatizer module, XML (Lexical Markup Framework), delimiter-separated value files
- **Use cases:** Pre-annotation of clinical trial texts (1200 texts), improved PoS tagging and lemmatization over default SpaCy/Stanza
- **License:** Open access

## MedCOD — Medical Chain-of-Dictionary for EN→ES Translation (EMNLP 2025)
- **Paper:** ACL Anthology 2025.findings-emnlp.350
- **Hybrid framework** combining chain-of-dictionary lookups with LLM translation
- **Focus:** English-to-Spanish medical translation accuracy
- **Relevance:** Directly applicable to SOMA's bilingual anatomy content pipeline

## Spanish Clinical Coding with Open-Source LLMs (2024)
- **Paper:** CEUR-WS Vol-4119
- **Explores LLM-based automatic clinical coding in Spanish**
- **Aligned with 2024 medical coding challenge**

## Hybrid NER Tool for Spanish Medical Texts (2025)
- **Paper:** PMC 11708069
- **Deep learning + lexicon-based named entity recognition for Spanish clinical texts**
- **Semantic annotation** with medical ontology linking

## SOMA Integration Notes
1. **MedLexSp** is the highest-priority resource — it provides the exact bilingual medical terminology foundation SOMA needs for EN/ES anatomy term mapping
2. The SpaCy/Stanza integration modules could be dropped directly into SOMA's bilingual terminology mapper
3. MedCOD's chain-of-dictionary approach could enhance SOMA's real-time translation of medical descriptions
4. UMLS CUI linking enables cross-referencing with English medical databases


## Sources

- https://link.springer.com/article/10.1186/s13326-022-00281-5
- https://aclanthology.org/2025.findings-emnlp.350.pdf
- https://ceur-ws.org/Vol-4119/d31_rev.pdf
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11708069/
