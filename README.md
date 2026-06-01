# Rygnal Core v0.1

**Runtime security and governance control layer for AI agent actions.**

Rygnal is a **local-first MVP** that intercepts AI-agent tool calls before execution, evaluates them against policies, assesses risk, and decides whether to **allow**, **block**, **simulate**, or **require approval** — all while maintaining a cryptographically secure audit log.

## ⚡ Quick Start

### Local Demo (30 seconds)
```bash
git clone https://github.com/Rygnal/rygnal-core.git
cd rygnal-core
python -m pip install -r requirements-dev.txt
python -m demo.run_demo
```

### Docker Demo (60 seconds)
```bash
docker compose build
docker compose run --rm rygnal python -m demo.run_demo
```

## What Rygnal Core Is

✅ **Local-first MVP** - Designed for development and testing, not yet production enterprise.

✅ **Tool-call interception** - Sits between AI agents and their tool requests to intercept, evaluate, and control execution.

✅ **Policy-driven decisions** - Uses YAML-based policy rules to decide ALLOW / BLOCK / SIMULATE / REQUIRE_APPROVAL.

✅ **Risk assessment** - Evaluates tool requests for inherent risk (tool type, target, inputs).

✅ **Audit logging** - Records every decision with full context (request, policy matched, risk score, decision, outcome).

✅ **Multiple runtime modes** - OBSERVE (log only), SIMULATE (test policies), ENFORCE (block decisions).

✅ **Demo scenarios** - Includes 5 real-world scenarios showing Rygnal catching risky actions.

## What Rygnal Core Is NOT

❌ **Not production enterprise software** — This is v0.1, a scoped MVP. Not all enterprise features are included.

❌ **Not SaaS** — This is local-first. No cloud deployment, multi-tenant workspaces, billing, or SSO.

❌ **Not connected to real AI agents yet** — v0.1 uses controlled scenario runners. Real LLM integration comes in v1+.

❌ **Not a real approval UI/API** — The approval workflow is basic and deterministic. Full UI/API workflow planned for v1+.

❌ **Not enterprise-ready policies** — v0.1 uses simple YAML rules. OPA/Rego support planned for v1+.

❌ **Not with real cloud integrations** — Tool adapters are sandbox-oriented. Real AWS/GCP/API integrations planned for v1+.

## Core Flow

```
Tool Request
    ↓
[Rygnal Interceptor]
    ├─ Risk Assessment
    ├─ Policy Matching
    ├─ Approval Check (if needed)
    └─ Audit Logging
    ↓
Decision: ALLOW / BLOCK / SIMULATE / REQUIRE_APPROVAL
    ↓
Tool Execution or Skip
    ↓
Secure Audit Log
```

## Key Components

| Component | Purpose | Status |
|-----------|---------|--------|
| **Interceptor** | Central control point for all tool requests | ✅ v0.1 |
| **Policy Engine** | Matches requests against YAML rules | ✅ v0.1 |
| **Risk Engine** | Scores tool requests for inherent risk | ✅ v0.1 |
| **Audit Logger** | Records all decisions with cryptographic integrity | ✅ v0.1 |
| **Tool Executor** | Safely executes or skips tools based on decision | ✅ v0.1 |
| **Approval Workflow** | Routes high-risk requests for human review | ✅ v0.1 |
| **Dashboard** | Web UI for monitoring and policy management | 📋 v1+ |
| **MCP Gateway** | Model Context Protocol integration | 📋 v1+ |

## 15-Minute Understanding

1. **What problem does Rygnal solve?** AI agents can perform dangerous actions (delete files, send secrets, run shell commands). Rygnal sits in the middle and enforces safety.

2. **How does it work?** Every time an AI agent tries to call a tool, Rygnal intercepts it, evaluates the request against policies, assesses risk, logs the decision, and then either allows or blocks execution.

3. **What policies does it use?** YAML files with simple rules like `if tool_name == file_delete, then require_approval` or `if action contains "rm -rf", then block`.

4. **What's in v0.1?** A working interceptor, policy engine, risk engine, audit logger, and 5 demo scenarios that show Rygnal catching risky actions.

5. **What's missing?** Real AI agent integration, cloud deployment, multi-user support, and enterprise policy engines. That's v1+.

## Documentation

- **[Getting Started](docs/getting-started.md)** — Installation, setup, and first use
- **[Architecture](docs/architecture.md)** — System design and component details
- **[v0.1 Scope](docs/v0.1-scope.md)** — What's included and what's planned
- **[Known Limitations](docs/known-limitations.md)** — Honest assessment of v0.1 boundaries
- **[Security Model](docs/14-security-hardening.md)** — How Rygnal secures itself

## Project Status

**v0.1 (Current)** - Local MVP with core interception, policy, and audit capabilities.

**v0.1+** - Community feedback, issue resolution, performance optimization.

**v1.0 (Planned)** - Real AI agent integration, multi-user support, cloud-ready deployment.

## For More Information

See the full documentation in the [docs/](docs/) directory.
