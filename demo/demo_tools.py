"""Real workflow demo tools for Rygnal.

These tools perform real actions only inside a controlled local sandbox.
They are intentionally strict because Rygnal is a security product.
"""

from __future__ import annotations

import subprocess  # nosec
from collections.abc import Callable
from pathlib import Path
from typing import Any

from rygnal.models import ToolRequest
from rygnal.security import (
    DEFAULT_ALLOWED_SHELL_COMMANDS,
    SecurityViolation,
    contains_secret,
    resolve_path_inside_sandbox,
    validate_http_url,
    validate_shell_command,
)
from rygnal.tool_executor import ToolExecutor

ToolHandler = Callable[[ToolRequest], dict[str, Any]]


def prepare_demo_sandbox(sandbox_path: str | Path) -> Path:
    """Create a controlled sandbox with realistic demo files."""
    sandbox = Path(sandbox_path)
    sandbox.mkdir(parents=True, exist_ok=True)

    (sandbox / "README.md").write_text(
        "Rygnal safe project documentation.\n",
        encoding="utf-8",
    )
    (sandbox / "customer_data.csv").write_text(
        "id,email,plan\n1,user@example.com,starter\n",
        encoding="utf-8",
    )
    (sandbox / "project_notes.txt").write_text(
        "Initial project notes.\n",
        encoding="utf-8",
    )
    (sandbox / ".env").write_text(
        "OPENAI_API_KEY=sk-demo-secret\nDATABASE_URL=postgres://demo\n",
        encoding="utf-8",
    )

    return sandbox


def build_file_read_tool(sandbox_path: str | Path) -> ToolHandler:
    """Build a safe file read tool."""

    def file_read(request: ToolRequest) -> dict[str, Any]:
        try:
            path = resolve_path_inside_sandbox(sandbox_path, request.target)
        except SecurityViolation as exc:
            return {"ok": False, "error": str(exc), "target": request.target}

        if not path.exists():
            return {"ok": False, "error": "File not found.", "target": request.target}

        if not path.is_file():
            return {"ok": False, "error": "Target is not a file.", "target": request.target}

        return {
            "ok": True,
            "target": request.target,
            "content": path.read_text(encoding="utf-8"),
        }

    return file_read


def build_file_write_tool(sandbox_path: str | Path) -> ToolHandler:
    """Build a safe file write tool."""

    def file_write(request: ToolRequest) -> dict[str, Any]:
        try:
            path = resolve_path_inside_sandbox(sandbox_path, request.target)
        except SecurityViolation as exc:
            return {"ok": False, "error": str(exc), "target": request.target}

        content = str(request.input or "")

        if contains_secret(content):
            return {
                "ok": False,
                "error": "Refusing to write content that appears to contain secrets.",
            }

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

        return {"ok": True, "target": request.target, "bytes_written": len(content.encode())}

    return file_write


def build_file_delete_tool(sandbox_path: str | Path) -> ToolHandler:
    """Build a safe file delete tool.

    In normal policy this should require approval before execution.
    """

    def file_delete(request: ToolRequest) -> dict[str, Any]:
        try:
            path = resolve_path_inside_sandbox(sandbox_path, request.target)
        except SecurityViolation as exc:
            return {"ok": False, "error": str(exc), "target": request.target}

        if not path.exists():
            return {"ok": False, "error": "File not found.", "target": request.target}

        if not path.is_file():
            return {"ok": False, "error": "Target is not a file.", "target": request.target}

        path.unlink()
        return {"ok": True, "deleted": request.target}

    return file_delete


def build_shell_command_tool(sandbox_path: str | Path) -> ToolHandler:
    """Build a restricted shell command tool with an allowlist."""

    def shell_command(request: ToolRequest) -> dict[str, Any]:
        command_text = str(request.input or "")

        try:
            command_parts = validate_shell_command(
                command_text,
                allowed_commands=DEFAULT_ALLOWED_SHELL_COMMANDS,
            )
        except SecurityViolation as exc:
            return {"ok": False, "error": str(exc)}

        completed = subprocess.run(  # nosec
            command_parts,
            cwd=Path(sandbox_path),
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )

        return {
            "ok": completed.returncode == 0,
            "command": command_text,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }

    return shell_command


def build_external_api_send_tool() -> ToolHandler:
    """Build a dry-run external send tool.

    This intentionally does not perform real network calls in v1.
    """

    def external_api_send(request: ToolRequest) -> dict[str, Any]:
        payload = request.input if isinstance(request.input, dict) else {}
        url = str(payload.get("url", ""))

        try:
            validate_http_url(url)
        except SecurityViolation as exc:
            return {"ok": False, "error": str(exc), "transport": "blocked"}

        if contains_secret(payload):
            return {"ok": False, "error": "Refusing to send payload containing secrets."}

        return {
            "ok": True,
            "transport": "dry_run",
            "message": "External send was captured but not transmitted.",
            "payload": request.input,
        }

    return external_api_send


def build_demo_tool_executor(sandbox_path: str | Path) -> ToolExecutor:
    """Build a tool executor with real controlled demo tools."""
    executor = ToolExecutor()

    executor.register("file_read", build_file_read_tool(sandbox_path))
    executor.register("file_write", build_file_write_tool(sandbox_path))
    executor.register("file_delete", build_file_delete_tool(sandbox_path))
    executor.register("shell_command", build_shell_command_tool(sandbox_path))
    executor.register("external_api_send", build_external_api_send_tool())

    return executor
