"""Run Rygnal local MVP demo."""

from pathlib import Path

from demo_tools import echo_tool, safe_file_read_tool

from rygnal.audit_logger import AuditLogger
from rygnal.interceptor import RygnalInterceptor
from rygnal.models import ToolRequest
from rygnal.policy_engine import load_default_policy_engine
from rygnal.tool_executor import ToolExecutor


def prepare_demo_sandbox() -> None:
    """Create safe demo files."""
    sandbox = Path("demo_sandbox")
    sandbox.mkdir(exist_ok=True)
    (sandbox / "README.md").write_text("Safe demo file.", encoding="utf-8")


def build_interceptor() -> RygnalInterceptor:
    """Build a local Rygnal interceptor instance."""
    executor = ToolExecutor()
    executor.register("file_read", safe_file_read_tool)
    executor.register("external_api_send", echo_tool)

    return RygnalInterceptor(
        policy_engine=load_default_policy_engine(),
        audit_logger=AuditLogger("logs/audit_log.jsonl"),
        tool_executor=executor,
    )


def main() -> None:
    """Run demo scenarios."""
    prepare_demo_sandbox()
    interceptor = build_interceptor()

    requests = [
        ToolRequest(tool_name="file_read", action="read_file", target="README.md"),
        ToolRequest(tool_name="file_read", action="read_file", target=".env"),
        ToolRequest(tool_name="file_delete", action="delete_file", target="customer_data.csv"),
        ToolRequest(tool_name="external_api_send", action="send_data", input={"payload": "demo"}),
    ]

    for request in requests:
        result = interceptor.intercept(request)
        print(
            f"{request.tool_name:<18} "
            f"decision={result.policy_decision.decision:<16} "
            f"executed={result.execution.executed}"
        )


if __name__ == "__main__":
    main()
