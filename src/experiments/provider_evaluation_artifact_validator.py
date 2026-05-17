from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "provider_manifest.json",
    "provider_requirement_table.csv",
    "provider_event_audit_table.csv",
    "license_notes.md",
    "query_cost_estimate.md",
    "raw_responses_manifest.csv",
    "snapshot_hashes.csv",
    "provider_evaluation_summary.md",
]

REQUIRED_MANIFEST_FIELDS = [
    "provider_name",
    "provider_slug",
    "account_type",
    "payment_authorized",
    "payment_cap_usd",
    "execution_date",
    "operator",
    "frozen_panel_report",
    "panel_expansion_report",
    "terms_url",
    "license_storage_verdict",
    "data_retention_allowed",
    "dataset_names",
    "api_versions",
    "query_budget_estimate_usd",
    "actual_query_cost_usd",
    "provider_query_executed",
]

REQUIRED_EVENT_AUDIT_COLUMNS = [
    "event_id",
    "provider_name",
    "provider_symbol_resolves",
    "historical_identifier_stable",
    "event_window_available",
    "raw_ohlcv_available",
    "adjusted_ohlcv_available",
    "corporate_action_metadata_available",
    "halt_or_suspension_visible",
    "delisted_history_available",
    "point_in_time_universe_supported",
    "licensing_allows_research_storage",
    "pipeline_integration_complexity",
    "severity",
    "verdict",
    "notes",
]

FROZEN_EVENT_IDS = {f"DPE-{index:03d}" for index in range(1, 11)}


def validate_provider_evaluation_artifacts(evaluation_dir: str | Path) -> dict[str, Any]:
    path = Path(evaluation_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "evaluation_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(path / "provider_manifest.json", checks, "manifest_json")
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)

    event_audit = None
    for filename in REQUIRED_FILES:
        file_path = path / filename
        if filename.endswith(".csv") and file_path.exists():
            frame = _read_csv(file_path, checks, f"csv_readable:{filename}")
            if filename == "provider_event_audit_table.csv":
                event_audit = frame
        if filename.endswith(".md") and file_path.exists():
            _read_text_file(file_path, checks, f"markdown_readable:{filename}")

    if event_audit is not None:
        _validate_event_audit_table(event_audit, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_provider_evaluation_artifacts(args.evaluation_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate expected artifacts in a provider evaluation directory.")
    parser.add_argument("--evaluation-dir", required=True, help="Provider evaluation artifact directory to validate.")
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    dataset_names_ok = isinstance(manifest.get("dataset_names"), list)
    api_versions_ok = isinstance(manifest.get("api_versions"), list)
    payment_authorized_ok = manifest.get("payment_authorized") is False
    payment_cap_ok = pd.to_numeric(pd.Series([manifest.get("payment_cap_usd")]), errors="coerce").notna().iat[0]
    query_executed_ok = isinstance(manifest.get("provider_query_executed"), bool)
    _add_check(
        checks,
        "manifest_required_fields",
        not missing and dataset_names_ok and api_versions_ok and payment_cap_ok and query_executed_ok,
        f"missing={missing}; dataset_names_ok={dataset_names_ok}; api_versions_ok={api_versions_ok}; payment_cap_ok={payment_cap_ok}; provider_query_executed_ok={query_executed_ok}",
    )
    _add_check(
        checks,
        "manifest_no_payment_authorized",
        payment_authorized_ok,
        f"payment_authorized={manifest.get('payment_authorized')}; payment_cap_usd={manifest.get('payment_cap_usd')}",
    )


def _validate_event_audit_table(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    columns = set(frame.columns)
    missing_columns = [column for column in REQUIRED_EVENT_AUDIT_COLUMNS if column not in columns]
    _add_check(checks, "event_audit_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    event_ids = {str(value) for value in frame["event_id"].dropna().tolist()}
    missing_events = sorted(FROZEN_EVENT_IDS - event_ids)
    extra_events = sorted(event_ids - FROZEN_EVENT_IDS)
    _add_check(checks, "event_panel_complete", not missing_events and not extra_events, f"missing={missing_events}; extra={extra_events}")


def _read_json(path: Path, checks: list[dict[str, str]], name: str) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]], name: str) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, not frame.empty and bool(frame.columns.tolist()), f"{path}: rows={len(frame)}; columns={len(frame.columns)}")
    return frame


def _read_text_file(path: Path, checks: list[dict[str, str]], name: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, bool(text.strip()), f"{path}: chars={len(text)}")
    return text


def _add_check(checks: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": str(detail)})


def _report(path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = [check for check in checks if check["status"] == "fail"]
    return {
        "evaluation_dir": str(path),
        "status": "pass" if not failed else "fail",
        "summary": {"total": len(checks), "failed": len(failed), "passed": len(checks) - len(failed)},
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
