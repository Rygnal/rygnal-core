"""Append-only audit logger for Rygnal.

The logger stores structured JSONL audit events and adds a simple hash chain
so future tampering can be detected.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from rygnal.models import AuditEvent, PolicyDecision, ToolRequest, new_trace_id

SENSITIVE_KEYWORDS = (
    "password",
    "passwd",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "credential",
)

REDACTED = "[REDACTED]"


class AuditLogger:
    """Write Rygnal audit events to an append-only JSONL file."""

    def __init__(self, log_path: str | Path = "logs/audit_log.jsonl") -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_decision(
        self,
        request: ToolRequest,
        policy_decision: PolicyDecision,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Create and persist an audit event for a policy decision."""
        trace_id = str(request.metadata.get("trace_id") or new_trace_id())

        event = AuditEvent(
            trace_id=trace_id,
            user_id=request.user_id,
            agent_id=request.agent_id,
            environment=request.environment,
            tool_name=request.tool_name,
            action=request.action,
            target=redact_sensitive_value(request.target),
            input=redact_sensitive_value(request.input),
            decision=policy_decision.decision,
            allowed=policy_decision.allowed,
            severity=policy_decision.severity,
            policy_id=policy_decision.policy_id,
            reason=policy_decision.reason,
            metadata=metadata or {},
        )

        self.write_event(event)
        return event

    def write_event(self, event: AuditEvent) -> None:
        """Append one audit event to the JSONL log file."""
        event.prev_event_hash = self._last_event_hash()
        event.event_hash = self._calculate_event_hash(event)

        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(event.model_dump(mode="json"), sort_keys=True) + "\n")

    def read_events(self) -> list[AuditEvent]:
        """Read all audit events from the log file."""
        if not self.log_path.exists():
            return []

        events: list[AuditEvent] = []
        for line in self.log_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(AuditEvent(**json.loads(line)))

        return events

    def verify_integrity(self) -> bool:
        """Verify the audit log hash chain."""
        events = self.read_events()
        previous_hash: str | None = None

        for event in events:
            expected_hash = event.event_hash
            event.prev_event_hash = previous_hash
            event.event_hash = None

            actual_hash = self._calculate_event_hash(event)

            if actual_hash != expected_hash:
                return False

            previous_hash = expected_hash

        return True

    def _last_event_hash(self) -> str | None:
        if not self.log_path.exists():
            return None

        lines = [line for line in self.log_path.read_text(encoding="utf-8").splitlines() if line]
        if not lines:
            return None

        last_event = json.loads(lines[-1])
        return last_event.get("event_hash")

    @staticmethod
    def _calculate_event_hash(event: AuditEvent) -> str:
        data = event.model_dump(mode="json")
        data["event_hash"] = None
        payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def redact_sensitive_value(value: Any) -> Any:
    """Redact secrets from nested dict/list/string values before logging."""
    if value is None:
        return None

    if isinstance(value, dict):
        return {
            key: REDACTED if is_sensitive_key(key) else redact_sensitive_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [redact_sensitive_value(item) for item in value]

    if isinstance(value, tuple):
        return tuple(redact_sensitive_value(item) for item in value)

    if isinstance(value, str):
        return redact_sensitive_string(value)

    return value


def is_sensitive_key(key: str) -> bool:
    """Return True when a key name looks sensitive."""
    normalized_key = key.lower().replace("-", "_")
    return any(keyword in normalized_key for keyword in SENSITIVE_KEYWORDS)


def redact_sensitive_string(value: str) -> str:
    """Redact common secret assignments inside strings."""
    pattern = re.compile(
        r"(?i)(password|passwd|secret|token|api_key|apikey|access_key|private_key)"
        r"\s*[:=]\s*[^\s,;]+"
    )
    return pattern.sub(lambda match: f"{match.group(1)}={REDACTED}", value)
