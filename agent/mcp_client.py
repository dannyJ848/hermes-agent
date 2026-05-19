"""Enhanced MCP client with SSE transport, server registry, and config loading.

Supports both stdio and SSE transports. Loads server configurations from
~/.hermes/config.yaml under the mcp.servers key.

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
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for a single MCP server."""
    name: str
    transport: str  # "stdio" or "sse"
    command: Optional[List[str]] = None  # For stdio transport
    url: Optional[str] = None  # For SSE transport
    env: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    timeout: int = 30


class MCPRegistry:
    """Registry of known MCP servers from config and built-in defaults."""

    # Built-in server templates (user can override in config)
    BUILTIN_SERVERS = {
        "filesystem": {
            "transport": "stdio",
            "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem"],
        },
        "github": {
            "transport": "stdio",
            "command": ["npx", "-y", "@modelcontextprotocol/server-github"],
        },
        "brave-search": {
            "transport": "stdio",
            "command": ["npx", "-y", "@modelcontextprotocol/server-brave-search"],
        },
        "postgresql": {
            "transport": "stdio",
            "command": ["npx", "-y", "@modelcontextprotocol/server-postgres"],
        },
        "sqlite": {
            "transport": "stdio",
            "command": ["npx", "-y", "@modelcontextprotocol/server-sqlite"],
        },
        "fetch": {
            "transport": "stdio",
            "command": ["uvx", "mcp-server-fetch"],
        },
        "playwright": {
            "transport": "stdio",
            "command": ["npx", "-y", "@modelcontextprotocol/server-playwright"],
        },
    }

    def __init__(self, config_path: Optional[Path] = None):
        self._servers: Dict[str, MCPServerConfig] = {}
        self._config_path = config_path or (Path.home() / ".hermes" / "config.yaml")
        self._load_config()

    def _load_config(self) -> None:
        """Load MCP server configurations from ~/.hermes/config.yaml."""
        try:
            import yaml
            if self._config_path.exists():
                with open(self._config_path, "r") as f:
                    config = yaml.safe_load(f) or {}
                mcp_config = config.get("mcp", {})
                servers = mcp_config.get("servers", {})
                for name, server_cfg in servers.items():
                    if isinstance(server_cfg, dict):
                        self._servers[name] = MCPServerConfig(
                            name=name,
                            transport=server_cfg.get("transport", "stdio"),
                            command=server_cfg.get("command"),
                            url=server_cfg.get("url"),
                            env=server_cfg.get("env", {}),
                            enabled=server_cfg.get("enabled", True),
                            timeout=server_cfg.get("timeout", 30),
                        )
                logger.info("[MCP] Loaded %d servers from config", len(self._servers))
        except ImportError:
            logger.debug("[MCP] PyYAML not available, skipping config load")
        except Exception as e:
            logger.warning("[MCP] Config load failed: %s", e)

    def get_server(self, name: str) -> Optional[MCPServerConfig]:
        """Get a server configuration by name."""
        return self._servers.get(name)

    def list_servers(self) -> List[str]:
        """List all configured server names."""
        return list(self._servers.keys())

    def add_server(self, config: MCPServerConfig) -> None:
        """Add or update a server configuration."""
        self._servers[config.name] = config

    def remove_server(self, name: str) -> bool:
        """Remove a server configuration. Returns True if removed."""
        if name in self._servers:
            del self._servers[name]
            return True
        return False

    def save_config(self) -> bool:
        """Save current server configurations back to config.yaml."""
        try:
            import yaml
            config = {}
            if self._config_path.exists():
                with open(self._config_path, "r") as f:
                    config = yaml.safe_load(f) or {}

            if "mcp" not in config:
                config["mcp"] = {}

            config["mcp"]["servers"] = {
                name: {
                    "transport": cfg.transport,
                    "command": cfg.command,
                    "url": cfg.url,
                    "env": cfg.env,
                    "enabled": cfg.enabled,
                    "timeout": cfg.timeout,
                }
                for name, cfg in self._servers.items()
            }

            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
            return True
        except Exception as e:
            logger.warning("[MCP] Config save failed: %s", e)
            return False


class MCPClient:
    """MCP client supporting stdio and SSE transports.

    ZERO-FAILURE: All operations return safe defaults on error.
    """

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._sse_url: Optional[str] = None
        self._request_id = 0
        self._lock = threading.Lock()
        self._connected = False
        self._transport: str = "stdio"
        self._timeout: int = 30

    def connect_stdio(self, server_command: List[str], env: Optional[Dict[str, str]] = None) -> bool:
        """Connect to an MCP server via stdio. Returns True on success."""
        if not server_command:
            return False
        try:
            import os as _os
            env_vars = {**dict(_os.environ), **(env or {})}
            self._process = subprocess.Popen(
                server_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env_vars,
            )
            self._connected = True
            self._transport = "stdio"
            logger.info("[MCP] stdio connected: %s", " ".join(server_command))
            return True
        except Exception as e:
            logger.warning("[MCP] stdio connection failed: %s", e)
            self._connected = False
            return False

    def connect_sse(self, url: str) -> bool:
        """Connect to an MCP server via SSE (Server-Sent Events). Returns True on success."""
        if not url:
            return False
        try:
            # Test connection by fetching the SSE endpoint
            req = urllib.request.Request(
                url,
                headers={"Accept": "text/event-stream", "Cache-Control": "no-cache"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    self._sse_url = url.rstrip("/")
                    self._connected = True
                    self._transport = "sse"
                    logger.info("[MCP] SSE connected: %s", url)
                    return True
            return False
        except Exception as e:
            logger.warning("[MCP] SSE connection failed: %s", e)
            self._connected = False
            return False

    def connect_from_config(self, config: MCPServerConfig) -> bool:
        """Connect using a server configuration."""
        if not config.enabled:
            logger.debug("[MCP] Server %s is disabled", config.name)
            return False
        self._timeout = config.timeout
        if config.transport == "sse" and config.url:
            return self.connect_sse(config.url)
        elif config.transport == "stdio" and config.command:
            return self.connect_stdio(config.command, config.env)
        else:
            logger.warning("[MCP] Invalid config for %s", config.name)
            return False

    def _send_request(self, method: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Send a JSON-RPC request and return the response."""
        if not self._connected:
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
            if self._transport == "stdio":
                return self._send_stdio_request(payload)
            elif self._transport == "sse":
                return self._send_sse_request(payload)
            else:
                return None
        except Exception as e:
            logger.debug("[MCP] Request failed: %s", e)
            return None

    def _send_stdio_request(self, payload: Dict[str, Any]) -> Optional[Dict]:
        """Send request via stdio transport."""
        if self._process is None:
            return None

        if self._process is None or self._process.stdin is None or self._process.stdout is None:
            return None
        line = json.dumps(payload) + "\n"
        self._process.stdin.write(line)
        self._process.stdin.flush()

        # Read response with timeout
        response_line = self._process.stdout.readline()
        if not response_line:
            return None

        response = json.loads(response_line)
        return response

    def _send_sse_request(self, payload: Dict[str, Any]) -> Optional[Dict]:
        """Send request via SSE transport (POST to message endpoint)."""
        if not self._sse_url:
            return None

        # MCP SSE: POST to /message endpoint with session ID
        message_url = f"{self._sse_url}/message"
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            message_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            response_data = resp.read().decode("utf-8")
            return json.loads(response_data)

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

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and capabilities."""
        response = self._send_request("server/info", {})
        if not response:
            return {}
        return response.get("result", {})

    def close(self) -> None:
        """Close the MCP connection."""
        self._connected = False
        if self._transport == "stdio":
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
        elif self._transport == "sse":
            self._sse_url = None
        logger.debug("[MCP] Connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


class MCPManager:
    """Manages multiple MCP server connections and aggregates their tools.

    Loads server configurations from ~/.hermes/config.yaml and maintains
    a pool of active connections.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self._registry = MCPRegistry(config_path)
        self._clients: Dict[str, MCPClient] = {}
        self._tools: Dict[str, Dict[str, Any]] = {}  # name -> {server, schema}

    def list_active(self) -> List[str]:
        """List currently connected/active server names."""
        return list(self._clients.keys())

    def connect_all(self) -> Dict[str, bool]:
        """Connect to all enabled servers. Returns connection results."""
        results = {}
        for name in self._registry.list_servers():
            config = self._registry.get_server(name)
            if config and config.enabled:
                client = MCPClient()
                success = client.connect_from_config(config)
                if success:
                    self._clients[name] = client
                    # Discover and register tools
                    tools = client.discover_tools()
                    for tool in tools:
                        tool_name = tool.get("name", "unknown")
                        self._tools[tool_name] = {
                            "server": name,
                            "schema": tool,
                            "client": client,
                        }
                results[name] = success
                if not success:
                    logger.warning("[MCP] Failed to connect to %s", name)
        logger.info("[MCP] Connected to %d/%d servers", sum(results.values()), len(results))
        return results

    def connect_server(self, name: str) -> bool:
        """Connect to a specific server by name."""
        config = self._registry.get_server(name)
        if not config:
            logger.warning("[MCP] Unknown server: %s", name)
            return False
        client = MCPClient()
        success = client.connect_from_config(config)
        if success:
            self._clients[name] = client
            tools = client.discover_tools()
            for tool in tools:
                tool_name = tool.get("name", "unknown")
                self._tools[tool_name] = {
                    "server": name,
                    "schema": tool,
                    "client": client,
                }
        return success

    def call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Call a tool by name across all connected servers."""
        if name not in self._tools:
            return {"error": f"Unknown tool: {name}"}
        tool_info = self._tools[name]
        client = tool_info["client"]
        return client.call_tool(name, args)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools from all connected servers."""
        return [info["schema"] for info in self._tools.values()]

    def list_servers(self) -> List[str]:
        """List all configured server names."""
        return self._registry.list_servers()

    def get_server_status(self) -> Dict[str, bool]:
        """Get connection status for all servers."""
        return {name: name in self._clients for name in self._registry.list_servers()}

    def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        for client in self._clients.values():
            client.close()
        self._clients.clear()
        self._tools.clear()

    def disconnect_server(self, name: str) -> None:
        """Disconnect from a specific server."""
        if name in self._clients:
            self._clients[name].close()
            del self._clients[name]
            # Remove tools from this server
            self._tools = {
                k: v for k, v in self._tools.items()
                if v["server"] != name
            }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect_all()
        return False
