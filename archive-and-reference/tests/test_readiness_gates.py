"""Tests for readiness gate decisions and remediation recommendations."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from transitiq_connectors.readiness_gates import evaluate_readiness_gates, load_scorecard_artifact


class ReadinessGateTests(unittest.TestCase):
    def _scorecard_payload(self) -> dict:
        return {
            "generated_at_utc": "2026-04-18T00:00:00Z",
            "overall_fail_triggered": False,
            "profiles": [
                {
                    "profile": "ntcip",
                    "metrics": {
                        "capability_coverage_pct": 100.0,
                        "mapping_consistency_pct": 100.0,
                        "validation_pass_rate_pct": 100.0,
                        "conformance_score_pct": 100.0,
                    },
                    "drift": {
                        "added_capabilities": [],
                        "removed_capabilities": [],
                        "changed_mappings": 0,
                        "removed_mappings": 0,
                        "added_mappings": 0,
                    },
                    "fail_triggered": False,
                    "fail_reasons": [],
                }
            ],
        }

    def test_gate_decision_logic_ready_watch_block(self) -> None:
        ready_payload = self._scorecard_payload()
        ready = evaluate_readiness_gates(ready_payload)
        self.assertEqual("ready", ready["overall_posture"])
        self.assertEqual("ready", ready["profiles"][0]["posture"])

        watch_payload = self._scorecard_payload()
        watch_payload["profiles"][0]["metrics"]["conformance_score_pct"] = 90.0
        watch = evaluate_readiness_gates(watch_payload)
        self.assertEqual("watch", watch["overall_posture"])
        self.assertEqual("watch", watch["profiles"][0]["posture"])

        block_payload = self._scorecard_payload()
        block_payload["profiles"][0]["fail_triggered"] = True
        block_payload["profiles"][0]["fail_reasons"] = ["changed_mappings_exceeded:1>0"]
        block_payload["profiles"][0]["drift"]["changed_mappings"] = 1
        block = evaluate_readiness_gates(block_payload)
        self.assertEqual("block", block["overall_posture"])
        self.assertEqual("block", block["profiles"][0]["posture"])

    def test_recommendation_ranking_prioritizes_removed_over_changed(self) -> None:
        payload = self._scorecard_payload()
        profile = payload["profiles"][0]
        profile["fail_triggered"] = True
        profile["fail_reasons"] = ["removed_mappings_exceeded:1>0", "changed_mappings_exceeded:1>0"]
        profile["drift"]["removed_mappings"] = 1
        profile["drift"]["changed_mappings"] = 1

        readiness = evaluate_readiness_gates(payload)
        recommendations = readiness["profiles"][0]["recommendations"]

        self.assertGreaterEqual(len(recommendations), 2)
        self.assertEqual("restore_removed_mappings", recommendations[0]["category"])
        self.assertEqual(1, recommendations[0]["priority"])

    def test_malformed_scorecard_raises_value_error(self) -> None:
        malformed_payload = {
            "profiles": [
                {
                    "profile": "ntcip",
                    "metrics": {
                        "capability_coverage_pct": 100.0,
                        "mapping_consistency_pct": 100.0,
                        "validation_pass_rate_pct": 100.0,
                    },
                    "drift": {
                        "changed_mappings": 0,
                        "removed_mappings": 0,
                        "added_mappings": 0,
                    },
                    "fail_triggered": False,
                    "fail_reasons": [],
                }
            ]
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
            json.dump(malformed_payload, handle)
            temp_path = Path(handle.name)

        self.addCleanup(lambda: temp_path.unlink(missing_ok=True))

        with self.assertRaisesRegex(ValueError, "conformance_score_pct"):
            load_scorecard_artifact(temp_path)

    def test_overall_rollup_prefers_block_over_watch(self) -> None:
        payload = {
            "generated_at_utc": "2026-04-19T00:00:00Z",
            "profiles": [
                {
                    "profile": "ntcip",
                    "metrics": {
                        "capability_coverage_pct": 100.0,
                        "mapping_consistency_pct": 100.0,
                        "validation_pass_rate_pct": 100.0,
                        "conformance_score_pct": 100.0,
                    },
                    "drift": {
                        "changed_mappings": 0,
                        "removed_mappings": 0,
                        "added_mappings": 0,
                    },
                    "fail_triggered": False,
                    "fail_reasons": [],
                },
                {
                    "profile": "solari",
                    "metrics": {
                        "capability_coverage_pct": 100.0,
                        "mapping_consistency_pct": 100.0,
                        "validation_pass_rate_pct": 100.0,
                        "conformance_score_pct": 90.0,
                    },
                    "drift": {
                        "changed_mappings": 1,
                        "removed_mappings": 0,
                        "added_mappings": 0,
                    },
                    "fail_triggered": False,
                    "fail_reasons": [],
                },
                {
                    "profile": "yaham",
                    "metrics": {
                        "capability_coverage_pct": 90.0,
                        "mapping_consistency_pct": 90.0,
                        "validation_pass_rate_pct": 90.0,
                        "conformance_score_pct": 90.0,
                    },
                    "drift": {
                        "changed_mappings": 1,
                        "removed_mappings": 1,
                        "added_mappings": 0,
                    },
                    "fail_triggered": True,
                    "fail_reasons": ["removed_mappings_exceeded:1>0"],
                },
            ],
        }

        readiness = evaluate_readiness_gates(payload)
        self.assertEqual("block", readiness["overall_posture"])
        postures = {item["profile"]: item["posture"] for item in readiness["profiles"]}
        self.assertEqual("ready", postures["ntcip"])
        self.assertEqual("watch", postures["solari"])
        self.assertEqual("block", postures["yaham"])

    def test_watch_with_no_drift_emits_observe_recommendation(self) -> None:
        payload = self._scorecard_payload()
        profile = payload["profiles"][0]
        profile["metrics"]["conformance_score_pct"] = 90.0
        profile["drift"]["changed_mappings"] = 0
        profile["drift"]["removed_mappings"] = 0
        profile["drift"]["added_mappings"] = 0
        profile["fail_triggered"] = False
        profile["fail_reasons"] = []

        readiness = evaluate_readiness_gates(payload)
        recommendations = readiness["profiles"][0]["recommendations"]

        self.assertEqual("watch", readiness["overall_posture"])
        self.assertEqual(1, len(recommendations))
        self.assertEqual("observe", recommendations[0]["category"])
        self.assertEqual(3, recommendations[0]["priority"])

    def test_fail_reasons_are_emitted_as_recommendations(self) -> None:
        payload = self._scorecard_payload()
        profile = payload["profiles"][0]
        profile["fail_triggered"] = True
        profile["fail_reasons"] = ["changed_mappings_exceeded:2>0"]
        profile["drift"]["changed_mappings"] = 2

        readiness = evaluate_readiness_gates(payload)
        recommendations = readiness["profiles"][0]["recommendations"]

        categories = [item["category"] for item in recommendations]
        self.assertIn("threshold_fail_reason", categories)

    def test_watch_recommendations_include_coverage_and_validation_gaps(self) -> None:
        payload = self._scorecard_payload()
        profile = payload["profiles"][0]
        profile["metrics"]["conformance_score_pct"] = 92.0
        profile["metrics"]["capability_coverage_pct"] = 95.0
        profile["metrics"]["validation_pass_rate_pct"] = 96.0

        readiness = evaluate_readiness_gates(payload)
        recommendations = readiness["profiles"][0]["recommendations"]

        categories = [item["category"] for item in recommendations]
        self.assertIn("capability_coverage", categories)
        self.assertIn("validation_reliability", categories)

    def test_recommendations_sorted_by_priority_then_category(self) -> None:
        payload = self._scorecard_payload()
        profile = payload["profiles"][0]
        profile["fail_triggered"] = True
        profile["fail_reasons"] = ["removed_mappings_exceeded:1>0"]
        profile["drift"]["removed_mappings"] = 1
        profile["drift"]["changed_mappings"] = 1

        readiness = evaluate_readiness_gates(payload)
        recommendations = readiness["profiles"][0]["recommendations"]
        sort_keys = [(item["priority"], item["category"]) for item in recommendations]

        self.assertEqual(sorted(sort_keys), sort_keys)


if __name__ == "__main__":
    unittest.main()