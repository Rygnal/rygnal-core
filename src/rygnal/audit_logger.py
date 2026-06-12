"""Append-only audit logger for Rygnal.

The logger stores structured JSONL audit events and adds a hash chain so
tampering can be detected. Each JSONL append is flushed and fsynced before
returning to reduce audit-loss risk after process or host failure.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from rygnal.models import AuditEvent, PolicyDecision, ToolRequest, new_trace_id
from rygnal.security import redact_sensitive_value

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

    def __init__(
        self,
        log_path: str | Path = "logs/audit_log.jsonl",
        storage_backend: Any | None = None,
    ) -> None:
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_backend = storage_backend

    def log_decision(
        self,
        request: ToolRequest,
        policy_decision: PolicyDecision,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Create, hash, durably append, and return an audit event."""
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
            metadata=redact_sensitive_value(metadata or {}),
        )

        return self.write_event(event)

    def write_event(self, event: AuditEvent) -> AuditEvent:
        """Append one immutable audit event to the JSONL log file."""
        event_with_previous_hash = event.model_copy(
            update={"prev_event_hash": self._last_event_hash()}
        )
        persisted_event = event_with_previous_hash.model_copy(
            update={"event_hash": self._calculate_event_hash(event_with_previous_hash)}
        )

        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(
                json.dumps(persisted_event.model_dump(mode="json"), sort_keys=True) + "\n"
            )
            log_file.flush()
            os.fsync(log_file.fileno())

        if self.storage_backend is not None:
            self.storage_backend.write_event(persisted_event)

        return persisted_event

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
        """Verify the audit log hash chain without mutating loaded events."""
        events = self.read_events()
        previous_hash: str | None = None

        for event in events:
            expected_hash = event.event_hash
            event_for_hash = event.model_copy(
                update={
                    "prev_event_hash": previous_hash,
                    "event_hash": None,
                }
            )
            actual_hash = self._calculate_event_hash(event_for_hash)

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
