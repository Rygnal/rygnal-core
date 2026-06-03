"""CLI output formatting for Rygnal scenario runs."""

from __future__ import annotations

from typing import Any


def render_run_report(outcomes: list[Any]) -> str:
    """Render a complete CLI report for scenario outcomes."""
    lines = [
        "",
        "Rygnal Real Scenario Runner v1",
        "=" * 36,
        "",
    ]

    for index, outcome in enumerate(outcomes, start=1):
        lines.extend(render_outcome(outcome, index=index))
        lines.append("")

    lines.extend(
        [
            "Summary",
            "-" * 36,
            f"Total scenarios: {len(outcomes)}",
            "Audit log: logs/audit_log.jsonl",
            "Sandbox: demo_sandbox/",
        ]
    )

    return "\n".join(lines)


def render_outcome(outcome: Any, index: int) -> list[str]:
    """Render one scenario outcome as readable CLI lines."""
    scenario = outcome.scenario
    result = outcome.result

    risk = normalize_risk(result.risk_assessment)
    policy_decision = result.policy_decision
    execution = result.execution
    audit_event = result.audit_event

    decision = enum_value(policy_decision.decision).upper()
    execution_status = enum_value(execution.status)
    runtime_mode = runtime_mode_value(result)

    risk_level = enum_value(risk.get("risk_level", "unknown"))
    risk_score = risk.get("risk_score", "n/a")

    policy_id = policy_decision.policy_id or "default-allow"
    reason = policy_decision.reason
    explanation = policy_explanation_value(policy_decision, audit_event)
    matched = "yes" if explanation.get("matched") else "no"
    default_decision = "yes" if explanation.get("default_decision") else "no"
    priority = explanation.get("matched_rule_priority") or "n/a"
    matched_conditions = explanation.get("matched_conditions") or []
    conditions = ", ".join(matched_conditions) if matched_conditions else "n/a"
    tool_name = scenario.request.tool_name
    action = scenario.request.action or "n/a"
    target = scenario.request.target or "n/a"

    return [
        f"{index}. [{decision}] {scenario.name}",
        f"   Description : {scenario.description}",
        f"   Tool        : {tool_name}",
        f"   Action      : {action}",
        f"   Target      : {target}",
        f"   Runtime     : {runtime_mode}",
        f"   Risk        : {risk_level} / {risk_score}",
        f"   Policy      : {policy_id}",
        f"   Priority    : {priority}",
        f"   Matched     : {matched}",
        f"   Conditions  : {conditions}",
        f"   Default     : {default_decision}",
        f"   Execution   : {execution_status}",
        f"   Reason      : {reason}",
        f"   Audit Event : {audit_event.event_id}",
    ]


def runtime_mode_value(result: Any) -> str:
    """Return runtime mode from audit metadata, result model, or safe default."""
    audit_event = getattr(result, "audit_event", None)
    metadata = getattr(audit_event, "metadata", {}) if audit_event else {}

    if isinstance(metadata, dict):
        value = metadata.get("runtime_mode")
        if value:
            return enum_value(value)

    runtime_mode = getattr(result, "runtime_mode", None)
    if runtime_mode is not None:
        value = enum_value(runtime_mode)
        if value and value != "unknown":
            return value

    return "enforce"


def policy_explanation_value(policy_decision: Any, audit_event: Any) -> dict[str, Any]:
    """Return policy explanation from policy decision or audit metadata."""
    explanation = getattr(policy_decision, "explanation", None)

    if explanation is not None:
        if hasattr(explanation, "model_dump"):
            return explanation.model_dump(mode="json")

        if isinstance(explanation, dict):
            return explanation

        return {
            "matched": getattr(explanation, "matched", False),
            "matched_rule_id": getattr(explanation, "matched_rule_id", None),
            "matched_rule_priority": getattr(explanation, "matched_rule_priority", None),
            "matched_conditions": getattr(explanation, "matched_conditions", []),
            "evaluated_rule_ids": getattr(explanation, "evaluated_rule_ids", []),
            "default_decision": getattr(explanation, "default_decision", False),
        }

    metadata = getattr(audit_event, "metadata", {}) if audit_event else {}
    if isinstance(metadata, dict):
        value = metadata.get("policy_explanation")
        if isinstance(value, dict):
            return value

    return {}


def normalize_risk(risk_assessment: Any) -> dict[str, Any]:
    """Normalize risk assessment from dict or Pydantic model."""
    if isinstance(risk_assessment, dict):
        return risk_assessment

    if hasattr(risk_assessment, "model_dump"):
        return risk_assessment.model_dump(mode="json")

    return {}


def enum_value(value: Any) -> str:
    """Return enum value or plain string."""
    return str(getattr(value, "value", value))
