"""Adapter profile drift checks against baseline compatibility snapshots."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable


CURRENT_PROFILE_MAP: Dict[str, Dict[str, object]] = {
    "ntcip": {
        "capabilities": {
            "connect",
            "discovery",
            "observed_status",
            "message_post",
            "brightness_control",
            "control_mode",
        },
        "class_mappings": {
            "connect": "health",
            "discovery": "debug",
            "observed_status": "health",
            "message_post": "operator_action",
            "brightness_control": "telemetry",
            "control_mode": "operator_action",
        },
    },
    "yaham": {
        "capabilities": {
            "connect",
            "discovery",
            "observed_status",
            "brightness_control",
            "playlist_control",
        },
        "class_mappings": {
            "connect": "health",
            "discovery": "debug",
            "observed_status": "health",
            "brightness_control": "telemetry",
            "playlist_control": "operator_action",
        },
    },
    "solari": {
        "capabilities": {
            "connect",
            "discovery",
            "observed_status",
            "control_mode",
            "predefined_message_activation",
            "template_activation",
        },
        "class_mappings": {
            "connect": "health",
            "discovery": "debug",
            "observed_status": "health",
            "control_mode": "operator_action",
            "predefined_message_activation": "operator_action",
            "template_activation": "operator_action",
        },
    },
}


def default_baseline_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "connector-profile-baseline-snapshot.json"


def _validate_list_of_strings(value: object, field_name: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"Malformed baseline: {field_name} must be a list of strings.")
    if len(set(value)) != len(value):
        raise ValueError(f"Malformed baseline: {field_name} contains duplicate entries.")
    return value


def _validate_mapping(value: object, field_name: str) -> dict[str, str]:
    if not isinstance(value, dict):
        raise ValueError(f"Malformed baseline: {field_name} must be an object.")

    normalized: dict[str, str] = {}
    for key, mapping_value in value.items():
        if not isinstance(key, str) or not isinstance(mapping_value, str):
            raise ValueError(f"Malformed baseline: {field_name} keys/values must be strings.")
        normalized[key] = mapping_value
    return normalized


def load_baseline_snapshot(path: Path | None = None) -> dict[str, Dict[str, object]]:
    baseline_path = path or default_baseline_path()
    payload = json.loads(baseline_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict) or not isinstance(payload.get("profiles"), dict):
        raise ValueError("Malformed baseline: top-level object must include 'profiles'.")

    profiles = payload["profiles"]
    normalized: dict[str, Dict[str, object]] = {}

    for profile_name, profile_data in profiles.items():
        if not isinstance(profile_name, str) or not isinstance(profile_data, dict):
            raise ValueError("Malformed baseline: profile entries must be objects keyed by name.")

        capabilities = _validate_list_of_strings(
            profile_data.get("capabilities"),
            f"profiles.{profile_name}.capabilities",
        )
        class_mappings = _validate_mapping(
            profile_data.get("class_mappings"),
            f"profiles.{profile_name}.class_mappings",
        )

        normalized[profile_name] = {
            "capabilities": set(capabilities),
            "class_mappings": class_mappings,
        }

    return normalized


def build_current_snapshot() -> dict[str, Dict[str, object]]:
    snapshot: dict[str, Dict[str, object]] = {}
    for profile_name, profile_data in CURRENT_PROFILE_MAP.items():
        snapshot[profile_name] = {
            "capabilities": set(profile_data["capabilities"]),
            "class_mappings": dict(profile_data["class_mappings"]),
        }
    return snapshot


def _iter_sorted(items: Iterable[str]) -> list[str]:
    return sorted(set(items))


def _profile_drift(
    profile_name: str,
    baseline_profile: dict[str, object] | None,
    current_profile: dict[str, object] | None,
) -> dict[str, object]:
    baseline_capabilities = set()
    baseline_mappings: dict[str, str] = {}
    current_capabilities = set()
    current_mappings: dict[str, str] = {}

    if baseline_profile is not None:
        baseline_capabilities = set(baseline_profile["capabilities"])
        baseline_mappings = dict(baseline_profile["class_mappings"])
    if current_profile is not None:
        current_capabilities = set(current_profile["capabilities"])
        current_mappings = dict(current_profile["class_mappings"])

    added_capabilities = _iter_sorted(current_capabilities - baseline_capabilities)
    removed_capabilities = _iter_sorted(baseline_capabilities - current_capabilities)

    added_class_mappings = {
        key: current_mappings[key]
        for key in sorted(set(current_mappings.keys()) - set(baseline_mappings.keys()))
    }
    removed_class_mappings = {
        key: baseline_mappings[key]
        for key in sorted(set(baseline_mappings.keys()) - set(current_mappings.keys()))
    }

    changed_class_mappings = {}
    for key in sorted(set(baseline_mappings.keys()).intersection(current_mappings.keys())):
        if baseline_mappings[key] == current_mappings[key]:
            continue
        changed_class_mappings[key] = {
            "baseline": baseline_mappings[key],
            "current": current_mappings[key],
        }

    has_drift = any(
        (
            added_capabilities,
            removed_capabilities,
            added_class_mappings,
            removed_class_mappings,
            changed_class_mappings,
        )
    )

    return {
        "profile": profile_name,
        "has_drift": has_drift,
        "added_capabilities": added_capabilities,
        "removed_capabilities": removed_capabilities,
        "added_class_mappings": added_class_mappings,
        "removed_class_mappings": removed_class_mappings,
        "changed_class_mappings": changed_class_mappings,
    }


def generate_drift_report(
    baseline_snapshot: dict[str, Dict[str, object]],
    current_snapshot: dict[str, Dict[str, object]] | None = None,
) -> dict[str, object]:
    current = current_snapshot or build_current_snapshot()
    profiles = sorted(set(baseline_snapshot.keys()).union(current.keys()))

    profile_reports = [
        _profile_drift(profile, baseline_snapshot.get(profile), current.get(profile))
        for profile in profiles
    ]

    return {
        "has_drift": any(bool(profile_report["has_drift"]) for profile_report in profile_reports),
        "profiles": profile_reports,
    }


def render_profile_summary(report: dict[str, object]) -> str:
    lines = [
        "| Adapter profile | Drift | Added caps | Removed caps | Changed mappings |",
        "|---|---|---:|---:|---:|",
    ]

    for profile_report in report["profiles"]:
        lines.append(
            "| {profile} | {drift} | {added_caps} | {removed_caps} | {changed_maps} |".format(
                profile=profile_report["profile"],
                drift="yes" if profile_report["has_drift"] else "no",
                added_caps=len(profile_report["added_capabilities"]),
                removed_caps=len(profile_report["removed_capabilities"]),
                changed_maps=len(profile_report["changed_class_mappings"]),
            )
        )

    return "\n".join(lines)


def run_drift_check(path: Path | None = None) -> dict[str, object]:
    baseline = load_baseline_snapshot(path)
    report = generate_drift_report(baseline)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run adapter profile drift checks.")
    parser.add_argument(
        "--baseline-path",
        type=Path,
        default=None,
        help="Optional baseline snapshot path.",
    )
    parser.add_argument(
        "--fail-on-drift",
        action="store_true",
        help="Return a non-zero exit code if drift is detected.",
    )
    args = parser.parse_args()

    report = run_drift_check(args.baseline_path)

    print("Adapter profile drift report")
    print(render_profile_summary(report))
    print(f"Drift detected: {'yes' if report['has_drift'] else 'no'}")

    if args.fail_on_drift and bool(report["has_drift"]):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())