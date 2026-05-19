import json
import subprocess
import threading
from typing import List, Dict, Any, Optional


class MCPClient:
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._request_id = 0

    def connect(self, server_command: List[str]) -> None:
        self.process = subprocess.Popen(
            server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if self.process is None or self.process.stdin is None or self.process.stdout is None:
            raise RuntimeError("MCP client is not connected")

        with self._lock:
            self._request_id += 1
            request_id = self._request_id

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params is not None:
            request["params"] = params

        request_line = json.dumps(request) + "\n"
        self.process.stdin.write(request_line)
        self.process.stdin.flush()

        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from MCP server")

        response = json.loads(response_line)
        if "error" in response:
            raise RuntimeError(f"MCP error: {response['error']}")

        return response.get("result", {})

    def discover_tools(self) -> List[Dict[str, Any]]:
        result = self._send_request("tools/list")
        return result.get("tools", [])

    def call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        params = {
            "name": name,
            "arguments": args,
        }
        return self._send_request("tools/call", params)

    def close(self) -> None:
        if self.process is not None:
            self.process.stdin.close()
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
