from pathlib import Path


def test_audit_viewer_dashboard_plan_doc_exists():
    assert Path("docs/37-audit-viewer-dashboard-plan.md").exists()


def test_audit_viewer_dashboard_plan_mentions_core_views():
    content = Path("docs/37-audit-viewer-dashboard-plan.md").read_text()

    required_terms = [
        "Audit Event List",
        "Audit Event Detail",
        "Filters",
        "Integrity Status",
    ]

    for term in required_terms:
        assert term in content


def test_audit_viewer_dashboard_plan_mentions_future_api_endpoints():
    content = Path("docs/37-audit-viewer-dashboard-plan.md").read_text()

    required_terms = [
        "GET /v1/audit/events",
        "GET /v1/audit/events/{event_id}",
        "GET /v1/audit/events/{event_id}/integrity",
        "GET /v1/audit/summary",
    ]

    for term in required_terms:
        assert term in content


def test_audit_viewer_dashboard_plan_is_read_only():
    content = Path("docs/37-audit-viewer-dashboard-plan.md").read_text()

    required_terms = [
        "read-only",
        "must not execute tools",
        "must not mutate audit events",
        "Sensitive values must remain redacted",
    ]

    for term in required_terms:
        assert term in content
