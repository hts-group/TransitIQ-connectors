# Execution Plan - Issue #9 Conformance Scorecards And Regression Budgets

Status: Active (claimed slice in progress)
Owner: Connectors / Integrations agent
Last updated: 2026-04-18

## Issue Input

- Implementation issue: https://github.com/hts-group/TransitIQ-connectors/issues/9

## Claimed Slice

- Generate per-profile conformance scorecards (coverage, mapping consistency,
  validation pass-rate).
- Add configurable regression budget thresholds for changed/removed mappings
  with explicit fail triggers.
- Emit machine-readable scorecard artifact for CI and release readiness checks.
- Add tests for scorecard math, threshold evaluation, and malformed input.

## Artifacts

- `docs/connector-conformance-input.json`
- `docs/connector-conformance-regression-budget.json`
- `transitiq_connectors/conformance_scorecards.py`
- `tests/test_conformance_scorecards.py`

## Blockers

Current blockers: None.

## Next Step

1. Run scorecard generator and tests.
2. Post issue #9 milestone with commit-linked evidence and validation output.