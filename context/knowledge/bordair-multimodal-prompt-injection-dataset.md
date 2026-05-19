# bordair-multimodal-prompt-injection-dataset

*Researched: 2026-04-10 09:13 CDT*

# Bordair: Multimodal Prompt Injection Test Suite

**Source:** Josh-blythe/bordair-multimodal-v1 (GitHub, April 2026)
**Size:** 61,875 labeled samples (38,117 attack + 23,758 benign)

## What It Covers
- **v1 (47,518 samples):** Cross-modal split attacks — text+image, text+document, text+audio, image+document, triple, and quad-modality combinations
- **v2 (14,358 samples):** Multi-turn orchestration, GCG adversarial suffixes, jailbreak templates via PyRIT + nanoGCG

## Attack Delivery Methods
- **Image:** OCR text, EXIF metadata, PNG chunks, XMP metadata, white-on-white text, LSB steganography, adversarial pixel perturbation
- **Document:** Body/footer/metadata/comment/hidden-layer embedding in PDF, DOCX, XLSX, PPTX
- **Audio:** Speech, ultrasonic, whispered, background, reversed, speed-shifted

## Cross-Modal Split Strategies
1. `benign_text_full_injection` — Benign text wrapper, full injection in non-text modality (FigStep, AAAI 2025)
2. `split_injection` — Payload split across modalities (CrossInject, ACM MM 2025)
3. `authority_payload_split` — Authority claim in one modality, command in another
4. `context_switch_injection` — Delimiter/context switch in one modality, payload in another

## Relevance to Hermes
- Directly applicable to email_screen and input validation for multimodal inputs
- The benign edge cases (".gitignore", "CSS override", "heart bypass surgery") are excellent test cases for reducing false positives in prompt injection detection
- The split-injection strategies reveal attack vectors that single-modality detectors miss

## Sources

- https://github.com/Josh-blythe/bordair-multimodal-v1
