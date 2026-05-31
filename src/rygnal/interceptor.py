"""Rygnal interceptor.

The interceptor is the runtime control point between AI agents and tools.
"""

from rygnal.audit_logger import AuditLogger
from rygnal.models import (
    Decision,
    ExecutionStatus,
    InterceptorResult,
    ToolExecutionResult,
    ToolRequest,
)
from rygnal.policy_engine import PolicyEngine
from rygnal.risk_engine import RiskEngine
from rygnal.tool_executor import ToolExecutor


class RygnalInterceptor:
    """Intercept AI-agent tool requests before execution."""

    def __init__(
        self,
        policy_engine: PolicyEngine,
        audit_logger: AuditLogger,
        tool_executor: ToolExecutor,
        risk_engine: RiskEngine | None = None,
    ) -> None:
        self.policy_engine = policy_engine
        self.audit_logger = audit_logger
        self.tool_executor = tool_executor
        self.risk_engine = risk_engine or RiskEngine()

    def intercept(self, request: ToolRequest) -> InterceptorResult:
        """Assess risk, apply policy, audit, and optionally execute a tool request."""
        risk_assessment = self.risk_engine.assess(request)
        policy_decision = self.policy_engine.evaluate(request)

        audit_metadata = {
            "risk_score": risk_assessment.risk_score,
            "risk_level": risk_assessment.risk_level.value,
            "risk_reasons": risk_assessment.reasons,
            "risk_signals": [signal.model_dump(mode="json") for signal in risk_assessment.signals],
        }

        audit_event = self.audit_logger.log_decision(
            request, policy_decision, metadata=audit_metadata
        )

        if policy_decision.decision == Decision.ALLOW:
            execution = self.tool_executor.execute(request)
        elif policy_decision.decision == Decision.SIMULATE:
            execution = ToolExecutionResult(
                status=ExecutionStatus.SIMULATED,
                executed=False,
                output="Simulated decision. Tool was not executed.",
            )
        else:
            execution = ToolExecutionResult(
                status=ExecutionStatus.SKIPPED,
                executed=False,
                error=f"Tool execution skipped because decision is: {policy_decision.decision}",
            )

        return InterceptorResult(
            request=request,
            policy_decision=policy_decision,
            audit_event=audit_event,
            execution=execution,
            risk_assessment=risk_assessment.model_dump(mode="json"),
        )

    def handle(self, request: ToolRequest) -> InterceptorResult:
        """Alias for intercept."""
        return self.intercept(request)
