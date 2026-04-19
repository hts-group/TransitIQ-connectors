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


class AdapterInterface(Protocol):
    """Contract skeleton for adapter routing behavior."""

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

        return adapter.route_request(request)


class ReferenceAdapterStub:
    """Reference stub demonstrating contract-compliant route handling."""

    SUPPORTED_ROUTES = {"health", "echo"}

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
