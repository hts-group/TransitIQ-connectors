"""Tests for connector closure dependency diagnostics and remediation priority."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from transitiq_connectors.closure_dependency_diagnostics import (
    evaluate_closure_diagnostics,
    load_dependency_input,
    load_release_candidate_gate,
)


class ClosureDependencyDiagnosticsTests(unittest.TestCase):
    def _dependency_input(self) -> dict:
        return {
            "dependencies": [
                {
                    "id": "status-freeze",
                    "name": "Frozen status mapping envelope",
                    "owner": "TransitIQ-control-plane",
                    "status": "open",
                    "severity": "high",
                    "canonical_contract": True,
                    "due_utc": "2026-04-21T18:00:00Z",
                    "remediation": "Confirm canonical status mapping publication and update connector mapping baseline.",
                },
                {
                    "id": "terminal-policy",
                    "name": "Terminal lifecycle strictness closure",
                    "owner": "TransitIQ-control-plane + Architect",
                    "status": "consumed",
                    "severity": "medium",
                    "canonical_contract": False,
                    "due_utc": "2026-04-21T18:00:00Z",
                    "remediation": "Keep consumed policy evidence linked in milestone updates.",
                },
            ]
        }

    def _release_candidate_ready(self) -> dict:
        return {
            "release_candidate_disposition": "ready",
            "prioritized_blockers": [],
        }

    def test_open_canonical_dependencies_result_in_watch_posture(self) -> None:
        diagnostics = evaluate_closure_diagnostics(
            self._dependency_input(),
            self._release_candidate_ready(),
            now_utc=datetime(2026, 4, 19, 0, 0, 0, tzinfo=timezone.utc),
        )

        self.assertEqual("watch", diagnostics["closure_posture"])
        self.assertEqual(2, diagnostics["summary"]["total_dependencies"])
        self.assertEqual(1, diagnostics["summary"]["resolved_dependencies"])
        self.assertEqual(1, diagnostics["summary"]["open_dependencies"])
        self.assertEqual(1, diagnostics["summary"]["open_canonical_contract_dependencies"])
        self.assertEqual(0, diagnostics["summary"]["overdue_dependencies"])

    def test_overdue_items_are_prioritized_and_block(self) -> None:
        dependency_input = self._dependency_input()
        dependency_input["dependencies"].append(
            {
                "id": "access-sessions",
                "name": "accessSessions lifecycle freeze",
                "owner": "TransitIQ-control-plane",
                "status": "open",
                "severity": "critical",
                "canonical_contract": True,
                "due_utc": "2026-04-18T18:00:00Z",
                "remediation": "Escalate owner and post overdue disposition in issue #2 checkpoint.",
            }
        )

        diagnostics = evaluate_closure_diagnostics(
            dependency_input,
            self._release_candidate_ready(),
            now_utc=datetime(2026, 4, 19, 0, 0, 0, tzinfo=timezone.utc),
        )

        self.assertEqual("block", diagnostics["closure_posture"])
        self.assertEqual(1, diagnostics["summary"]["overdue_dependencies"])
        self.assertEqual("access-sessions", diagnostics["prioritized_remediation"][0]["dependency_id"])
        self.assertTrue(diagnostics["prioritized_remediation"][0]["overdue"])

    def test_malformed_input_raises_value_error(self) -> None:
        malformed_dependency_input = {
            "dependencies": [
                {
                    "id": "status-freeze",
                    "name": "Frozen status mapping envelope",
                    "owner": "TransitIQ-control-plane",
                    "status": "open",
                    "severity": "urgent",
                    "canonical_contract": True,
                    "due_utc": "2026-04-21T18:00:00Z",
                    "remediation": "Publish mapping.",
                }
            ]
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as dep_handle:
            json.dump(malformed_dependency_input, dep_handle)
            dep_path = Path(dep_handle.name)

        malformed_release_candidate = {
            "release_candidate_disposition": "ship",
            "prioritized_blockers": [],
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as rc_handle:
            json.dump(malformed_release_candidate, rc_handle)
            rc_path = Path(rc_handle.name)

        self.addCleanup(lambda: dep_path.unlink(missing_ok=True))
        self.addCleanup(lambda: rc_path.unlink(missing_ok=True))

        with self.assertRaisesRegex(ValueError, "severity"):
            load_dependency_input(dep_path)

        with self.assertRaisesRegex(ValueError, "release_candidate_disposition"):
            load_release_candidate_gate(rc_path)

    def test_release_candidate_block_forces_closure_block(self) -> None:
        dependency_input = {
            "dependencies": [
                {
                    "id": "status-freeze",
                    "name": "Frozen status mapping envelope",
                    "owner": "TransitIQ-control-plane",
                    "status": "closed",
                    "severity": "high",
                    "canonical_contract": True,
                    "due_utc": "2026-04-21T18:00:00Z",
                    "remediation": "No action.",
                }
            ]
        }
        release_candidate_block = {
            "release_candidate_disposition": "block",
            "prioritized_blockers": [
                {
                    "priority": 1,
                    "profile": "solari",
                    "category": "restore_removed_mappings",
                    "action": "Restore removed mappings.",
                }
            ],
        }

        diagnostics = evaluate_closure_diagnostics(
            dependency_input,
            release_candidate_block,
            now_utc=datetime(2026, 4, 19, 0, 0, 0, tzinfo=timezone.utc),
        )

        self.assertEqual("block", diagnostics["closure_posture"])
        self.assertEqual(1, diagnostics["summary"]["release_candidate_blockers"])

    def test_invalid_due_timestamp_raises_value_error(self) -> None:
        malformed_dependency_input = {
            "dependencies": [
                {
                    "id": "status-freeze",
                    "name": "Frozen status mapping envelope",
                    "owner": "TransitIQ-control-plane",
                    "status": "open",
                    "severity": "high",
                    "canonical_contract": True,
                    "due_utc": "2026-04-21",
                    "remediation": "Publish mapping.",
                }
            ]
        }

        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as dep_handle:
            json.dump(malformed_dependency_input, dep_handle)
            dep_path = Path(dep_handle.name)

        self.addCleanup(lambda: dep_path.unlink(missing_ok=True))

        with self.assertRaisesRegex(ValueError, "YYYY-MM-DDTHH:MM:SSZ"):
            load_dependency_input(dep_path)


if __name__ == "__main__":
    unittest.main()