"""Tests for adapter compatibility fixture corpus and validation summary."""

from __future__ import annotations

import unittest

from transitiq_connectors.compatibility_fixtures import (
    load_fixture_corpus,
    render_summary_table,
    summarize_validation_by_profile,
    validate_fixture_corpus,
)


class CompatibilityFixtureValidationTests(unittest.TestCase):
    def test_fixture_corpus_has_valid_and_invalid_cases_per_profile(self) -> None:
        fixtures = load_fixture_corpus()
        by_profile = {}

        for fixture in fixtures:
            by_profile.setdefault(fixture.adapter_profile, {"valid": 0, "invalid": 0})
            if fixture.expected_valid:
                by_profile[fixture.adapter_profile]["valid"] += 1
            else:
                by_profile[fixture.adapter_profile]["invalid"] += 1

        for profile in ("ntcip", "yaham", "solari"):
            self.assertIn(profile, by_profile)
            self.assertGreater(by_profile[profile]["valid"], 0)
            self.assertGreater(by_profile[profile]["invalid"], 0)

    def test_fixture_validation_has_no_mismatches(self) -> None:
        fixtures = load_fixture_corpus()
        results = validate_fixture_corpus(fixtures)

        failures = [result for result in results if not bool(result["validation_passed"])]
        self.assertEqual([], failures)

    def test_validation_summary_is_rendered_by_adapter_profile(self) -> None:
        fixtures = load_fixture_corpus()
        results = validate_fixture_corpus(fixtures)
        summary = summarize_validation_by_profile(results)
        table = render_summary_table(summary)

        self.assertIn("| ntcip |", table)
        self.assertIn("| yaham |", table)
        self.assertIn("| solari |", table)

        for profile in ("ntcip", "yaham", "solari"):
            self.assertEqual(0, summary[profile]["fail"])


if __name__ == "__main__":
    unittest.main()