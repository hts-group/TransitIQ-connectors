"""TransitIQ connector adapter framework.

This package provides an internal adapter boundary for vendor-specific connectors.
It intentionally does not define canonical control-plane contracts.
"""

from .adapters import NtcipAdapter, SolariAdapter, YahamAdapter
from .capabilities import (
    AuthMode,
    AuthProfile,
    NTCIP_CAPABILITIES,
    SOLARI_CAPABILITIES,
    YAHAM_CAPABILITIES,
    Capability,
    CapabilityProfile,
)
from .contracts import AdapterDescriptor, ConnectorAdapter, NormalizedObservation
from .taxonomy import (
    SIGNAL_TAXONOMY_MATRIX,
    TaxonomyMapping,
    build_signal_taxonomy_rows,
    supported_placeholder_patterns,
    validate_supported_placeholder_paths,
)

__all__ = [
    "AdapterDescriptor",
    "AuthMode",
    "AuthProfile",
    "Capability",
    "CapabilityProfile",
    "ConnectorAdapter",
    "NTCIP_CAPABILITIES",
    "NtcipAdapter",
    "NormalizedObservation",
    "SOLARI_CAPABILITIES",
    "SolariAdapter",
    "SIGNAL_TAXONOMY_MATRIX",
    "TaxonomyMapping",
    "YAHAM_CAPABILITIES",
    "YahamAdapter",
    "build_signal_taxonomy_rows",
    "supported_placeholder_patterns",
    "validate_supported_placeholder_paths",
]
