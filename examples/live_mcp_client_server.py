"""Live MCP-style client/server prototype protected by Rygnal.

This is a local in-process prototype. It does not require a real external MCP server.
"""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from examples.mcp_tool_call_adapter import build_demo_rygnal, handle_mcp_tool_call
from rygnal import Rygnal


class LiveMCPServer:
    """Local MCP-style server that routes tool calls through Rygnal."""

    def __init__(self, rygnal: Rygnal) -> None:
        self.rygnal = rygnal

    def handle_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Handle one MCP-style JSON-RPC request."""
        if payload.get("method") != "tools/call":
            return {
                "jsonrpc": payload.get("jsonrpc", "2.0"),
                "id": payload.get("id"),
                "error": {
                    "code": -32601,
                    "message": "Unsupported MCP method.",
                },
            }

        return handle_mcp_tool_call(payload, self.rygnal)


class LiveMCPClient:
    """Local MCP-style client for calling the protected server."""

    def __init__(self, server: LiveMCPServer) -> None:
        self.server = server

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Call one MCP-style tool through the server."""
        payload = {
            "jsonrpc": "2.0",
            "id": request_id or f"mcp_{uuid4().hex}",
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments or {},
            },
        }

        return self.server.handle_request(payload)


def build_live_mcp_demo(audit_log_path: str) -> tuple[LiveMCPClient, LiveMCPServer]:
    """Build a local MCP client/server demo protected by Rygnal."""
    rygnal = build_demo_rygnal(audit_log_path)
    server = LiveMCPServer(rygnal)
    client = LiveMCPClient(server)
    return client, server


def run_live_mcp_demo(
    *,
    target: str = "README.md",
    audit_log_path: str = "logs/live_mcp_audit_log.jsonl",
) -> dict[str, Any]:
    """Run the local live MCP-style demo."""
    client, _server = build_live_mcp_demo(audit_log_path)

    return client.call_tool(
        "file_read",
        {
            "action": "read_file",
            "target": target,
        },
        request_id="live_mcp_demo",
    )


def main() -> None:
    """Run the local live MCP-style demo from the command line."""
    print(json.dumps(run_live_mcp_demo(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
