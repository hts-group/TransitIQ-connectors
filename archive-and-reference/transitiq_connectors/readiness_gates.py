"""Evaluate release readiness gates from conformance scorecard artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def default_scorecard_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "connector-conformance-scorecard.latest.json"


def default_output_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "connector-readiness-gates.latest.json"


def load_scorecard_artifact(path: Path | None = None) -> dict[str, Any]:
    scorecard_path = path or default_scorecard_path()
    payload = json.loads(scorecard_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Malformed scorecard artifact: expected top-level object.")

    profiles = payload.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("Malformed scorecard artifact: 'profiles' must be a list.")

    for idx, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            raise ValueError(f"Malformed scorecard artifact: profiles[{idx}] must be an object.")

        if not isinstance(profile.get("profile"), str):
            raise ValueError(f"Malformed scorecard artifact: profiles[{idx}].profile must be a string.")

        metrics = profile.get("metrics")
        if not isinstance(metrics, dict):
            raise ValueError(f"Malformed scorecard artifact: profiles[{idx}].metrics must be an object.")

        required_metric_keys = (
            "capability_coverage_pct",
            "mapping_consistency_pct",
            "validation_pass_rate_pct",
            "conformance_score_pct",
        )
        for key in required_metric_keys:
            if not isinstance(metrics.get(key), (int, float)):
                raise ValueError(
                    f"Malformed scorecard artifact: profiles[{idx}].metrics.{key} must be numeric."
                )

        drift = profile.get("drift")
        if not isinstance(drift, dict):
            raise ValueError(f"Malformed scorecard artifact: profiles[{idx}].drift must be an object.")
        for drift_key in ("changed_mappings", "removed_mappings", "added_mappings"):
            if not isinstance(drift.get(drift_key), int):
                raise ValueError(
                    f"Malformed scorecard artifact: profiles[{idx}].drift.{drift_key} must be an integer."
                )

        if not isinstance(profile.get("fail_triggered"), bool):
            raise ValueError(f"Malformed scorecard artifact: profiles[{idx}].fail_triggered must be a boolean.")
        if not isinstance(profile.get("fail_reasons"), list):
            raise ValueError(f"Malformed scorecard artifact: profiles[{idx}].fail_reasons must be a list.")

    return payload


def evaluate_profile_posture(profile: dict[str, Any]) -> str:
    metrics = profile["metrics"]
    fail_triggered = bool(profile["fail_triggered"])
    score = float(metrics["conformance_score_pct"])

    if fail_triggered:
        return "block"
    if score >= 95.0:
        return "ready"
    return "watch"


def _recommendations_for_profile(profile: dict[str, Any], posture: str) -> List[dict[str, Any]]:
    recommendations: List[dict[str, Any]] = []
    metrics = profile["metrics"]
    drift = profile["drift"]
    fail_reasons = profile.get("fail_reasons", [])

    if posture == "ready":
        recommendations.append(
            {
                "priority": 3,
                "category": "maintain",
                "action": "Keep baseline and scorecard artifact synced at each milestone.",
            }
        )
        return recommendations

    if drift["removed_mappings"] > 0:
        recommendations.append(
            {
                "priority": 1,
                "category": "restore_removed_mappings",
                "action": "Restore removed mappings or explicitly approve/remap before release.",
            }
        )

    if drift["changed_mappings"] > 0:
        recommendations.append(
            {
                "priority": 2,
                "category": "review_changed_mappings",
                "action": "Review changed mappings against approved baseline and update rationale.",
            }
        )

    if float(metrics["capability_coverage_pct"]) < 100.0:
        recommendations.append(
            {
                "priority": 2,
                "category": "capability_coverage",
                "action": "Close missing capability coverage gaps before release posture is raised.",
            }
        )

    if float(metrics["validation_pass_rate_pct"]) < 100.0:
        recommendations.append(
            {
                "priority": 2,
                "category": "validation_reliability",
                "action": "Increase validation pass-rate to 100% for release-ready confidence.",
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "priority": 3,
                "category": "observe",
                "action": "Monitor profile in watch posture and re-evaluate on next scorecard update.",
            }
        )

    for reason in fail_reasons:
        recommendations.append(
            {
                "priority": 2,
                "category": "threshold_fail_reason",
                "action": f"Address threshold failure reason: {reason}",
            }
        )

    recommendations.sort(key=lambda item: (item["priority"], item["category"]))
    return recommendations


def evaluate_readiness_gates(scorecard_payload: dict[str, Any]) -> dict[str, Any]:
    profiles_out: List[dict[str, Any]] = []
    overall_posture = "ready"

    for profile in sorted(scorecard_payload["profiles"], key=lambda item: item["profile"]):
        posture = evaluate_profile_posture(profile)
        recommendations = _recommendations_for_profile(profile, posture)

        if posture == "block":
            overall_posture = "block"
        elif posture == "watch" and overall_posture == "ready":
            overall_posture = "watch"

        profiles_out.append(
            {
                "profile": profile["profile"],
                "posture": posture,
                "metrics": profile["metrics"],
                "drift": profile["drift"],
                "fail_triggered": profile["fail_triggered"],
                "recommendations": recommendations,
            }
        )

    return {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overall_posture": overall_posture,
        "profiles": profiles_out,
    }


def write_readiness_artifact(readiness: dict[str, Any], output_path: Path | None = None) -> Path:
    target = output_path or default_output_path()
    target.write_text(json.dumps(readiness, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def render_readiness_summary(readiness: dict[str, Any]) -> str:
    lines = [
        "| Profile | Posture | Score | Fail Trigger |",
        "|---|---|---:|---|",
    ]
    for profile in readiness["profiles"]:
        lines.append(
            "| {profile} | {posture} | {score:.2f} | {failed} |".format(
                profile=profile["profile"],
                posture=profile["posture"],
                score=float(profile["metrics"]["conformance_score_pct"]),
                failed="yes" if bool(profile["fail_triggered"]) else "no",
            )
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate readiness gates from scorecard artifacts.")
    parser.add_argument("--scorecard-path", type=Path, default=None, help="Optional scorecard artifact input path.")
    parser.add_argument("--output-path", type=Path, default=None, help="Optional readiness artifact output path.")
    args = parser.parse_args()

    scorecards = load_scorecard_artifact(args.scorecard_path)
    readiness = evaluate_readiness_gates(scorecards)
    output_path = write_readiness_artifact(readiness, args.output_path)

    print("Connector readiness gate summary")
    print(render_readiness_summary(readiness))
    print(f"Overall posture: {readiness['overall_posture']}")
    print(f"Artifact: {output_path}")

    return 2 if readiness["overall_posture"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())