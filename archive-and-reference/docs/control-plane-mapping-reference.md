# Connector To Control-Plane Mapping Reference

## Purpose

Provide a review artifact for how connector-boundary fields are expected to map
into canonical contracts owned by TransitIQ-control-plane.

This file does not define canonical semantics. It documents integration intent
and dependencies so cross-repo alignment can be reviewed explicitly.

Related artifact:

- `docs/connector-signal-taxonomy-matrix.md` documents connector signal mapping
  into observability and analytics taxonomy classes with guard enforcement
  coverage.

## Scope And Boundaries

- Source shape is `NormalizedObservation` from
  `transitiq_connectors/contracts.py`.
- Target canonical contracts are owned by TransitIQ-control-plane.
- Any canonical field names below are placeholders until control-plane confirms
  final schemas.

## Temporary Bridge Policy

- Bridge mappings and placeholders in this document are temporary.
- Until canonical contracts are frozen and published by TransitIQ-control-plane,
  connector mappings remain draft placeholders only.
- Once frozen control-plane semantics are published, connectors consume those
  semantics as-is at the adapter boundary and replace temporary placeholders.
- If interpretation is unclear, escalate for control-plane clarification instead
  of implementing connector-local semantic drift.

## Canonical Anchor Consumption

- Canonical anchor consumed: `cp.shortLivedPermit.v1`
- Source publication:
  https://github.com/hts-group/TransitIQ-control-plane/issues/2#issuecomment-4265513104

Consumed into this repo as:

- Boundary ownership rule: control-plane owns canonical naming and permit
  semantics; connectors consume and do not redefine.
- Bridge policy reinforcement: placeholders remain draft until control-plane
  freeze outputs are available for each mapping area.
- Dependency dates adopted from control-plane publication:
  - Contract review freeze target: 2026-04-21
  - Downstream consumption start target: 2026-04-24

Latest linked-work consumption update (from control-plane issue #2):

- Readiness-gate status consumed: not-ready.
- Source updates:
  - https://github.com/hts-group/TransitIQ-control-plane/issues/2#issuecomment-4265741226
  - https://github.com/hts-group/TransitIQ-control-plane/issues/2#issuecomment-4265761038
- Bridge field placement clarifications consumed for downstream mapping:
  - `tokenHash` bridge field -> `activationConstraints.tokenProof.digest`
  - `tunnelIp` bridge field -> `activationConstraints.binding.expectedTunnelIp`
  - `publicKey` bridge field -> `activationConstraints.binding.expectedClientPublicKey`
  - bridge `sessionId` linkage context -> canonical `permitId` linkage

Latest linked-work consumption update (device contract publication):

- PM dispatch source:
  - https://github.com/hts-group/TransitIQ-control-plane/issues/2#issuecomment-4266008025
- Published control-plane contract details consumed:
  - https://github.com/hts-group/TransitIQ-control-plane/issues/2#issuecomment-4266015835
- Canonical device contract publication details now available for downstream
  bridge-retirement planning:
  - desired intent field name: canonical `desiredState` (`desiredStatus` remains
    bridge alias only)
  - connectivity projection field name: canonical `connectivityState`
  - effective publication date: 2026-04-17
  - contract freeze target: 2026-04-21
  - downstream bridge-retirement window start target: 2026-04-24

Latest linked-work consumption update (policy closure publication):

- Source update:
  - https://github.com/hts-group/TransitIQ-control-plane/issues/2#issuecomment-4266067893
- Published readiness-policy closure outputs consumed for downstream planning:
  - Replay-control strictness final output published (`bounded_retry`,
    `maxAttempts: 3`, `consumeOnSuccess: true`,
    `lockoutReasonCode: rate_limited`)
  - Activation transport/security hard profile final output published
    (`wg_tunnel_bound_v1`, `wireguard_tunnel_only`, token/source/public-key
    binding checks, `gateway_service_identity` boundary)
  - Terminal lifecycle strictness final output published (fixed terminal
    statuses, no transitions out of terminal states, convergence target window)

Latest linked-work consumption update (operational-mode and endpoint binding
publication):

- Source updates:
  - https://github.com/hts-group/TransitIQ-control-plane/issues/2#issuecomment-4266198929
  - https://github.com/hts-group/TransitIQ-control-plane/issues/2#issuecomment-4266250289
- Publication details consumed for downstream bridge-retirement planning:
  - Canonical desired field: `desired/current.operationalMode`
  - Allowed values: `active | maintenance | decommissioned`
  - Write authority: control-plane authoritative writer only
  - Operational-mode write-path APIs published:
    - `setNetworkOperationalMode`
    - `setAccessDeviceOperationalMode`
  - Permit endpoint-binding publication consumed under
    `adapterHints.endpointBinding`:
    - `endpointRef`
    - `transport=wireguard_tunnel_only`
    - `serviceAuth=gateway_service_identity`
    - optional `boundAt` / `boundBy`

Latest linked-work consumption update (permit endpoint unblock closeout):

- Source updates:
  - https://github.com/hts-group/TransitIQ-control-plane/issues/2#issuecomment-4271310118
  - https://github.com/hts-group/TransitIQ-control-plane/issues/2#issuecomment-4271376056
- Downstream confirmation reference:
  - https://github.com/hts-group/TransitIQ-vpn/issues/2#issuecomment-4271308938
- Consumed outcome:
  - vpn-app reproduced authenticated allow/issued flow against published
    endpoint details
  - temporary fixture credential rotation/removal was completed in control-plane
  - readiness line in linked control-plane thread moved to `ready` for
    control-plane implementation scope

## Current Mapping Intent (Draft)

| Connector boundary field | Intended canonical target area | Notes |
|---|---|---|
| `status.device_status` | Device runtime status aggregate | Connector should only provide observed state facts. |
| `telemetry.*` | Telemetry timeseries / metrics | Metric naming and units finalized by control-plane. |
| `command_surface.*` | Capability/command eligibility view | Control-plane decides policy, authorization, and command semantics. |
| `raw_vendor_payload` | Adapter debug/trace channel (optional) | Not for portal-facing canonical UX models. |

## Adapter-Specific Notes

### NTCIP Adapter

- Source: `NtcipAdapter.get_normalized_observation()`
- Observed channels:
  - status from NTCIP status monitor
  - telemetry includes brightness snapshot
  - command surface advertises message, control mode, brightness abilities

### Yaham Adapter

- Source: `YahamAdapter.get_normalized_observation()`
- Observed channels:
  - status from Yaham runtime reads
  - telemetry includes ambient lux and temperature
  - command surface advertises playlist and brightness abilities

### Solari Adapter

- Source: `SolariAdapter.get_normalized_observation()`
- Observed channels:
  - status from FEP status queries by discovered device IDs
  - telemetry includes discovered device count
  - command surface advertises control mode and message activation abilities

## Cross-Repo Contract Questions For Control-Plane

1. What is the canonical envelope for runtime status versus telemetry?
2. Should command capability be represented as static profile, observed runtime
   flags, or both?
3. What canonical treatment is expected for passthrough vendor payloads?
4. Which canonical unit conventions apply for brightness, temperature, and
   ambient metrics?

## Change Management

- Any update to this file that implies canonical contract changes requires
  TransitIQ-control-plane review.
- Connector changes can update source observations immediately, but canonical
  mappings must remain explicitly versioned and reviewed.

## Dependency Log

| Dependency | Status | Owner | Action |
|---|---|---|---|
| Canonical status field mapping | Pending signoff | TransitIQ-control-plane | Confirm canonical runtime status envelope and field names. |
| Canonical telemetry field mapping | Pending signoff | TransitIQ-control-plane | Confirm metric naming, units, and schema conventions. |
| Canonical command capability mapping | Pending signoff | TransitIQ-control-plane | Confirm capability representation semantics and policy interaction. |
| Frozen canonical semantics publication | Anchor published, freeze pending | TransitIQ-control-plane | Anchor `cp.shortLivedPermit.v1` is published; broader mapping freeze still pending. |
| Canonical device desired/connectivity contract publication | Published (consumed), freeze pending | TransitIQ-control-plane | `desiredState`/`connectivityState` publication consumed; connector placeholders still retire only after freeze-gated conditions are met. |
| accessSessions lifecycle field freeze | Pending | TransitIQ-control-plane | Full canonical lifecycle field set/transition model is still unresolved in control-plane addendum. |
| Bridge field placement clarification (tokenHash/tunnelIp/publicKey/session linkage) | Closed (consumed and downstream confirmed) | TransitIQ-control-plane + TransitIQ-vpn-server + TransitIQ-connectors | Field placement dependency is closed for these mappings; remaining readiness items are policy/lifecycle closures. |

## Placeholder Retirement Plan (Bridge -> Canonical)

| Placeholder item | Current status | Retirement condition | Target date | Owner |
|---|---|---|---|---|
| `status.device_status` target area | Bridge still present | Control-plane frozen status envelope published and reviewed for connector mapping | 2026-04-24 checkpoint | TransitIQ-connectors + TransitIQ-control-plane |
| `telemetry.*` target area | Bridge still present | Canonical telemetry naming/units freeze published and accepted | 2026-04-24 checkpoint | TransitIQ-connectors + TransitIQ-control-plane |
| `command_surface.*` target area | Bridge still present | Canonical command capability semantics freeze (including policy interaction boundaries) | 2026-04-24 checkpoint | TransitIQ-connectors + TransitIQ-control-plane |
| `raw_vendor_payload` handling note | Bridge still present | Control-plane confirms canonical treatment and retention boundary for passthrough debug data | 2026-04-24 checkpoint | TransitIQ-connectors + TransitIQ-control-plane |

Freeze-follow statement:

- All placeholders above remain temporary and non-canonical until their
  retirement conditions are met.

## Stage-Bounded Bridge Retirement Sequence (Containment)

| Stage | Scope | Disruption window | Rollback/compatibility path | Closure evidence |
|---|---|---|---|---|
| Stage 1: Freeze-follow bridge mode (current) | Keep placeholders active while consuming frozen control-plane semantics and readiness outputs | None expected for connector runtime behavior | Dual-read/bridge placeholders remain active; no canonical-only cutover yet | Contract tests passing; dependency ledger reflects freeze-gated state |
| Stage 2: Freeze confirmation cutover prep | Confirm canonical status/telemetry/command + accessSessions lifecycle freeze outputs and validate mapping bindings | Stage-bounded maintenance window allowed if data-shape checks require temporary mapping toggles | Preserve bridge placeholders as fallback until canonical mapping checks pass for all adapters | Validation pass across adapter contract suite and mapping guards with freeze outputs consumed |
| Stage 3: Bridge retirement execution | Remove placeholder mappings that meet retirement conditions and keep canonical-only paths | Short stage-bounded disruption allowed if adapter payload transforms require restart/reload | Rollback to prior bridge path allowed only within stage window; no persistent breakage beyond stage | Post-retirement contract tests, explicit dependency reduction report, and issue checkpoint confirming stable downstream contracts |

## Readiness Gate Tracking

- Sign-off readiness state: not-ready.
- Final architect sign-off request is deferred until all readiness-gate items are
  closed in control-plane.
- Missing control-plane detail for tokenHash/tunnelIp/publicKey bridge-field
  placement: none currently.

Published readiness-policy closure outputs consumed from linked control-plane
updates:

- Replay-control strictness output published.
- Activation transport/security hard-requirement profile output published.
- Terminal lifecycle strictness output published.

Remaining readiness-gate dependencies:

- Governance closure confirmation for published policy outputs.
- Canonical status/telemetry/command freeze confirmation for connector mapping.
- accessSessions lifecycle field/transition freeze confirmation.

## Active Dependencies (Owner + Target Date)

| Dependency item | Owner | Target date | Notes |
|---|---|---|---|
| Control-plane frozen status mapping envelope | TransitIQ-control-plane | 2026-04-21 | Needed before retiring `status.device_status` placeholder. |
| Control-plane frozen telemetry naming/units | TransitIQ-control-plane | 2026-04-21 | Needed before retiring `telemetry.*` placeholder. |
| Control-plane frozen command-capability semantics | TransitIQ-control-plane | 2026-04-21 | Needed before retiring `command_surface.*` placeholder. |
| accessSessions lifecycle field/transition freeze | TransitIQ-control-plane | 2026-04-21 | Required to complete session linkage/lifecycle semantic binding. |
| Replay-control strictness closure publication consumed | TransitIQ-control-plane + Architect | 2026-04-21 | Published in linked control-plane update; downstream governance closure confirmation still pending. |
| Activation transport/security hard profile publication consumed | TransitIQ-control-plane + Architect | 2026-04-21 | Published in linked control-plane update; downstream governance closure confirmation still pending. |
| Terminal lifecycle strictness publication consumed | TransitIQ-control-plane + Architect | 2026-04-21 | Published in linked control-plane update; downstream governance closure confirmation still pending. |
| Readiness-gate governance closure confirmation | TransitIQ-control-plane + Architect | 2026-04-21 | Required before readiness can move from not-ready to ready. |
| Freeze confirmation for published `desiredState`/`connectivityState` contracts | TransitIQ-control-plane | 2026-04-21 | Publication is consumed; final bridge-retirement actions remain freeze-gated. |
| Placeholder retirement verification checkpoint | TransitIQ-connectors | 2026-04-24 | Execute retirement only when all relevant freeze outputs are published. |

## Escalation Rule

If connector-local observations or capability declarations conflict with
control-plane semantic direction, do not implement local contract drift in this
repo. Record the mismatch as a cross-repo dependency and escalate for
control-plane signoff before changing mapping intent.

Details currently requiring cross-repo closure confirmation before bridge
retirement:

- Governance confirmation that published policy-closure outputs satisfy
  readiness-gate closure criteria.
- Unresolved canonical accessSessions lifecycle field set/transition model freeze
  confirmation.
