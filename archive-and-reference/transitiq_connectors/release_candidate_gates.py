"""Aggregate per-profile readiness outputs into release-candidate disposition."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_POSTURES = {"ready", "watch", "block"}


def default_readiness_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "connector-readiness-gates.latest.json"


def default_output_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "connector-release-candidate-gates.latest.json"


def load_readiness_artifact(path: Path | None = None) -> dict[str, Any]:
    readiness_path = path or default_readiness_path()
    payload = json.loads(readiness_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Malformed readiness artifact: expected top-level object.")

    profiles = payload.get("profiles")
    if not isinstance(profiles, list):
        raise ValueError("Malformed readiness artifact: 'profiles' must be a list.")

    for idx, profile in enumerate(profiles):
        if not isinstance(profile, dict):
            raise ValueError(f"Malformed readiness artifact: profiles[{idx}] must be an object.")

        if not isinstance(profile.get("profile"), str):
            raise ValueError(f"Malformed readiness artifact: profiles[{idx}].profile must be a string.")

        posture = profile.get("posture")
        if posture not in VALID_POSTURES:
            raise ValueError(
                f"Malformed readiness artifact: profiles[{idx}].posture must be one of ready/watch/block."
            )

        if not isinstance(profile.get("fail_triggered"), bool):
            raise ValueError(f"Malformed readiness artifact: profiles[{idx}].fail_triggered must be a boolean.")

        metrics = profile.get("metrics")
        if not isinstance(metrics, dict):
            raise ValueError(f"Malformed readiness artifact: profiles[{idx}].metrics must be an object.")
        if not isinstance(metrics.get("conformance_score_pct"), (int, float)):
            raise ValueError(
                f"Malformed readiness artifact: profiles[{idx}].metrics.conformance_score_pct must be numeric."
            )

        recommendations = profile.get("recommendations")
        if not isinstance(recommendations, list):
            raise ValueError(f"Malformed readiness artifact: profiles[{idx}].recommendations must be a list.")

        for rec_idx, recommendation in enumerate(recommendations):
            if not isinstance(recommendation, dict):
                raise ValueError(
                    "Malformed readiness artifact: "
                    f"profiles[{idx}].recommendations[{rec_idx}] must be an object."
                )
            if not isinstance(recommendation.get("priority"), int):
                raise ValueError(
                    "Malformed readiness artifact: "
                    f"profiles[{idx}].recommendations[{rec_idx}].priority must be an integer."
                )
            if not isinstance(recommendation.get("category"), str):
                raise ValueError(
                    "Malformed readiness artifact: "
                    f"profiles[{idx}].recommendations[{rec_idx}].category must be a string."
                )
            if not isinstance(recommendation.get("action"), str):
                raise ValueError(
                    "Malformed readiness artifact: "
                    f"profiles[{idx}].recommendations[{rec_idx}].action must be a string."
                )

    return payload


def _disposition_from_profiles(profiles: list[dict[str, Any]]) -> str:
    postures = {item["posture"] for item in profiles}
    if "block" in postures:
        return "block"
    if "watch" in postures:
        return "watch"
    return "ready"


def _posture_rank(posture: str) -> int:
    if posture == "block":
        return 0
    if posture == "watch":
        return 1
    return 2


def aggregate_release_candidate_gate(readiness: dict[str, Any]) -> dict[str, Any]:
    profiles_in = sorted(readiness["profiles"], key=lambda item: item["profile"])

    summary_counts = {"ready": 0, "watch": 0, "block": 0}
    blocker_candidates: list[dict[str, Any]] = []
    profile_rollup: list[dict[str, Any]] = []

    for profile in profiles_in:
        posture = profile["posture"]
        summary_counts[posture] += 1

        profile_rollup.append(
            {
                "profile": profile["profile"],
                "posture": posture,
                "conformance_score_pct": round(float(profile["metrics"]["conformance_score_pct"]), 2),
                "fail_triggered": bool(profile["fail_triggered"]),
            }
        )

        if posture == "ready":
            continue

        for recommendation in profile["recommendations"]:
            blocker_candidates.append(
                {
                    "profile": profile["profile"],
                    "posture": posture,
                    "priority": int(recommendation["priority"]),
                    "category": recommendation["category"],
                    "action": recommendation["action"],
                }
            )

    blocker_candidates.sort(
        key=lambda item: (
            item["priority"],
            _posture_rank(item["posture"]),
            item["profile"],
            item["category"],
            item["action"],
        )
    )

    return {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_readiness_generated_at_utc": readiness.get("generated_at_utc"),
        "release_candidate_disposition": _disposition_from_profiles(profiles_in),
        "summary": {
            "total_profiles": len(profiles_in),
            "ready_profiles": summary_counts["ready"],
            "watch_profiles": summary_counts["watch"],
            "block_profiles": summary_counts["block"],
        },
        "profiles": profile_rollup,
        "prioritized_blockers": blocker_candidates,
    }


def write_release_candidate_artifact(
    release_candidate_gate: dict[str, Any], output_path: Path | None = None
) -> Path:
    target = output_path or default_output_path()
    target.write_text(json.dumps(release_candidate_gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def render_release_candidate_summary(release_candidate_gate: dict[str, Any]) -> str:
    lines = [
        "| Profile | Posture | Score | Fail Trigger |",
        "|---|---|---:|---|",
    ]

    for profile in release_candidate_gate["profiles"]:
        lines.append(
            "| {profile} | {posture} | {score:.2f} | {failed} |".format(
                profile=profile["profile"],
                posture=profile["posture"],
                score=float(profile["conformance_score_pct"]),
                failed="yes" if profile["fail_triggered"] else "no",
            )
        )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aggregate per-profile readiness outputs into release-candidate gate disposition."
    )
    parser.add_argument("--readiness-path", type=Path, default=None, help="Optional readiness artifact input path.")
    parser.add_argument("--output-path", type=Path, default=None, help="Optional release-candidate output path.")
    args = parser.parse_args()

    readiness = load_readiness_artifact(args.readiness_path)
    release_candidate_gate = aggregate_release_candidate_gate(readiness)
    output_path = write_release_candidate_artifact(release_candidate_gate, args.output_path)

    print("Connector release-candidate gate summary")
    print(render_release_candidate_summary(release_candidate_gate))
    print(f"Disposition: {release_candidate_gate['release_candidate_disposition']}")
    print(f"Prioritized blockers: {len(release_candidate_gate['prioritized_blockers'])}")
    print(f"Artifact: {output_path}")

    return 2 if release_candidate_gate["release_candidate_disposition"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())