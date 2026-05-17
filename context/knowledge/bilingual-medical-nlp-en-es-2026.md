# bilingual-medical-nlp-en-es-2026

*Researched: 2026-04-02 18:18 CDT*

# Bilingual (EN/ES) Medical NLP for SOMA — 2026 Landscape

## Tier 1: Production LLMs
- **BioMistral-7B** — Medical domain, evaluated on 7 European languages incl. Spanish. Paper: arXiv:2402.10373
- **Qwen2.5-7B-Instruct** — Strong multilingual incl. Spanish, good for symptom descriptions
- **Aya-23-8B/35B** (Cohere For AI) — Purpose-built multilingual, good cross-lingual transfer

## Tier 2: Encoder Models (NER, Classification)
- **PlanTL-GOB-ES/roberta-large-biomedical-es** — Best-in-class for Spanish biomedical NER
- **PlanTL-GOB-ES/bert-base-biomedical-es** — Lighter, mobile-friendly
- **xlm-roberta-large** (fine-tuned) — Cross-lingual transfer EN→ES
- **microsoft/mdeberta-v3-base** — Efficient multilingual classifier

## Code-Switching (Spanglish)
- Don't fight it — use multilingual models that handle it natively (XLM-RoBERTa, mDeBERTa, BioMistral)
- Skip language detection as preprocessing — models handle mixed language
- For UI routing: use **lingua-py** (only library that handles short mixed-language text)
- LinCE benchmark: https://ritual.uh.edu/lince

## SNOMED-CT EN↔ES Alignment
- **SNOMED International Spanish Edition** — official translation, ~70-80% coverage
- **UMLS Metathesaurus** — Spanish terms via MRCONSO.RRF (LAT=SPA)
- **Snowstorm** (open-source SNOMED server) — supports Spanish language refsets
- **QuickUMLS** — fuzzy UMLS concept recognition (multilingual)
- Gotcha: SNOMED Spanish ≠ uniform across countries (Mexican vs Argentine vs Peninsular)
- Gotcha: Patients say "llaga" (sore), SNOMED says "úlcera" (ulcer) — need colloquial→formal mapping

## Open-Source Datasets
- **PharmaCoNER** (BSC) — Spanish clinical NER, ~1K cases
- **Cantemist** (BSC) — Spanish tumor morphology NER, ~9K cases
- **SciELO Parallel Corpus** — EN↔ES biomedical articles, ~200K sentence pairs
- **UFAL Medical Corpus** — EN↔ES medical texts, ~2M tokens
- **MedMCQA** — Medical MCQA, community ES translations on HF

## SOMA Architecture Recommendation
1. Generate bilingual content in parallel (not translate post-hoc)
2. PlanTL RoBERTa-es for NER/extraction
3. BioMistral-7B for generation/reasoning
4. UMLS lookup service for terminology alignment
5. Code-switching: let multilingual models handle it natively


## Sources

- arXiv:2402.10373
- https://huggingface.co/PlanTL-GOB-ES
- https://temu.bsc.es/pharmaconer/
- https://github.com/IHTSDO/snowstorm
