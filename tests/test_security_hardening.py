import json

from demo.demo_tools import (
    build_external_api_send_tool,
    build_file_read_tool,
    build_file_write_tool,
    build_shell_command_tool,
)
from rygnal.audit_logger import AuditLogger
from rygnal.models import Decision, PolicyDecision, Severity, ToolRequest
from rygnal.security import (
    REDACTED,
    SecurityViolation,
    contains_secret,
    redact_sensitive_value,
    resolve_path_inside_sandbox,
    validate_http_url,
    validate_shell_command,
)


def test_path_traversal_is_rejected(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    try:
        resolve_path_inside_sandbox(sandbox, "../outside.txt")
    except SecurityViolation as exc:
        assert "outside" in str(exc)
    else:
        raise AssertionError("Expected path traversal to be rejected.")


def test_file_read_tool_blocks_path_traversal(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    tool = build_file_read_tool(sandbox)
    result = tool(ToolRequest(tool_name="file_read", target="../secret.txt"))

    assert result["ok"] is False
    assert "outside" in result["error"]


def test_file_write_tool_refuses_secret_content(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    tool = build_file_write_tool(sandbox)
    result = tool(
        ToolRequest(
            tool_name="file_write",
            target="notes.txt",
            input="api_key=sk-test-secret-value",
        )
    )

    assert result["ok"] is False
    assert "secrets" in result["error"]
    assert not (sandbox / "notes.txt").exists()


def test_shell_command_rejects_dangerous_command():
    try:
        validate_shell_command("rm -rf /tmp/demo")
    except SecurityViolation as exc:
        assert "Dangerous command" in str(exc)
    else:
        raise AssertionError("Expected dangerous command to be rejected.")


def test_shell_command_rejects_metacharacters():
    try:
        validate_shell_command("echo hello && rm -rf /")
    except SecurityViolation as exc:
        assert "metacharacters" in str(exc)
    else:
        raise AssertionError("Expected shell metacharacters to be rejected.")


def test_shell_tool_blocks_unallowlisted_command(tmp_path):
    tool = build_shell_command_tool(tmp_path)
    result = tool(ToolRequest(tool_name="shell_command", input="whoami"))

    assert result["ok"] is False
    assert "allowlisted" in result["error"]


def test_https_url_allowlist_accepts_known_safe_host():
    assert validate_http_url("https://example.com/collect") == "https://example.com/collect"


def test_http_url_rejects_non_https():
    try:
        validate_http_url("http://example.com/collect")
    except SecurityViolation as exc:
        assert "HTTPS" in str(exc)
    else:
        raise AssertionError("Expected non-HTTPS URL to be rejected.")


def test_http_url_rejects_localhost():
    try:
        validate_http_url("https://127.0.0.1/collect", allowed_hosts={"127.0.0.1"})
    except SecurityViolation as exc:
        assert "Private or local" in str(exc)
    else:
        raise AssertionError("Expected local host to be rejected.")


def test_external_send_tool_blocks_secret_payload():
    tool = build_external_api_send_tool()
    result = tool(
        ToolRequest(
            tool_name="external_api_send",
            input={
                "url": "https://example.com/collect",
                "payload": "token=secret-token-value",
            },
        )
    )

    assert result["ok"] is False
    assert "secrets" in result["error"]


def test_contains_secret_detects_common_secret_patterns():
    assert contains_secret("OPENAI_API_KEY=sk-test-secret-value") is True
    assert contains_secret({"token": "abc123"}) is True


def test_redaction_removes_secret_values():
    value = {
        "api_key": "sk-test-secret-value",
        "nested": {"token": "abc123", "safe": "hello"},
        "message": "password=super-secret",
    }

    redacted = redact_sensitive_value(value)
    serialized = json.dumps(redacted)

    assert redacted["api_key"] == REDACTED
    assert redacted["nested"]["token"] == REDACTED
    assert redacted["nested"]["safe"] == "hello"
    assert "super-secret" not in serialized


def test_audit_logger_redacts_sensitive_metadata(tmp_path):
    logger = AuditLogger(tmp_path / "audit_log.jsonl")

    request = ToolRequest(tool_name="file_read", target="README.md")
    decision = PolicyDecision(
        decision=Decision.ALLOW,
        allowed=True,
        severity=Severity.LOW,
        reason="Allowed.",
    )

    logger.log_decision(
        request,
        decision,
        metadata={"api_key": "sk-test-secret-value", "safe": "ok"},
    )

    event = logger.read_events()[0]
    serialized = json.dumps(event.model_dump(mode="json"))

    assert event.metadata["api_key"] == REDACTED
    assert event.metadata["safe"] == "ok"
    assert "sk-test-secret-value" not in serialized
