# Connector Readiness Gate Playbook

## Purpose

Define operator actions for per-profile readiness gate outcomes emitted from
scorecard artifacts.

This playbook now includes release-candidate aggregation outputs that combine
all profile postures into a single go/watch/hold disposition.

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

## Release-Candidate Aggregation

Input artifact:

- `docs/connector-readiness-gates.latest.json`

Output artifact:

- `docs/connector-release-candidate-gates.latest.json`

Disposition rollup rule:

1. `block` if any profile is `block`.
2. `watch` if no profile is `block` and at least one profile is `watch`.
3. `ready` only when all profiles are `ready`.

Prioritized blocker list rule:

- Blockers are emitted from non-ready profile recommendations and sorted by:
  `priority`, then posture severity (`block` before `watch`), then profile,
  category, and action for deterministic tie-breaking.

Operator response:

1. `ready`: proceed with release candidate checkpoint.
2. `watch`: proceed only with explicit tracking of prioritized blocker burn-down.
3. `block`: hold release candidate checkpoint until priority-1 blockers are
   remediated and gate output is re-generated.

## Closure Dependency Diagnostics

Input artifacts:

- `docs/connector-closure-dependencies.input.json`
- `docs/connector-release-candidate-gates.latest.json`

Output artifact:

- `docs/connector-closure-remediation.latest.json`

Diagnostic posture rule:

1. `block` if release-candidate disposition is `block`.
2. `block` if any open dependency is overdue.
3. `watch` when open dependencies remain but none are overdue.
4. `ready` only when all closure dependencies are consumed or closed.

Remediation ordering rule:

- Remediation is sorted by priority with deterministic ties: overdue first,
  canonical-contract dependencies before non-canonical dependencies, then due
  date and dependency name.

Operator response:

1. `ready`: maintain dependency-watch checkpoint cadence.
2. `watch`: execute highest-priority remediation items before next checkpoint.
3. `block`: escalate overdue dependency owners and post escalation evidence in
  issue #2 before requesting closure.