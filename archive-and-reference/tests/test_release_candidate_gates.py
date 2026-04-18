"""Tests for release-candidate gate aggregation and blocker prioritization."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from transitiq_connectors.release_candidate_gates import (
    aggregate_release_candidate_gate,
    load_readiness_artifact,
)


class ReleaseCandidateGateTests(unittest.TestCase):
    def _readiness_payload(self) -> dict:
        return {
            "generated_at_utc": "2026-04-19T00:00:00Z",
            "overall_posture": "watch",
            "profiles": [
                {
                    "profile": "ntcip",
                    "posture": "ready",
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
                    "recommendations": [
                        {
                            "priority": 3,
                            "category": "maintain",
                            "action": "Maintain current readiness posture.",
                        }
                    ],
                },
                {
                    "profile": "solari",
                    "posture": "watch",
                    "metrics": {
                        "capability_coverage_pct": 95.0,
                        "mapping_consistency_pct": 95.0,
                        "validation_pass_rate_pct": 95.0,
                        "conformance_score_pct": 95.0,
                    },
                    "drift": {
                        "added_capabilities": [],
                        "removed_capabilities": [],
                        "changed_mappings": 1,
                        "removed_mappings": 0,
                        "added_mappings": 0,
                    },
                    "fail_triggered": False,
                    "recommendations": [
                        {
                            "priority": 2,
                            "category": "review_changed_mappings",
                            "action": "Review changed mappings.",
                        }
                    ],
                },
            ],
        }

    def test_aggregation_rolls_profile_postures_into_watch_disposition(self) -> None:
        payload = self._readiness_payload()

        release_candidate = aggregate_release_candidate_gate(payload)

        self.assertEqual("watch", release_candidate["release_candidate_disposition"])
        self.assertEqual(2, release_candidate["summary"]["total_profiles"])
        self.assertEqual(1, release_candidate["summary"]["ready_profiles"])
        self.assertEqual(1, release_candidate["summary"]["watch_profiles"])
        self.assertEqual(0, release_candidate["summary"]["block_profiles"])
        self.assertEqual(1, len(release_candidate["prioritized_blockers"]))
        self.assertEqual("solari", release_candidate["prioritized_blockers"][0]["profile"])

    def test_tie_breaking_is_deterministic_for_same_priority(self) -> None:
        payload = self._readiness_payload()
        payload["profiles"] = [
            {
                "profile": "yaham",
                "posture": "block",
                "metrics": {
                    "capability_coverage_pct": 90.0,
                    "mapping_consistency_pct": 90.0,
                    "validation_pass_rate_pct": 90.0,
                    "conformance_score_pct": 90.0,
                },
                "drift": {
                    "added_capabilities": [],
                    "removed_capabilities": [],
                    "changed_mappings": 1,
                    "removed_mappings": 1,
                    "added_mappings": 0,
                },
                "fail_triggered": True,
                "recommendations": [
                    {
                        "priority": 1,
                        "category": "restore_removed_mappings",
                        "action": "Restore removed mappings first.",
                    },
                    {
                        "priority": 2,
                        "category": "review_changed_mappings",
                        "action": "Review changed mappings.",
                    },
                ],
            },
            {
                "profile": "solari",
                "posture": "block",
                "metrics": {
                    "capability_coverage_pct": 91.0,
                    "mapping_consistency_pct": 91.0,
                    "validation_pass_rate_pct": 91.0,
                    "conformance_score_pct": 91.0,
                },
                "drift": {
                    "added_capabilities": [],
                    "removed_capabilities": [],
                    "changed_mappings": 1,
                    "removed_mappings": 1,
                    "added_mappings": 0,
                },
                "fail_triggered": True,
                "recommendations": [
                    {
                        "priority": 1,
                        "category": "restore_removed_mappings",
                        "action": "Restore removed mappings first.",
                    }
                ],
            },
        ]

        release_candidate = aggregate_release_candidate_gate(payload)
        blockers = release_candidate["prioritized_blockers"]

        self.assertEqual("block", release_candidate["release_candidate_disposition"])
        self.assertEqual(3, len(blockers))
        self.assertEqual("solari", blockers[0]["profile"])
        self.assertEqual("yaham", blockers[1]["profile"])
        self.assertEqual(1, blockers[0]["priority"])
        self.assertEqual(1, blockers[1]["priority"])

    def test_malformed_readiness_input_raises_value_error(self) -> None:
        malformed_payload = {
            "generated_at_utc": "2026-04-19T00:00:00Z",
            "profiles": [
                {
                    "profile": "ntcip",
                    "posture": "ready",
                    "metrics": {
                        "conformance_score_pct": 100.0,
                    },
                    "drift": {
                        "changed_mappings": 0,
                        "removed_mappings": 0,
                        "added_mappings": 0,
                    },
                    "fail_triggered": False,
                }
            ],
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
            json.dump(malformed_payload, handle)
            temp_path = Path(handle.name)

        self.addCleanup(lambda: temp_path.unlink(missing_ok=True))

        with self.assertRaisesRegex(ValueError, "recommendations"):
            load_readiness_artifact(temp_path)


if __name__ == "__main__":
    unittest.main()