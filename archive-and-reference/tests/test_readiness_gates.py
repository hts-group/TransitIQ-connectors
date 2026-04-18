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


if __name__ == "__main__":
    unittest.main()