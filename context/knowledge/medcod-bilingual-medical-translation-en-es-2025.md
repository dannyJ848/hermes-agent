# medcod-bilingual-medical-translation-en-es-2025

*Researched: 2026-04-04 20:59 CDT*

# MedCOD: EN→ES Medical Translation via Chain-of-Dictionary (EMNLP 2025 Findings)

## Paper Details
**Authors:** Salim, Fu, Ramakrishnan, Yao, Yu (UMass Lowell, UMass Amherst, VA Bedford)
**Venue:** Findings of EMNLP 2025
**DOI:** 10.18653/v1/2025.findings-emnlp.350

## Key Innovation
MedCOD (Medical Chain-of-Dictionary) integrates domain-specific structured knowledge into LLMs for English-to-Spanish medical translation. Combines UMLS knowledge + LLM-as-Knowledge-Base paradigm.

## Architecture
1. **Structured Prompts:** Incorporate multilingual variants, medical synonyms, UMLS-derived definitions
2. **LoRA Fine-tuning:** Adapted on 2,999 parallel EN-ES MedlinePlus articles
3. **Evaluation:** 100-sentence test set with structured medical context annotations

## Results
- **Phi-4 + MedCOD + LoRA:** BLEU 44.23, chrF++ 28.91, COMET 0.863
- **Surpasses GPT-4o and GPT-4o-mini** on medical translation metrics
- Open-source models (Phi-4, Qwen2.5-14B, Qwen2.5-7B, LLaMA-3.1-8B) all improved
- Ablation: Both prompting and fine-tuning independently contribute gains

## Relevance to SOMA
- **Direct application:** SOMA's bilingual medical encyclopedia can use MedCOD-style structured prompts
- **UMLS integration:** SOMA's medical content pipeline should leverage UMLS for term consistency
- **Training data:** MedlinePlus parallel corpus is a potential resource for SOMA content
- **Architecture pattern:** Chain-of-Dictionary prompting could enhance SOMA's medical term mapper

## Implementation Ideas for SOMA
1. Build a medical synonym dictionary using UMLS for SOMA's term mapper
2. Use structured prompts with term variants when generating bilingual content
3. Consider LoRA fine-tuning a smaller model (Phi-4 or Qwen2.5-7B) on SOMA-specific medical content
4. Create a quality evaluation pipeline using BLEU/chrF++/COMET metrics for generated translations


## Sources

- https://pmc.ncbi.nlm.nih.gov/articles/PMC12878947/
