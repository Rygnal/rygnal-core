from pathlib import Path

from examples.live_mcp_client_server import (
    LiveMCPClient,
    LiveMCPServer,
    build_live_mcp_demo,
    run_live_mcp_demo,
)
from examples.mcp_tool_call_adapter import build_demo_rygnal


def test_live_mcp_client_server_allows_safe_file_read(tmp_path):
    audit_log_path = tmp_path / "live_mcp_audit.jsonl"
    client, _server = build_live_mcp_demo(str(audit_log_path))

    result = client.call_tool(
        "file_read",
        {
            "action": "read_file",
            "target": "README.md",
        },
        request_id="live_safe_read",
    )

    assert result["id"] == "live_safe_read"
    assert result["allowed"] is True
    assert result["executed"] is True
    assert result["decision"] == "allow"
    assert result["result"]["target"] == "README.md"
    assert Path(audit_log_path).exists()


def test_live_mcp_client_server_blocks_secret_file_read(tmp_path):
    audit_log_path = tmp_path / "live_mcp_audit.jsonl"
    client, _server = build_live_mcp_demo(str(audit_log_path))

    result = client.call_tool(
        "file_read",
        {
            "action": "read_file",
            "target": ".env",
        },
        request_id="live_secret_read",
    )

    assert result["id"] == "live_secret_read"
    assert result["allowed"] is False
    assert result["executed"] is False
    assert result["decision"] == "block"
    assert result["result"] is None
    assert Path(audit_log_path).exists()


def test_live_mcp_server_rejects_unsupported_method(tmp_path):
    rygnal = build_demo_rygnal(str(tmp_path / "audit.jsonl"))
    server = LiveMCPServer(rygnal)

    result = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": "bad_method",
            "method": "tools/list",
        }
    )

    assert result["id"] == "bad_method"
    assert result["error"]["code"] == -32601
    assert result["error"]["message"] == "Unsupported MCP method."


def test_live_mcp_client_generates_request_id(tmp_path):
    audit_log_path = tmp_path / "live_mcp_audit.jsonl"
    client, _server = build_live_mcp_demo(str(audit_log_path))

    result = client.call_tool(
        "file_read",
        {
            "action": "read_file",
            "target": "README.md",
        },
    )

    assert result["id"].startswith("mcp_")
    assert result["allowed"] is True


def test_run_live_mcp_demo_creates_audit_log(tmp_path):
    audit_log_path = tmp_path / "live_mcp_audit.jsonl"

    result = run_live_mcp_demo(audit_log_path=str(audit_log_path))

    assert result["id"] == "live_mcp_demo"
    assert result["allowed"] is True
    assert audit_log_path.exists()


def test_live_mcp_client_type_is_exported_by_example_module(tmp_path):
    audit_log_path = tmp_path / "audit.jsonl"
    client, server = build_live_mcp_demo(str(audit_log_path))

    assert isinstance(client, LiveMCPClient)
    assert isinstance(server, LiveMCPServer)
