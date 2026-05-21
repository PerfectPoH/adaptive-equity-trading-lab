from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_FILES = [
    "single_probe_approval_manifest.json",
    "single_probe_scope.csv",
    "expected_probe_output_schema.csv",
    "single_probe_stop_rules.csv",
    "single_probe_blocked_actions.csv",
    "single_probe_approval_summary.md",
]

REQUIRED_SCOPE_FIELDS = {
    "provider",
    "symbol",
    "endpoint",
    "lookback_window",
    "raw_payload_retention",
    "max_provider_calls",
    "output_directory",
    "trial_ledger_entry",
}

REQUIRED_OUTPUT_FIELDS = {
    "provider",
    "symbol",
    "endpoint",
    "query_timestamp_utc",
    "event_count",
    "report_time_values_seen",
    "unspecified_count",
    "unspecified_rate",
    "coverage_start",
    "coverage_end",
    "raw_payload_saved",
    "secret_values_present",
    "decision",
}

REQUIRED_STOP_RULES = {
    "provider_auth_error",
    "rate_limit",
    "raw_payload_needed_for_debug",
    "secret_detected_in_output",
    "endpoint_missing_report_time",
    "more_than_one_symbol_requested",
    "more_than_one_provider_call_requested",
}

REQUIRED_BLOCKED_ACTIONS = {
    "execute_probe",
    "query_more_than_one_symbol",
    "query_more_than_one_provider",
    "query_price_volume_data",
    "save_raw_payload",
    "implement_extractor",
    "download_market_data",
    "run_oos",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
}


def validate_xmom_earnings_single_probe_approval(artifact_dir: str | Path) -> dict[str, Any]:
    root = Path(artifact_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "artifact_dir_exists", root.exists() and root.is_dir(), str(root))
    if not root.exists() or not root.is_dir():
        return _report(root, checks)

    for filename in REQUIRED_FILES:
        path = root / filename
        _add_check(checks, f"required_file:{filename}", path.exists() and path.is_file(), str(path))

    manifest = _read_json(root / "single_probe_approval_manifest.json", checks, "json_readable:single_probe_approval_manifest.json")
    scope = _read_csv(root / "single_probe_scope.csv", checks, "csv_readable:single_probe_scope.csv")
    output = _read_csv(root / "expected_probe_output_schema.csv", checks, "csv_readable:expected_probe_output_schema.csv")
    stop_rules = _read_csv(root / "single_probe_stop_rules.csv", checks, "csv_readable:single_probe_stop_rules.csv")
    blocked = _read_csv(root / "single_probe_blocked_actions.csv", checks, "csv_readable:single_probe_blocked_actions.csv")
    summary = _read_text(root / "single_probe_approval_summary.md", checks, "markdown_readable:single_probe_approval_summary.md")

    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)
    if scope is not None:
        _validate_scope(scope, checks)
    if output is not None:
        _validate_output_schema(output, checks)
    if stop_rules is not None:
        _validate_stop_rules(stop_rules, checks)
    if blocked is not None:
        _validate_blocked_actions(blocked, checks)
    if summary is not None:
        _validate_summary(summary, checks)

    return _report(root, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_xmom_earnings_single_probe_approval(args.artifact_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate XMOM earnings single-probe approval artifact.")
    parser.add_argument("--artifact-dir", required=True)
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    status_ok = manifest.get("status") == "SPEC_ONLY_AWAITING_SEPARATE_APPROVAL"
    approval_ok = manifest.get("separate_user_approval_required") is True and manifest.get("approval_status") == "not_granted"
    no_execution = all(
        manifest.get(flag) is False
        for flag in [
            "provider_query_performed",
            "network_call_performed",
            "market_data_downloaded",
            "extractor_implemented",
            "backtest_performed",
            "strategy_promotion_performed",
            "secret_values_disclosed",
        ]
    )
    bounded = manifest.get("max_provider_count") == 1 and manifest.get("max_symbol_count") == 1 and manifest.get("max_endpoint_count") == 1
    raw_blocked = manifest.get("raw_payload_retention_allowed") is False
    _add_check(checks, "manifest_status_awaiting_approval", status_ok, f"status={manifest.get('status')}")
    _add_check(checks, "manifest_separate_approval_not_granted", approval_ok, f"approval={manifest.get('approval_status')}")
    _add_check(checks, "manifest_no_execution_or_secret_flags", no_execution, f"no_execution={no_execution}")
    _add_check(checks, "manifest_probe_scope_bounded_to_one", bounded, f"provider={manifest.get('max_provider_count')}; symbol={manifest.get('max_symbol_count')}; endpoint={manifest.get('max_endpoint_count')}")
    _add_check(checks, "manifest_raw_retention_blocked", raw_blocked, f"raw_payload_retention_allowed={manifest.get('raw_payload_retention_allowed')}")


def _validate_scope(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"field", "value", "status", "notes"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "scope_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    rows = {str(row["field"]): row for _, row in frame.iterrows()}
    missing_fields = sorted(REQUIRED_SCOPE_FIELDS - set(rows))
    _add_check(checks, "scope_required_fields", not missing_fields, f"missing={missing_fields}")
    if missing_fields:
        return
    provider_unselected = str(rows["provider"]["value"]) == "unselected"
    symbol_unselected = str(rows["symbol"]["value"]) == "unselected"
    max_calls_one = str(rows["max_provider_calls"]["value"]) == "1"
    raw_false = str(rows["raw_payload_retention"]["value"]).lower() == "false"
    output_blocked = str(rows["output_directory"]["status"]) == "blocked_until_approval"
    ledger_blocked = str(rows["trial_ledger_entry"]["status"]) == "blocked_until_approval"
    _add_check(checks, "scope_provider_and_symbol_unselected", provider_unselected and symbol_unselected, f"provider={rows['provider']['value']}; symbol={rows['symbol']['value']}")
    _add_check(checks, "scope_max_provider_calls_one", max_calls_one, f"max_provider_calls={rows['max_provider_calls']['value']}")
    _add_check(checks, "scope_raw_retention_false", raw_false, f"raw_payload_retention={rows['raw_payload_retention']['value']}")
    _add_check(checks, "scope_outputs_blocked_until_approval", output_blocked and ledger_blocked, f"output={rows['output_directory']['status']}; ledger={rows['trial_ledger_entry']['status']}")


def _validate_output_schema(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"field", "required", "allowed_or_format", "redaction_policy"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "output_schema_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    fields = set(frame["field"].astype(str))
    missing_fields = sorted(REQUIRED_OUTPUT_FIELDS - fields)
    all_required = frame["required"].astype(str).str.lower().eq("yes").all()
    secret_row = frame[frame["field"].astype(str).eq("secret_values_present")]
    raw_row = frame[frame["field"].astype(str).eq("raw_payload_saved")]
    secret_redacted = len(secret_row) == 1 and "redact" in str(secret_row.iloc[0]["redaction_policy"]).lower()
    raw_false = len(raw_row) == 1 and str(raw_row.iloc[0]["allowed_or_format"]).lower() == "false"
    _add_check(checks, "output_schema_required_fields", not missing_fields, f"missing={missing_fields}")
    _add_check(checks, "output_schema_all_fields_required", bool(all_required), f"all_required={bool(all_required)}")
    _add_check(checks, "output_schema_secret_redaction_declared", secret_redacted, f"secret_rows={len(secret_row)}")
    _add_check(checks, "output_schema_raw_payload_false", raw_false, f"raw_rows={len(raw_row)}")


def _validate_stop_rules(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"stop_rule", "trigger", "required_action"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "stop_rules_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    rules = set(frame["stop_rule"].astype(str))
    missing_rules = sorted(REQUIRED_STOP_RULES - rules)
    all_stop = frame["required_action"].astype(str).str.lower().str.contains("stop").all()
    _add_check(checks, "stop_rules_required_set", not missing_rules, f"missing={missing_rules}")
    _add_check(checks, "stop_rules_all_stop_actions", bool(all_stop), f"all_stop={bool(all_stop)}")


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
    status = "spec_only_awaiting_separate_approval" in lower
    one_only = all(marker in lower for marker in ["one provider", "one symbol", "one endpoint"])
    blocked = all(marker in lower for marker in ["provider query", "raw payload retention", "extractor implementation"])
    _add_check(checks, "summary_status_awaiting_approval", status, "status present")
    _add_check(checks, "summary_one_provider_one_symbol_scope", one_only, "one-only scope present")
    _add_check(checks, "summary_blocked_actions_present", blocked, "blocked actions present")


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
        "artifact_dir": str(path),
        "status": "fail" if failed else "pass",
        "gate_decision": "EARNINGS_SINGLE_PROBE_APPROVAL_SPEC_PASS" if failed == 0 else "EARNINGS_SINGLE_PROBE_APPROVAL_SPEC_FAIL",
        "provider_query_performed": False,
        "network_call_performed": False,
        "extractor_implemented": False,
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
