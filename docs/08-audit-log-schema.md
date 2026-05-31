# Audit Log Schema

Rygnal audit logs are append-only JSONL events.

## Goals

- Record every AI-agent tool decision
- Preserve security context
- Avoid storing raw secrets
- Support future compliance review
- Provide tamper-evident hash chaining

## Event Fields

- `schema_version`
- `event_id`
- `timestamp`
- `trace_id`
- `user_id`
- `agent_id`
- `environment`
- `tool_name`
- `action`
- `target`
- `input`
- `decision`
- `allowed`
- `severity`
- `policy_id`
- `reason`
- `metadata`
- `prev_event_hash`
- `event_hash`
