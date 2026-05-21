from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_FILES = [
    "earnings_provider_selection_manifest.json",
    "provider_requirements.csv",
    "candidate_provider_roles.csv",
    "coverage_quality_policy.csv",
    "blocked_actions.csv",
    "earnings_provider_selection_summary.md",
]

REQUIRED_MANIFEST_FIELDS = {
    "status",
    "gate_id",
    "trial_id",
    "no_provider_query",
    "no_network_call",
    "no_market_data_download",
    "no_extractor_implementation",
    "no_oos_execution",
    "no_backtest",
    "no_paper_trading",
    "no_live_trading",
    "no_strategy_promotion",
    "requires_separate_probe_approval",
}

REQUIRED_REQUIREMENTS = {
    "historical_earnings_calendar",
    "report_time_flag",
    "unspecified_rate_audit",
    "point_in_time_symbols",
    "delisted_symbol_handling",
    "event_timestamp_timezone",
    "licensing_retention_policy",
    "rate_limit_policy",
    "coverage_window_declared",
    "missingness_policy",
}

REQUIRED_PROVIDER_ROLES = {
    "primary_earnings_calendar",
    "secondary_crosscheck",
    "pit_universe_source",
    "price_volume_source",
}

REQUIRED_QUALITY_METRICS = {
    "max_unspecified_report_time_rate",
    "min_report_time_coverage_rate",
    "min_valid_rolling_zscore_observations",
    "earnings_scope",
    "dmt_policy",
    "amc_mapping",
    "bmo_mapping",
    "ecdf_bootstrap_ci",
}

REQUIRED_BLOCKED_ACTIONS = {
    "query_provider",
    "implement_extractor",
    "download_market_data",
    "use_static_today_ticker_list",
    "accept_unspecified_report_time",
    "widen_to_universal_anomaly_days",
    "run_oos",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
}


def validate_xmom_earnings_provider_selection(gate_dir: str | Path) -> dict[str, Any]:
    path = Path(gate_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "gate_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(path / "earnings_provider_selection_manifest.json", checks, "json_readable:earnings_provider_selection_manifest.json")
    requirements = _read_csv(path / "provider_requirements.csv", checks, "csv_readable:provider_requirements.csv")
    roles = _read_csv(path / "candidate_provider_roles.csv", checks, "csv_readable:candidate_provider_roles.csv")
    quality = _read_csv(path / "coverage_quality_policy.csv", checks, "csv_readable:coverage_quality_policy.csv")
    blocked = _read_csv(path / "blocked_actions.csv", checks, "csv_readable:blocked_actions.csv")
    summary = _read_text(path / "earnings_provider_selection_summary.md", checks, "markdown_readable:earnings_provider_selection_summary.md")

    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)
    if requirements is not None:
        _validate_requirements(requirements, checks)
    if roles is not None:
        _validate_roles(roles, checks)
    if quality is not None:
        _validate_quality(quality, checks)
    if blocked is not None:
        _validate_blocked_actions(blocked, checks)
    if summary is not None:
        _validate_summary(summary, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_xmom_earnings_provider_selection(args.gate_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate XMOM earnings provider selection gate artifacts.")
    parser.add_argument("--gate-dir", required=True)
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))
    _add_check(checks, "manifest_required_fields", not missing, f"missing={missing}")
    if missing:
        return
    status_ok = manifest.get("status") == "SPEC_ONLY_NOT_QUERIED"
    no_execution = all(
        manifest.get(flag) is True
        for flag in [
            "no_provider_query",
            "no_network_call",
            "no_market_data_download",
            "no_extractor_implementation",
            "no_oos_execution",
            "no_backtest",
            "no_paper_trading",
            "no_live_trading",
            "no_strategy_promotion",
            "requires_separate_probe_approval",
        ]
    )
    _add_check(checks, "manifest_status_spec_only_not_queried", status_ok, f"status={manifest.get('status')}")
    _add_check(checks, "manifest_no_execution_or_query_flags", no_execution, f"no_execution={no_execution}")


def _validate_requirements(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"requirement_id", "severity", "required_status", "pass_condition", "failure_action"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "requirements_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    requirement_ids = set(frame["requirement_id"].astype(str))
    missing_ids = sorted(REQUIRED_REQUIREMENTS - requirement_ids)
    critical = frame[frame["severity"].astype(str).str.lower().eq("critical")]
    critical_blocking = critical["failure_action"].astype(str).str.lower().isin({"block_extractor", "block_probe"}).all()
    all_required = frame["required_status"].astype(str).str.lower().eq("required").all()
    _add_check(checks, "requirements_required_ids", not missing_ids, f"missing={missing_ids}")
    _add_check(checks, "requirements_all_required", bool(all_required), f"all_required={bool(all_required)}")
    _add_check(checks, "requirements_critical_are_blocking", bool(critical_blocking), f"critical_blocking={bool(critical_blocking)}")


def _validate_roles(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"role", "status", "allowed_use", "blocked_use", "notes"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "roles_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    roles = set(frame["role"].astype(str))
    missing_roles = sorted(REQUIRED_PROVIDER_ROLES - roles)
    primary_unselected = str(frame.loc[frame["role"].astype(str).eq("primary_earnings_calendar"), "status"].iloc[0]) == "unselected"
    static_today_blocked = frame["blocked_use"].astype(str).str.contains("today_static_universe_backfill|execution_without_coverage_audit", regex=True).any()
    _add_check(checks, "roles_required_set", not missing_roles, f"missing={missing_roles}")
    _add_check(checks, "roles_primary_not_preselected", primary_unselected, f"primary_unselected={primary_unselected}")
    _add_check(checks, "roles_static_today_or_unaudited_execution_blocked", bool(static_today_blocked), f"blocked={bool(static_today_blocked)}")


def _validate_quality(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"metric", "status", "threshold", "measurement_policy", "failure_action"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "quality_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    rows = {str(row["metric"]): row for _, row in frame.iterrows()}
    missing_metrics = sorted(REQUIRED_QUALITY_METRICS - set(rows))
    all_locked = frame["status"].astype(str).str.lower().eq("locked").all()
    _add_check(checks, "quality_required_metrics", not missing_metrics, f"missing={missing_metrics}")
    _add_check(checks, "quality_all_locked", bool(all_locked), f"all_locked={bool(all_locked)}")
    if missing_metrics:
        return
    unspecified_ok = float(rows["max_unspecified_report_time_rate"]["threshold"]) <= 0.30
    coverage_ok = float(rows["min_report_time_coverage_rate"]["threshold"]) >= 0.70
    min_periods_ok = int(rows["min_valid_rolling_zscore_observations"]["threshold"]) >= 45
    scope_ok = str(rows["earnings_scope"]["threshold"]) == "earnings_only"
    dmt_ok = str(rows["dmt_policy"]["threshold"]) == "purge"
    mapping_ok = str(rows["amc_mapping"]["threshold"]) == "next_trading_session" and str(rows["bmo_mapping"]["threshold"]) == "same_trading_session"
    bootstrap_ok = str(rows["ecdf_bootstrap_ci"]["threshold"]) == "required"
    _add_check(checks, "quality_unspecified_rate_threshold", unspecified_ok, f"threshold={rows['max_unspecified_report_time_rate']['threshold']}")
    _add_check(checks, "quality_report_time_coverage_threshold", coverage_ok, f"threshold={rows['min_report_time_coverage_rate']['threshold']}")
    _add_check(checks, "quality_min_periods_threshold", min_periods_ok, f"threshold={rows['min_valid_rolling_zscore_observations']['threshold']}")
    _add_check(checks, "quality_earnings_only_scope", scope_ok, f"scope={rows['earnings_scope']['threshold']}")
    _add_check(checks, "quality_reaction_session_policy", dmt_ok and mapping_ok, f"dmt={rows['dmt_policy']['threshold']}; amc={rows['amc_mapping']['threshold']}; bmo={rows['bmo_mapping']['threshold']}")
    _add_check(checks, "quality_ecdf_bootstrap_required", bootstrap_ok, f"bootstrap={rows['ecdf_bootstrap_ci']['threshold']}")


def _validate_blocked_actions(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"action", "status", "reason"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "blocked_actions_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    actions = set(frame["action"].astype(str))
    missing_actions = sorted(REQUIRED_BLOCKED_ACTIONS - actions)
    all_blocked = frame["status"].astype(str).str.lower().eq("blocked").all()
    _add_check(checks, "blocked_actions_required_set", not missing_actions, f"missing={missing_actions}")
    _add_check(checks, "blocked_actions_all_blocked", bool(all_blocked), f"all_blocked={bool(all_blocked)}")


def _validate_summary(text: str, checks: list[dict[str, str]]) -> None:
    lower = text.lower()
    _add_check(checks, "summary_status_spec_only_not_queried", "spec_only_not_queried" in lower, "status present")
    _add_check(checks, "summary_reaction_session_contract", all(item in lower for item in ["bmo -> same", "amc -> next", "dmt -> purge", "unspecified -> purge"]), "reaction-session contract present")
    _add_check(checks, "summary_no_query_authorization", "does not authorize provider queries" in lower, "no query authorization")


def _read_json(path: Path, checks: list[dict[str, str]], name: str) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {type(exc).__name__}: {exc}")
        return None
    _add_check(checks, name, True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]], name: str) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {type(exc).__name__}: {exc}")
        return None
    _add_check(checks, name, not frame.empty and bool(frame.columns.tolist()), f"{path}: rows={len(frame)}; columns={len(frame.columns)}")
    return frame


def _read_text(path: Path, checks: list[dict[str, str]], name: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {type(exc).__name__}: {exc}")
        return None
    _add_check(checks, name, bool(text.strip()), f"{path}: chars={len(text)}")
    return text


def _add_check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": str(detail)})


def _report(path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "gate_dir": str(path),
        "status": "fail" if failed else "pass",
        "gate_decision": "EARNINGS_PROVIDER_SELECTION_GATE_PASS" if failed == 0 else "EARNINGS_PROVIDER_SELECTION_GATE_FAIL",
        "provider_query_performed": False,
        "network_call_performed": False,
        "market_data_downloaded": False,
        "extractor_implemented": False,
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
