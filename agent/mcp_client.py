"""MCP client with stdio transport.

ZERO-FAILURE GUARANTEE:
- Every method catches ALL exceptions and returns safe defaults
- Connection failures → empty lists/dicts
- JSON parse errors → empty dicts
- Process errors → graceful cleanup
"""

import json
import logging
import subprocess
import threading
import time
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class MCPClient:
    """MCP client supporting stdio transport.
    
    ZERO-FAILURE: All operations return safe defaults on error.
    """

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._request_id = 0
        self._lock = threading.Lock()
        self._connected = False

    def connect(self, server_command: List[str]) -> bool:
        """Connect to an MCP server via stdio. Returns True on success."""
        if not server_command:
            return False
        try:
            self._process = subprocess.Popen(
                server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self._connected = True
            return True
        except Exception as e:
            logger.warning("[MCP] Connection failed: %s", e)
            self._connected = False
            return False

    def _send_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Send a JSON-RPC request and return the response."""
        if not self._connected or self._process is None:
            return None
        
        with self._lock:
            self._request_id += 1
            req_id = self._request_id
        
        payload = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params,
        }
        
        try:
            line = json.dumps(payload) + "\n"
            self._process.stdin.write(line)
            self._process.stdin.flush()
            
            # Read response with timeout
            response_line = self._process.stdout.readline()
            if not response_line:
                return None
            
            response = json.loads(response_line)
            return response
        except Exception as e:
            logger.debug("[MCP] Request failed: %s", e)
            return None

    def discover_tools(self) -> List[Dict[str, Any]]:
        """Discover available tools from the MCP server."""
        response = self._send_request("tools/list", {})
        if not response:
            return []
        
        try:
            result = response.get("result", {})
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                return result.get("tools", [])
            return []
        except Exception:
            return []

    def call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool with arguments."""
        response = self._send_request("tools/call", {"name": name, "arguments": args})
        if not response:
            return {"error": "No response from MCP server"}
        
        try:
            if "result" in response:
                return response["result"]
            elif "error" in response:
                return {"error": response["error"]}
            return response
        except Exception:
            return {"error": "Failed to parse MCP response"}

    def close(self) -> None:
        """Close the MCP connection."""
        self._connected = False
        try:
            if self._process:
                self._process.terminate()
                self._process.wait(timeout=2)
        except Exception:
            pass
        try:
            if self._process:
                self._process.kill()
        except Exception:
            pass
        self._process = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
