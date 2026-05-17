from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

PropertyStatus = Literal["pass", "fail", "insufficient_evidence"]


@dataclass(frozen=True)
class NctrlPropertyCheckResult:
    property_id: str
    status: PropertyStatus
    evidence: str
    notes: str = ""


def build_nctrl_property_check_report(trial_id: str, checks: list[NctrlPropertyCheckResult]) -> dict[str, object]:
    properties = [
        {
            "property": str(check.property_id),
            "status": str(check.status),
            "evidence": str(check.evidence),
            "notes": str(check.notes),
        }
        for check in checks
    ]
    return {
        "trial_id": str(trial_id),
        "overall_status": _overall_status(checks),
        "properties": properties,
    }


def write_nctrl_property_check_report_markdown(
    trial_id: str,
    checks: list[NctrlPropertyCheckResult],
    output_path: str | Path,
) -> dict[str, object]:
    report = build_nctrl_property_check_report(trial_id, checks)
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_to_markdown(report), encoding="utf-8")
    return report


def _overall_status(checks: list[NctrlPropertyCheckResult]) -> str:
    statuses = [check.status for check in checks]
    if not statuses:
        return "insufficient_evidence"
    if "fail" in statuses:
        return "fail"
    if "insufficient_evidence" in statuses:
        return "insufficient_evidence"
    return "pass"


def _to_markdown(report: dict[str, object]) -> str:
    lines = [
        f"# {report['trial_id']} Property Check Report",
        "",
        f"Overall status: `{report['overall_status']}`",
        "",
        "| Property | Status | Evidence | Notes |",
        "| --- | --- | --- | --- |",
    ]
    for row in report["properties"]:
        if isinstance(row, dict):
            lines.append(
                "| "
                + " | ".join(
                    [
                        _escape_markdown_cell(row.get("property", "")),
                        _escape_markdown_cell(row.get("status", "")),
                        _escape_markdown_cell(row.get("evidence", "")),
                        _escape_markdown_cell(row.get("notes", "")),
                    ]
                )
                + " |"
            )
    return "\n".join(lines) + "\n"


def _escape_markdown_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
