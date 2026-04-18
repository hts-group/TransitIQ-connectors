# Connector Profile Drift Response Playbook

## Purpose

Define additive operator actions when adapter profile drift checks report
changes against baseline snapshots.

## Drift Outcome Classes

1. No drift
   - Criteria: no added/removed capabilities and no changed class mappings.
   - Action: record clean checkpoint in issue update and continue planned work.
2. Expected drift
   - Criteria: drift is present and directly tied to an approved connector
     implementation slice.
   - Action: update baseline snapshot in the same change set, include rationale,
     and post commit-linked evidence.
3. Unexpected drift
   - Criteria: drift is present without approved scope context.
   - Action:
     - hold release-facing connector profile claims for the affected adapter
     - open follow-up implementation issue with impacted profile list
     - request architect/control-plane review if mapping semantics are affected
4. Malformed baseline
   - Criteria: baseline load/validation fails.
   - Action:
     - treat as tooling/configuration failure
     - repair baseline structure before interpreting drift outcomes
     - rerun drift utility and post corrected evidence

## Required Evidence In Milestone Updates

- Drift summary output by adapter profile (added/removed/changed counts).
- Test evidence for no-drift/expected-drift/malformed-baseline behavior.
- Compatibility statement: additive only, no persistent runtime breakage.

## Guardrail

- Connectors can detect and report drift; canonical semantic ownership remains in
  control-plane threads.