import json

from rygnal.audit_logger import AuditLogger
from rygnal.models import Decision, PolicyDecision, Severity, ToolRequest

RAW_SECRETS = (
    "trace-secret-value",
    "target-secret-value",
    "input-password-value",
    "nested-token-value",
    "metadata-api-key-value",
    "approval-password-value",
)


def serialized_event(log_path) -> str:
    return log_path.read_text(encoding="utf-8")


def assert_no_raw_secret_leaks(payload: str) -> None:
    for secret in RAW_SECRETS:
        assert secret not in payload


def blocked_decision() -> PolicyDecision:
    return PolicyDecision(
        decision=Decision.BLOCK,
        allowed=False,
        severity=Severity.CRITICAL,
        policy_id="block-secret-regression",
        reason="Blocked for raw secret leak regression.",
    )


def test_audit_log_never_persists_raw_secrets_across_request_fields(tmp_path):
    log_path = tmp_path / "audit_log.jsonl"
    logger = AuditLogger(log_path)

    request = ToolRequest(
        tool_name="external_api_send",
        action="send_data",
        target="token=target-secret-value",
        input={
            "password": "input-password-value",
            "payload": [
                {"token": "nested-token-value"},
                "api_key=metadata-api-key-value",
            ],
            "safe": "hello",
        },
        metadata={
            "trace_id": "token=trace-secret-value",
            "api_key": "metadata-api-key-value",
        },
    )

    logger.log_decision(
        request=request,
        policy_decision=blocked_decision(),
        metadata={
            "api_key": "metadata-api-key-value",
            "approval": {
                "approval_id": "apr_safe",
                "status": "rejected",
                "metadata": {
                    "password": "approval-password-value",
                    "nested": {"token": "nested-token-value"},
                },
            },
        },
    )

    payload = serialized_event(log_path)

    assert_no_raw_secret_leaks(payload)
    assert "[REDACTED]" in payload

    saved_event = json.loads(payload.splitlines()[0])
    assert "[REDACTED]" in saved_event["trace_id"]
    assert saved_event["input"]["password"] == "[REDACTED]"
    assert saved_event["input"]["payload"][0]["token"] == "[REDACTED]"
    assert saved_event["metadata"]["api_key"] == "[REDACTED]"
    assert saved_event["metadata"]["approval"]["metadata"]["password"] == "[REDACTED]"
