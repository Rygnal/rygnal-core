"""Safe demo tools for Rygnal MVP."""

from pathlib import Path

from rygnal.models import ToolRequest

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
