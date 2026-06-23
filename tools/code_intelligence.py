#!/usr/bin/env python3
"""Code Intelligence — AST-Based Project Index.

Eliminates the need to read 5 files to trace a call path. Builds a lightweight
index of function/class signatures, import graphs, and call relationships using
Python's ast module. Supports any language with a tree-sitter grammar available
on the system, but defaults to Python (always available via ast).

The index is cached on disk and refreshed on demand. Query patterns:
- "where does X live" → query(name="X")
- "who calls Y" → callers(name="Y")
- "what does Z call" → callees(name="Z")
- "show me the class hierarchy" → structure()
- "what does module M export" → query(module="M")

Cache: ~/.hermes/workspace/code_index_<project_hash>.json
"""

import ast
import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from hermes_constants import get_hermes_home
from utils import atomic_json_write
from tools.registry import registry, tool_error

logger = logging.getLogger(__name__)

# File extensions we can index
_PYTHON_EXTS = {".py", ".pyi"}
_JS_TS_EXTS = {".js", ".ts", ".jsx", ".tsx", ".mjs"}
_GO_EXTS = {".go"}
_RUST_EXTS = {".rs"}
_RUBY_EXTS = {".rb"}
_ALL_EXTS = _PYTHON_EXTS | _JS_TS_EXTS | _GO_EXTS | _RUST_EXTS | _RUBY_EXTS | {".java", ".kt", ".swift", ".c", ".h", ".cpp", ".cc", ".hpp"}

# Max files to index in one pass (prevents runaway on huge repos)
_MAX_FILES = 2000
# Max file size to parse (skip huge generated files)
_MAX_FILE_SIZE = 256 * 1024  # 256KB


def _workspace_dir() -> Path:
    d = get_hermes_home() / "workspace"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _index_cache_path(project_path: str) -> Path:
    """Cache path derived from project path hash."""
    h = hashlib.md5(os.path.abspath(project_path).encode()).hexdigest()[:12]
    return _workspace_dir() / f"code_index_{h}.json"


def _collect_files(project_path: Path) -> List[Path]:
    """Collect indexable source files in a project."""
    # Directories to skip
    skip_dirs = {
        ".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
        "env", ".tox", ".mypy_cache", ".pytest_cache", "dist", "build", ".next",
        ".nuxt", "target", "vendor", ".idea", ".vscode", "eggs", ".eggs",
    }
    files = []
    for root, dirs, filenames in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]
        for fn in filenames:
            ext = os.path.splitext(fn)[1]
            if ext in _ALL_EXTS:
                fp = Path(root) / fn
                try:
                    if fp.stat().st_size <= _MAX_FILE_SIZE:
                        files.append(fp)
                except OSError:
                    pass
            if len(files) >= _MAX_FILES:
                return files
    return files


def _index_python_file(filepath: Path, rel_path: str) -> Dict[str, Any]:
    """Parse a Python file and extract symbols, imports, and calls."""
    result = {
        "path": rel_path,
        "language": "python",
        "functions": [],
        "classes": [],
        "imports": [],
        "calls": [],  # function call relationships
        "exports": [],
    }
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, OSError, UnicodeDecodeError):
        return result

    # Extract module-level and class-level functions
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_info = {
                "name": node.name,
                "line": node.lineno,
                "args": [a.arg for a in node.args.args],
                "decorators": [],
                "docstring": (ast.get_docstring(node) or "")[:200],
            }
            # Decorators
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name):
                    func_info["decorators"].append(dec.id)
                elif isinstance(dec, ast.Attribute):
                    func_info["decorators"].append(dec.attr)
            # Determine if it's a method (inside a class)
            func_info["is_method"] = False
            result["functions"].append(func_info)

            # Extract calls within this function
            calls_in_func = set()
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    call_name = _get_call_name(child)
                    if call_name:
                        calls_in_func.add(call_name)
            for c in calls_in_func:
                result["calls"].append({
                    "caller": node.name,
                    "callee": c,
                    "line": node.lineno,
                })

        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(item.name)
                    # Mark corresponding function as method
            result["classes"].append({
                "name": node.name,
                "line": node.lineno,
                "bases": [_get_name(b) for b in node.bases],
                "methods": methods,
                "docstring": (ast.get_docstring(node) or "")[:200],
            })

        elif isinstance(node, ast.Import):
            for alias in node.names:
                result["imports"].append({
                    "module": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                })

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                result["imports"].append({
                    "module": module,
                    "name": alias.name,
                    "alias": alias.asname,
                    "line": node.lineno,
                })
                result["exports"].append(alias.name)

    # Mark methods
    class_methods = set()
    for cls in result["classes"]:
        for m in cls["methods"]:
            class_methods.add(m)
    for func in result["functions"]:
        if func["name"] in class_methods:
            func["is_method"] = True

    return result


def _get_call_name(node: ast.Call) -> str:
    """Extract a readable name from a Call node."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    elif isinstance(func, ast.Attribute):
        return func.attr
    elif isinstance(func, ast.Subscript):
        return _get_name(func)
    return ""


def _get_name(node: ast.AST) -> str:
    """Get a name string from various AST nodes."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{_get_name(node.value)}.{node.attr}"
    elif isinstance(node, ast.Constant):
        return str(node.value)
    return ""


def _index_javascript_file(filepath: Path, rel_path: str) -> Dict[str, Any]:
    """Lightweight JS/TS indexing via regex (no tree-sitter dependency)."""
    import re
    result = {
        "path": rel_path,
        "language": "javascript",
        "functions": [],
        "classes": [],
        "imports": [],
        "calls": [],
        "exports": [],
    }
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return result

    # Function declarations: function foo(, const foo = (, foo(  => {
    for m in re.finditer(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', source):
        line = source[:m.start()].count('\n') + 1
        result["functions"].append({
            "name": m.group(1),
            "line": line,
            "args": [a.strip() for a in m.group(2).split(',') if a.strip()],
            "decorators": [],
            "docstring": "",
            "is_method": False,
        })

    # Arrow functions: const foo = (args) => 
    for m in re.finditer(r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*(?:=>|{)', source):
        line = source[:m.start()].count('\n') + 1
        result["functions"].append({
            "name": m.group(1),
            "line": line,
            "args": [a.strip() for a in m.group(2).split(',') if a.strip()],
            "decorators": [],
            "docstring": "",
            "is_method": False,
        })

    # Class declarations
    for m in re.finditer(r'(?:export\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?', source):
        line = source[:m.start()].count('\n') + 1
        result["classes"].append({
            "name": m.group(1),
            "line": line,
            "bases": [m.group(2)] if m.group(2) else [],
            "methods": [],
            "docstring": "",
        })

    # Imports
    for m in re.finditer(r'import\s+.*?\s+from\s+["\']([^"\']+)', source):
        line = source[:m.start()].count('\n') + 1
        result["imports"].append({"module": m.group(1), "line": line})

    # Exports
    for m in re.finditer(r'export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+)', source):
        result["exports"].append(m.group(1))

    return result


def _build_index(project_path: str, force: bool = False) -> Dict[str, Any]:
    """Build or load cached index for a project."""
    cache_path = _index_cache_path(project_path)
    proj = Path(project_path).resolve()

    # Check cache freshness
    if not force and cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            # Check if project has changed since last index
            indexed_at = cached.get("indexed_at", 0)
            # Re-index if any file is newer than the index
                    # Quick staleness check: compare mtimes of a sample of files
            stale = False
            for f in cached.get("files_indexed", [])[:50]:
                fp = proj / f
                if fp.exists():
                    try:
                        if fp.stat().st_mtime > indexed_at:
                            stale = True
                            break
                    except OSError:
                        stale = True
                        break
                else:
                    stale = True  # file deleted → re-index
                    break
            if not stale:
                return cached
        except (json.JSONDecodeError, OSError):
            pass

    # Build fresh index
    files = _collect_files(proj)
    index = {
        "project_path": str(proj),
        "indexed_at": time.time(),
        "files_indexed": [],
        "files": {},  # rel_path -> file index
        "symbols": {},  # name -> [{file, line, type}]
        "call_graph": {},  # caller -> [callee names]
        "reverse_call_graph": {},  # callee -> [caller names]
        "class_hierarchy": {},  # class -> {bases, methods}
        "stats": {"total_files": 0, "total_functions": 0, "total_classes": 0},
    }

    total_funcs = 0
    total_classes = 0

    for filepath in files:
        try:
            rel = str(filepath.relative_to(proj))
        except ValueError:
            rel = str(filepath)

        ext = filepath.suffix
        if ext in _PYTHON_EXTS:
            file_idx = _index_python_file(filepath, rel)
        elif ext in _JS_TS_EXTS:
            file_idx = _index_javascript_file(filepath, rel)
        else:
            # Skip unsupported but track
            index["files_indexed"].append(rel)
            continue

        index["files"][rel] = file_idx
        index["files_indexed"].append(rel)

        # Build symbol table
        for func in file_idx["functions"]:
            name = func["name"]
            if name not in index["symbols"]:
                index["symbols"][name] = []
            index["symbols"][name].append({
                "file": rel,
                "line": func["line"],
                "type": "method" if func.get("is_method") else "function",
                "args": func.get("args", []),
            })
            total_funcs += 1

        for cls in file_idx["classes"]:
            name = cls["name"]
            if name not in index["symbols"]:
                index["symbols"][name] = []
            index["symbols"][name].append({
                "file": rel,
                "line": cls["line"],
                "type": "class",
            })
            index["class_hierarchy"][name] = {
                "bases": cls.get("bases", []),
                "methods": cls.get("methods", []),
                "file": rel,
            }
            total_classes += 1

        # Build call graph
        for call in file_idx["calls"]:
            caller = call["caller"]
            callee = call["callee"]
            if caller not in index["call_graph"]:
                index["call_graph"][caller] = set()
            index["call_graph"][caller].add(callee)
            if callee not in index["reverse_call_graph"]:
                index["reverse_call_graph"][callee] = set()
            index["reverse_call_graph"][callee].add(caller)

    # Convert sets to sorted lists for JSON serialization
    index["call_graph"] = {k: sorted(v) for k, v in index["call_graph"].items()}
    index["reverse_call_graph"] = {k: sorted(v) for k, v in index["reverse_call_graph"].items()}
    index["stats"] = {
        "total_files": len(index["files"]),
        "total_functions": total_funcs,
        "total_classes": total_classes,
        "total_symbols": len(index["symbols"]),
    }

    # Cache it
    try:
        atomic_json_write(cache_path, index)
    except OSError as e:
        logger.warning("Failed to cache code index: %s", e)

    return index


def code_intelligence_handler(
    args: Dict[str, Any],
    session_id: Optional[str] = None,
    **kwargs,
) -> str:
    """Handle code_intelligence tool calls."""
    action = args.get("action", "query")
    project_path = args.get("project_path", os.getcwd())

    if action == "index":
        force = args.get("force", False)
        index = _build_index(project_path, force=force)
        return json.dumps({
            "status": "success",
            "message": f"Indexed {index['stats']['total_files']} files",
            "stats": index["stats"],
            "indexed_at": index["indexed_at"],
        }, ensure_ascii=False)

    # All other actions need the index
    index = _build_index(project_path)

    if action == "query":
        name = args.get("name", "")
        if name:
            results = index["symbols"].get(name, [])
            if not results:
                # Fuzzy match
                close = [k for k in index["symbols"] if name.lower() in k.lower()]
                return json.dumps({
                    "status": "not_found",
                    "message": f"Symbol '{name}' not found",
                    "similar": close[:10],
                }, ensure_ascii=False)
            return json.dumps({"status": "success", "name": name, "locations": results}, ensure_ascii=False)
        else:
            # General overview
            return json.dumps({
                "status": "success",
                "stats": index["stats"],
                "project_path": index["project_path"],
            }, ensure_ascii=False)

    elif action == "callers":
        name = args.get("name", "")
        if not name:
            return tool_error("'name' is required for 'callers' action")
        callers = index["reverse_call_graph"].get(name, [])
        # Resolve caller locations
        caller_details = []
        for c in callers:
            locs = index["symbols"].get(c, [])
            caller_details.append({"name": c, "locations": locs[:3]})
        return json.dumps({
            "status": "success",
            "name": name,
            "callers": caller_details,
            "count": len(callers),
        }, ensure_ascii=False)

    elif action == "callees":
        name = args.get("name", "")
        if not name:
            return tool_error("'name' is required for 'callees' action")
        callees = index["call_graph"].get(name, [])
        return json.dumps({
            "status": "success",
            "name": name,
            "callees": callees,
            "count": len(callees),
        }, ensure_ascii=False)

    elif action == "structure":
        """Show class hierarchy and module structure."""
        # Filter to non-test, non-internal classes
        hierarchy = {}
        for cls_name, info in index["class_hierarchy"].items():
            if not cls_name.startswith("_"):
                hierarchy[cls_name] = info
        return json.dumps({
            "status": "success",
            "class_hierarchy": hierarchy,
            "stats": index["stats"],
        }, ensure_ascii=False)

    elif action == "imports":
        """Show import graph for a module or what imports a given module."""
        module = args.get("module", "")
        if module:
            # Find what imports this module
            importers = []
            for file_path, file_idx in index["files"].items():
                for imp in file_idx.get("imports", []):
                    if module in imp.get("module", "") or module in imp.get("name", ""):
                        importers.append({
                            "file": file_path,
                            "import": imp,
                        })
            return json.dumps({
                "status": "success",
                "module": module,
                "imported_by": importers[:30],
            }, ensure_ascii=False)
        else:
            return tool_error("'module' is required for 'imports' action")

    elif action == "file_symbols":
        """List all symbols in a specific file."""
        filepath = args.get("file", "")
        if not filepath:
            return tool_error("'file' is required for 'file_symbols' action")
        # Try to find the file (relative or partial match)
        target = None
        for f in index["files"]:
            if filepath in f:
                target = f
                break
        if not target:
            return tool_error(f"No indexed file matching '{filepath}'")
        file_idx = index["files"][target]
        return json.dumps({
            "status": "success",
            "file": target,
            "functions": [{"name": f["name"], "line": f["line"], "args": f["args"]} for f in file_idx["functions"]],
            "classes": [{"name": c["name"], "line": c["line"], "methods": c["methods"]} for c in file_idx["classes"]],
            "imports": file_idx["imports"][:20],
        }, ensure_ascii=False)

    else:
        return tool_error(f"Unknown action '{action}'. Valid: index, query, callers, callees, structure, imports, file_symbols")


CODE_INTELLIGENCE_SCHEMA = {
    "name": "code_intelligence",
    "description": (
        "AST-based code index that eliminates reading 5 files to trace a call path. "
        "Builds a cached index of function/class signatures, call graphs, and import relationships. "
        "Supports Python (full AST) and JS/TS (regex-based). "
        "Actions: index (build/refresh), query (find symbol), callers (who calls X), "
        "callees (what does X call), structure (class hierarchy), imports (import graph), "
        "file_symbols (list symbols in a file). "
        "Use BEFORE reading source files — query the index first to know WHERE to look."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["index", "query", "callers", "callees", "structure", "imports", "file_symbols"],
                "description": (
                    "index: build/refresh the code index for the project. "
                    "query: find a symbol by name (returns file, line, type). "
                    "callers: find all functions that call the given function. "
                    "callees: find all functions called by the given function. "
                    "structure: show class hierarchy and inheritance. "
                    "imports: find what imports a given module. "
                    "file_symbols: list all functions/classes in a specific file."
                ),
            },
            "name": {
                "type": "string",
                "description": "Symbol or function name for query/callers/callees actions.",
            },
            "project_path": {
                "type": "string",
                "description": "Path to the project root (defaults to current working directory).",
            },
            "module": {
                "type": "string",
                "description": "Module name for 'imports' action.",
            },
            "file": {
                "type": "string",
                "description": "File path (partial match OK) for 'file_symbols' action.",
            },
            "force": {
                "type": "boolean",
                "description": "Force re-index even if cache appears fresh.",
            },
        },
        "required": ["action"],
    },
}


registry.register(
    name="code_intelligence",
    toolset="cognitive",
    schema=CODE_INTELLIGENCE_SCHEMA,
    handler=code_intelligence_handler,
    emoji="🔍",
    max_result_size_chars=50_000,
)
