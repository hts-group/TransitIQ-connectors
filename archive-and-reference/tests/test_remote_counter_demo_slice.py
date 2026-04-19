"""Issue #70 demo-slice tests for remote counter ingestion path."""

from __future__ import annotations

import unittest

from transitiq_connectors.remote_counter_demo import (
    FIRMWARE_TRACK,
    INGESTION_METHOD,
    RemoteCounterBinding,
    RemoteCounterDemoAdapter,
)


class RemoteCounterDemoSliceTests(unittest.IsolatedAsyncioTestCase):
    async def test_mqtt_ingestion_normalizes_demo_fields(self) -> None:
        adapter = RemoteCounterDemoAdapter(
            RemoteCounterBinding(org_id="org-a", site_id="site-1", device_id="counter-01")
        )

        connection = await adapter.connect()
        adapter.ingest_mqtt_payload(
            topic="demo/counter/01",
            payload={
                "counter_total": 128,
                "online": True,
                "fault_state": "ok",
                "metadata": {"firmware": "rp2350"},
            },
            received_at_utc="2026-04-19T04:20:00Z",
        )
        normalized = await adapter.get_normalized_observation()

        self.assertEqual(INGESTION_METHOD, connection["ingestion_method"])
        self.assertEqual(FIRMWARE_TRACK, connection["firmware_track"])
        self.assertEqual("counter-01", normalized.status["device_identity"]["device_id"])
        self.assertTrue(normalized.status["connectivity"]["online"])
        self.assertEqual("2026-04-19T04:20:00Z", normalized.status["connectivity"]["last_seen_utc"])
        self.assertEqual(128, normalized.telemetry["counter_total"])
        self.assertEqual("ok", normalized.status["fault_state"])

    async def test_diagnostics_expose_parsing_failure(self) -> None:
        adapter = RemoteCounterDemoAdapter(
            RemoteCounterBinding(org_id="org-a", site_id="site-1", device_id="counter-01")
        )

        await adapter.connect()
        adapter.ingest_mqtt_payload(
            topic="demo/counter/01",
            payload={
                "online": True,
                "fault_state": "ok",
            },
            received_at_utc="2026-04-19T04:21:00Z",
        )

        diagnostics = adapter.diagnostics_snapshot()
        self.assertEqual(
            "payload_parse_error",
            diagnostics["auth_connectivity_parsing"]["last_error"]["code"],
        )
        self.assertIn(
            "counter_total",
            diagnostics["auth_connectivity_parsing"]["last_error"]["message"],
        )

    async def test_canonical_demo_fields_are_exposed(self) -> None:
        adapter = RemoteCounterDemoAdapter(
            RemoteCounterBinding(org_id="org-a", site_id="site-1", device_id="counter-01")
        )

        await adapter.connect()
        adapter.ingest_mqtt_payload(
            topic="demo/counter/01",
            payload={"counter_total": 17, "online": False, "fault_state": "sensor_fault"},
            received_at_utc="2026-04-19T04:22:00Z",
        )

        fields = adapter.canonical_demo_fields()
        self.assertEqual("org-a", fields["org_id"])
        self.assertEqual("site-1", fields["site_id"])
        self.assertEqual("counter-01", fields["device_id"])
        self.assertEqual("2026-04-19T04:22:00Z", fields["last_seen_utc"])
        self.assertEqual("false", fields["online"])
        self.assertEqual("17", fields["counter_total"])
        self.assertEqual("sensor_fault", fields["fault_state"])


if __name__ == "__main__":
    unittest.main()
