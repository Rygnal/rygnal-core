# Known Limitations - Rygnal Core v0.1

This document honestly describes what Rygnal Core v0.1 does **not** do and the boundaries of the MVP.

## MVP Context

Rygnal Core v0.1 is a **scoped, local-first MVP** designed to:
- Prove the core interception and policy model works
- Provide a foundation for community feedback
- Demonstrate the value proposition before building enterprise features

This is intentionally not:
- A production-ready enterprise product
- A SaaS platform
- A finished AI integration
- A policy engine for all use cases

## Current Limitations

### 1. AI Agent Integration

**Limitation:** No real AI agent integration yet.

**Details:**
- v0.1 uses controlled demo scenarios, not actual LLM agents
- Scenarios are pre-scripted and deterministic
- No integration with LangChain, AutoGen, or other agent frameworks
- No OpenAI API integration

**Workaround:** Manually construct `ToolRequest` objects and pass them to the interceptor.

**Planned for v1+:** Real integration with popular agent frameworks.

---

### 2. Policy Engine

**Limitation:** Simple YAML-based policies only. No advanced policy languages.

**Details:**
- Policies are declarative YAML rules with simple string matching
- Only supports exact matches and substring contains checks
- No regex patterns
- No boolean logic (AND/OR/NOT)
- No contextual or conditional rules
- No policy versioning or rollback
- No hot-reload (policies loaded at startup)
- No conflict detection for overlapping rules

**Example of what you CAN'T do in v0.1:**
```yaml
# NO: Complex boolean logic
- id: example-not-supported
  condition: "(tool_name == 'shell_command' AND NOT is_admin) OR (tool_name == 'file_read' AND environment == 'production')"
  decision: require_approval
```

**Example of what you CAN do in v0.1:**
```yaml
# YES: Simple substring matching
- id: block-env-read
  tool_name: file_read
  target_contains: ".env"
  decision: block
```

**Workaround:** Create multiple simple rules, accept that policies are flat and linear.

**Planned for v1+:**
- OPA/Rego for enterprise policy logic
- Regex pattern matching
- Policy versioning and hot-reload
- Conflict detection and resolution

---

### 3. Risk Scoring

**Limitation:** Deterministic, rule-based risk scoring. No machine learning or heuristics.

**Details:**
- Risk scores are calculated from fixed rules (tool type, action, target, input patterns)
- No machine learning or statistical analysis
- No learning from historical decisions
- No anomaly detection
- No behavioral analysis
- No integration with threat intelligence feeds

**Workaround:** Adjust risk scoring logic in `risk_engine.py` for your specific use case.

**Planned for v1+:** ML-based risk scoring with historical analysis.

---

### 4. Approval Workflow

**Limitation:** Basic, deterministic approval workflow. No real UI or notifications.

**Details:**
- Current implementation auto-approves all approval requests
- No web UI for approval dashboard
- No email notifications
- No Slack/Teams notifications
- No API for programmatic approvals
- No approval deadlines or auto-denial
- No role-based approval chains
- No approval history or audit trail beyond main audit log

**Workaround:** Implement a custom `ApprovalWorkflow` class for your needs.

**Planned for v1+:**
- Web dashboard
- Email/Slack notifications
- Approval deadlines
- Role-based chains
- Programmatic API

---

### 5. Tool Execution

**Limitation:** Tool adapters are sandbox-oriented and local-only.

**Details:**
- No support for cloud tool execution
- External API adapter is dry-run only (doesn't actually send data)
- Shell command adapter runs locally with potential security risks
- No built-in sandboxing or containerization
- No integration with AWS/GCP/Azure APIs
- No support for remote tool execution

**Current Tool Types:**
- `file_read` - Read local files
- `file_write` - Write local files
- `file_delete` - Delete local files
- `shell_command` - Run local shell commands (with risk)
- `external_api_send` - Simulated (doesn't actually send)

**Workaround:** Implement custom tool adapters for your cloud APIs.

**Planned for v1+:**
- Real AWS/GCP/Azure integrations
- Sandboxed tool execution
- Remote execution support

---

### 6. Audit Logging

**Limitation:** File-based audit logs, single-node only.

**Details:**
- Audit logs are written to local files (JSON lines format)
- No real-time log aggregation
- No distributed logging
- No database backend
- No log rotation or archival
- No retention policies
- No real-time alerting on policy violations

**Workaround:** Implement custom audit logger that writes to your chosen backend.

**Planned for v1+:**
- Database backends (PostgreSQL, MongoDB, etc.)
- Cloud logging (CloudWatch, Stackdriver, Datadog, etc.)
- Log aggregation
- Retention policies
- Real-time alerting

---

### 7. Authentication & Multi-user

**Limitation:** No authentication, no multi-user support.

**Details:**
- No user identity in requests
- No role-based access control (RBAC)
- No team/organization support
- No audit trail of who approved what
- Single-user/single-tenant only
- No API keys or tokens
- No integration with directory services (LDAP, Azure AD, Okta)

**Workaround:** Add user context to ToolRequest objects manually if needed.

**Planned for v1+:** Full multi-user, multi-tenant support with RBAC and directory integration.

---

### 8. Deployment

**Limitation:** Local/Docker only. No cloud deployment.

**Details:**
- No Kubernetes manifests
- No Helm charts
- No cloud-native deployment guides
- No multi-region support
- No high availability setup
- No load balancing
- Not suitable for production scale

**Current Deployment Options:**
- Local Python execution
- Docker (single container)
- Docker Compose (for local multi-container testing)

**Workaround:** Deploy locally for development and testing.

**Planned for v1+:** Kubernetes, managed cloud services, multi-region deployment.

---

### 9. Monitoring & Observability

**Limitation:** Basic logging only. No real monitoring.

**Details:**
- No metrics collection
- No performance monitoring
- No real-time dashboards
- No alerting system
- No distributed tracing
- No integration with monitoring platforms (Prometheus, New Relic, Datadog, etc.)

**Workaround:** Parse audit logs and implement custom monitoring.

**Planned for v1+:** Full observability with metrics, dashboards, and alerting.

---

### 10. Development & Testing

**Limitation:** Limited tooling for policy development and testing.

**Details:**
- No policy linter or validator
- No policy testing framework
- No policy dry-run tool
- No policy simulation UI
- No policy coverage analysis
- No policy debugging tools

**Workaround:** Write Python scripts to test policies manually.

**Planned for v1+:** Full policy development toolkit with testing and debugging.

---

### 11. Performance & Scalability

**Limitation:** No optimization for high-scale deployments.

**Details:**
- Policy evaluation is O(n) where n = number of rules
- No caching of policy matches
- No async/parallel processing
- Risk assessment has no optimization
- Audit logging is sequential (no batch writes)
- No connection pooling or resource optimization

**Typical Performance:**
- Policy matching: < 1ms for < 100 rules
- Risk assessment: < 1ms
- Audit logging: < 5ms (file I/O dependent)

**Not suitable for:**
- Millions of requests per second
- Distributed deployments with hundreds of nodes
- Real-time low-latency systems

**Workaround:** Optimize locally or implement caching layer.

**Planned for v1+:** Performance optimization, distributed caching, async processing.

---

### 12. Security Hardening

**Limitation:** v0.1 focuses on logic security, not operational hardening.

**Details:**
- No encryption at rest (audit logs stored as plaintext JSON)
- No encryption in transit (no TLS for local use)
- No secrets management
- No rate limiting or DDoS protection
- No intrusion detection
- Audit logs are not encrypted by default (though they are signed)
- No support for Hardware Security Modules (HSM)

**Workaround:** For production use, add encryption, TLS, and secrets management yourself.

**Planned for v1+:** Full security hardening including encryption, secrets management, and intrusion detection.

---

### 13. Documentation

**Limitation:** v0.1 documentation is foundational, not exhaustive.

**Details:**
- Getting started guide is basic
- No advanced cookbook or examples
- No API reference documentation
- No troubleshooting guide
- No integration guides for common tools
- No policy template library
- No FAQ

**Planned for v1+:** Comprehensive documentation and guides.

---

### 14. License & Support

**Limitation:** Community-driven open source.

**Details:**
- No commercial support
- No SLA or uptime guarantees
- No dedicated support team
- Community-driven issue resolution
- Contributions are welcome but not guaranteed to be merged

**Planned for v1+:** Commercial support options.

---

## What Works Well in v0.1

Despite these limitations, v0.1 demonstrates core value:

✅ **Core interception model** - The fundamental architecture of intercepting, evaluating, and deciding on tool requests works well.

✅ **Policy engine** - Simple YAML policies are easy to understand and modify.

✅ **Risk assessment** - Deterministic risk scoring is predictable and debuggable.

✅ **Audit logging** - Clear, auditable records of every decision.

✅ **Demo scenarios** - Effective at showing the value proposition.

✅ **Local development** - Easy to set up and experiment with.

✅ **Extensibility** - Architecture supports adding custom components.

---

## Feedback & Roadmap

This honest assessment of limitations helps us:
1. Set appropriate expectations for v0.1
2. Prioritize v1+ features based on user feedback
3. Build a roadmap that addresses real needs
4. Make conscious trade-offs between features and scope

**Have feedback?** Open an issue or discussion on GitHub.

**Want to contribute?** See CONTRIBUTING.md (planned for v1+).
