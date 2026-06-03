from demo.demo_tools import (
    build_external_api_send_tool,
    build_file_read_tool,
    build_file_write_tool,
    build_shell_command_tool,
)
from rygnal.models import ToolRequest
from rygnal.security import (
    SecurityViolation,
    contains_secret,
    resolve_path_inside_sandbox,
    validate_http_url,
    validate_shell_command,
)


def test_rejects_nested_path_traversal(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    try:
        resolve_path_inside_sandbox(sandbox, "safe/../../outside.txt")
    except SecurityViolation as exc:
        assert "outside" in str(exc)
    else:
        raise AssertionError("Expected nested path traversal to be rejected.")


def test_rejects_absolute_path_escape(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    try:
        resolve_path_inside_sandbox(sandbox, "/etc/passwd")
    except SecurityViolation as exc:
        assert "outside" in str(exc)
    else:
        raise AssertionError("Expected absolute path escape to be rejected.")


def test_file_read_tool_blocks_encoded_like_traversal_attempt(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    tool = build_file_read_tool(sandbox)
    result = tool(ToolRequest(tool_name="file_read", target="../.env.backup"))

    assert result["ok"] is False
    assert "outside" in result["error"]


def test_file_write_tool_blocks_nested_secret_payload(tmp_path):
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()

    tool = build_file_write_tool(sandbox)
    result = tool(
        ToolRequest(
            tool_name="file_write",
            target="notes.txt",
            input={
                "message": "safe text",
                "metadata": {"token": "hidden-secret-value"},
            },
        )
    )

    assert result["ok"] is False
    assert "secrets" in result["error"]
    assert not (sandbox / "notes.txt").exists()


def test_contains_secret_detects_nested_list_payload():
    payload = {
        "events": [
            {"type": "safe", "value": "hello"},
            {"type": "secret", "value": "api_key=sk-hidden-value"},
        ]
    }

    assert contains_secret(payload) is True


def test_shell_command_blocks_command_chaining():
    try:
        validate_shell_command("echo safe && cat .env")
    except SecurityViolation as exc:
        assert "metacharacters" in str(exc)
    else:
        raise AssertionError("Expected command chaining to be rejected.")


def test_shell_command_blocks_pipe_exfiltration():
    try:
        validate_shell_command("cat README.md | cat .env")
    except SecurityViolation as exc:
        assert "metacharacters" in str(exc)
    else:
        raise AssertionError("Expected pipe usage to be rejected.")


def test_shell_tool_blocks_unallowlisted_identity_command(tmp_path):
    tool = build_shell_command_tool(tmp_path)
    result = tool(ToolRequest(tool_name="shell_command", input="whoami"))

    assert result["ok"] is False
    assert "allowlisted" in result["error"]


def test_http_url_blocks_cloud_metadata_ip():
    try:
        validate_http_url(
            "https://169.254.169.254/latest/meta-data",
            allowed_hosts={"169.254.169.254"},
        )
    except SecurityViolation as exc:
        assert "Private or local" in str(exc)
    else:
        raise AssertionError("Expected metadata IP to be rejected.")


def test_external_send_blocks_hidden_secret_payload():
    tool = build_external_api_send_tool()
    result = tool(
        ToolRequest(
            tool_name="external_api_send",
            input={
                "url": "https://example.com/collect",
                "events": [
                    {"kind": "safe", "value": "hello"},
                    {"kind": "hidden", "value": "token=secret-token-value"},
                ],
            },
        )
    )

    assert result["ok"] is False
    assert "secrets" in result["error"]


def test_external_send_blocks_private_network_destination():
    tool = build_external_api_send_tool()
    result = tool(
        ToolRequest(
            tool_name="external_api_send",
            input={
                "url": "https://127.0.0.1/collect",
                "payload": "safe",
            },
        )
    )

    assert result["ok"] is False
    assert result["transport"] == "blocked"
