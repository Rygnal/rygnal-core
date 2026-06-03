# OpenAI Tool-Calling Integration Prototype

This integration proves that an OpenAI-style tool call payload can be routed through Rygnal before execution.

## Goal

Protect native OpenAI-style tool calls with Rygnal policy, risk scoring, audit logging, and safe execution behavior.

## What This Includes

- OpenAI-style tool call adapter
- Conversion from tool call payload to Rygnal ToolRequest
- Safe file read allowed through Rygnal
- Secret file read blocked through Rygnal
- Audit event generated for each tool call
- Tests that run without paid API keys

## Why No Paid API Call in CI

This prototype uses real OpenAI-style tool call payloads but does not call the OpenAI API.

This keeps tests stable, avoids API key leaks, avoids accidental cost, and prevents CI failures from missing keys or rate limits.

## Run Tests

pytest -q tests/test_openai_tool_calling_integration.py

## Security Notes

- Never commit API keys
- Never require paid API calls in CI
- Keep live provider demos separate and optional
- Convert tool calls into ToolRequest before execution
- Route every protected tool call through Rygnal
- Audit every protected tool call

## Future Work

- Add optional live OpenAI API demo in a separate issue
- Add OpenAI Responses API tool-call example
- Add multi-tool call handling
- Add stricter schema validation for tool arguments
- Add MCP integration prototype
