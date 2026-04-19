"""Issue #71 tests for demo-safe NTCIP VMS slice."""

from __future__ import annotations

import unittest
from typing import Any, Dict

from transitiq_connectors.ntcip_vms_demo import NtcipVmsBinding, NtcipVmsDemoSlice


class _FakeObservedStateAdapter:
    async def get_observed_state(self) -> Dict[str, Any]:
        return {
            "summary": {"device": "demo-vms", "host": "10.0.0.20"},
            "status": {
                "device_status": {
                    "reachability": "online",
                    "current_message": "ROAD WORK AHEAD",
                }
            },
        }


class _FaultyObservedStateAdapter:
    async def get_observed_state(self) -> Dict[str, Any]:
        raise RuntimeError("snmp timeout")


class NtcipVmsDemoSliceTests(unittest.IsolatedAsyncioTestCase):
    async def test_onboarding_snapshot_exposes_binding_reachability_and_state(self) -> None:
        slice_runner = NtcipVmsDemoSlice(
            binding=NtcipVmsBinding(
                org_id="org-a",
                site_id="site-ntcip-1",
                device_id="vms-01",
                host="10.0.0.20",
            ),
            observed_state_adapter=_FakeObservedStateAdapter(),
        )

        snapshot = await slice_runner.onboarding_snapshot()

        self.assertEqual("status_and_current_message_visibility", snapshot["capability_target"])
        self.assertEqual("org-a", snapshot["binding"]["org_id"])
        self.assertEqual("site-ntcip-1", snapshot["binding"]["site_id"])
        self.assertEqual("vms-01", snapshot["binding"]["device_id"])
        self.assertTrue(snapshot["reachability"]["reachable"])
        self.assertEqual("ROAD WORK AHEAD", snapshot["visible_state"]["current_message"])
        self.assertFalse(snapshot["transport_assumptions"]["vpn_required"])
        self.assertEqual([161], snapshot["transport_assumptions"]["ports"])

    async def test_demo_read_operation_returns_visible_state(self) -> None:
        slice_runner = NtcipVmsDemoSlice(
            binding=NtcipVmsBinding(
                org_id="org-a",
                site_id="site-ntcip-1",
                device_id="vms-01",
                host="10.0.0.20",
            ),
            observed_state_adapter=_FakeObservedStateAdapter(),
        )

        result = await slice_runner.demo_operation_read_status()

        self.assertEqual("read_status", result["operation"])
        self.assertTrue(result["ok"])
        self.assertEqual(
            "ROAD WORK AHEAD",
            result["result"]["current_message"],
        )

    async def test_failure_path_is_diagnosable(self) -> None:
        slice_runner = NtcipVmsDemoSlice(
            binding=NtcipVmsBinding(
                org_id="org-a",
                site_id="site-ntcip-1",
                device_id="vms-01",
                host="10.0.0.20",
            ),
            observed_state_adapter=_FaultyObservedStateAdapter(),
        )

        snapshot = await slice_runner.onboarding_snapshot()

        self.assertFalse(snapshot["reachability"]["reachable"])
        self.assertEqual(
            "ntcip_observed_state_error",
            snapshot["diagnostics"]["failure_surface"]["auth_connectivity_parsing"]["code"],
        )
        self.assertIn(
            "snmp timeout",
            snapshot["diagnostics"]["failure_surface"]["auth_connectivity_parsing"]["message"],
        )


if __name__ == "__main__":
    unittest.main()
