# Audit Viewer Dashboard Plan

## Goal

Plan a future local audit viewer dashboard for Rygnal.

This is planning-only. It does not implement a dashboard, frontend, or API query endpoints.

## Current State

Rygnal already has:

- JSONL audit logs
- Tamper-evident audit hash chaining
- SQLite audit storage backend
- Local FastAPI service
- Policy explain data in audit metadata

## Why This Dashboard Is Needed

A dashboard will help users review:

- what an agent attempted
- what policy decision was made
- why the decision happened
- what risk level was detected
- whether the action was allowed, blocked, simulated, or required approval
- audit history for debugging and governance

## MVP Dashboard Views

### 1. Audit Event List

Show recent audit events with:

- timestamp
- event_id
- trace_id
- tool_name
- action
- environment
- decision
- allowed
- severity
- policy_id

### 2. Audit Event Detail

Show full event details:

- request context
- policy decision
- risk metadata
- policy explanation
- approval metadata when available
- event hash
- previous event hash

### 3. Filters

Basic filters should include:

- decision
- severity
- policy_id
- tool_name
- environment
- allowed
- trace_id

### 4. Integrity Status

Show whether the audit log hash chain is valid.

## API Direction

Future API endpoints may include:

- `GET /v1/audit/events`
- `GET /v1/audit/events/{event_id}`
- `GET /v1/audit/events/{event_id}/integrity`
- `GET /v1/audit/summary`

These endpoints should read from SQLite audit storage first.

JSONL should remain useful for local fallback and tamper-evident verification.

## Dashboard Direction

Recommended frontend direction later:

- simple local web UI first
- read-only audit viewer first
- no editing audit records
- no destructive actions from dashboard
- approval UI should be separate from audit viewer

## Security Boundaries

The audit viewer must be read-only.

The dashboard must not:

- must not execute tools
- must not mutate audit events
- bypass policy decisions
- approve or reject requests in the audit view
- must not expose raw secrets

Sensitive values must remain redacted.

## Not Included Yet

Do not build these in this issue:

- frontend dashboard
- React/Next.js app
- audit query API implementation
- authentication
- authorization
- production deployment
- SIEM export
- advanced analytics

## Recommended Future Phases

### Phase 1: Plan

Define dashboard views, filters, API direction, and security boundaries.

### Phase 2: Audit Query API

Add read-only audit query endpoints on top of SQLite audit storage.

### Phase 3: Local Dashboard Prototype

Add a simple read-only local UI.

### Phase 4: Approval UI

Add separate approval queue UI after approval APIs exist.

### Phase 5: Enterprise Export

Add SIEM/export integrations later.

## Decision

Start with a read-only local audit viewer plan.

Do not build dashboard UI until audit query APIs are implemented.
