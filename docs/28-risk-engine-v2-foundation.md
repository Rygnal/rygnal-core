# Risk Engine v2 Foundation

Risk Engine v2 foundation adds a cleaner structure for contextual and explainable risk scoring.

## What Changed

- Added RiskContext
- Added RiskSignalCategory
- Added RiskScoringProfile
- Added RiskSignalRegistry
- Added detector-based signal architecture
- Added confidence and explanation fields to RiskAssessment
- Kept existing RiskAssessment behavior backward compatible

## Core Design

Risk Engine v2 is built around deterministic signal detectors.

The engine flow is:

1. Convert ToolRequest into RiskContext
2. Run registered RiskSignal detectors
3. Collect explainable signals
4. Calculate deterministic score
5. Map score to RiskLevel
6. Return RiskAssessment with reasons, signals, confidence, and explanation

## Current Detectors

- ToolCapabilityDetector
- TargetSensitivityDetector
- InputSensitivityDetector
- EnvironmentDetector

## Compatibility

This foundation keeps existing Risk Engine behavior working.

Existing fields still exist:

- risk_score
- risk_level
- reasons
- signals

New fields are additive:

- confidence
- explanation
- signal category
- signal evidence
- signal reversibility

## Not Included Yet

- Chain-risk detection
- Policy-risk bridge
- Rust implementation
- LLM-based risk judgment
- Runtime behavior changes

## Next Steps

- Add more signal detectors
- Add policy-risk bridge
- Add risk scenario fixtures
- Add chain-risk detection later
