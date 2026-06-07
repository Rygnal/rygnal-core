# Approval Queue and API Design

This document defines the future Approval Queue and API direction for Rygnal Core.

## Goal

Design a local approval queue API so actions requiring human approval can be reviewed, approved, or rejected through a service layer.

This is a design-only step. It does not implement the approval queue runtime yet.

## Current State

Rygnal currently supports approval workflow through `ApprovalWorkflow`.

The current approval flow is resolver-based:

1. Policy decision returns `require_approval`
2. ApprovalWorkflow creates an ApprovalRequest
3. A resolver returns an ApprovalDecision
4. Interceptor continues or skips execution based on the decision

The local FastAPI service currently supports health and evaluation endpoints, but it does not yet expose approval queue endpoints.

## Why Approval Queue Is Needed

A queue-based approval system is needed for:

- API-driven approval review
- future dashboard approval UI
- team-based approval workflows
- auditability of pending/approved/rejected actions
- safer handling of high-risk agent actions

## Approval Lifecycle

Approval requests should move through this lifecycle:

1. pending
2. approved or rejected
3. audit recorded
4. tool execution allowed only when approved and policy requires approval

## Future Data Model

A future approval queue item should include:

- approval_id
- trace_id
- created_at
- requested_by
- agent_id
- environment
- tool_name
- action
- target
- policy_id
- reason
- risk_assessment
- metadata
- status
- decided_by
- decided_at
- decision_reason

## Proposed API Endpoints

### POST /v1/approvals

Create an approval request.

This may be used internally by the interceptor or service layer.

### GET /v1/approvals

List approval requests.

Supported filters later may include:

- status
- environment
- agent_id
- requested_by
- policy_id

### GET /v1/approvals/{approval_id}

Read a single approval request.

### POST /v1/approvals/{approval_id}/approve

Approve a pending request.

### POST /v1/approvals/{approval_id}/reject

Reject a pending request.

## API Response Shape

Approval API responses should include:

- approval request data
- current status
- decision metadata if decided
- audit/event references when available

## Storage Direction

Short term:

- in-memory approval queue for local development

Medium term:

- SQLite approval queue storage

Long term:

- Postgres-backed approval queue for team/cloud use

## Security Boundaries

Approval APIs must not become a bypass around policy enforcement.

Important rules:

- only pending requests can be approved or rejected
- approval decision must match approval_id
- approved request should still be audited
- rejected request must not execute
- API must not execute tools directly
- auth/RBAC is required before production use

## Not Included Yet

- implementation
- dashboard UI
- authentication
- role-based approval permissions
- multi-approver workflows
- production deployment
- notification system

## Recommended Implementation Phases

### Phase 1: In-Memory Queue

- ApprovalQueue class
- create/list/get/approve/reject methods
- local API endpoints
- tests

### Phase 2: SQLite Queue Storage

- persistent approval queue
- query filters
- audit references

### Phase 3: Dashboard/API Integration

- dashboard approval list
- approve/reject buttons
- audit trail view

### Phase 4: RBAC and Team Approval

- approver roles
- protected approval actions
- multi-user workflow

## Decision

Approval Queue API should be designed before implementation.

The next implementation should start with a local in-memory queue and API endpoints, not dashboard or production auth.
