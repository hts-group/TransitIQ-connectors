"""Issue #71 demo-safe NTCIP VMS integration slice."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol


@dataclass(frozen=True)
class NtcipVmsBinding:
    """Tenant and physical binding for one VMS demo sign."""

    org_id: str
    site_id: str
    device_id: str
    host: str


class NtcipObservedStateAdapter(Protocol):
    async def get_observed_state(self) -> Dict[str, Any]:
        """Return observed state from NTCIP adapter."""


class NtcipVmsDemoSlice:
    """Monitoring-first connector slice for one NTCIP VMS sign."""

    TRANSPORT_ASSUMPTIONS = {
        "transport": "snmp",
        "access_path": "direct_ip_or_routed_lan",
        "ports": [161],
        "vpn_required": False,
        "broker_required": False,
    }

    CAPABILITY_TARGET = "status_and_current_message_visibility"

    def __init__(self, binding: NtcipVmsBinding, observed_state_adapter: NtcipObservedStateAdapter) -> None:
        self._binding = binding
        self._adapter = observed_state_adapter
        self._last_error: Dict[str, str] = {"code": "", "message": ""}

    async def onboarding_snapshot(self) -> Dict[str, Any]:
        """Return tenant binding plus reachable key visible state for demo."""

        try:
            observed = await self._adapter.get_observed_state()
        except Exception as exc:
            self._last_error = {
                "code": "ntcip_observed_state_error",
                "message": str(exc),
            }
            return {
                "binding": self.binding_fields(),
                "capability_target": self.CAPABILITY_TARGET,
                "transport_assumptions": self.TRANSPORT_ASSUMPTIONS,
                "reachability": {"reachable": False},
                "visible_state": {},
                "diagnostics": self.diagnostics_snapshot(),
            }

        status = observed.get("status", {}) if isinstance(observed, dict) else {}
        device_status = status.get("device_status", {}) if isinstance(status, dict) else {}
        summary = observed.get("summary", {}) if isinstance(observed, dict) else {}
        current_message = None
        if isinstance(device_status, dict):
            current_message = device_status.get("current_message")

        self._last_error = {"code": "", "message": ""}
        return {
            "binding": self.binding_fields(),
            "capability_target": self.CAPABILITY_TARGET,
            "transport_assumptions": self.TRANSPORT_ASSUMPTIONS,
            "reachability": {
                "reachable": True,
                "host": self._binding.host,
            },
            "visible_state": {
                "status": device_status,
                "current_message": current_message,
                "summary": summary,
            },
            "diagnostics": self.diagnostics_snapshot(),
        }

    async def demo_operation_read_status(self) -> Dict[str, Any]:
        """Single demo-safe operation: read status visibility only."""

        snapshot = await self.onboarding_snapshot()
        return {
            "operation": "read_status",
            "ok": snapshot["reachability"].get("reachable", False),
            "result": snapshot["visible_state"],
        }

    def binding_fields(self) -> Dict[str, str]:
        return {
            "org_id": self._binding.org_id,
            "site_id": self._binding.site_id,
            "device_id": self._binding.device_id,
            "host": self._binding.host,
        }

    def diagnostics_snapshot(self) -> Dict[str, Dict[str, str]]:
        return {
            "failure_surface": {
                "auth_connectivity_parsing": self._last_error,
            }
        }
