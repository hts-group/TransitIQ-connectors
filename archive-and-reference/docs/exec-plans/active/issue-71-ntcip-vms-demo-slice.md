# Execution Plan - Issue #71 NTCIP VMS Demo Slice

Status: Active (claimed slice in progress)
Owner: Connectors / Integrations agent
Last updated: 2026-04-19

## Issue Input

- Implementation issue: https://github.com/hts-group/TransitIQ-connectors/issues/71

## Scope

- Minimum viable NTCIP VMS demo connector path for one sign.
- Monitoring/visibility baseline only.
- One demo-safe operation: read-only status visibility.

## PM Anchors

- Capability target: status + current message visibility
- Transport assumptions:
  - SNMP transport
  - direct IP or routed LAN access path
  - UDP/161
  - no VPN app/server/broker dependency on first path
- Org/site/device binding exposed for one VMS sign
- Failure handling explicitly diagnosable

## Artifacts

- `transitiq_connectors/ntcip_vms_demo.py`
- `tests/test_ntcip_vms_demo_slice.py`

## Dependency-Watch Status

- No additional external package dependencies introduced.
- requirements pins unchanged.

## Blockers

Current blockers: None.

## Next Step

1. Run demo-slice and contract validation tests.
2. Merge PR.
3. Post evidence bundle in issue #71.
