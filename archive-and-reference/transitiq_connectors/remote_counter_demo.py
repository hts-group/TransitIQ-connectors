"""Remote counter demo adapter path for issue #70.

This module intentionally keeps scope minimal and monitoring-first.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict

from .capabilities import REMOTE_COUNTER_DEMO_CAPABILITIES, CapabilityProfile
from .contracts import AdapterDescriptor, NormalizedObservation

INGESTION_METHOD = "mqtt"
FIRMWARE_TRACK = "remote-counter/rp2350"


@dataclass(frozen=True)
class RemoteCounterBinding:
    """Stable org/site/device binding for a demo remote counter."""

    org_id: str
    site_id: str
    device_id: str


class RemoteCounterDemoAdapter:
    """Monitoring-only demo adapter for a single remote counter device."""

    def __init__(self, binding: RemoteCounterBinding) -> None:
        self._binding = binding
        self._connected = False
        self._last_received_at_utc: str | None = None
        self._last_payload: Dict[str, Any] = {}
        self._last_error: Dict[str, str] = {"code": "", "message": ""}

    async def connect(self) -> Dict[str, Any]:
        self._connected = True
        return {
            "ingestion_method": INGESTION_METHOD,
            "firmware_track": FIRMWARE_TRACK,
            "binding": self._binding_dict(),
        }

    async def disconnect(self) -> None:
        self._connected = False

    def ingest_mqtt_payload(
        self,
        topic: str,
        payload: Dict[str, Any],
        received_at_utc: str | None = None,
    ) -> None:
        """Accept one firmware MQTT payload and keep latest snapshot."""

        if not isinstance(payload, dict):
            self._set_error("payload_parse_error", "Payload is not a dictionary.")
            return

        counter_value = payload.get("counter_total")
        if not isinstance(counter_value, int):
            self._set_error("payload_parse_error", "counter_total is required and must be int.")
            return

        online = payload.get("online")
        if not isinstance(online, bool):
            self._set_error("payload_parse_error", "online is required and must be bool.")
            return

        timestamp = received_at_utc or datetime.now(timezone.utc).isoformat()
        self._last_received_at_utc = timestamp
        self._last_payload = {
            "topic": topic,
            "counter_total": counter_value,
            "online": online,
            "fault_state": payload.get("fault_state", "unknown"),
            "metadata": payload.get("metadata", {}),
        }
        self._last_error = {"code": "", "message": ""}

    async def get_observed_state(self) -> Dict[str, Any]:
        return {
            "binding": self._binding_dict(),
            "connectivity": {
                "connected": self._connected,
                "last_seen_utc": self._last_received_at_utc,
                "online": self._last_payload.get("online", False),
            },
            "counter": {
                "counter_total": self._last_payload.get("counter_total", 0),
            },
            "health": {
                "fault_state": self._last_payload.get("fault_state", "unknown"),
            },
        }

    async def get_normalized_observation(self) -> NormalizedObservation:
        observed = await self.get_observed_state()
        return NormalizedObservation(
            status={
                "device_identity": observed["binding"],
                "connectivity": observed["connectivity"],
                "fault_state": observed["health"]["fault_state"],
            },
            telemetry={
                "counter_total": observed["counter"]["counter_total"],
            },
            command_surface={
                "monitoring_only": True,
                "control_supported": False,
            },
            raw_vendor_payload={
                "firmware_track": FIRMWARE_TRACK,
                "last_payload": self._last_payload,
                "diagnostics": self.diagnostics_snapshot(),
            },
        )

    def get_descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            adapter_id="remote_counter_demo_rp2350",
            vendor="remote_counter",
            protocol="mqtt",
            product_family="people_counter",
            connector_version="1.0.0",
        )

    def get_capabilities(self) -> CapabilityProfile:
        return REMOTE_COUNTER_DEMO_CAPABILITIES

    def diagnostics_snapshot(self) -> Dict[str, Any]:
        return {
            "auth_connectivity_parsing": {
                "last_error": self._last_error,
                "connected": self._connected,
                "last_topic": self._last_payload.get("topic", ""),
            }
        }

    def canonical_demo_fields(self) -> Dict[str, str]:
        return {
            "org_id": self._binding.org_id,
            "site_id": self._binding.site_id,
            "device_id": self._binding.device_id,
            "last_seen_utc": self._last_received_at_utc or "",
            "online": str(self._last_payload.get("online", False)).lower(),
            "counter_total": str(self._last_payload.get("counter_total", 0)),
            "fault_state": str(self._last_payload.get("fault_state", "unknown")),
        }

    def _set_error(self, code: str, message: str) -> None:
        self._last_error = {"code": code, "message": message}

    def _binding_dict(self) -> Dict[str, str]:
        return {
            "org_id": self._binding.org_id,
            "site_id": self._binding.site_id,
            "device_id": self._binding.device_id,
        }
