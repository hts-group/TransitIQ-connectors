"""Tests for conformance scorecard generation and regression budgets."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from transitiq_connectors.conformance_scorecards import (
    generate_scorecards,
    load_conformance_input,
    load_regression_budget,
)


class ConformanceScorecardTests(unittest.TestCase):
    def _baseline_input(self) -> dict[str, dict[str, object]]:
        return {
            "ntcip": {
                "required_capabilities": {"connect", "discovery", "message_post"},
                "current_capabilities": {"connect", "discovery", "message_post"},
                "baseline_class_mappings": {
                    "connect": "health",
                    "discovery": "debug",
                    "message_post": "operator_action",
                },
                "current_class_mappings": {
                    "connect": "health",
                    "discovery": "debug",
                    "message_post": "operator_action",
                },
                "validation": {"passed": 10, "total": 10},
            }
        }

    def _baseline_budget(self) -> dict[str, object]:
        return {
            "default": {
                "max_changed_mappings": 0,
                "max_removed_mappings": 0,
            },
            "profiles": {},
        }

    def test_scorecard_math_is_100_for_clean_profile(self) -> None:
        scorecards = generate_scorecards(self._baseline_input(), self._baseline_budget(), "2026-04-18T00:00:00Z")
        self.assertFalse(scorecards["overall_fail_triggered"])

        profile = scorecards["profiles"][0]
        self.assertEqual(100.0, profile["metrics"]["capability_coverage_pct"])
        self.assertEqual(100.0, profile["metrics"]["mapping_consistency_pct"])
        self.assertEqual(100.0, profile["metrics"]["validation_pass_rate_pct"])
        self.assertEqual(100.0, profile["metrics"]["conformance_score_pct"])
        self.assertFalse(profile["fail_triggered"])

    def test_threshold_fail_trigger_for_changed_mapping(self) -> None:
        modified_input = self._baseline_input()
        modified_input["ntcip"]["current_class_mappings"]["message_post"] = "debug"

        scorecards = generate_scorecards(modified_input, self._baseline_budget(), "2026-04-18T00:00:00Z")
        self.assertTrue(scorecards["overall_fail_triggered"])

        profile = scorecards["profiles"][0]
        self.assertTrue(profile["fail_triggered"])
        self.assertIn("changed_mappings_exceeded", profile["fail_reasons"][0])

    def test_malformed_input_safety_raises_value_error(self) -> None:
        malformed_payload = {
            "profiles": {
                "ntcip": {
                    "required_capabilities": ["connect"],
                    "current_capabilities": ["connect"],
                    "baseline_class_mappings": {"connect": "health"},
                    "current_class_mappings": {"connect": "health"},
                    "validation": {"passed": 1}
                }
            }
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
            json.dump(malformed_payload, handle)
            temp_path = Path(handle.name)

        self.addCleanup(lambda: temp_path.unlink(missing_ok=True))

        with self.assertRaisesRegex(ValueError, "validation"):
            load_conformance_input(temp_path)

    def test_malformed_budget_safety_raises_value_error(self) -> None:
        malformed_budget = {
            "default": {
                "max_changed_mappings": -1,
                "max_removed_mappings": 0,
            },
            "profiles": {},
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
            json.dump(malformed_budget, handle)
            temp_path = Path(handle.name)

        self.addCleanup(lambda: temp_path.unlink(missing_ok=True))

        with self.assertRaisesRegex(ValueError, "max_changed_mappings"):
            load_regression_budget(temp_path)


if __name__ == "__main__":
    unittest.main()