"""Adapter wrappers that isolate vendor-specific connector complexity."""

from __future__ import annotations

from typing import Any, Dict

from transitiq_ntcip import NtcipConnector
from transitiq_solari import SolariConnector
from transitiq_yaham import YahamConnector

from .capabilities import (
    NTCIP_CAPABILITIES,
    REMOTE_COUNTER_DEMO_CAPABILITIES,
    SOLARI_CAPABILITIES,
    YAHAM_CAPABILITIES,
    CapabilityProfile,
)
from .contracts import AdapterDescriptor, NormalizedObservation
from .remote_counter_demo import FIRMWARE_TRACK, INGESTION_METHOD, RemoteCounterBinding, RemoteCounterDemoAdapter


class NtcipAdapter:
    def __init__(self, host: str, **connector_kwargs: Any) -> None:
        self._connector = NtcipConnector(host, **connector_kwargs)

    async def connect(self) -> Dict[str, Any]:
        return await self._connector.connect()

    async def disconnect(self) -> None:
        self._connector.disconnect()

    async def get_observed_state(self) -> Dict[str, Any]:
        return {
            "summary": self._connector.get_summary(),
            "status": await self._connector.get_status(),
            "brightness": await self._connector.get_brightness(),
        }

    async def get_normalized_observation(self) -> NormalizedObservation:
        status = await self._connector.get_status()
        brightness = await self._connector.get_brightness()
        return NormalizedObservation(
            status={"device_status": status},
            telemetry={"brightness": brightness},
            command_surface={
                "supports_message_post": True,
                "supports_control_mode": True,
                "supports_brightness_control": True,
            },
            raw_vendor_payload={"summary": self._connector.get_summary()},
        )

    def get_descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            adapter_id="ntcip_dms",
            vendor="ntcip",
            protocol="NTCIP 1203",
            product_family="dms_vms",
            connector_version="1.0.0",
        )

    def get_capabilities(self) -> CapabilityProfile:
        return NTCIP_CAPABILITIES


class YahamAdapter:
    def __init__(self, host: str, **connector_kwargs: Any) -> None:
        self._connector = YahamConnector(host, **connector_kwargs)

    async def connect(self) -> Dict[str, Any]:
        return await self._connector.connect()

    async def disconnect(self) -> None:
        await self._connector.disconnect()

    async def get_observed_state(self) -> Dict[str, Any]:
        return {
            "summary": self._connector.get_summary().__dict__,
            "status": await self._connector.get_status(),
            "discovery": self._connector.discovery,
        }

    async def get_normalized_observation(self) -> NormalizedObservation:
        status = await self._connector.get_status()
        return NormalizedObservation(
            status={"device_status": status},
            telemetry={
                "ambient_lux": status.get("ambient_lux"),
                "temperature_c": status.get("temperature_c"),
            },
            command_surface={
                "supports_playlist_control": True,
                "supports_brightness_control": True,
                "supports_message_post": False,
            },
            raw_vendor_payload={"discovery": self._connector.discovery},
        )

    def get_descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            adapter_id="yaham_yh31h",
            vendor="yaham",
            protocol="YH31H",
            product_family="led_sign",
            connector_version="1.0.0",
        )

    def get_capabilities(self) -> CapabilityProfile:
        return YAHAM_CAPABILITIES


class SolariAdapter:
    def __init__(self, host: str, **connector_kwargs: Any) -> None:
        self._connector = SolariConnector(host, **connector_kwargs)

    async def connect(self) -> Dict[str, Any]:
        return await self._connector.connect()

    async def disconnect(self) -> None:
        await self._connector.disconnect()

    async def get_observed_state(self) -> Dict[str, Any]:
        device_ids = [int(d["id"]) for d in self._connector.discovery.get("devices", []) if isinstance(d, dict) and "id" in d]
        status = await self._connector.get_status_by_device_ids(device_ids) if device_ids else {}
        return {
            "summary": self._connector.get_summary().__dict__,
            "status": status,
            "discovery": self._connector.discovery,
        }

    async def get_normalized_observation(self) -> NormalizedObservation:
        device_ids = [
            int(d["id"]) for d in self._connector.discovery.get("devices", [])
            if isinstance(d, dict) and "id" in d
        ]
        status = await self._connector.get_status_by_device_ids(device_ids) if device_ids else {}
        return NormalizedObservation(
            status={"device_status": status},
            telemetry={"device_count": len(device_ids)},
            command_surface={
                "supports_control_mode": True,
                "supports_predefined_message_activation": True,
                "supports_template_activation": True,
            },
            raw_vendor_payload={"discovery": self._connector.discovery},
        )

    def get_descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            adapter_id="solari_fep",
            vendor="solari",
            protocol="FEP SOAP",
            product_family="passenger_information_display",
            connector_version="1.0.0",
        )

    def get_capabilities(self) -> CapabilityProfile:
        return SOLARI_CAPABILITIES


class DemoRemoteCounterAdapter:
    """Thin adapter wrapper that binds the issue-70 remote counter demo path."""

    def __init__(self, org_id: str, site_id: str, device_id: str) -> None:
        self._adapter = RemoteCounterDemoAdapter(
            RemoteCounterBinding(org_id=org_id, site_id=site_id, device_id=device_id)
        )

    async def connect(self) -> Dict[str, Any]:
        return await self._adapter.connect()

    async def disconnect(self) -> None:
        await self._adapter.disconnect()

    async def get_observed_state(self) -> Dict[str, Any]:
        return await self._adapter.get_observed_state()

    async def get_normalized_observation(self) -> NormalizedObservation:
        return await self._adapter.get_normalized_observation()

    def ingest_mqtt_payload(self, topic: str, payload: Dict[str, Any], received_at_utc: str | None = None) -> None:
        self._adapter.ingest_mqtt_payload(topic, payload, received_at_utc)

    def diagnostics_snapshot(self) -> Dict[str, Any]:
        return self._adapter.diagnostics_snapshot()

    def canonical_demo_fields(self) -> Dict[str, str]:
        return self._adapter.canonical_demo_fields()

    def get_descriptor(self) -> AdapterDescriptor:
        return AdapterDescriptor(
            adapter_id="remote_counter_demo_rp2350",
            vendor="remote_counter",
            protocol=INGESTION_METHOD,
            product_family="people_counter",
            connector_version="1.0.0",
        )

    def get_capabilities(self) -> CapabilityProfile:
        return REMOTE_COUNTER_DEMO_CAPABILITIES

    def firmware_track(self) -> str:
        return FIRMWARE_TRACK
