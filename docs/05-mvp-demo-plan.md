# MVP Demo Plan

## Status

Historical archive note. This early demo planning document is retained for context and is not a canonical product guide.

Use `docs/getting-started.md` and `docs/release-readiness-v0.1.md` for current runnable validation and demo expectations.

## Demo Goal

AI agent tries risky action -> Rygnal intercepts -> policy checks -> action blocked/allowed -> audit log created.

## First Demo Scenarios

1. Agent tries to read .env
2. Agent tries to delete important file
3. Agent tries to run dangerous shell command
4. Agent tries to send secret to external API
5. Agent tries to read safe file
