# bilingual-en-es-medical-nlp-2026

*Researched: 2026-04-02 20:05 CDT*

# Bilingual EN/ES Medical NLP for SOMA (April 2026)

## Key Architecture Recommendations
1. **RAG approach** — Store MedLinePlus + MeSH terms in vector DB (Chroma/Qdrant), retrieve verified EN/ES definitions before LLM formatting
2. **Terminology API** — UMLS-backed dictionary with toggle: "Technical Terms (SNOMED)" vs "Plain Terms (MedLinePlus)"
3. **Model Selection** — Llama-3-8B-Instruct or Mistral-7B with medical system prompts (small enough for cheap hosting, smart enough for regional nuance)
4. **Regional Nuance** — Explicitly prompt for "standard Latin American Spanish with common regional variants"

## SNOMED CT Spanish: Key Challenges
- **No single "Spanish SNOMED"** — each country maintains national extensions (Spain, Argentina, Chile, Mexico, Colombia)
- **Coverage gaps in layman terms** — SNOMED is clinician-focused, needs mapping to consumer health vocabularies
- **Solution:** Use UMLS Metathesaurus to map SNOMED → MeSH → MedLinePlus across languages

## Best Open-Source Medical Corpora (EN/ES)
| Corpus | Use Case | Quality |
|--------|----------|---------|
| **MedLinePlus** (NIH) | Patient-facing medical Spanish, parallel EN/ES articles | ★★★★★ Foundation for app RAG |
| **SciELO** | Clinician-facing, peer-reviewed Latin American journals | ★★★★ For technical content |
| **CIE-10/ICD-10 Spanish** | Disease classification NER training | ★★★★ For structured data |
| **ClinSpEn** | Clinical Spanish-English parallel corpus | ★★★ For translation models |

## Translation Model Landscape (2025-2026)
- **Helsinki-NLP/Opus-MT:** Outdated for medical contexts — literal errors (e.g., "discharge" → *descarga* instead of *alta médica*)
- **Meta NLLB:** Better fluency, 600M-3.3B variants viable for on-device, but needs constrained decoding for medical terms
- **2025 Trend:** Instruction-tuned LLMs (Llama-3-8B, Mistral-7B) prompted as translators OUTPERFORM dedicated MT models in clinical accuracy
- **ClinSpEn/CliniTrad:** HuggingFace models fine-tuned on clinical EN/ES corpus

## Regional Variation Examples (Critical for SOMA)
- "Wheezing" → *sibilancias* (Mexico) vs *exceso de pitos* (Dominican Republic)
- Must handle both technical (doctor-facing) and plain language (patient-facing) registers

## SOMA Integration Plan
1. Build UMLS-backed terminology API with SNOMED → MedLinePlus mapping
2. Use MedLinePlus Spanish as primary RAG source for patient education
3. Fine-tune translation with ClinSpEn corpus for medical accuracy
4. Implement regional variant detection/selection in UI

## Sources

- https://medlineplus.gov/spanish/
- https://www.scielo.org
- https://www.nlm.nih.gov/research/umls/
