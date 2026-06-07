# Local FastAPI Service

Rygnal includes an experimental local FastAPI service layer.

## Goal

Expose Rygnal policy and risk evaluation through a local HTTP API.

This helps prepare for future dashboard, approval queue, and service integrations.

## Endpoints

### GET /health

Returns service health.

### POST /v1/evaluate

Evaluates a tool request with:

- Risk Engine
- Policy Engine
- Optional AuditLogger

This endpoint does not execute tools.

## Example Request

    {
      "tool_name": "file_read",
      "action": "read_file",
      "target": ".env"
    }

## Current Behavior

The API returns:

- request
- risk_assessment
- policy_decision
- audit_event, if audit logging is enabled

## Not Included Yet

- authentication
- authorization
- approval queue API
- dashboard API
- production deployment
- rate limiting

## Status

This is a local experimental API foundation, not a production SaaS API.
