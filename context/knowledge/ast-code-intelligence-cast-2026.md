# ast-code-intelligence-cast-2026

*Researched: 2026-04-05 18:30 CDT*

# AST-Driven Code Intelligence (cAST-inspired)

## Source
- cAST paper (arXiv 2506.15655) - Carnegie Mellon / Augment Code
- Key insight: Line-based chunking breaks semantic structures, degrading RAG quality

## Implementation
- Location: ~/subconscious/code_intelligence.py
- Algorithm: Recursive AST split-then-merge (mirrors cAST paper)
- Python: Native `ast` module for precise function/class/method boundaries
- JS/TS: Regex-based structure detection (functions, classes, interfaces, components)
- Generic: Line-based fallback with natural boundary detection

## Architecture
- DB: ~/.hermes/code_intelligence.db (SQLite)
- Tables: code_chunks (19K+ entries), file_index (1K+ files)
- Indexes: file_path, chunk_type, name
- Max chunk size: 2000 chars (configurable)
- File hash tracking for incremental re-indexing

## Chunk Types
- function, class, method, module, block, interface, component
- _part suffix for recursively split oversized chunks
- Metadata: lines, size, language

## Integration Points
- search(query, language, chunk_type, file_path_pattern) -> ranked chunks
- get_context_for(file, line, radius) -> neighboring chunks for context
- index_file / index_directory for bulk indexing
- Stats: 724 files, 19199 chunks in hermes-agent; 3950 files, 17620 chunks in soma

## Key Results from cAST Paper
- +4.3 Recall@5 on RepoEval retrieval
- +2.67 Pass@1 on SWE-bench generation
- +5.5 avg points on StarCoder2-7B
- Cross-language consistent (language-agnostic algorithm)


## Sources

- https://arxiv.org/html/2506.15655v1
