# Live MCP Client/Server Prototype

## Goal

Add a local MCP-style client/server prototype protected by Rygnal.

This is a local in-process prototype. It does not require a real external MCP server.

## Current Behavior

Rygnal already supports MCP-style `tools/call` payloads through the MCP adapter.

This prototype adds:

- `LiveMCPServer`
- `LiveMCPClient`
- `build_live_mcp_demo`
- `run_live_mcp_demo`

## Safety Rules

- MCP tool calls must not execute directly
- MCP requests must route through Rygnal first
- Policy Engine must decide allow/block/simulate/approval
- Risk Engine must assess the request
- Audit logs must be generated
- Unsupported MCP methods must return an error

## How To Run

Run the local MCP-style demo:

    python -m examples.live_mcp_client_server

## What This Proves

This proves that a client/server-shaped MCP flow can be protected by Rygnal before real external MCP integration.

## Not Included Yet

- real external MCP server
- network transport
- MCP authentication
- multi-tool session handling
- streaming
- production MCP gateway
