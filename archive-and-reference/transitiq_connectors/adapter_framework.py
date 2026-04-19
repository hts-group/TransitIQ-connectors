"""Minimal adapter framework skeleton for connector-side contract routing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol


@dataclass(frozen=True)
class AdapterRequest:
    """Connector-local request envelope for adapter route handling."""

    route: str
    payload: Dict[str, Any]


@dataclass(frozen=True)
class AdapterResponse:
    """Connector-local response envelope with explicit error surface."""

    ok: bool
    route: str
    result: Dict[str, Any]
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True)
class AdapterLifecycleSnapshot:
    """Typed lifecycle snapshot for connect/read/normalize/health stages."""

    adapter_id: str
    connected: Dict[str, Any]
    read_state: Dict[str, Any]
    normalized: Dict[str, Any]
    health: Dict[str, Any]


class AdapterInterface(Protocol):
    """Contract skeleton for adapter routing behavior."""

    def connect(self) -> Dict[str, Any]:
        """Establish adapter connection lifecycle hook."""

    def read(self) -> Dict[str, Any]:
        """Read adapter state lifecycle hook."""

    def normalize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize adapter payload lifecycle hook."""

    def health(self) -> Dict[str, Any]:
        """Return adapter health lifecycle hook output."""

    def route_request(self, request: AdapterRequest) -> AdapterResponse:
        """Route a connector-local request to a supported adapter surface."""


class AdapterFramework:
    """Minimal adapter registry and router for connector-side framework wiring."""

    def __init__(self) -> None:
        self._adapters: Dict[str, AdapterInterface] = {}

    def register(self, adapter_id: str, adapter: AdapterInterface) -> None:
        self._adapters[adapter_id] = adapter

    def register_or_replace(self, adapter_id: str, adapter: AdapterInterface) -> bool:
        replaced_existing = adapter_id in self._adapters
        self._adapters[adapter_id] = adapter
        return replaced_existing

    def has_adapter(self, adapter_id: str) -> bool:
        return adapter_id in self._adapters

    def unregister(self, adapter_id: str) -> bool:
        if adapter_id not in self._adapters:
            return False

        del self._adapters[adapter_id]
        return True

    def list_registered_adapters(self) -> list[str]:
        return sorted(self._adapters.keys())

    def supports_route(self, adapter_id: str, route: str) -> bool:
        adapter = self._adapters.get(adapter_id)
        if adapter is None:
            return False

        supported_routes = getattr(adapter, "SUPPORTED_ROUTES", None)
        if supported_routes is None:
            return False

        return route in supported_routes

    def list_supported_routes(self, adapter_id: str) -> list[str]:
        adapter = self._adapters.get(adapter_id)
        if adapter is None:
            return []

        supported_routes = getattr(adapter, "SUPPORTED_ROUTES", None)
        if supported_routes is None:
            return []

        return sorted(supported_routes)

    def supported_routes_snapshot(self) -> Dict[str, list[str]]:
        snapshot: Dict[str, list[str]] = {}
        for adapter_id in self.list_registered_adapters():
            snapshot[adapter_id] = self.list_supported_routes(adapter_id)

        return snapshot

    def adapter_metadata(self, adapter_id: str) -> Dict[str, Any]:
        adapter = self._adapters.get(adapter_id)
        if adapter is None:
            return {
                "adapter_id": adapter_id,
                "registered": False,
                "supported_routes": [],
            }

        return {
            "adapter_id": adapter_id,
            "registered": True,
            "supported_routes": self.list_supported_routes(adapter_id),
        }

    def registered_adapter_count(self) -> int:
        return len(self._adapters)

    def is_registry_empty(self) -> bool:
        return self.registered_adapter_count() == 0

    def registry_summary(self) -> Dict[str, Any]:
        return {
            "adapter_count": self.registered_adapter_count(),
            "adapter_ids": self.list_registered_adapters(),
            "supported_routes": self.supported_routes_snapshot(),
        }

    def contract_surface(self) -> Dict[str, Any]:
        return {
            "request": ["route", "payload"],
            "response": ["ok", "route", "result", "error_code", "error_message"],
            "lifecycle_hooks": ["connect", "read", "normalize", "health"],
            "framework_error_codes": [
                "adapter_not_found",
                "adapter_route_error",
                "adapter_lifecycle_error",
            ],
        }

    def route(self, adapter_id: str, request: AdapterRequest) -> AdapterResponse:
        adapter = self._adapters.get(adapter_id)
        if adapter is None:
            return AdapterResponse(
                ok=False,
                route=request.route,
                result={},
                error_code="adapter_not_found",
                error_message=f"Adapter '{adapter_id}' is not registered.",
            )
        try:
            return adapter.route_request(request)
        except Exception as exc:
            return AdapterResponse(
                ok=False,
                route=request.route,
                result={},
                error_code="adapter_route_error",
                error_message=f"Adapter route execution failed: {exc}",
            )

    def run_lifecycle(self, adapter_id: str, payload: Dict[str, Any]) -> AdapterResponse:
        adapter = self._adapters.get(adapter_id)
        if adapter is None:
            return AdapterResponse(
                ok=False,
                route="lifecycle",
                result={},
                error_code="adapter_not_found",
                error_message=f"Adapter '{adapter_id}' is not registered.",
            )

        try:
            snapshot = AdapterLifecycleSnapshot(
                adapter_id=adapter_id,
                connected=adapter.connect(),
                read_state=adapter.read(),
                normalized=adapter.normalize(payload),
                health=adapter.health(),
            )
            return AdapterResponse(
                ok=True,
                route="lifecycle",
                result={
                    "adapter_id": snapshot.adapter_id,
                    "connected": snapshot.connected,
                    "read_state": snapshot.read_state,
                    "normalized": snapshot.normalized,
                    "health": snapshot.health,
                },
            )
        except Exception as exc:
            return AdapterResponse(
                ok=False,
                route="lifecycle",
                result={},
                error_code="adapter_lifecycle_error",
                error_message=f"Adapter lifecycle execution failed: {exc}",
            )


class ReferenceAdapterStub:
    """Reference stub demonstrating contract-compliant route handling."""

    SUPPORTED_ROUTES = {"health", "echo"}

    def connect(self) -> Dict[str, Any]:
        return {"connected": True, "adapter": "reference_stub"}

    def read(self) -> Dict[str, Any]:
        return {"source": "reference_stub", "state": "ready"}

    def normalize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"payload": payload, "normalized": True}

    def health(self) -> Dict[str, Any]:
        return {"status": "ok", "adapter": "reference_stub"}

    def route_request(self, request: AdapterRequest) -> AdapterResponse:
        if request.route == "health":
            return AdapterResponse(
                ok=True,
                route=request.route,
                result={"status": "ok", "adapter": "reference_stub"},
            )

        if request.route == "echo":
            return AdapterResponse(
                ok=True,
                route=request.route,
                result={"payload": request.payload},
            )

        return AdapterResponse(
            ok=False,
            route=request.route,
            result={},
            error_code="unsupported_route",
            error_message="Route is not supported by reference stub.",
        )
