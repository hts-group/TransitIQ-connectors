"""Generate connector conformance scorecards and regression budget checks."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable


def default_input_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "connector-conformance-input.json"


def default_budget_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "connector-conformance-regression-budget.json"


def default_output_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "connector-conformance-scorecard.latest.json"


def _validate_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"Malformed scorecard input: {field_name} must be a list of strings.")
    return value


def _validate_string_mapping(value: Any, field_name: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"Malformed scorecard input: {field_name} must be an object.")

    normalized: dict[str, str] = {}
    for key, mapped in value.items():
        if not isinstance(key, str) or not isinstance(mapped, str):
            raise ValueError(f"Malformed scorecard input: {field_name} keys and values must be strings.")
        normalized[key] = mapped
    return normalized


def _validate_profile_payload(profile_name: str, payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError(f"Malformed scorecard input: profiles.{profile_name} must be an object.")

    required_capabilities = _validate_string_list(
        payload.get("required_capabilities"),
        f"profiles.{profile_name}.required_capabilities",
    )
    current_capabilities = _validate_string_list(
        payload.get("current_capabilities"),
        f"profiles.{profile_name}.current_capabilities",
    )
    baseline_class_mappings = _validate_string_mapping(
        payload.get("baseline_class_mappings"),
        f"profiles.{profile_name}.baseline_class_mappings",
    )
    current_class_mappings = _validate_string_mapping(
        payload.get("current_class_mappings"),
        f"profiles.{profile_name}.current_class_mappings",
    )

    validation = payload.get("validation")
    if not isinstance(validation, dict):
        raise ValueError(f"Malformed scorecard input: profiles.{profile_name}.validation must be an object.")
    passed = validation.get("passed")
    total = validation.get("total")
    if not isinstance(passed, int) or not isinstance(total, int) or passed < 0 or total <= 0 or passed > total:
        raise ValueError(f"Malformed scorecard input: profiles.{profile_name}.validation has invalid counts.")

    return {
        "required_capabilities": set(required_capabilities),
        "current_capabilities": set(current_capabilities),
        "baseline_class_mappings": baseline_class_mappings,
        "current_class_mappings": current_class_mappings,
        "validation": {"passed": passed, "total": total},
    }


def load_conformance_input(path: Path | None = None) -> dict[str, dict[str, Any]]:
    input_path = path or default_input_path()
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    profiles = payload.get("profiles") if isinstance(payload, dict) else None

    if not isinstance(profiles, dict) or not profiles:
        raise ValueError("Malformed scorecard input: top-level 'profiles' must be a non-empty object.")

    normalized: dict[str, dict[str, Any]] = {}
    for profile_name, profile_payload in profiles.items():
        if not isinstance(profile_name, str):
            raise ValueError("Malformed scorecard input: profile names must be strings.")
        normalized[profile_name] = _validate_profile_payload(profile_name, profile_payload)
    return normalized


def load_regression_budget(path: Path | None = None) -> dict[str, Any]:
    budget_path = path or default_budget_path()
    payload = json.loads(budget_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Malformed budget input: expected JSON object.")

    default_budget = payload.get("default")
    if not isinstance(default_budget, dict):
        raise ValueError("Malformed budget input: 'default' must be an object.")

    for key in ("max_changed_mappings", "max_removed_mappings"):
        value = default_budget.get(key)
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"Malformed budget input: default.{key} must be a non-negative integer.")

    profiles = payload.get("profiles", {})
    if not isinstance(profiles, dict):
        raise ValueError("Malformed budget input: 'profiles' must be an object.")

    return {
        "default": default_budget,
        "profiles": profiles,
    }


def _safe_pct(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def _mapping_drift_counts(baseline: dict[str, str], current: dict[str, str]) -> dict[str, int]:
    baseline_keys = set(baseline.keys())
    current_keys = set(current.keys())

    changed = 0
    for key in baseline_keys.intersection(current_keys):
        if baseline[key] != current[key]:
            changed += 1

    removed = len(baseline_keys - current_keys)
    added = len(current_keys - baseline_keys)
    return {
        "changed": changed,
        "removed": removed,
        "added": added,
    }


def _profile_budget(profile_name: str, budget: dict[str, Any]) -> dict[str, int]:
    defaults = budget["default"]
    profile_overrides = budget["profiles"].get(profile_name, {})
    if not isinstance(profile_overrides, dict):
        raise ValueError(f"Malformed budget input: profiles.{profile_name} must be an object.")

    result: dict[str, int] = {
        "max_changed_mappings": defaults["max_changed_mappings"],
        "max_removed_mappings": defaults["max_removed_mappings"],
    }
    for key in ("max_changed_mappings", "max_removed_mappings"):
        if key not in profile_overrides:
            continue
        value = profile_overrides[key]
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"Malformed budget input: profiles.{profile_name}.{key} must be a non-negative integer.")
        result[key] = value
    return result


def _iter_sorted(values: Iterable[str]) -> list[str]:
    return sorted(set(values))


def generate_scorecards(
    conformance_input: dict[str, dict[str, Any]],
    budget: dict[str, Any],
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    profiles: list[dict[str, Any]] = []
    any_fail_triggered = False

    for profile_name in sorted(conformance_input.keys()):
        payload = conformance_input[profile_name]
        required_caps = set(payload["required_capabilities"])
        current_caps = set(payload["current_capabilities"])

        present_required = required_caps.intersection(current_caps)
        coverage_pct = _safe_pct(len(present_required), len(required_caps))

        drift_counts = _mapping_drift_counts(payload["baseline_class_mappings"], payload["current_class_mappings"])
        baseline_mapping_count = len(payload["baseline_class_mappings"])
        consistent_mappings = baseline_mapping_count - drift_counts["changed"] - drift_counts["removed"]
        mapping_consistency_pct = _safe_pct(max(consistent_mappings, 0), max(baseline_mapping_count, 1))

        passed = payload["validation"]["passed"]
        total = payload["validation"]["total"]
        validation_pass_rate_pct = _safe_pct(passed, total)

        conformance_score_pct = round(
            (coverage_pct + mapping_consistency_pct + validation_pass_rate_pct) / 3.0,
            2,
        )

        budget_limits = _profile_budget(profile_name, budget)
        fail_reasons: list[str] = []

        if drift_counts["changed"] > budget_limits["max_changed_mappings"]:
            fail_reasons.append(
                "changed_mappings_exceeded:{actual}>{limit}".format(
                    actual=drift_counts["changed"],
                    limit=budget_limits["max_changed_mappings"],
                )
            )
        if drift_counts["removed"] > budget_limits["max_removed_mappings"]:
            fail_reasons.append(
                "removed_mappings_exceeded:{actual}>{limit}".format(
                    actual=drift_counts["removed"],
                    limit=budget_limits["max_removed_mappings"],
                )
            )

        fail_triggered = len(fail_reasons) > 0
        any_fail_triggered = any_fail_triggered or fail_triggered

        profiles.append(
            {
                "profile": profile_name,
                "metrics": {
                    "capability_coverage_pct": coverage_pct,
                    "mapping_consistency_pct": mapping_consistency_pct,
                    "validation_pass_rate_pct": validation_pass_rate_pct,
                    "conformance_score_pct": conformance_score_pct,
                },
                "drift": {
                    "added_capabilities": _iter_sorted(current_caps - required_caps),
                    "removed_capabilities": _iter_sorted(required_caps - current_caps),
                    "changed_mappings": drift_counts["changed"],
                    "removed_mappings": drift_counts["removed"],
                    "added_mappings": drift_counts["added"],
                },
                "budget": budget_limits,
                "fail_triggered": fail_triggered,
                "fail_reasons": fail_reasons,
            }
        )

    return {
        "generated_at_utc": generated_at_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overall_fail_triggered": any_fail_triggered,
        "profiles": profiles,
    }


def write_scorecard_artifact(scorecards: dict[str, Any], output_path: Path | None = None) -> Path:
    target = output_path or default_output_path()
    target.write_text(json.dumps(scorecards, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def render_scorecard_summary(scorecards: dict[str, Any]) -> str:
    lines = [
        "| Profile | Coverage | Consistency | Pass Rate | Score | Fail Trigger |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for item in scorecards["profiles"]:
        metrics = item["metrics"]
        lines.append(
            "| {profile} | {coverage:.2f} | {consistency:.2f} | {pass_rate:.2f} | {score:.2f} | {failed} |".format(
                profile=item["profile"],
                coverage=metrics["capability_coverage_pct"],
                consistency=metrics["mapping_consistency_pct"],
                pass_rate=metrics["validation_pass_rate_pct"],
                score=metrics["conformance_score_pct"],
                failed="yes" if item["fail_triggered"] else "no",
            )
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate connector conformance scorecards.")
    parser.add_argument("--input-path", type=Path, default=None, help="Optional conformance input JSON path.")
    parser.add_argument("--budget-path", type=Path, default=None, help="Optional regression budget JSON path.")
    parser.add_argument("--output-path", type=Path, default=None, help="Optional scorecard artifact output path.")
    args = parser.parse_args()

    conformance_input = load_conformance_input(args.input_path)
    budget = load_regression_budget(args.budget_path)
    scorecards = generate_scorecards(conformance_input, budget)
    output_path = write_scorecard_artifact(scorecards, args.output_path)

    print("Connector conformance scorecard summary")
    print(render_scorecard_summary(scorecards))
    print(f"Artifact: {output_path}")
    print("Overall fail trigger: {state}".format(state="yes" if scorecards["overall_fail_triggered"] else "no"))

    return 2 if scorecards["overall_fail_triggered"] else 0


if __name__ == "__main__":
    raise SystemExit(main())