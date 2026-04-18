# Execution Plan - Issue #9 Conformance Scorecards And Regression Budgets

Status: Active (claimed slice delivered; awaiting PM verification)
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

1. Monitor issue #9 for PM verification or follow-on directives.
2. If budget thresholds or score math require updates, keep changes additive and
   post refreshed commit-linked evidence.

## Closure Evidence

- Issue #9 milestone update:
  - https://github.com/hts-group/TransitIQ-connectors/issues/9#issuecomment-4272358045
- Owner-check completion addendum:
  - https://github.com/hts-group/TransitIQ-connectors/issues/9#issuecomment-4272360311
- Merged PR:
  - https://github.com/hts-group/TransitIQ-connectors/pull/10
- Merge commit on main:
  - https://github.com/hts-group/TransitIQ-connectors/commit/c43446dcddc041537fe2166e0fb890ab05016abf
- Validation:
  - `python -m transitiq_connectors.conformance_scorecards`
  - `python -m unittest tests.test_conformance_scorecards -v`