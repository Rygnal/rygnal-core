from pathlib import Path


def test_role_based_approval_design_doc_exists():
    assert Path("docs/35-role-based-approval-design.md").exists()


def test_role_based_approval_design_defines_config_separation():
    content = Path("docs/35-role-based-approval-design.md").read_text()

    required_terms = [
        "policies/roles.yaml",
        "default_policy.yaml",
        "PolicyEngine",
        "ApprovalAuthorizationEngine",
    ]

    for term in required_terms:
        assert term in content


def test_role_based_approval_design_defines_hard_invariants():
    content = Path("docs/35-role-based-approval-design.md").read_text()

    required_terms = [
        "requester must not approve their own request",
        "only pending requests can be approved or rejected",
        "rejected requests must never execute",
        "every approval decision must be audited",
    ]

    for term in required_terms:
        assert term in content


def test_role_based_approval_design_defines_enforcement_order():
    content = Path("docs/35-role-based-approval-design.md").read_text()

    required_terms = [
        "Self-approval guard",
        "Pending-state check",
        "Role permission check",
        "Audit write",
    ]

    for term in required_terms:
        assert term in content


def test_role_based_approval_design_defines_reviewer_role_storage():
    content = Path("docs/35-role-based-approval-design.md").read_text()

    assert "reviewer_role" in content
    assert "stored at decision time" in content
    assert "roles can change later" in content
