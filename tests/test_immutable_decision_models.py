import pytest
from pydantic import ValidationError

from rygnal.models import (
    AuditEvent,
    Decision,
    PolicyDecision,
    PolicyExplanation,
    Severity,
)


def test_policy_explanation_is_immutable() -> None:
    explanation = PolicyExplanation(
        policy_version="policy.v2",
        matched=False,
        default_decision=True,
    )

    with pytest.raises(ValidationError):
        explanation.default_decision = False


def test_policy_decision_is_immutable() -> None:
    decision = PolicyDecision(
        decision=Decision.BLOCK,
        allowed=False,
        severity=Severity.HIGH,
        reason="Blocked.",
    )

    with pytest.raises(ValidationError):
        decision.reason = "Mutated."


def test_audit_event_is_immutable() -> None:
    event = AuditEvent(
        user_id="user",
        agent_id="agent",
        environment="local",
        tool_name="file_read",
        decision=Decision.BLOCK,
        allowed=False,
        severity=Severity.HIGH,
        reason="Blocked.",
    )

    with pytest.raises(ValidationError):
        event.reason = "Mutated."
