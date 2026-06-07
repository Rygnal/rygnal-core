"""Local FastAPI service for Rygnal Core."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from rygnal.audit_logger import AuditLogger
from rygnal.models import AuditEvent, PolicyDecision, ToolRequest
from rygnal.policy_engine import PolicyEngine, load_default_policy_engine
from rygnal.risk_engine import RiskAssessment, RiskEngine


class EvaluateRequest(BaseModel):
    """Request body for local policy/risk evaluation."""

    tool_name: str
    action: str | None = None
    target: str | None = None
    input: Any | None = None
    user_id: str = "api_user"
    agent_id: str = "api_agent"
    environment: str = "local"
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_tool_request(self) -> ToolRequest:
        """Convert API payload to ToolRequest."""
        return ToolRequest(
            tool_name=self.tool_name,
            action=self.action,
            target=self.target,
            input=self.input,
            user_id=self.user_id,
            agent_id=self.agent_id,
            environment=self.environment,
            metadata=self.metadata,
        )


def create_app(
    *,
    policy_engine: PolicyEngine | None = None,
    risk_engine: RiskEngine | None = None,
    audit_logger: AuditLogger | None = None,
) -> FastAPI:
    """Create the local Rygnal FastAPI app."""
    app = FastAPI(
        title="Rygnal Core Local API",
        version="0.1.0",
        description="Local API for evaluating AI-agent tool actions.",
    )

    active_policy_engine = policy_engine or load_default_policy_engine()
    active_risk_engine = risk_engine or RiskEngine()
    active_audit_logger = audit_logger

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "rygnal-core"}

    @app.post("/v1/evaluate")
    def evaluate(payload: EvaluateRequest) -> dict[str, Any]:
        request = payload.to_tool_request()
        risk_assessment: RiskAssessment = active_risk_engine.assess(request)
        policy_decision: PolicyDecision = active_policy_engine.evaluate(
            request,
            risk_assessment=risk_assessment,
        )

        audit_event: AuditEvent | None = None
        if active_audit_logger is not None:
            audit_event = active_audit_logger.log_decision(
                request=request,
                policy_decision=policy_decision,
                metadata={
                    "source": "local_fastapi",
                    "risk": risk_assessment.model_dump(mode="json"),
                },
            )

        return {
            "request": request.model_dump(mode="json"),
            "risk_assessment": risk_assessment.model_dump(mode="json"),
            "policy_decision": policy_decision.model_dump(mode="json"),
            "audit_event": audit_event.model_dump(mode="json") if audit_event else None,
        }

    return app


app = create_app()
