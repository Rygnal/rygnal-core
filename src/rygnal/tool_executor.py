"""Safe tool executor for Rygnal.

The executor only runs explicitly registered tools. It never executes arbitrary
agent-generated code by default.
"""

from collections.abc import Callable
from typing import Any

from rygnal.models import ExecutionStatus, ToolExecutionResult, ToolRequest

ToolHandler = Callable[[ToolRequest], Any]


class ToolExecutor:
    """Execute registered tools after Rygnal approval."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolHandler] = {}

    def register(self, tool_name: str, handler: ToolHandler) -> None:
        """Register a trusted tool handler."""
        self._tools[tool_name] = handler

    def has_tool(self, tool_name: str) -> bool:
        """Return True when a tool is registered."""
        return tool_name in self._tools

    def execute(self, request: ToolRequest) -> ToolExecutionResult:
        """Execute a registered tool safely."""
        handler = self._tools.get(request.tool_name)

        if handler is None:
            return ToolExecutionResult(
                status=ExecutionStatus.FAILED,
                executed=False,
                error=f"No registered tool handler for: {request.tool_name}",
            )

        try:
            output = handler(request)
        except Exception as exc:
            return ToolExecutionResult(
                status=ExecutionStatus.FAILED,
                executed=True,
                error=f"Tool execution failed: {exc}",
            )

        return ToolExecutionResult(
            status=ExecutionStatus.EXECUTED,
            executed=True,
            output=output,
        )
