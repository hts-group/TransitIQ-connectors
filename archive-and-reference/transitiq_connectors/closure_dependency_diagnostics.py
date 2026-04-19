"""Evaluate connector closure dependencies and emit prioritized remediation diagnostics."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_DEPENDENCY_STATUS = {"open", "consumed", "closed"}
VALID_SEVERITY = {"critical", "high", "medium", "low"}


def default_dependency_input_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "connector-closure-dependencies.input.json"


def default_release_candidate_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "connector-release-candidate-gates.latest.json"


def default_output_path() -> Path:
    return Path(__file__).resolve().parents[1] / "docs" / "connector-closure-remediation.latest.json"


def _parse_utc_timestamp(raw: Any, field_name: str) -> datetime:
    if not isinstance(raw, str):
        raise ValueError(f"Malformed dependency input: {field_name} must be a UTC timestamp string.")
    try:
        return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(f"Malformed dependency input: {field_name} must use format YYYY-MM-DDTHH:MM:SSZ.") from exc


def load_dependency_input(path: Path | None = None) -> dict[str, Any]:
    input_path = path or default_dependency_input_path()
    payload = json.loads(input_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Malformed dependency input: expected top-level object.")

    dependencies = payload.get("dependencies")
    if not isinstance(dependencies, list):
        raise ValueError("Malformed dependency input: 'dependencies' must be a list.")

    normalized_dependencies: list[dict[str, Any]] = []
    for idx, dependency in enumerate(dependencies):
        if not isinstance(dependency, dict):
            raise ValueError(f"Malformed dependency input: dependencies[{idx}] must be an object.")

        for required_string in ("id", "name", "owner", "status", "severity", "remediation"):
            if not isinstance(dependency.get(required_string), str):
                raise ValueError(
                    f"Malformed dependency input: dependencies[{idx}].{required_string} must be a string."
                )

        status = dependency["status"]
        if status not in VALID_DEPENDENCY_STATUS:
            raise ValueError(
                f"Malformed dependency input: dependencies[{idx}].status must be one of open/consumed/closed."
            )

        severity = dependency["severity"]
        if severity not in VALID_SEVERITY:
            raise ValueError(
                f"Malformed dependency input: dependencies[{idx}].severity must be one of critical/high/medium/low."
            )

        due_utc = _parse_utc_timestamp(dependency.get("due_utc"), f"dependencies[{idx}].due_utc")
        canonical_contract = dependency.get("canonical_contract")
        if not isinstance(canonical_contract, bool):
            raise ValueError(
                f"Malformed dependency input: dependencies[{idx}].canonical_contract must be a boolean."
            )

        normalized_dependencies.append(
            {
                "id": dependency["id"],
                "name": dependency["name"],
                "owner": dependency["owner"],
                "status": status,
                "severity": severity,
                "due_utc": due_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "due_datetime": due_utc,
                "canonical_contract": canonical_contract,
                "remediation": dependency["remediation"],
            }
        )

    return {"dependencies": normalized_dependencies}


def load_release_candidate_gate(path: Path | None = None) -> dict[str, Any]:
    release_path = path or default_release_candidate_path()
    payload = json.loads(release_path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Malformed release-candidate artifact: expected top-level object.")

    disposition = payload.get("release_candidate_disposition")
    if disposition not in {"ready", "watch", "block"}:
        raise ValueError(
            "Malformed release-candidate artifact: release_candidate_disposition must be one of ready/watch/block."
        )

    blockers = payload.get("prioritized_blockers")
    if not isinstance(blockers, list):
        raise ValueError("Malformed release-candidate artifact: prioritized_blockers must be a list.")

    return payload


def _severity_rank(severity: str) -> int:
    return {
        "critical": 1,
        "high": 2,
        "medium": 3,
        "low": 4,
    }[severity]


def _dependency_due_datetime(dependency: dict[str, Any]) -> datetime:
    due_datetime = dependency.get("due_datetime")
    if isinstance(due_datetime, datetime):
        return due_datetime
    return _parse_utc_timestamp(dependency.get("due_utc"), "dependency.due_utc")


def evaluate_closure_diagnostics(
    dependency_input: dict[str, Any], release_candidate_gate: dict[str, Any], now_utc: datetime | None = None
) -> dict[str, Any]:
    now = now_utc or datetime.now(timezone.utc)
    dependencies = dependency_input["dependencies"]

    unresolved: list[dict[str, Any]] = []
    consumed_or_closed = 0
    for dependency in dependencies:
        if dependency["status"] in {"closed", "consumed"}:
            consumed_or_closed += 1
            continue
        unresolved.append(dependency)

    canonical_open = [item for item in unresolved if item["canonical_contract"]]
    overdue = [item for item in unresolved if _dependency_due_datetime(item) < now]

    remediation: list[dict[str, Any]] = []
    for dependency in unresolved:
        is_overdue = _dependency_due_datetime(dependency) < now
        priority = _severity_rank(dependency["severity"])
        if dependency["canonical_contract"] and priority > 1:
            priority -= 1
        if is_overdue and priority > 1:
            priority -= 1

        remediation.append(
            {
                "priority": priority,
                "dependency_id": dependency["id"],
                "dependency": dependency["name"],
                "owner": dependency["owner"],
                "severity": dependency["severity"],
                "status": dependency["status"],
                "canonical_contract": dependency["canonical_contract"],
                "due_utc": dependency["due_utc"],
                "overdue": is_overdue,
                "recommended_action": dependency["remediation"],
            }
        )

    remediation.sort(
        key=lambda item: (
            item["priority"],
            0 if item["overdue"] else 1,
            0 if item["canonical_contract"] else 1,
            item["due_utc"],
            item["dependency"],
        )
    )

    release_disposition = release_candidate_gate["release_candidate_disposition"]
    if release_disposition == "block":
        closure_posture = "block"
    elif overdue:
        closure_posture = "block"
    elif canonical_open:
        closure_posture = "watch"
    elif unresolved:
        closure_posture = "watch"
    else:
        closure_posture = "ready"

    return {
        "generated_at_utc": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "release_candidate_disposition": release_disposition,
        "closure_posture": closure_posture,
        "summary": {
            "total_dependencies": len(dependencies),
            "resolved_dependencies": consumed_or_closed,
            "open_dependencies": len(unresolved),
            "open_canonical_contract_dependencies": len(canonical_open),
            "overdue_dependencies": len(overdue),
            "release_candidate_blockers": len(release_candidate_gate["prioritized_blockers"]),
        },
        "prioritized_remediation": remediation,
    }


def write_closure_diagnostics_artifact(diagnostics: dict[str, Any], output_path: Path | None = None) -> Path:
    target = output_path or default_output_path()
    target.write_text(json.dumps(diagnostics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def render_diagnostics_summary(diagnostics: dict[str, Any]) -> str:
    lines = [
        "| Closure Posture | Open | Canonical Open | Overdue |",
        "|---|---:|---:|---:|",
        "| {posture} | {open_count} | {canonical_open} | {overdue} |".format(
            posture=diagnostics["closure_posture"],
            open_count=diagnostics["summary"]["open_dependencies"],
            canonical_open=diagnostics["summary"]["open_canonical_contract_dependencies"],
            overdue=diagnostics["summary"]["overdue_dependencies"],
        ),
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate connector closure dependencies and remediation diagnostics."
    )
    parser.add_argument(
        "--dependency-input-path",
        type=Path,
        default=None,
        help="Optional closure dependency input JSON path.",
    )
    parser.add_argument(
        "--release-candidate-path",
        type=Path,
        default=None,
        help="Optional release-candidate artifact input path.",
    )
    parser.add_argument("--output-path", type=Path, default=None, help="Optional diagnostics artifact output path.")
    args = parser.parse_args()

    dependency_input = load_dependency_input(args.dependency_input_path)
    release_candidate = load_release_candidate_gate(args.release_candidate_path)
    diagnostics = evaluate_closure_diagnostics(dependency_input, release_candidate)
    output_path = write_closure_diagnostics_artifact(diagnostics, args.output_path)

    print("Connector closure dependency diagnostics")
    print(render_diagnostics_summary(diagnostics))
    print(f"Release candidate disposition: {diagnostics['release_candidate_disposition']}")
    print(f"Closure posture: {diagnostics['closure_posture']}")
    print(f"Prioritized remediation items: {len(diagnostics['prioritized_remediation'])}")
    print(f"Artifact: {output_path}")

    return 2 if diagnostics["closure_posture"] == "block" else 0


if __name__ == "__main__":
    raise SystemExit(main())