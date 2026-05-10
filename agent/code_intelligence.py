#!/usr/bin/env python3
"""
AST-Driven Code Intelligence (cAST-inspired)
Based on: cAST paper (arXiv 2506.15655) - Recursive AST chunking for RAG

Structure-aware code chunking that respects syntactic boundaries.
Supports Python (native ast), JS/TS (regex-based), and generic files.
"""

import ast
import os
import re
import sqlite3
import hashlib
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional

DB_PATH = os.path.expanduser("~/.hermes/code_intelligence.db")

class CodeChunk:
    """A semantically coherent code chunk."""
    def __init__(self, content: str, chunk_type: str, name: str, 
                 file_path: str, start_line: int, end_line: int,
                 language: str, metadata: Dict = None):
        self.content = content
        self.chunk_type = chunk_type  # function, class, method, module, block
        self.name = name
        self.file_path = file_path
        self.start_line = start_line
        self.end_line = end_line
        self.language = language
        self.metadata = metadata or {}
        self.chunk_id = hashlib.md5(f"{file_path}:{start_line}:{end_line}:{name}".encode()).hexdigest()[:12]
    
    def to_dict(self):
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "chunk_type": self.chunk_type,
            "name": self.name,
            "file_path": self.file_path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "language": self.language,
            "metadata": self.metadata,
        }


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".tsx": "typescript", ".jsx": "javascript", ".rs": "rust",
        ".go": "go", ".java": "java", ".cpp": "cpp", ".c": "c",
        ".rb": "ruby", ".php": "php", ".swift": "swift", ".kt": "kotlin",
    }
    return ext_map.get(Path(file_path).suffix, "unknown")


def chunk_python_file(file_path: str, content: str, max_chunk_size: int = 2000) -> List[CodeChunk]:
    """AST-based recursive chunking for Python files (cAST algorithm)."""
    chunks = []
    lines = content.split("\n")
    
    try:
        tree = ast.parse(content)
    except SyntaxError:
        # Fallback: line-based chunking
        return _chunk_generic(file_path, content, "python", max_chunk_size)
    
    # Collect top-level nodes with their line ranges
    node_ranges = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            node_ranges.append((node.lineno, node.end_lineno, "function", node.name, node))
        elif isinstance(node, ast.ClassDef):
            # Class header + methods
            methods = []
            for item in ast.iter_child_nodes(node):
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append((item.lineno, item.end_lineno, "method", 
                                  f"{node.name}.{item.name}", item))
            
            # If class is small enough, keep as one chunk
            class_size = sum(len(lines[i-1]) for i in range(node.lineno, min(node.end_lineno + 1, len(lines) + 1)))
            if class_size <= max_chunk_size:
                node_ranges.append((node.lineno, node.end_lineno, "class", node.name, node))
            else:
                # Split class into header + methods
                header_end = methods[0][0] - 1 if methods else node.end_lineno
                node_ranges.append((node.lineno, header_end, "class_header", node.name, node))
                node_ranges.extend(methods)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            continue  # Skip import statements as standalone chunks
        elif isinstance(node, ast.Assign):
            node_ranges.append((node.lineno, node.end_lineno, "assignment", 
                              getattr(node.targets[0], 'id', 'var') if node.targets else 'var', node))
    
    # Track which lines are covered
    covered = set()
    
    for start, end, ctype, name, _ in node_ranges:
        chunk_lines = lines[start-1:end]
        chunk_content = "\n".join(chunk_lines)
        
        if len(chunk_content) > max_chunk_size:
            # Recursive split for oversized chunks
            sub_chunks = _split_oversized(file_path, chunk_content, "python", 
                                         ctype, name, start, max_chunk_size)
            chunks.extend(sub_chunks)
        else:
            # Add file header (imports, module docstring) to first chunk
            header = _get_module_header(lines, tree)
            if header and not covered:
                chunk_content = header + "\n\n" + chunk_content
            
            chunks.append(CodeChunk(
                content=chunk_content,
                chunk_type=ctype,
                name=name,
                file_path=file_path,
                start_line=start,
                end_line=end,
                language="python",
                metadata={"lines": end - start + 1, "size": len(chunk_content)}
            ))
        covered.update(range(start, end + 1))
    
    # Collect remaining top-level code (not in any function/class)
    remaining_lines = []
    remaining_start = None
    for i, line in enumerate(lines, 1):
        if i not in covered and line.strip():
            if remaining_start is None:
                remaining_start = i
            remaining_lines.append(line)
        elif remaining_lines and i in covered:
            content_str = "\n".join(remaining_lines)
            if len(content_str) > 20:  # Skip trivial fragments
                chunks.append(CodeChunk(
                    content=content_str,
                    chunk_type="module",
                    name=f"{Path(file_path).stem}_module",
                    file_path=file_path,
                    start_line=remaining_start,
                    end_line=i - 1,
                    language="python",
                ))
            remaining_lines = []
            remaining_start = None
    
    return chunks


def chunk_js_ts_file(file_path: str, content: str, max_chunk_size: int = 2000) -> List[CodeChunk]:
    """Regex-based structure-aware chunking for JS/TS files."""
    lang = detect_language(file_path)
    chunks = []
    lines = content.split("\n")
    
    # Patterns for JS/TS structures
    patterns = [
        # export function/class/const
        r'^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)',
        r'^\s*(?:export\s+)?(?:default\s+)?class\s+(\w+)',
        r'^\s*(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\([^)]*\)\s*=>|\w+\s*=>)',
        r'^\s*(?:export\s+)?(?:async\s+)?(?:const|let|var)\s+(\w+)\s*=\s*\(',
        # interface/type definitions
        r'^\s*(?:export\s+)?(?:interface|type)\s+(\w+)',
        # React components
        r'^\s*(?:export\s+)?(?:default\s+)?function\s+(\w+)(?:\s*<[^>]*>)?\s*\(',
    ]
    
    # Find all structure boundaries
    boundaries = []
    for i, line in enumerate(lines):
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                name = match.group(1)
                # Determine type
                if 'class ' in line:
                    ctype = 'class'
                elif 'interface ' in line or 'type ' in line:
                    ctype = 'interface'
                elif name and name[0].isupper():
                    ctype = 'component'
                else:
                    ctype = 'function'
                boundaries.append((i + 1, ctype, name))
                break
    
    # Create chunks from boundaries
    for idx, (start, ctype, name) in enumerate(boundaries):
        end = boundaries[idx + 1][0] - 1 if idx + 1 < len(boundaries) else len(lines)
        chunk_content = "\n".join(lines[start-1:end])
        
        if len(chunk_content) > max_chunk_size:
            sub_chunks = _split_oversized(file_path, chunk_content, lang, ctype, name, start, max_chunk_size)
            chunks.extend(sub_chunks)
        else:
            chunks.append(CodeChunk(
                content=chunk_content,
                chunk_type=ctype,
                name=name,
                file_path=file_path,
                start_line=start,
                end_line=end,
                language=lang,
                metadata={"lines": end - start + 1, "size": len(chunk_content)}
            ))
    
    # If no boundaries found, chunk the whole file
    if not chunks and len(content) > 20:
        chunks.append(CodeChunk(
            content=content,
            chunk_type="module",
            name=Path(file_path).stem,
            file_path=file_path,
            start_line=1,
            end_line=len(lines),
            language=lang,
        ))
    
    return chunks


def _chunk_generic(file_path: str, content: str, language: str, 
                   max_chunk_size: int = 2000) -> List[CodeChunk]:
    """Fallback line-based chunking for unknown languages."""
    lines = content.split("\n")
    chunks = []
    
    current_lines = []
    current_start = 1
    
    for i, line in enumerate(lines, 1):
        current_lines.append(line)
        current_size = len("\n".join(current_lines))
        
        # Split at natural boundaries (blank lines, size limit)
        if (current_size >= max_chunk_size and not line.strip()) or current_size >= max_chunk_size * 1.5:
            chunk_content = "\n".join(current_lines)
            if chunk_content.strip():
                chunks.append(CodeChunk(
                    content=chunk_content,
                    chunk_type="block",
                    name=f"block_{current_start}",
                    file_path=file_path,
                    start_line=current_start,
                    end_line=i,
                    language=language,
                ))
            current_lines = []
            current_start = i + 1
    
    if current_lines:
        chunk_content = "\n".join(current_lines)
        if chunk_content.strip():
            chunks.append(CodeChunk(
                content=chunk_content,
                chunk_type="block",
                name=f"block_{current_start}",
                file_path=file_path,
                start_line=current_start,
                end_line=len(lines),
                language=language,
            ))
    
    return chunks


def _split_oversized(file_path, content, language, parent_type, parent_name, 
                     start_line, max_chunk_size) -> List[CodeChunk]:
    """Recursively split oversized chunks."""
    lines = content.split("\n")
    mid = len(lines) // 2
    
    # Find nearest blank line for clean split
    split_at = mid
    for offset in range(min(10, mid)):
        if mid + offset < len(lines) and not lines[mid + offset].strip():
            split_at = mid + offset + 1
            break
        if mid - offset >= 0 and not lines[mid - offset].strip():
            split_at = mid - offset
            break
    
    chunks = []
    for part_lines, part_start in [(lines[:split_at], start_line), 
                                     (lines[split_at:], start_line + split_at)]:
        part_content = "\n".join(part_lines)
        if len(part_content) > max_chunk_size:
            chunks.extend(_split_oversized(file_path, part_content, language,
                                          parent_type, parent_name, part_start, max_chunk_size))
        elif part_content.strip():
            chunks.append(CodeChunk(
                content=part_content,
                chunk_type=f"{parent_type}_part",
                name=f"{parent_name}_p{part_start}",
                file_path=file_path,
                start_line=part_start,
                end_line=part_start + len(part_lines) - 1,
                language=language,
            ))
    
    return chunks


def _get_module_header(lines: List[str], tree: ast.Module) -> str:
    """Extract import statements and module docstring."""
    header_parts = []
    
    # Module docstring
    if (tree.body and isinstance(tree.body[0], ast.Expr) and 
        isinstance(tree.body[0].value, ast.Str)):
        header_parts.append(lines[tree.body[0].lineno - 1])
    
    # Imports
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            header_parts.append(lines[node.lineno - 1])
    
    return "\n".join(header_parts) if header_parts else ""


class CodeIntelligenceDB:
    """SQLite-backed storage for code chunks with search."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
    
    def _init_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS code_chunks (
                chunk_id TEXT PRIMARY KEY,
                file_path TEXT NOT NULL,
                chunk_type TEXT NOT NULL,
                name TEXT NOT NULL,
                start_line INTEGER,
                end_line INTEGER,
                language TEXT,
                content TEXT NOT NULL,
                metadata TEXT,
                file_hash TEXT,
                indexed_at REAL
            );
            CREATE INDEX IF NOT EXISTS idx_chunks_file ON code_chunks(file_path);
            CREATE INDEX IF NOT EXISTS idx_chunks_type ON code_chunks(chunk_type);
            CREATE INDEX IF NOT EXISTS idx_chunks_name ON code_chunks(name);
            
            CREATE TABLE IF NOT EXISTS file_index (
                file_path TEXT PRIMARY KEY,
                language TEXT,
                file_hash TEXT,
                total_lines INTEGER,
                total_chunks INTEGER,
                indexed_at REAL
            );
        """)
        self.conn.commit()
    
    def index_file(self, file_path: str, max_chunk_size: int = 2000) -> int:
        """Index a single file. Returns number of chunks created."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except (IOError, OSError):
            return 0
        
        file_hash = hashlib.md5(content.encode()).hexdigest()
        
        # Check if file changed since last index
        existing = self.conn.execute(
            "SELECT file_hash FROM file_index WHERE file_path = ?", 
            (file_path,)
        ).fetchone()
        
        if existing and existing['file_hash'] == file_hash:
            return 0  # Unchanged
        
        # Remove old chunks for this file
        self.conn.execute("DELETE FROM code_chunks WHERE file_path = ?", (file_path,))
        
        # Chunk the file
        language = detect_language(file_path)
        if language == "python":
            chunks = chunk_python_file(file_path, content, max_chunk_size)
        elif language in ("javascript", "typescript"):
            chunks = chunk_js_ts_file(file_path, content, max_chunk_size)
        else:
            chunks = _chunk_generic(file_path, content, language, max_chunk_size)
        
        # Store chunks
        for chunk in chunks:
            self.conn.execute("""
                INSERT OR REPLACE INTO code_chunks 
                (chunk_id, file_path, chunk_type, name, start_line, end_line, 
                 language, content, metadata, file_hash, indexed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                chunk.chunk_id, chunk.file_path, chunk.chunk_type, chunk.name,
                chunk.start_line, chunk.end_line, chunk.language, chunk.content,
                json.dumps(chunk.metadata), file_hash, time.time()
            ))
        
        # Update file index
        self.conn.execute("""
            INSERT OR REPLACE INTO file_index 
            (file_path, language, file_hash, total_lines, total_chunks, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (file_path, language, file_hash, len(content.split("\n")), 
              len(chunks), time.time()))
        
        self.conn.commit()
        return len(chunks)
    
    def index_directory(self, dir_path: str, max_chunk_size: int = 2000,
                       ignore_dirs: List[str] = None) -> Dict:
        """Index an entire directory. Returns stats."""
        ignore = set(ignore_dirs or ['.git', 'node_modules', '__pycache__', 
                     'venv', '.venv', 'dist', 'build', '.next', 'coverage'])
        ignore_ext = {'.pyc', '.pyo', '.so', '.dylib', '.dll', '.exe', 
                     '.png', '.jpg', '.gif', '.ico', '.woff', '.woff2', 
                     '.ttf', '.eot', '.map', '.min.js', '.min.css'}
        
        stats = {"files_indexed": 0, "chunks_created": 0, "errors": 0, "skipped": 0}
        
        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in ignore]
            
            for fname in files:
                fpath = os.path.join(root, fname)
                ext = Path(fname).suffix
                
                if ext in ignore_ext or fname.startswith('.'):
                    stats["skipped"] += 1
                    continue
                
                if detect_language(fpath) == "unknown":
                    stats["skipped"] += 1
                    continue
                
                try:
                    n = self.index_file(fpath, max_chunk_size)
                    if n > 0:
                        stats["files_indexed"] += 1
                        stats["chunks_created"] += n
                except Exception:
                    stats["errors"] += 1
        
        return stats
    
    def search(self, query: str, language: str = None, chunk_type: str = None,
               file_path_pattern: str = None, limit: int = 10) -> List[Dict]:
        """Search code chunks by keyword/regex."""
        conditions = []
        params = []
        
        # Full-text search on content and name
        search_terms = query.split()
        for term in search_terms:
            conditions.append("(content LIKE ? OR name LIKE ?)")
            params.extend([f"%{term}%", f"%{term}%"])
        
        if language:
            conditions.append("language = ?")
            params.append(language)
        
        if chunk_type:
            conditions.append("chunk_type = ?")
            params.append(chunk_type)
        
        if file_path_pattern:
            conditions.append("file_path LIKE ?")
            params.append(f"%{file_path_pattern}%")
        
        where = " AND ".join(conditions)
        sql = f"SELECT * FROM code_chunks WHERE {where} ORDER BY indexed_at DESC LIMIT ?"
        params.append(limit)
        
        rows = self.conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    
    def get_context_for(self, file_path: str, line_number: int, 
                        context_radius: int = 50) -> List[Dict]:
        """Get relevant context chunks around a specific file:line."""
        # Get the chunk containing the line
        containing = self.conn.execute("""
            SELECT * FROM code_chunks 
            WHERE file_path = ? AND start_line <= ? AND end_line >= ?
            ORDER BY start_line
        """, (file_path, line_number, line_number)).fetchall()
        
        # Get neighboring chunks
        neighbors = self.conn.execute("""
            SELECT * FROM code_chunks 
            WHERE file_path = ? AND (
                start_line BETWEEN ? AND ?
                OR end_line BETWEEN ? AND ?
            )
            ORDER BY start_line
        """, (file_path, 
              max(1, line_number - context_radius), line_number + context_radius,
              max(1, line_number - context_radius), line_number + context_radius
        )).fetchall()
        
        # Combine and deduplicate
        seen = set()
        results = []
        for row in list(containing) + list(neighbors):
            if row['chunk_id'] not in seen:
                seen.add(row['chunk_id'])
                results.append(dict(row))
        
        return results
    
    def get_stats(self) -> Dict:
        """Get index statistics."""
        files = self.conn.execute("SELECT COUNT(*) as c FROM file_index").fetchone()['c']
        chunks = self.conn.execute("SELECT COUNT(*) as c FROM code_chunks").fetchone()['c']
        languages = self.conn.execute("""
            SELECT language, COUNT(*) as c FROM code_chunks GROUP BY language ORDER BY c DESC
        """).fetchall()
        types = self.conn.execute("""
            SELECT chunk_type, COUNT(*) as c FROM code_chunks GROUP BY chunk_type ORDER BY c DESC
        """).fetchall()
        
        return {
            "files": files,
            "chunks": chunks,
            "languages": {r['language']: r['c'] for r in languages},
            "chunk_types": {r['chunk_type']: r['c'] for r in types},
        }


# ── CLI Interface ──
if __name__ == "__main__":
    import sys
    
    db = CodeIntelligenceDB()
    
    if len(sys.argv) < 2:
        print("Usage: code_intelligence.py <command> [args]")
        print("Commands: index <path>, search <query>, context <file> <line>, stats")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "index":
        path = sys.argv[2] if len(sys.argv) > 2 else "."
        if os.path.isfile(path):
            n = db.index_file(os.path.abspath(path))
            print(f"Indexed {path}: {n} chunks")
        else:
            stats = db.index_directory(os.path.abspath(path))
            print(f"Indexed: {stats['files_indexed']} files, {stats['chunks_created']} chunks, "
                  f"{stats['skipped']} skipped, {stats['errors']} errors")
    
    elif cmd == "search":
        query = " ".join(sys.argv[2:])
        results = db.search(query, limit=10)
        for r in results:
            print(f"\n[{r['chunk_type']}] {r['name']} ({r['file_path']}:{r['start_line']}-{r['end_line']})")
            # Show first 3 lines
            for line in r['content'].split("\n")[:3]:
                print(f"  {line}")
            if r['content'].count("\n") > 3:
                print(f"  ... ({r['end_line'] - r['start_line'] + 1} lines)")
    
    elif cmd == "context":
        if len(sys.argv) < 4:
            print("Usage: context <file> <line>")
            sys.exit(1)
        results = db.get_context_for(sys.argv[2], int(sys.argv[3]))
        for r in results:
            print(f"\n[{r['chunk_type']}] {r['name']} (L{r['start_line']}-{r['end_line']})")
            print(r['content'][:500])
    
    elif cmd == "stats":
        stats = db.get_stats()
        print(f"Files: {stats['files']}, Chunks: {stats['chunks']}")
        print(f"Languages: {stats['languages']}")
        print(f"Types: {stats['chunk_types']}")
    
    else:
        print(f"Unknown command: {cmd}")
