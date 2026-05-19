# spanish-medical-nlp-soma

*Researched: 2026-04-02 18:08 CDT*

# Spanish-Language Medical NLP for SOMA

## Key Finding: PlanTL-GOB-ES Ecosystem is the Foundation

The Barcelona Supercomputing Center (BSC) has built the most mature Spanish medical NLP ecosystem under PlanTL:

### Pretrained Biomedical Encoders
| Model | Corpus | Use Case |
|-------|--------|----------|
| `PlanTL-GOB-ES/roberta-base-biomedical-es` | ~2B tokens Spanish biomedical | General medical NER encoder |
| `PlanTL-GOB-ES/roberta-base-biomedical-clinical-es` | Clinical cases + guidelines | Clinical text specifically |

### NER Tasks Covered
- ✅ **PharmaCoNER**: Medications, active ingredients, dosages from Spanish clinical cases
- ✅ **DisTEMIST**: Diseases/disorders NER
- ✅ **MedProcNER**: Medical procedures
- ✅ **MEDDOCAN**: Personal health information detection (anonymization)
- ⚠️ **Partial**: Lab tests, vital signs, temporal expressions
- ❌ **Missing**: Social determinants, negation detection for Spanish

### No Single Model Extracts Everything
Must combine multiple NER heads or use LLM fallback for: conditions + medications + labs + vitals in one pass.

### Recommended SOMA Pipeline
```
spaCy (pipeline orchestration, Spanish tokenization)
├── HuggingFace Transformers
│   ├── PlanTL-GOB-ES/roberta-base-biomedical-es (encoder)
│   ├── Fine-tuned NER heads for conditions, medications
│   └── Separate models/rules for labs/vitals
├── Custom rule-based (regex)
│   ├── Spanish dosage/frequency patterns
│   ├── Lab value extraction (numeric + units)
│   └── Negation detection (Spanish linguistic patterns)
└── LLM fallback (GPT-4/Claude) for complex/ambiguous cases
```

### LLM Performance on Spanish Medical NER
| Approach | F1 Conditions | F1 Medications | Cost/1K docs |
|----------|--------------|---------------|-------------|
| GPT-4o (few-shot) | 88-92% | 90-94% | $5-20 |
| Fine-tuned encoder NER | 85-90% | 88-92% | $0.10-0.50 |
| Rule + encoder hybrid | 80-87% | 85-90% | $0.05-0.20 |

### Key Benchmarks
- **PharmaCoNER** (BioCreative V.5): Pharmacological NER, ~1000 Spanish cancer cases
- **MEDDOCAN** (IberLEF): Clinical document anonymization, 29 entity types
- **Cantemist** (IberLEF): Cancer text mining, NER + coding
- **DisTEMIST**: Disease NER and SNOMED CT coding in Spanish

### FHIR Terminology for Spanish
- **SNOMED CT Spanish Edition**: Available via SNOMED International
- **LOINC Spanish**: Partial translations available
- **UMLS Spanish**: Via Metathesaurus API, contains Spanish translations

### For SOMA Import Pipeline
Best approach: **Hybrid** — fine-tuned encoder for high-volume structured extraction + LLM fallback for messy PDFs/OCR output. Flag low-confidence extractions for user review.


## Sources

- https://huggingface.co/PlanTL-GOB-ES
- https://github.com/PlanTL
- https://temu.bsc.es/
- https://zenodo.org/record/3728enton
