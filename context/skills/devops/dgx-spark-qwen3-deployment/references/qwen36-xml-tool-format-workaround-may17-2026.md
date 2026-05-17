# Qwen3.6 XML Tool Format — OBSOLETE: See Correct Fix

## Status: OBSOLETE

This workaround document is **obsolete**. The correct fix is to use vLLM's built-in `qwen3_xml` tool parser.

**See:** `references/qwen36-xml-tool-format-fix-may17-2026.md` for the correct solution.

## Why This Was Wrong

The text-based workaround in this file was created because we incorrectly assumed vLLM had no parser for Qwen3's XML tool format. In fact, vLLM 0.20.2+ ships with `qwen3_xml` parser specifically for this purpose.

The real issue was using `--tool-call-parser hermes` (designed for JSON output) with a model that outputs XML.

## Lesson

> When debugging tool calling failures, always check if vLLM has a built-in parser for the model's output format BEFORE building custom workarounds.
>
> List available parsers: check `vllm/tool_parsers/` directory in the container or trigger the error to see the full list in the error message.
