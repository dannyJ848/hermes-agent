# medgemma-1.5-google-medical-vlm

*Researched: 2026-04-03 21:03 CDT*

# MedGemma 1.5: Google's Open Medical Vision Language Model

**Source:** Google DeepMind / Health AI Developer Foundations
**Released:** January 2026
**License:** Open access (Gemma terms)

## What It Does
- First public open multimodal LLM interpreting high-dimensional medical images
- Collection of Gemma 3 variants trained for medical text + image comprehension
- Supports: radiology report drafting, image-based medical Q&A, clinical data extraction
- Companion MedASR model for medical speech-to-text

## Key Capabilities
- Interprets medical images (X-ray, CT, pathology slides, dermatology)
- Generates radiology reports from images
- Extracts pertinent clinical data
- Multilingual text comprehension (relevant for SOMA's EN/ES bilingual needs)

## Relevance to SOMA
- HIGH: Could power "explain this scan" feature for medical students
- EN/ES bilingual medical text comprehension aligns with SOMA's target audience
- Open weights available via HuggingFace
- Can be quantized (GGUF) for on-device or edge deployment
- MedASR useful for voice-driven anatomy exploration

## Integration Path
1. Download weights from HuggingFace (google/medgemma-1.5)
2. Quantize with llama.cpp for mobile inference
3. Expose via REST API for SOMA's anatomy viewer
4. Use for bilingual medical content generation (encyclopedia entries)


## Sources

- https://research.google/blog/next-generation-medical-image-interpretation-with-medgemma-15-and-medical-speech-to-text-with-medasr/
- https://developers.google.com/health-ai-developer-foundations/medgemma/model-card
- https://deepmind.google/models/gemma/medgemma/
