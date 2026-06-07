from pathlib import Path


def test_live_mcp_client_server_doc_exists():
    assert Path("docs/40-live-mcp-client-server.md").exists()


def test_live_mcp_client_server_doc_mentions_core_components():
    content = Path("docs/40-live-mcp-client-server.md").read_text()

    required_terms = [
        "LiveMCPServer",
        "LiveMCPClient",
        "build_live_mcp_demo",
        "run_live_mcp_demo",
    ]

    for term in required_terms:
        assert term in content


def test_live_mcp_client_server_doc_mentions_safety_rules():
    content = Path("docs/40-live-mcp-client-server.md").read_text()

    required_terms = [
        "MCP tool calls must not execute directly",
        "MCP requests must route through Rygnal first",
        "Audit logs must be generated",
        "Unsupported MCP methods must return an error",
    ]

    for term in required_terms:
        assert term in content


def test_live_mcp_client_server_doc_mentions_not_included_yet():
    content = Path("docs/40-live-mcp-client-server.md").read_text()

    required_terms = [
        "real external MCP server",
        "network transport",
        "MCP authentication",
        "production MCP gateway",
    ]

    for term in required_terms:
        assert term in content
