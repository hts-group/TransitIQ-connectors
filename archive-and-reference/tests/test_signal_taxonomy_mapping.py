"""Tests for connector signal taxonomy mapping and guard enforcement."""

from __future__ import annotations

import unittest
from typing import Any, Dict

from transitiq_connectors import NtcipAdapter, SolariAdapter, YahamAdapter
from transitiq_connectors.contracts import NormalizedObservation
from transitiq_connectors.taxonomy import (
    SIGNAL_TAXONOMY_MATRIX,
    build_signal_taxonomy_rows,
    validate_supported_placeholder_paths,
)


class _FakeNtcipConnector:
    async def connect(self) -> Dict[str, Any]:
        return {"ok": True}

    def disconnect(self) -> None:
        return None

    async def get_status(self) -> Dict[str, Any]:
        return {"health": "ok"}

    async def get_brightness(self) -> Dict[str, Any]:
        return {"level": 42}

    def get_summary(self) -> Dict[str, Any]:
        return {"device": "ntcip"}


class _FakeYahamSummary:
    def __init__(self) -> None:
        self.host = "127.0.0.1"
        self.transport = "udp"
        self.port = 5000


class _FakeYahamConnector:
    discovery = {"device": {"transport": "udp"}}

    async def connect(self) -> Dict[str, Any]:
        return {"ok": True}

    async def disconnect(self) -> None:
        return None

    async def get_status(self) -> Dict[str, Any]:
        return {"ambient_lux": 123, "temperature_c": 22.5}

    def get_summary(self) -> _FakeYahamSummary:
        return _FakeYahamSummary()


class _FakeSolariSummary:
    def __init__(self) -> None:
        self.host = "127.0.0.1"
        self.base_url = "http://127.0.0.1"
        self.device_count = 1
        self.device_type_count = 1


class _FakeSolariConnector:
    discovery = {"devices": [{"id": 101}]}

    async def connect(self) -> Dict[str, Any]:
        return {"ok": True}

    async def disconnect(self) -> None:
        return None

    async def get_status_by_device_ids(self, _device_ids) -> Dict[str, Any]:
        return {"devices": [{"id": 101, "status": "online"}]}

    def get_summary(self) -> _FakeSolariSummary:
        return _FakeSolariSummary()


class SignalTaxonomyMappingTests(unittest.IsolatedAsyncioTestCase):
    def test_matrix_contains_expected_patterns(self) -> None:
        self.assertIn("status.device_status", SIGNAL_TAXONOMY_MATRIX)
        self.assertIn("telemetry.*", SIGNAL_TAXONOMY_MATRIX)
        self.assertIn("command_surface.*", SIGNAL_TAXONOMY_MATRIX)
        self.assertIn("raw_vendor_payload.*", SIGNAL_TAXONOMY_MATRIX)

    async def test_adapters_map_to_supported_taxonomy_rows(self) -> None:
        adapters = [
            self._build_ntcip_adapter(),
            self._build_yaham_adapter(),
            self._build_solari_adapter(),
        ]

        for adapter in adapters:
            observation = await adapter.get_normalized_observation()
            paths = validate_supported_placeholder_paths(observation)
            rows = build_signal_taxonomy_rows(observation)

            self.assertTrue(paths)
            self.assertEqual(len(paths), len(rows))

            for row in rows:
                self.assertIn(row["observability_class"], {"health", "telemetry", "operator_action", "debug"})
                self.assertIn(
                    row["analytics_class"],
                    {"state_snapshot", "timeseries", "capability_coverage", "diagnostic_trace"},
                )

    def test_guard_rejects_unsupported_placeholder_paths(self) -> None:
        observation = NormalizedObservation(
            status={"unexpected_status_shape": {"value": "bad"}},
            telemetry={},
            command_surface={},
            raw_vendor_payload={},
        )

        with self.assertRaisesRegex(ValueError, "status.unexpected_status_shape"):
            validate_supported_placeholder_paths(observation)

    def _build_ntcip_adapter(self) -> NtcipAdapter:
        adapter = NtcipAdapter("127.0.0.1")
        adapter._connector = _FakeNtcipConnector()
        return adapter

    def _build_yaham_adapter(self) -> YahamAdapter:
        adapter = YahamAdapter("127.0.0.1")
        adapter._connector = _FakeYahamConnector()
        return adapter

    def _build_solari_adapter(self) -> SolariAdapter:
        adapter = SolariAdapter("127.0.0.1")
        adapter._connector = _FakeSolariConnector()
        return adapter


if __name__ == "__main__":
    unittest.main()
