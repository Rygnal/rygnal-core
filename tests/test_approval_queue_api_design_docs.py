from pathlib import Path


def test_approval_queue_api_design_doc_exists():
    assert Path("docs/34-approval-queue-api-design.md").exists()


def test_approval_queue_api_design_mentions_required_endpoints():
    content = Path("docs/34-approval-queue-api-design.md").read_text()

    required_terms = [
        "POST /v1/approvals",
        "GET /v1/approvals",
        "GET /v1/approvals/{approval_id}",
        "POST /v1/approvals/{approval_id}/approve",
        "POST /v1/approvals/{approval_id}/reject",
    ]

    for term in required_terms:
        assert term in content


def test_approval_queue_api_design_states_security_boundaries():
    content = Path("docs/34-approval-queue-api-design.md").read_text()

    required_terms = [
        "API must not execute tools directly",
        "auth/RBAC is required before production use",
        "rejected request must not execute",
        "only pending requests can be approved or rejected",
    ]

    for term in required_terms:
        assert term in content
