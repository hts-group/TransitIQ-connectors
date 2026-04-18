"""Signal taxonomy mapping and guard enforcement for connector observations.

This module maps connector-boundary placeholder paths into observability and
analytics taxonomy classes. It does not define canonical control-plane
semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from .contracts import NormalizedObservation


@dataclass(frozen=True)
class TaxonomyMapping:
    """Taxonomy classification for a connector placeholder path pattern."""

    placeholder_pattern: str
    observability_class: str
    analytics_class: str
    notes: str


SIGNAL_TAXONOMY_MATRIX: Dict[str, TaxonomyMapping] = {
    "status.device_status": TaxonomyMapping(
        placeholder_pattern="status.device_status",
        observability_class="health",
        analytics_class="state_snapshot",
        notes="Runtime health/state snapshot emitted by adapter status reads.",
    ),
    "telemetry.*": TaxonomyMapping(
        placeholder_pattern="telemetry.*",
        observability_class="telemetry",
        analytics_class="timeseries",
        notes="Numeric/series signals such as brightness, lux, and temperature.",
    ),
    "command_surface.*": TaxonomyMapping(
        placeholder_pattern="command_surface.*",
        observability_class="operator_action",
        analytics_class="capability_coverage",
        notes="Observed command eligibility and control-surface capability flags.",
    ),
    "raw_vendor_payload.*": TaxonomyMapping(
        placeholder_pattern="raw_vendor_payload.*",
        observability_class="debug",
        analytics_class="diagnostic_trace",
        notes="Vendor passthrough payloads retained for diagnostics only.",
    ),
}


def _matches_pattern(path: str, pattern: str) -> bool:
    if pattern.endswith(".*"):
        prefix = pattern[:-2]
        return path.startswith(prefix + ".")
    return path == pattern


def _resolve_mapping(path: str) -> TaxonomyMapping | None:
    for pattern, mapping in SIGNAL_TAXONOMY_MATRIX.items():
        if _matches_pattern(path, pattern):
            return mapping
    return None


def iter_observation_paths(observation: NormalizedObservation) -> List[str]:
    """Return one-level flattened connector placeholder paths."""

    paths: List[str] = []
    channels = {
        "status": observation.status,
        "telemetry": observation.telemetry,
        "command_surface": observation.command_surface,
        "raw_vendor_payload": observation.raw_vendor_payload,
    }

    for channel_name, values in channels.items():
        for key in values.keys():
            paths.append(f"{channel_name}.{key}")

    paths.sort()
    return paths


def validate_supported_placeholder_paths(observation: NormalizedObservation) -> List[str]:
    """Validate placeholder paths and fail safely for unsupported patterns."""

    paths = iter_observation_paths(observation)
    unsupported = [path for path in paths if _resolve_mapping(path) is None]

    if unsupported:
        supported = ", ".join(sorted(SIGNAL_TAXONOMY_MATRIX.keys()))
        unsupported_joined = ", ".join(unsupported)
        raise ValueError(
            f"Unsupported placeholder path(s): {unsupported_joined}. "
            f"Supported patterns: {supported}."
        )

    return paths


def build_signal_taxonomy_rows(observation: NormalizedObservation) -> List[Dict[str, str]]:
    """Build taxonomy rows for each observed placeholder path."""

    rows: List[Dict[str, str]] = []
    for path in validate_supported_placeholder_paths(observation):
        mapping = _resolve_mapping(path)
        if mapping is None:
            # Defensive guard. This should not be reachable after validation.
            continue
        rows.append(
            {
                "placeholder_path": path,
                "placeholder_pattern": mapping.placeholder_pattern,
                "observability_class": mapping.observability_class,
                "analytics_class": mapping.analytics_class,
                "notes": mapping.notes,
            }
        )

    return rows


def supported_placeholder_patterns() -> Iterable[str]:
    """Return all supported placeholder patterns."""

    return SIGNAL_TAXONOMY_MATRIX.keys()
