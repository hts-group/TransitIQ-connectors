# Connector Readiness Gate Playbook

## Purpose

Define operator actions for per-profile readiness gate outcomes emitted from
scorecard artifacts.

## Posture Actions

1. ready
   - Release posture: profile may proceed in planned release window.
   - Required action: record clean checkpoint and keep baseline artifacts
     synchronized.
2. watch
   - Release posture: proceed with caution and heightened monitoring.
   - Required action: prioritize recommendation backlog before next release gate
     review and track delta in issue milestone updates.
3. block
   - Release posture: hold profile from release readiness claims.
   - Required action: execute highest-priority remediation recommendation,
     re-run scorecard and readiness evaluations, and post updated evidence.

## Rollback Triggers

- Any `block` outcome with removed mappings above budget.
- Repeated threshold failures for changed mappings across two consecutive
  evaluation runs.
- Malformed scorecard artifact input that prevents trustworthy gate evaluation.

## Rollback Path

- Revert to the last known-good scorecard input/budget files.
- Re-run scorecard and readiness gate generators.
- Post corrected artifact links and remediation status before reopening release
  readiness claims.

## Guardrail

- This playbook governs connector-local release posture and does not redefine
  canonical control-plane semantics.