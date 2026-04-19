# Execution Plan - Issue #70 Remote Counter Demo Slice

Status: Active (claimed slice in progress)
Owner: Connectors / Integrations agent
Last updated: 2026-04-19

## Issue Input

- Implementation issue: https://github.com/hts-group/TransitIQ-connectors/issues/70

## Scope

- Monitoring-first remote counter demo integration path.
- One concrete firmware/device path: remote-counter rp2350.
- No broadening into feature-complete support.

## PM Anchors

- Ingestion method: MQTT
- Minimum demo telemetry set:
  - connectivity/last-seen
  - counter_total
  - device identity metadata (org/site/device)
  - fault_state when available
- Canonical fields exposed in this slice:
  - org_id
  - site_id
  - device_id
  - last_seen_utc
  - online
  - counter_total
  - fault_state

## Artifacts

- `transitiq_connectors/remote_counter_demo.py`
- `transitiq_connectors/capabilities.py`
- `tests/test_remote_counter_demo_slice.py`

## Dependency-Watch Status

- No additional external package dependencies introduced.
- requirements pins unchanged.

## Blockers

Current blockers: None.

## Next Step

1. Validate tests for remote counter demo slice.
2. Merge PR.
3. Post evidence bundle in issue #70.
