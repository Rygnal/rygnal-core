"""Safe demo tools for Rygnal MVP."""

import shlex
import subprocess  # nosec
from pathlib import Path
from typing import Any

from rygnal.models import ToolRequest
from rygnal.tool_executor import ToolExecutor, ToolHandler

DEMO_SANDBOX = Path("demo_sandbox")


def safe_file_read_tool(request: ToolRequest) -> dict[str, str]:
    """Read files only from the local demo sandbox."""
    target = str(request.target or "")
    sandbox = DEMO_SANDBOX.resolve()
    candidate = (sandbox / target).resolve()

    if candidate != sandbox and sandbox not in candidate.parents:
        return {"error": "Target is outside demo sandbox."}

    if not candidate.exists():
        return {"error": "File not found.", "target": target}

    return {"target": target, "content": candidate.read_text(encoding="utf-8")}


def echo_tool(request: ToolRequest) -> dict[str, object]:
    """Echo safe demo input."""
    return {
        "tool_name": request.tool_name,
        "action": request.action,
        "target": request.target,
        "input": request.input,
    }


def prepare_demo_sandbox(sandbox_path: str | Path = "demo_sandbox") -> Path:
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


def resolve_sandbox_path(sandbox_path: str | Path, target: str | None) -> Path:
    """Resolve a target path safely inside the sandbox."""
    if not target:
        raise ValueError("Target path is required.")

    sandbox = Path(sandbox_path).resolve()
    candidate = (sandbox / target).resolve()

    if candidate != sandbox and sandbox not in candidate.parents:
        raise ValueError("Target path is outside the allowed sandbox.")

    return candidate


def build_file_read_tool(sandbox_path: str | Path) -> ToolHandler:
    """Build a safe file read tool."""

    def file_read(request: ToolRequest) -> dict[str, Any]:
        path = resolve_sandbox_path(sandbox_path, request.target)

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
        path = resolve_sandbox_path(sandbox_path, request.target)
        content = str(request.input or "")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

        return {"ok": True, "target": request.target, "bytes_written": len(content.encode())}

    return file_write


def build_file_delete_tool(sandbox_path: str | Path) -> ToolHandler:
    """Build a safe file delete tool.

    In normal policy this should require approval before execution.
    """

    def file_delete(request: ToolRequest) -> dict[str, Any]:
        path = resolve_sandbox_path(sandbox_path, request.target)

        if not path.exists():
            return {"ok": False, "error": "File not found.", "target": request.target}

        if not path.is_file():
            return {"ok": False, "error": "Target is not a file.", "target": request.target}

        path.unlink()
        return {"ok": True, "deleted": request.target}

    return file_delete


def build_shell_command_tool(sandbox_path: str | Path) -> ToolHandler:
    """Build a restricted shell command tool with an allowlist."""

    ALLOWED_SHELL_COMMANDS = {"echo", "ls", "pwd", "cat", "head", "tail"}

    def shell_command(request: ToolRequest) -> dict[str, Any]:
        command_text = str(request.input or "")
        command_parts = shlex.split(command_text)

        if not command_parts:
            return {"ok": False, "error": "Shell command input is empty."}

        command_name = command_parts[0]

        if command_name not in ALLOWED_SHELL_COMMANDS:
            return {
                "ok": False,
                "error": f"Command not allowlisted: {command_name}",
                "allowed_commands": sorted(ALLOWED_SHELL_COMMANDS),
            }

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
    Policy should normally simulate/block this action before execution.
    """

    def external_api_send(request: ToolRequest) -> dict[str, Any]:
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
