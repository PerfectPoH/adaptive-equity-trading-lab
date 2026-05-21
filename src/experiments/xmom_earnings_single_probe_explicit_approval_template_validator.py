from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_TEMPLATE_DIR = "experiments/provider_aware_research/xmom_earnings_single_probe_explicit_approval_template_20260521"
EXPECTED_GATE_ID = "EARNINGS-SINGLE-PROBE-XMOM-CATALYST-001"
EXPECTED_TRIAL_ID = "TRIAL-XMOM-CATALYST-001"
EXPECTED_OUTPUT_ID = "XMOM-EARNINGS-SINGLE-PROBE-001"
REQUIRED_FILES = {
    "explicit_approval_template_manifest.json",
    "approval_fields_required.csv",
    "pre_execution_package_checklist.csv",
    "blocked_until_approval.csv",
    "README.md",
}
REQUIRED_BLOCKED_ACTIONS = {
    "copy_to_live_approval_dir",
    "create_output_directory",
    "create_trial_ledger_entry",
    "execute_probe",
    "query_provider",
    "save_raw_payload",
    "implement_extractor",
    "run_oos",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
}


def validate_xmom_earnings_single_probe_explicit_approval_template(template_dir: str | Path = DEFAULT_TEMPLATE_DIR) -> dict[str, Any]:
    root = Path(template_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "template_dir_exists", root.exists() and root.is_dir(), str(root))
    if not root.exists() or not root.is_dir():
        return _report(root, checks)

    for filename in sorted(REQUIRED_FILES):
        _add_check(checks, f"required_file:{filename}", (root / filename).is_file(), str(root / filename))

    manifest = _read_json(root / "explicit_approval_template_manifest.json", checks)
    fields = _read_csv(root / "approval_fields_required.csv", checks)
    checklist = _read_csv(root / "pre_execution_package_checklist.csv", checks)
    blocked = _read_csv(root / "blocked_until_approval.csv", checks)
    readme = _read_text(root / "README.md", checks)

    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)
    if fields is not None:
        _validate_fields(fields, checks)
    if checklist is not None:
        _validate_checklist(checklist, checks)
    if blocked is not None:
        _validate_blocked(blocked, checks)
    if readme is not None:
        _validate_readme(readme, checks)

    return _report(root, checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate XMOM earnings single-probe explicit approval template.")
    parser.add_argument("--template-dir", default=DEFAULT_TEMPLATE_DIR)
    args = parser.parse_args(argv)
    report = validate_xmom_earnings_single_probe_explicit_approval_template(args.template_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    identity_ok = (
        manifest.get("status") == "TEMPLATE_ONLY_NOT_GRANTED"
        and manifest.get("approval_status") == "not_granted"
        and manifest.get("gate_id") == EXPECTED_GATE_ID
        and manifest.get("trial_id") == EXPECTED_TRIAL_ID
        and manifest.get("output_id") == EXPECTED_OUTPUT_ID
    )
    unresolved_ok = manifest.get("provider") == "TBD" and manifest.get("symbol") == "TBD"
    prep_not_done = manifest.get("output_directory_created") is False and manifest.get("trial_ledger_entry_created") is False
    scope_ok = (
        manifest.get("max_provider_calls") == 1
        and manifest.get("max_provider_count") == 1
        and manifest.get("max_symbol_count") == 1
        and manifest.get("max_endpoint_count") == 1
    )
    safe_flags = (
        manifest.get("raw_payload_retention_allowed") is False
        and manifest.get("provider_query_performed") is False
        and manifest.get("network_call_performed") is False
        and manifest.get("market_data_downloaded") is False
        and manifest.get("extractor_implemented") is False
        and manifest.get("backtest_performed") is False
        and manifest.get("strategy_promotion_performed") is False
    )
    _add_check(checks, "manifest_template_identity_not_granted", identity_ok, f"status={manifest.get('status')}; approval={manifest.get('approval_status')}")
    _add_check(checks, "manifest_provider_symbol_unresolved", unresolved_ok, f"provider={manifest.get('provider')}; symbol={manifest.get('symbol')}")
    _add_check(checks, "manifest_pre_execution_package_not_created", prep_not_done, f"output={manifest.get('output_directory_created')}; ledger={manifest.get('trial_ledger_entry_created')}")
    _add_check(checks, "manifest_scope_bounded", scope_ok, f"calls={manifest.get('max_provider_calls')}; providers={manifest.get('max_provider_count')}; symbols={manifest.get('max_symbol_count')}; endpoints={manifest.get('max_endpoint_count')}")
    _add_check(checks, "manifest_no_execution_or_raw_payload", safe_flags, f"safe={safe_flags}")


def _validate_fields(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"field", "required", "future_value_policy", "status"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "fields_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    rows = {str(row["field"]): row for _, row in frame.iterrows()}
    required_fields = {
        "status",
        "gate_id",
        "trial_id",
        "provider",
        "symbol",
        "endpoint",
        "output_id",
        "output_directory_created",
        "trial_ledger_entry_created",
        "max_provider_calls",
        "raw_payload_retention_allowed",
        "provider_query_performed",
        "network_call_performed",
        "extractor_implemented",
        "backtest_performed",
        "strategy_promotion_performed",
    }
    missing_fields = sorted(required_fields - set(rows))
    all_required = frame["required"].astype(str).str.lower().eq("yes").all()
    raw_locked = str(rows.get("raw_payload_retention_allowed", {}).get("future_value_policy", "")).endswith("false")
    _add_check(checks, "fields_required_set", not missing_fields, f"missing={missing_fields}")
    _add_check(checks, "fields_all_required", bool(all_required), f"all_required={bool(all_required)}")
    _add_check(checks, "fields_raw_payload_must_remain_false", raw_locked, "raw payload policy locked false")


def _validate_checklist(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"item", "status", "required_before_execution"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "checklist_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    required_yes = frame["required_before_execution"].astype(str).str.lower().eq("yes").all()
    statuses = set(frame["status"].astype(str))
    has_missing = "missing" in statuses
    has_defined_controls = "defined" in statuses
    _add_check(checks, "checklist_all_required_before_execution", bool(required_yes), f"all_required={bool(required_yes)}")
    _add_check(checks, "checklist_still_not_ready", has_missing, f"statuses={sorted(statuses)}")
    _add_check(checks, "checklist_has_defined_controls", has_defined_controls, f"statuses={sorted(statuses)}")


def _validate_blocked(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"action", "status", "reason"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "blocked_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    actions = set(frame["action"].astype(str))
    missing_actions = sorted(REQUIRED_BLOCKED_ACTIONS - actions)
    all_blocked = frame["status"].astype(str).str.lower().eq("blocked").all()
    _add_check(checks, "blocked_required_actions", not missing_actions, f"missing={missing_actions}")
    _add_check(checks, "blocked_all_actions_blocked", bool(all_blocked), f"all_blocked={bool(all_blocked)}")


def _validate_readme(text: str, checks: list[dict[str, str]]) -> None:
    lower = text.lower()
    _add_check(checks, "readme_template_not_granted", "template_only_not_granted" in lower, "status marker")
    _add_check(checks, "readme_live_dir_separate", "live approval directory does not exist" in lower, "live dir separation")
    _add_check(checks, "readme_no_query_statement", "no provider query" in lower and "no network call" in lower, "no-query statement")


def _read_json(path: Path, checks: list[dict[str, str]]) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, f"json_readable:{path.name}", False, f"{type(exc).__name__}: {exc}")
        return None
    _add_check(checks, f"json_readable:{path.name}", True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]]) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        _add_check(checks, f"csv_readable:{path.name}", False, f"{type(exc).__name__}: {exc}")
        return None
    _add_check(checks, f"csv_readable:{path.name}", not frame.empty, f"rows={len(frame)}")
    return frame


def _read_text(path: Path, checks: list[dict[str, str]]) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        _add_check(checks, f"text_readable:{path.name}", False, f"{type(exc).__name__}: {exc}")
        return None
    _add_check(checks, f"text_readable:{path.name}", bool(text.strip()), f"chars={len(text)}")
    return text


def _add_check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": str(detail)})


def _report(path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "template_dir": str(path),
        "status": "fail" if failed else "pass",
        "decision": "XMOM_EARNINGS_SINGLE_PROBE_EXPLICIT_APPROVAL_TEMPLATE_PASS" if failed == 0 else "XMOM_EARNINGS_SINGLE_PROBE_EXPLICIT_APPROVAL_TEMPLATE_FAIL",
        "approval_granted": False,
        "provider_query_performed": False,
        "network_call_performed": False,
        "extractor_implemented": False,
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
