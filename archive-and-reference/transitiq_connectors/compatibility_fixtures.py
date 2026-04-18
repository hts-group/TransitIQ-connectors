"""Compatibility fixture validation for adapter capability and signal-class pairs."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


ADAPTER_CAPABILITIES: Dict[str, set[str]] = {
    "ntcip": {
        "connect",
        "discovery",
        "observed_status",
        "message_post",
        "brightness_control",
        "control_mode",
    },
    "yaham": {
        "connect",
        "discovery",
        "observed_status",
        "brightness_control",
        "playlist_control",
    },
    "solari": {
        "connect",
        "discovery",
        "observed_status",
        "control_mode",
        "predefined_message_activation",
        "template_activation",
    },
}

ADAPTER_SIGNAL_CLASSES: Dict[str, set[str]] = {
    "ntcip": {"health", "telemetry", "operator_action", "debug"},
    "yaham": {"health", "telemetry", "operator_action", "debug"},
    "solari": {"health", "operator_action", "debug"},
}


@dataclass(frozen=True)
class CompatibilityFixtureCase:
    case_id: str
    adapter_profile: str
    capability: str
    signal_class: str
    expected_valid: bool
    notes: str


def default_fixture_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "connector-compatibility-fixture-corpus.json"


def load_fixture_corpus(path: Path | None = None) -> List[CompatibilityFixtureCase]:
    fixture_path = path or default_fixture_path()
    raw_cases = json.loads(fixture_path.read_text(encoding="utf-8"))

    return [
        CompatibilityFixtureCase(
            case_id=item["case_id"],
            adapter_profile=item["adapter_profile"],
            capability=item["capability"],
            signal_class=item["signal_class"],
            expected_valid=bool(item["expected_valid"]),
            notes=item.get("notes", ""),
        )
        for item in raw_cases
    ]


def evaluate_fixture_case(case: CompatibilityFixtureCase) -> Dict[str, object]:
    reasons: List[str] = []
    profile_capabilities = ADAPTER_CAPABILITIES.get(case.adapter_profile)
    profile_signal_classes = ADAPTER_SIGNAL_CLASSES.get(case.adapter_profile)

    if profile_capabilities is None or profile_signal_classes is None:
        reasons.append("unknown_adapter_profile")
    else:
        if case.capability not in profile_capabilities:
            reasons.append("unsupported_capability")
        if case.signal_class not in profile_signal_classes:
            reasons.append("unsupported_signal_class")

    computed_valid = len(reasons) == 0
    validation_passed = computed_valid == case.expected_valid

    if validation_passed:
        reason = "matched_expected_validity"
        if reasons:
            reason += ":" + ",".join(reasons)
    else:
        reason = "expected_validity_mismatch"
        if reasons:
            reason += ":" + ",".join(reasons)

    return {
        "case_id": case.case_id,
        "adapter_profile": case.adapter_profile,
        "capability": case.capability,
        "signal_class": case.signal_class,
        "expected_valid": case.expected_valid,
        "computed_valid": computed_valid,
        "validation_passed": validation_passed,
        "reason": reason,
    }


def validate_fixture_corpus(cases: List[CompatibilityFixtureCase]) -> List[Dict[str, object]]:
    return [evaluate_fixture_case(case) for case in cases]


def summarize_validation_by_profile(results: List[Dict[str, object]]) -> Dict[str, Dict[str, int]]:
    summary: Dict[str, Dict[str, int]] = {}

    for result in results:
        profile = str(result["adapter_profile"])
        summary.setdefault(profile, {"pass": 0, "fail": 0})
        key = "pass" if bool(result["validation_passed"]) else "fail"
        summary[profile][key] += 1

    return summary


def render_summary_table(summary: Dict[str, Dict[str, int]]) -> str:
    lines = [
        "| Adapter profile | Pass | Fail |",
        "|---|---:|---:|",
    ]

    for profile in sorted(summary.keys()):
        lines.append(f"| {profile} | {summary[profile]['pass']} | {summary[profile]['fail']} |")

    return "\n".join(lines)


def run_validation(path: Path | None = None) -> tuple[str, int, List[Dict[str, object]]]:
    cases = load_fixture_corpus(path)
    results = validate_fixture_corpus(cases)
    summary = summarize_validation_by_profile(results)
    table = render_summary_table(summary)
    failed_count = len([result for result in results if not bool(result["validation_passed"])])

    return table, failed_count, results


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate connector compatibility fixture corpus.")
    parser.add_argument(
        "--fixture-path",
        type=Path,
        default=None,
        help="Optional path to fixture corpus JSON.",
    )
    args = parser.parse_args()

    table, failed_count, results = run_validation(args.fixture_path)

    print("Compatibility fixture validation summary")
    print(table)
    print(f"Total cases: {len(results)}")
    print(f"Failed validations: {failed_count}")

    if failed_count:
        print("Mismatched cases:")
        for result in results:
            if bool(result["validation_passed"]):
                continue
            print(
                "- {case_id}: expected_valid={expected_valid}, computed_valid={computed_valid}, reason={reason}".format(
                    case_id=result["case_id"],
                    expected_valid=result["expected_valid"],
                    computed_valid=result["computed_valid"],
                    reason=result["reason"],
                )
            )

    return 1 if failed_count else 0


if __name__ == "__main__":
    raise SystemExit(main())