"""Risk engine for Rygnal.

Risk Engine v2 foundation provides deterministic, contextual, and explainable
risk scoring for AI-agent tool requests before execution.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from enum import StrEnum
from typing import Any, Protocol

from pydantic import BaseModel, Field

from rygnal.models import ToolRequest


class RiskLevel(StrEnum):
    """Risk level for an AI-agent tool request."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskSignalCategory(StrEnum):
    """Category for an explainable risk signal."""

    BASELINE = "baseline"
    CAPABILITY = "capability"
    ACTION = "action"
    ASSET = "asset"
    DATA = "data"
    DESTINATION = "destination"
    ENVIRONMENT = "environment"
    COMMAND = "command"


class RiskContext(BaseModel):
    """Normalized context used by Risk Engine v2."""

    tool_name: str
    action: str | None = None
    target: Any | None = None
    input: Any | None = None
    user_id: str
    agent_id: str
    environment: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    tool_name_normalized: str
    target_text: str = ""
    input_text: str = ""

    @classmethod
    def from_request(cls, request: ToolRequest) -> RiskContext:
        """Build normalized risk context from a tool request."""
        return cls(
            tool_name=request.tool_name,
            action=request.action,
            target=request.target,
            input=request.input,
            user_id=request.user_id,
            agent_id=request.agent_id,
            environment=request.environment,
            metadata=request.metadata,
            tool_name_normalized=request.tool_name.lower(),
            target_text=str(request.target or "").lower(),
            input_text=stringify_value(request.input),
        )


class RiskSignal(BaseModel):
    """A single explainable risk signal."""

    code: str
    severity: RiskLevel
    score: int = Field(ge=0, le=100)
    reason: str
    category: RiskSignalCategory = RiskSignalCategory.BASELINE
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    evidence: dict[str, Any] = Field(default_factory=dict)
    reversible: bool | None = None


class RiskAssessment(BaseModel):
    """Final risk assessment for a tool request."""

    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    reasons: list[str]
    signals: list[RiskSignal]
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    explanation: str = ""


class RiskScoringProfile(BaseModel):
    """Deterministic thresholds for mapping score to risk level."""

    medium_threshold: int = 30
    high_threshold: int = 60
    critical_threshold: int = 85

    def level_from_score(self, score: int) -> RiskLevel:
        """Map a risk score to a risk level."""
        if score >= self.critical_threshold:
            return RiskLevel.CRITICAL

        if score >= self.high_threshold:
            return RiskLevel.HIGH

        if score >= self.medium_threshold:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW


class RiskSignalDetector(Protocol):
    """Protocol for risk signal detectors."""

    def detect(self, context: RiskContext) -> list[RiskSignal]:
        """Return risk signals for the provided context."""


class ToolCapabilityDetector:
    """Detect risk based on tool capability."""

    def detect(self, context: RiskContext) -> list[RiskSignal]:
        signals: list[RiskSignal] = []
        tool_name = context.tool_name_normalized

        if tool_name in {"file_delete", "delete_file"}:
            signals.append(
                RiskSignal(
                    code="file-delete",
                    category=RiskSignalCategory.CAPABILITY,
                    severity=RiskLevel.HIGH,
                    score=75,
                    reason="Agent requested file deletion.",
                    evidence={"tool_name": context.tool_name},
                    reversible=False,
                )
            )

        if tool_name in {"shell_command", "terminal", "exec", "run_command"}:
            signals.append(
                RiskSignal(
                    code="shell-execution",
                    category=RiskSignalCategory.CAPABILITY,
                    severity=RiskLevel.HIGH,
                    score=70,
                    reason="Agent requested shell or terminal execution.",
                    evidence={"tool_name": context.tool_name},
                    reversible=None,
                )
            )

        if tool_name in {"external_api_send", "http_request", "webhook_send", "api_call"}:
            signals.append(
                RiskSignal(
                    code="external-data-send",
                    category=RiskSignalCategory.DESTINATION,
                    severity=RiskLevel.HIGH,
                    score=65,
                    reason="Agent requested sending data to an external destination.",
                    evidence={"tool_name": context.tool_name},
                    reversible=False,
                )
            )

        if tool_name in {
            "database_write",
            "database_delete",
            "db_write",
            "db_delete",
            "sql_execute",
        }:
            signals.append(
                RiskSignal(
                    code="database-mutation",
                    category=RiskSignalCategory.CAPABILITY,
                    severity=RiskLevel.HIGH,
                    score=80,
                    reason="Agent requested database modification.",
                    evidence={"tool_name": context.tool_name},
                    reversible=False,
                )
            )

        if tool_name in {"database_read", "db_read", "sql_query"}:
            signals.append(
                RiskSignal(
                    code="database-read",
                    category=RiskSignalCategory.CAPABILITY,
                    severity=RiskLevel.MEDIUM,
                    score=45,
                    reason="Agent requested database read access.",
                    evidence={"tool_name": context.tool_name},
                    reversible=True,
                )
            )

        return signals


class TargetSensitivityDetector:
    """Detect risk based on sensitive targets/assets."""

    SENSITIVE_TARGET_PATTERNS = (
        ".env",
        ".env.backup",
        "secrets.yaml",
        "secrets.yml",
        "credentials.json",
        "credential.json",
        ".npmrc",
        ".pypirc",
        "id_rsa",
        "id_dsa",
        "private.key",
        "private.pem",
        "service-account.json",
        "service_account.json",
        "database.yml",
        "database.yaml",
        "db.yml",
        "db.yaml",
    )

    def detect(self, context: RiskContext) -> list[RiskSignal]:
        target = context.target_text
        signals: list[RiskSignal] = []

        if not target:
            return signals

        if ".env" in target or target.endswith("env"):
            signals.append(
                RiskSignal(
                    code="env-file-access",
                    category=RiskSignalCategory.ASSET,
                    severity=RiskLevel.CRITICAL,
                    score=95,
                    reason="Agent targeted an environment secret file.",
                    evidence={"target": context.target},
                    reversible=True,
                )
            )

        if any(pattern in target for pattern in self.SENSITIVE_TARGET_PATTERNS):
            signals.append(
                RiskSignal(
                    code="sensitive-config-target",
                    category=RiskSignalCategory.ASSET,
                    severity=RiskLevel.CRITICAL,
                    score=90,
                    reason="Agent targeted a sensitive configuration, credential, or key file.",
                    evidence={"target": context.target},
                    reversible=True,
                )
            )

        if any(keyword in target for keyword in ("secret", "credential", "private_key", "token")):
            signals.append(
                RiskSignal(
                    code="sensitive-target",
                    category=RiskSignalCategory.ASSET,
                    severity=RiskLevel.HIGH,
                    score=70,
                    reason="Agent targeted a path or object that appears sensitive.",
                    evidence={"target": context.target},
                    reversible=True,
                )
            )

        if any(keyword in target for keyword in ("customer", "user", "payment", "invoice")):
            signals.append(
                RiskSignal(
                    code="sensitive-business-data",
                    category=RiskSignalCategory.DATA,
                    severity=RiskLevel.MEDIUM,
                    score=45,
                    reason="Agent targeted possible sensitive business or customer data.",
                    evidence={"target": context.target},
                    reversible=True,
                )
            )

        return signals


class InputSensitivityDetector:
    """Detect risk based on sensitive or dangerous input content."""

    SECRET_PATTERNS = (
        re.compile(r"(?i)\bapi[_-]?key\b\s*[:=]\s*\S+"),
        re.compile(r"(?i)\btoken\b\s*[:=]\s*\S+"),
        re.compile(r"(?i)\bsecret\b\s*[:=]\s*\S+"),
        re.compile(r"(?i)\bpassword\b\s*[:=]\s*\S+"),
        re.compile(r"(?i)\bprivate[_-]?key\b"),
        re.compile(r"(?i)\baws_access_key_id\b"),
        re.compile(r"(?i)\baws_secret_access_key\b"),
        re.compile(r"(?i)sk-[A-Za-z0-9_-]{12,}"),
    )

    DANGEROUS_SHELL_PATTERNS = (
        re.compile(r"rm\s+-rf"),
        re.compile(r"sudo\s+"),
        re.compile(r"chmod\s+777"),
        re.compile(r"curl\s+"),
        re.compile(r"wget\s+"),
        re.compile(r"nc\s+"),
        re.compile(r"bash\s+-c"),
        re.compile(r"sh\s+-c"),
        re.compile(r">\s*/etc/"),
    )

    def detect(self, context: RiskContext) -> list[RiskSignal]:
        raw_input = context.input_text
        signals: list[RiskSignal] = []

        if not raw_input:
            return signals

        if any(pattern.search(raw_input) for pattern in self.SECRET_PATTERNS):
            signals.append(
                RiskSignal(
                    code="secret-in-input",
                    category=RiskSignalCategory.DATA,
                    severity=RiskLevel.CRITICAL,
                    score=95,
                    reason="Agent input appears to contain a secret or credential.",
                    evidence={"input_detected": True},
                    reversible=False,
                )
            )

        if any(pattern.search(raw_input) for pattern in self.DANGEROUS_SHELL_PATTERNS):
            signals.append(
                RiskSignal(
                    code="dangerous-shell-pattern",
                    category=RiskSignalCategory.COMMAND,
                    severity=RiskLevel.CRITICAL,
                    score=90,
                    reason="Agent input contains a dangerous shell command pattern.",
                    evidence={"input_detected": True},
                    reversible=False,
                )
            )

        return signals


class EnvironmentDetector:
    """Detect risk based on execution environment."""

    def detect(self, context: RiskContext) -> list[RiskSignal]:
        environment = context.environment.lower()

        if environment == "production":
            return [
                RiskSignal(
                    code="production-environment",
                    category=RiskSignalCategory.ENVIRONMENT,
                    severity=RiskLevel.MEDIUM,
                    score=25,
                    reason="Agent action is running in a production environment.",
                    evidence={"environment": context.environment},
                    reversible=None,
                )
            ]

        return []


class RiskSignalRegistry:
    """Registry of deterministic risk signal detectors."""

    def __init__(self, detectors: Iterable[RiskSignalDetector] | None = None) -> None:
        self.detectors = list(detectors or [])

    @classmethod
    def default(cls) -> RiskSignalRegistry:
        """Return the default Risk Engine v2 signal registry."""
        return cls(
            detectors=[
                ToolCapabilityDetector(),
                TargetSensitivityDetector(),
                InputSensitivityDetector(),
                EnvironmentDetector(),
            ]
        )

    def detect(self, context: RiskContext) -> list[RiskSignal]:
        """Run all registered detectors."""
        signals: list[RiskSignal] = []

        for detector in self.detectors:
            signals.extend(detector.detect(context))

        return signals


class RiskEngine:
    """Deterministic, contextual risk scorer for AI-agent tool requests."""

    def __init__(
        self,
        registry: RiskSignalRegistry | None = None,
        scoring_profile: RiskScoringProfile | None = None,
    ) -> None:
        self.registry = registry or RiskSignalRegistry.default()
        self.scoring_profile = scoring_profile or RiskScoringProfile()

    def assess(self, request: ToolRequest) -> RiskAssessment:
        """Assess risk for a tool request."""
        context = RiskContext.from_request(request)
        signals = self.registry.detect(context)

        if not signals:
            signals.append(
                RiskSignal(
                    code="baseline-low-risk",
                    category=RiskSignalCategory.BASELINE,
                    severity=RiskLevel.LOW,
                    score=10,
                    confidence=0.8,
                    reason="No risky tool, target, or input pattern detected.",
                    evidence={"tool_name": request.tool_name},
                    reversible=True,
                )
            )

        risk_score = min(sum(signal.score for signal in signals), 100)
        risk_level = self.scoring_profile.level_from_score(risk_score)
        reasons = [signal.reason for signal in signals]
        confidence = self._confidence(signals)

        return RiskAssessment(
            risk_score=risk_score,
            risk_level=risk_level,
            reasons=reasons,
            signals=signals,
            confidence=confidence,
            explanation=self._explanation(risk_score, risk_level, signals),
        )

    @staticmethod
    def _confidence(signals: list[RiskSignal]) -> float:
        if not signals:
            return 0.0

        return round(sum(signal.confidence for signal in signals) / len(signals), 2)

    @staticmethod
    def _explanation(
        risk_score: int,
        risk_level: RiskLevel,
        signals: list[RiskSignal],
    ) -> str:
        signal_codes = ", ".join(signal.code for signal in signals)
        return f"Risk score {risk_score} mapped to {risk_level.value} based on: {signal_codes}."


def stringify_value(value: Any) -> str:
    """Stringify values for deterministic pattern matching."""
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    return str(value)
