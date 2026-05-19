# paddleocr-mcp-server-integration

*Researched: 2026-04-05 02:07 CDT*

# PaddleOCR MCP Server — Drop-in Integration for Hermes Agent

## Executive Summary
PaddleOCR ships a **native MCP server** (`mcp_server/` in their GitHub repo). This means Hermes can add OCR + document parsing as a first-class tool with zero custom code — just config. No GPU required for basic OCR (CPU-mode supported).

## Key Discovery
- **Repository:** github.com/PaddlePaddle/PaddleOCR (74.9k stars)
- **MCP Server Location:** `mcp_server/` directory in the repo
- **License:** Apache 2.0
- **Integration method:** Standard MCP server — add to Hermes `config.yaml` under `mcp_servers`

## MCP Server Tools
The server exposes 2 primary tools:
1. **OCR Tool** — Extract text from images/PDFs → structured Markdown/JSON
2. **Document Structure Tool** (PP-StructureV3) — Parse complex documents with layout understanding (tables, figures, headers)

## Deployment Modes
- **Local mode** (recommended for Hermes): Runs on CPU, no GPU needed for basic OCR
- **Server mode**: For high-throughput production use
- **PaddleOCR-VL-1.5**: 0.9B parameter VLM for complex document parsing (needs more resources)

## Integration Steps for Hermes
1. Install PaddleOCR: `pip install paddleocr paddlepaddle`
2. Add to `~/.hermes/config.yaml`:
```yaml
mcp_servers:
  paddleocr:
    command: python
    args: ["-m", "paddleocr.mcp_server"]
    # or point to the mcp_server entry point in the installed package
```
3. Hermes auto-discovers MCP tools on startup — OCR becomes available as `mcp_paddleocr_*` tools

## SOMA Relevance
- Medical document OCR (PDFs, scanned records, prescriptions)
- Bilingual EN/ES medical text extraction
- Structured data from medical images (tables, charts)
- Part of the OCR fallback pipeline identified in Cycle 10

## Comparison to Alternatives
| Tool | MCP-native | GPU Required | Accuracy | Stars |
|------|-----------|-------------|----------|-------|
| PaddleOCR MCP | YES | No (CPU OK) | Industry-leading | 74.9k |
| OmniParser V2 | No | Recommended | 39.5% ScreenSpot Pro | 24.6k |
| Tesseract | No | No | Lower | N/A |

## OmniParser V2 Notes
- 24.6k GitHub stars, Microsoft Research
- Requires: YOLOv8 model + Florence-2 + caption model
- ScreenSpot Pro benchmark: 39.5% (SOTA for UI parsing)
- GPU recommended but OpenVINO optimization available for CPU
- Best for: UI element detection (interactive zones), NOT text OCR
- **Complementary to PaddleOCR** — OmniParser for UI structure, PaddleOCR for text content

## Recommended Integration Priority
1. **Quick win (30 min):** Add PaddleOCR MCP server to Hermes config
2. **Medium (1 day):** Create a vision pipeline skill that chains OmniParser (UI elements) + PaddleOCR (text) + browser_vision (current)
3. **Long-term:** Fine-tune PaddleOCR on medical document types for SOMA

## Sources
- https://github.com/PaddlePaddle/PaddleOCR
- https://github.com/microsoft/omniparser
- https://skywork.ai/skypage/en/unlocking-document-ai-paddleocr-server/


## Sources

- https://github.com/PaddlePaddle/PaddleOCR
- https://github.com/microsoft/omniparser
- https://skywork.ai/skypage/en/unlocking-document-ai-paddleocr-server/
