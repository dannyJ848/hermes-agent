# ocr-visual-grounding-medical-2025

*Researched: 2026-04-05 02:26 CDT*

# OCR & Visual Grounding for Medical Applications (2025-2026)

## OCR Landscape Revolution

### Pipeline → End-to-End VLM Shift
Traditional OCR required separate models for text detection, recognition, and layout analysis. 2024-2025 saw a paradigm shift to **end-to-end Vision Language Models (VLMs)** that process document images in a single pass, outputting structured markdown/HTML. Complex tables, equations, multi-column layouts handled natively.

### October 2025: 6 Major OCR Releases
- **Nanonets OCR2-3B** — Lightweight, fast
- **PaddleOCR-VL-0.9B** — VLM variant of most-starred OCR project (73K+ GitHub stars)
- **DeepSeek-OCR-3B** — Strong on technical documents
- **Chandra-OCR-8B** — Larger model, higher accuracy
- **OlmOCR-2-7B** — Allen AI's contribution
- **LightOnOCR-1B** — Efficient small model

### Cost Comparison
- Proprietary APIs: $1.50/1K pages (basic), $10-50/1K pages (structured)
- Self-hosted open-source: <$0.01/1K pages (GPU time only)
- 10M pages/month: $100K-500K (proprietary) vs <$10K (self-hosted)

### Top Recommendations for SOMA
1. **PaddleOCR-VL-0.9B** — Best for bilingual (EN/ES) medical text. Excellent non-Latin script support. Small enough for mobile edge inference. 73K+ stars, active community.
2. **DeepSeek-OCR-3B** — Strong on technical/scientific documents with formulas and diagrams.
3. **Tesseract 5.x** — Still viable for simple Latin-script text extraction, but outclassed by VLM approaches on complex layouts.

## Set-of-Mark (SoM) Visual Grounding

### What It Is
Microsoft Research (arXiv:2310.11441). Uses interactive segmentation (SAM/SEEM) to partition images into regions, overlays numbered marks (alphanumerics, masks, boxes). Multimodal models (GPT-4V, etc.) can then answer grounded visual questions.

### Key Results
- Zero-shot SoM + GPT-4V **beats SOTA fine-tuned** referring expression comprehension on RefCOCOg
- Enables visual QA without any training data
- Code: github.com/microsoft/SoM

### Extension: Graph-of-Mark (AAAI)
Adds spatial relationship graph between marks, enabling spatial reasoning (left-of, contains, adjacent-to). Published at AAAI.

## SOMA Integration Pathways

### 1. Medical Document Processing
- Self-hosted PaddleOCR-VL for HIPAA compliance
- Extract text from medical textbook scans, radiology reports, pharmaceutical labels
- Bilingual EN/ES support matches SOMA's target market

### 2. Visual Regression Testing
- SoM-style marking on SOMA's 3D anatomy viewer screenshots
- Ask VLM: "Is label #3 correctly positioned near the femur?" 
- Automated QA for label placement after code changes

### 3. Anatomy Image Annotation
- OCR to extract text labels from existing anatomy atlas images
- Cross-reference with SOMA's bilingual medical terminology database
- Automate content creation from open-source medical atlases

### 4. Screen Understanding for Testing
- Combine SoM + OCR to verify SOMA's UI state
- "Does the currently displayed anatomy model show the correct labels?"
- "Is the language toggle working (Spanish labels visible)?"

## Sources
- arxiv.org/abs/2310.11441 (SoM)
- e2enetworks.com/blog/complete-guide-open-source-ocr-models-2025
- unstract.com/blog/best-opensource-ocr-tools/ (2026 update)
- github.com/PADDLEPADDLE/PADDLEOCR


## Sources

- https://arxiv.org/abs/2310.11441
- https://www.e2enetworks.com/blog/complete-guide-open-source-ocr-models-2025
- https://unstract.com/blog/best-opensource-ocr-tools/
- https://github.com/PADDLEPADDLE/PADDLEOCR
- https://github.com/microsoft/SoM
