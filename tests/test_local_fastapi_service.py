from fastapi.testclient import TestClient

from rygnal.api import create_app
from rygnal.audit_logger import AuditLogger


def test_local_api_health_endpoint():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "rygnal-core"}


def test_local_api_evaluate_blocks_env_file():
    client = TestClient(create_app())

    response = client.post(
        "/v1/evaluate",
        json={
            "tool_name": "file_read",
            "action": "read_file",
            "target": ".env",
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert data["risk_assessment"]["risk_level"] == "critical"
    assert data["policy_decision"]["decision"] == "block"
    assert data["policy_decision"]["allowed"] is False
    assert data["policy_decision"]["policy_id"] == "block-env-read"
    assert data["audit_event"] is None


def test_local_api_evaluate_with_audit_logger(tmp_path):
    audit_logger = AuditLogger(tmp_path / "api_audit.jsonl")
    client = TestClient(create_app(audit_logger=audit_logger))

    response = client.post(
        "/v1/evaluate",
        json={
            "tool_name": "shell_command",
            "action": "execute",
            "input": "rm -rf /tmp/demo",
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert data["policy_decision"]["decision"] == "block"
    assert data["audit_event"] is not None
    assert data["audit_event"]["event_id"].startswith("evt_")
    assert (tmp_path / "api_audit.jsonl").exists()


def test_local_api_safe_request_defaults_to_allow():
    client = TestClient(create_app())

    response = client.post(
        "/v1/evaluate",
        json={
            "tool_name": "file_read",
            "action": "read_file",
            "target": "README.md",
        },
    )

    data = response.json()

    assert response.status_code == 200
    assert data["policy_decision"]["decision"] == "allow"
    assert data["policy_decision"]["allowed"] is True
