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

    def test_framework_unregister_returns_true_for_registered_adapter(self) -> None:
        framework = AdapterFramework()
        framework.register("reference", ReferenceAdapterStub())

        self.assertTrue(framework.unregister("reference"))
        self.assertEqual([], framework.list_registered_adapters())

    def test_framework_unregister_returns_false_for_missing_adapter(self) -> None:
        framework = AdapterFramework()

        self.assertFalse(framework.unregister("missing"))

    def test_framework_route_after_unregister_returns_not_found(self) -> None:
        framework = AdapterFramework()
        framework.register("reference", ReferenceAdapterStub())
        framework.unregister("reference")

        response = framework.route("reference", AdapterRequest(route="health", payload={}))

        self.assertFalse(response.ok)
        self.assertEqual("adapter_not_found", response.error_code)

    def test_register_or_replace_reports_new_then_replace(self) -> None:
        framework = AdapterFramework()

        first = framework.register_or_replace("reference", ReferenceAdapterStub())
        second = framework.register_or_replace("reference", ReferenceAdapterStub())

        self.assertFalse(first)
        self.assertTrue(second)

    def test_has_adapter_tracks_registration_and_unregistration(self) -> None:
        framework = AdapterFramework()

        self.assertFalse(framework.has_adapter("reference"))
        framework.register("reference", ReferenceAdapterStub())
        self.assertTrue(framework.has_adapter("reference"))
        framework.unregister("reference")
        self.assertFalse(framework.has_adapter("reference"))

    def test_list_supported_routes_for_registered_adapter(self) -> None:
        framework = AdapterFramework()
        framework.register("reference", ReferenceAdapterStub())

        self.assertEqual(["echo", "health"], framework.list_supported_routes("reference"))

    def test_list_supported_routes_for_missing_adapter_is_empty(self) -> None:
        framework = AdapterFramework()

        self.assertEqual([], framework.list_supported_routes("missing"))

    def test_supported_routes_snapshot_for_registered_adapters(self) -> None:
        framework = AdapterFramework()
        framework.register("b", ReferenceAdapterStub())
        framework.register("a", ReferenceAdapterStub())

        self.assertEqual(
            {
                "a": ["echo", "health"],
                "b": ["echo", "health"],
            },
            framework.supported_routes_snapshot(),
        )

    def test_supported_routes_snapshot_is_empty_when_no_adapters(self) -> None:
        framework = AdapterFramework()

        self.assertEqual({}, framework.supported_routes_snapshot())

    def test_adapter_metadata_for_registered_adapter(self) -> None:
        framework = AdapterFramework()
        framework.register("reference", ReferenceAdapterStub())

        self.assertEqual(
            {
                "adapter_id": "reference",
                "registered": True,
                "supported_routes": ["echo", "health"],
            },
            framework.adapter_metadata("reference"),
        )

    def test_adapter_metadata_for_missing_adapter(self) -> None:
        framework = AdapterFramework()

        self.assertEqual(
            {
                "adapter_id": "missing",
                "registered": False,
                "supported_routes": [],
            },
            framework.adapter_metadata("missing"),
        )

    def test_registered_adapter_count_tracks_registry_size(self) -> None:
        framework = AdapterFramework()

        self.assertEqual(0, framework.registered_adapter_count())
        framework.register("one", ReferenceAdapterStub())
        framework.register("two", ReferenceAdapterStub())
        self.assertEqual(2, framework.registered_adapter_count())
        framework.unregister("one")
        self.assertEqual(1, framework.registered_adapter_count())

    def test_is_registry_empty_reflects_registration_state(self) -> None:
        framework = AdapterFramework()

        self.assertTrue(framework.is_registry_empty())
        framework.register("reference", ReferenceAdapterStub())
        self.assertFalse(framework.is_registry_empty())

    def test_registry_summary_for_empty_framework(self) -> None:
        framework = AdapterFramework()

        self.assertEqual(
            {
                "adapter_count": 0,
                "adapter_ids": [],
                "supported_routes": {},
            },
            framework.registry_summary(),
        )

    def test_registry_summary_for_populated_framework(self) -> None:
        framework = AdapterFramework()
        framework.register("b", ReferenceAdapterStub())
        framework.register("a", ReferenceAdapterStub())

        self.assertEqual(
            {
                "adapter_count": 2,
                "adapter_ids": ["a", "b"],
                "supported_routes": {
                    "a": ["echo", "health"],
                    "b": ["echo", "health"],
                },
            },
            framework.registry_summary(),
        )

    def test_reference_adapter_lifecycle_hooks_return_structured_output(self) -> None:
        adapter = ReferenceAdapterStub()

        self.assertTrue(adapter.connect()["connected"])
        self.assertEqual("ready", adapter.read()["state"])
        self.assertTrue(adapter.normalize({"x": 1})["normalized"])
        self.assertEqual("ok", adapter.health()["status"])

    def test_framework_maps_adapter_route_exceptions(self) -> None:
        class FaultyAdapter:
            SUPPORTED_ROUTES = {"health"}

            def connect(self):
                return {}

            def read(self):
                return {}

            def normalize(self, payload):
                return payload

            def health(self):
                return {"status": "ok"}

            def route_request(self, request):
                raise ValueError("forced failure")

        framework = AdapterFramework()
        framework.register("faulty", FaultyAdapter())

        response = framework.route("faulty", AdapterRequest(route="health", payload={}))

        self.assertFalse(response.ok)
        self.assertEqual("adapter_route_error", response.error_code)
        self.assertTrue(response.error_message)

    def test_smoke_adapter_loads_routes_and_returns_structured_output(self) -> None:
        framework = AdapterFramework()
        framework.register("reference", ReferenceAdapterStub())

        response = framework.route("reference", AdapterRequest(route="echo", payload={"k": "v"}))

        self.assertTrue(response.ok)
        self.assertEqual("echo", response.route)
        self.assertEqual({"k": "v"}, response.result["payload"])

    def test_lifecycle_run_returns_structured_snapshot(self) -> None:
        framework = AdapterFramework()
        framework.register("reference", ReferenceAdapterStub())

        response = framework.run_lifecycle("reference", {"k": "v"})

        self.assertTrue(response.ok)
        self.assertEqual("lifecycle", response.route)
        self.assertEqual("reference", response.result["adapter_id"])
        self.assertTrue(response.result["connected"]["connected"])
        self.assertEqual("ready", response.result["read_state"]["state"])
        self.assertTrue(response.result["normalized"]["normalized"])
        self.assertEqual("ok", response.result["health"]["status"])

    def test_lifecycle_run_for_missing_adapter_returns_not_found(self) -> None:
        framework = AdapterFramework()

        response = framework.run_lifecycle("missing", {"k": "v"})

        self.assertFalse(response.ok)
        self.assertEqual("adapter_not_found", response.error_code)

    def test_lifecycle_run_maps_adapter_exceptions(self) -> None:
        class FaultyLifecycleAdapter:
            SUPPORTED_ROUTES = {"health"}

            def connect(self):
                raise RuntimeError("connect failed")

            def read(self):
                return {}

            def normalize(self, payload):
                return payload

            def health(self):
                return {"status": "ok"}

            def route_request(self, request):
                return None

        framework = AdapterFramework()
        framework.register("faulty_lifecycle", FaultyLifecycleAdapter())

        response = framework.run_lifecycle("faulty_lifecycle", {"k": "v"})

        self.assertFalse(response.ok)
        self.assertEqual("adapter_lifecycle_error", response.error_code)
        self.assertTrue(response.error_message)

    def test_contract_surface_exposes_request_response_and_errors(self) -> None:
        framework = AdapterFramework()

        surface = framework.contract_surface()

        self.assertEqual(
            {
                "id": "transitiq.connectors.adapter_framework.contract_surface",
                "version": "1.0.0",
                "fingerprint": "transitiq.connectors.adapter_framework.contract_surface@1.0.0",
            },
            surface["contract_signature"],
        )
        self.assertEqual(
            "transitiq.connectors.adapter_framework.contract_surface@1.0.0",
            surface["contract_fingerprint"],
        )
        self.assertEqual(
            {
                "id": "transitiq.connectors.adapter_framework.contract_surface",
                "version": "1.0.0",
            },
            surface["contract_coordinates"],
        )
        self.assertEqual(
            "transitiq.connectors.adapter_framework.contract_surface",
            surface["contract_surface_id"],
        )
        self.assertEqual("1.0.0", surface["contract_surface_version"])
        self.assertEqual(
            ["AdapterRequest", "AdapterResponse", "AdapterLifecycleSnapshot"],
            surface["contracts"],
        )
        self.assertEqual(["route", "payload"], surface["request"])
        self.assertIn("error_code", surface["response"])
        self.assertIn("connect", surface["lifecycle_hooks"])
        self.assertIn("adapter_route_error", surface["framework_error_codes"])

    def test_smoke_validation_report_for_registered_adapter(self) -> None:
        framework = AdapterFramework()
        framework.register("reference", ReferenceAdapterStub())

        report = framework.smoke_validation_report("reference", {"k": "v"})

        self.assertTrue(report["adapter_loaded"])
        self.assertTrue(report["route"]["ok"])
        self.assertEqual("echo", report["route"]["route"])
        self.assertEqual({"k": "v"}, report["route"]["result"]["payload"])
        self.assertTrue(report["lifecycle"]["ok"])
        self.assertEqual("lifecycle", report["lifecycle"]["route"])
        self.assertEqual("reference", report["lifecycle"]["result"]["adapter_id"])

    def test_smoke_validation_report_for_missing_adapter(self) -> None:
        framework = AdapterFramework()

        report = framework.smoke_validation_report("missing", {"k": "v"})

        self.assertFalse(report["adapter_loaded"])
        self.assertFalse(report["route"]["ok"])
        self.assertEqual("adapter_not_found", report["route"]["error_code"])
        self.assertFalse(report["lifecycle"]["ok"])
        self.assertEqual("adapter_not_found", report["lifecycle"]["error_code"])

    def test_smoke_validation_profile_for_registered_adapter(self) -> None:
        framework = AdapterFramework()
        framework.register("reference", ReferenceAdapterStub())

        profile = framework.smoke_validation_profile("reference", {"k": "v"})

        self.assertEqual("repo-backed", profile["classification"])
        self.assertEqual(
            "transitiq.connectors.adapter_framework.contract_surface@1.0.0",
            profile["contract_signature"]["fingerprint"],
        )
        self.assertIn("reference", profile["registry"]["adapter_ids"])
        self.assertTrue(profile["smoke"]["route"]["ok"])
        self.assertTrue(profile["smoke"]["lifecycle"]["ok"])

    def test_smoke_validation_profile_for_missing_adapter(self) -> None:
        framework = AdapterFramework()

        profile = framework.smoke_validation_profile("missing", {"k": "v"})

        self.assertEqual("repo-backed", profile["classification"])
        self.assertEqual([], profile["registry"]["adapter_ids"])
        self.assertFalse(profile["smoke"]["route"]["ok"])
        self.assertFalse(profile["smoke"]["lifecycle"]["ok"])

    def test_command_sync_refresh_evidence_for_registered_adapter(self) -> None:
        framework = AdapterFramework()
        framework.register("reference", ReferenceAdapterStub())

        evidence = framework.command_sync_refresh_evidence("reference", {"k": "v"})

        self.assertEqual("repo-backed", evidence["classification"])
        self.assertTrue(evidence["contract_types_complete"])
        self.assertTrue(evidence["registry_router_complete"])
        self.assertTrue(evidence["reference_adapter_wired"])
        self.assertTrue(evidence["smoke_profile"]["smoke"]["route"]["ok"])
        self.assertIn("adapter_route_error", evidence["deterministic_framework_error_codes"])

    def test_command_sync_refresh_evidence_for_missing_adapter(self) -> None:
        framework = AdapterFramework()

        evidence = framework.command_sync_refresh_evidence("missing", {"k": "v"})

        self.assertEqual("repo-backed", evidence["classification"])
        self.assertFalse(evidence["reference_adapter_wired"])
        self.assertFalse(evidence["smoke_profile"]["smoke"]["route"]["ok"])
        self.assertEqual(
            "adapter_not_found",
            evidence["smoke_profile"]["smoke"]["route"]["error_code"],
        )


if __name__ == "__main__":
    unittest.main()