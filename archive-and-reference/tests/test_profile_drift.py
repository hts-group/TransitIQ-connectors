"""Tests for adapter profile drift checks and baseline validation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from transitiq_connectors.profile_drift import (
    build_current_snapshot,
    generate_drift_report,
    load_baseline_snapshot,
)


class ProfileDriftTests(unittest.TestCase):
    def test_no_drift_when_baseline_matches_current_snapshot(self) -> None:
        report = generate_drift_report(build_current_snapshot(), build_current_snapshot())
        self.assertFalse(report["has_drift"])

        for profile_report in report["profiles"]:
            self.assertFalse(profile_report["has_drift"])
            self.assertEqual([], profile_report["added_capabilities"])
            self.assertEqual([], profile_report["removed_capabilities"])
            self.assertEqual({}, profile_report["changed_class_mappings"])

    def test_expected_drift_detected_for_capability_and_mapping_changes(self) -> None:
        baseline = build_current_snapshot()
        baseline["yaham"]["capabilities"].remove("playlist_control")
        baseline["solari"]["class_mappings"]["control_mode"] = "debug"

        report = generate_drift_report(baseline, build_current_snapshot())
        self.assertTrue(report["has_drift"])

        yaham = next(profile for profile in report["profiles"] if profile["profile"] == "yaham")
        self.assertIn("playlist_control", yaham["added_capabilities"])

        solari = next(profile for profile in report["profiles"] if profile["profile"] == "solari")
        self.assertIn("control_mode", solari["changed_class_mappings"])
        self.assertEqual("debug", solari["changed_class_mappings"]["control_mode"]["baseline"])
        self.assertEqual("operator_action", solari["changed_class_mappings"]["control_mode"]["current"])

    def test_malformed_baseline_raises_value_error(self) -> None:
        malformed_payload = {
            "version": "2026-04-18",
            "profiles": {
                "ntcip": {
                    "capabilities": "connect",
                    "class_mappings": {"connect": "health"},
                }
            },
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
            json.dump(malformed_payload, handle)
            temp_path = Path(handle.name)

        self.addCleanup(lambda: temp_path.unlink(missing_ok=True))

        with self.assertRaisesRegex(ValueError, "capabilities"):
            load_baseline_snapshot(temp_path)


if __name__ == "__main__":
    unittest.main()