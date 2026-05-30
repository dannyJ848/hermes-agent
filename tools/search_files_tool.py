"""search_files_tool.py - Backward compatibility shim for search_files.

Redirects to the canonical implementation in tools.file_tools.
"""

from tools.file_tools import _handle_search_files as search_files

__all__ = ["search_files"]
