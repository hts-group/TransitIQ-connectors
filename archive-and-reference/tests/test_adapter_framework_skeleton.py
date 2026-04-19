"""Tests for adapter framework skeleton contract and routing behavior."""

from __future__ import annotations

import unittest

from transitiq_connectors.adapter_framework import AdapterRequest, ReferenceAdapterStub


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


if __name__ == "__main__":
    unittest.main()