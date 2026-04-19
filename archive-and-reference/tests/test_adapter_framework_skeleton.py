"""Tests for adapter framework skeleton contract and routing behavior."""

from __future__ import annotations

import unittest

from transitiq_connectors.adapter_framework import AdapterFramework, AdapterRequest, ReferenceAdapterStub


class AdapterFrameworkSkeletonTests(unittest.TestCase):
    def test_health_route_returns_ok_status(self) -> None:
        adapter = ReferenceAdapterStub()
        response = adapter.route_request(AdapterRequest(route="health", payload={}))

        self.assertTrue(response.ok)
        self.assertEqual("health", response.route)
        self.assertEqual("ok", response.result["status"])
        self.assertIsNone(response.error_code)

    def test_echo_route_returns_payload(self) -> None:
        adapter = ReferenceAdapterStub()
        payload = {"message": "hello", "id": 1}
        response = adapter.route_request(AdapterRequest(route="echo", payload=payload))

        self.assertTrue(response.ok)
        self.assertEqual(payload, response.result["payload"])

    def test_unsupported_route_exposes_error_surface(self) -> None:
        adapter = ReferenceAdapterStub()
        response = adapter.route_request(AdapterRequest(route="configure", payload={"mode": "safe"}))

        self.assertFalse(response.ok)
        self.assertEqual("unsupported_route", response.error_code)
        self.assertTrue(response.error_message)

    def test_framework_routes_to_registered_adapter(self) -> None:
        framework = AdapterFramework()
        framework.register("reference", ReferenceAdapterStub())

        response = framework.route("reference", AdapterRequest(route="health", payload={}))

        self.assertTrue(response.ok)
        self.assertEqual("health", response.route)
        self.assertEqual("ok", response.result["status"])

    def test_framework_returns_adapter_not_found_error(self) -> None:
        framework = AdapterFramework()

        response = framework.route("missing", AdapterRequest(route="health", payload={}))

        self.assertFalse(response.ok)
        self.assertEqual("adapter_not_found", response.error_code)
        self.assertTrue(response.error_message)

    def test_framework_lists_registered_adapters_sorted(self) -> None:
        framework = AdapterFramework()
        framework.register("zeta", ReferenceAdapterStub())
        framework.register("alpha", ReferenceAdapterStub())

        self.assertEqual(["alpha", "zeta"], framework.list_registered_adapters())

    def test_framework_supports_known_and_unknown_routes(self) -> None:
        framework = AdapterFramework()
        framework.register("reference", ReferenceAdapterStub())

        self.assertTrue(framework.supports_route("reference", "health"))
        self.assertFalse(framework.supports_route("reference", "configure"))
        self.assertFalse(framework.supports_route("missing", "health"))


if __name__ == "__main__":
    unittest.main()