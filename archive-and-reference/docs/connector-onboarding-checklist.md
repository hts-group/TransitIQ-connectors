# Connector Onboarding Checklist

## Purpose

Provide additive onboarding checks so new connector profiles stay aligned with
capability declarations and signal-class compatibility expectations.

## Issue #5 Fixture-Derived Checklist Deltas

1. Run compatibility fixture validation before publishing onboarding guidance.
   - Command:
     - `python -m transitiq_connectors.compatibility_fixtures`
2. Verify per-profile validation summary has zero failed rows.
   - Required profiles in summary:
     - `ntcip`
     - `yaham`
     - `solari`
3. Confirm invalid fixture combinations remain explicitly invalid.
   - Unsupported capability and unsupported signal-class combinations must not
     be silently accepted.
4. For any new adapter profile, add at least one valid and one invalid fixture
   case before claiming compatibility readiness.
5. Post commit-linked fixture/test evidence in implementation issue updates.

## Compatibility Guardrail

- These checks are additive and connector-local.
- They do not alter canonical control-plane semantics or freeze-follow
  dependency ownership boundaries.