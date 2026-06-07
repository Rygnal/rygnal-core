# Optional Live OpenAI Demo

## Goal

Add an optional live OpenAI demo that routes OpenAI-style tool calls through Rygnal.

This demo is optional and must not be required for CI.

## Current Behavior

Rygnal already supports OpenAI-style tool-call payloads through the local adapter.

The optional live demo adds a real OpenAI client path when `OPENAI_API_KEY` is available.

## Safety Rules

- CI must not require a live OpenAI API call
- Demo must skip cleanly when `OPENAI_API_KEY` is missing
- Tool calls must still pass through Rygnal
- Audit logs must still be generated
- The demo must not bypass policy, risk, or audit layers

## How To Run

Install the optional dependency:

    pip install -e ".[live-openai]"

Set an API key:

    export OPENAI_API_KEY="..."

Run:

    python -m examples.live_openai_demo

Optional model override:

    export OPENAI_MODEL="gpt-4.1-mini"

## What This Proves

The demo proves that a live OpenAI-style tool-calling workflow can be protected by Rygnal.

## Not Included Yet

- CI live API calls
- production OpenAI integration
- streaming tool calls
- multi-tool execution loop
- hosted service integration
