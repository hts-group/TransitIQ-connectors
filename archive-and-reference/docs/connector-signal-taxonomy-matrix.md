# Connector Signal Taxonomy Matrix

## Purpose

Define a connector-local mapping matrix from adapter output placeholder paths to
observability and analytics taxonomy classes for parallel programme workstreams.

This document is connector-boundary planning guidance only. It does not define
canonical control-plane semantics.

## Matrix

| Placeholder path pattern | Observability class | Analytics class | Intended use |
|---|---|---|---|
| `status.device_status` | `health` | `state_snapshot` | Runtime state/health snapshots from adapter status reads. |
| `telemetry.*` | `telemetry` | `timeseries` | Numeric signal streams (for example brightness/lux/temperature). |
| `command_surface.*` | `operator_action` | `capability_coverage` | Control eligibility and command-surface feature visibility. |
| `raw_vendor_payload.*` | `debug` | `diagnostic_trace` | Vendor payload passthrough for diagnostics only. |

## Guard Enforcement

- Guard implementation: `transitiq_connectors/taxonomy.py`
- Guard rule: unsupported placeholder paths fail safely with a `ValueError`.
- Supported patterns are limited to the matrix rows above.

## Stage-Bounded Disruption And Compatibility

- Current stage scope: documentation/mapping guard increment only.
- Expected disruption window: none for runtime behavior in this stage.
- Compatibility path: bridge placeholders remain active until freeze-gated
  retirement conditions are met.
- Rollback path: if a future cutover stage fails mapping validation, revert to
  bridge placeholder path within that same stage window.

## Closure Evidence For This Slice

- Mapping matrix artifact published in this document.
- Guard behavior enforced in `transitiq_connectors/taxonomy.py`.
- Coverage tests in `tests/test_signal_taxonomy_mapping.py`.
