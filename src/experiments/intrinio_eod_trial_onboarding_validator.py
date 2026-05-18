from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "intrinio_eod_trial_onboarding_manifest.json",
    "intrinio_trial_terms_checklist.csv",
    "intrinio_eod_endpoint_questions.csv",
    "intrinio_credential_policy.csv",
    "intrinio_probe_budget.csv",
    "intrinio_blocker_register.csv",
    "intrinio_eod_trial_onboarding_summary.md",
]

REQUIRED_TERMS_ITEMS = {
    "trial_active",
    "eod_one_year_history",
    "us_small_cap_coverage",
    "delisted_symbol_coverage",
    "adjustment_policy",
    "raw_retention_rights",
    "rate_limits",
    "endpoint_selection",
}

REQUIRED_CREDENTIAL_POLICIES = {
    "credential_source",
    "credential_disclosure",
    "prior_key_rotation",
    "credential_preflight",
    "account_page_access",
}

REQUIRED_BLOCKERS = {
    "prior_key_exposed_in_chat",
    "terms_for_derived_artifacts_unknown",
    "endpoint_not_confirmed",
    "rate_limits_unknown",
    "separate_probe_approval_missing",
    "output_directory_not_created",
    "trial_ledger_entry_not_created",
}


def validate_intrinio_eod_trial_onboarding(artifact_dir: str | Path) -> dict[str, Any]:
    root = Path(artifact_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "artifact_dir_exists", root.exists() and root.is_dir(), str(root))
    for filename in REQUIRED_FILES:
        _add_check(checks, f"required_file:{filename}", (root / filename).exists(), str(root / filename))
    manifest = _read_json(root / "intrinio_eod_trial_onboarding_manifest.json", checks)
    terms = _read_csv(root / "intrinio_trial_terms_checklist.csv", checks)
    questions = _read_csv(root / "intrinio_eod_endpoint_questions.csv", checks)
    credentials = _read_csv(root / "intrinio_credential_policy.csv", checks)
    budget = _read_csv(root / "intrinio_probe_budget.csv", checks)
    blockers = _read_csv(root / "intrinio_blocker_register.csv", checks)
    _read_markdown(root / "intrinio_eod_trial_onboarding_summary.md", checks)
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)
    if terms is not None:
        _validate_terms(terms, checks)
    if questions is not None:
        _validate_questions(questions, checks)
    if credentials is not None:
        _validate_credentials(credentials, checks)
    if budget is not None:
        _validate_budget(budget, checks)
    if blockers is not None:
        _validate_blockers(blockers, checks)
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "artifact_dir": str(root),
        "status": "pass" if failed == 0 else "fail",
        "decision": "INTRINIO_EOD_TRIAL_ONBOARDING_GATE_VALID" if failed == 0 else "INTRINIO_EOD_TRIAL_ONBOARDING_GATE_INVALID",
        "provider_query_performed": False,
        "network_call_performed": False,
        "market_data_downloaded": False,
        "secret_values_disclosed": False,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Intrinio EOD trial onboarding gate artifacts.")
    parser.add_argument("--artifact-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_intrinio_eod_trial_onboarding(args.artifact_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    status_ok = manifest.get("status") in {"SPEC_ONLY_INTRINIO_TRIAL_ACTIVE_NOT_QUERIED", "SPEC_ONLY_INTRINIO_TRIAL_INFO_RESOLVED_NOT_QUERIED"}
    decision_ok = manifest.get("decision") in {"INTRINIO_EOD_TRIAL_ONBOARDING_DEFINED_NOT_EXECUTED", "INTRINIO_EOD_TRIAL_READY_FOR_ONE_PROBE_PREPARATION_NOT_APPROVED"}
    no_execution = (
        manifest.get("provider_query_performed") is False
        and manifest.get("network_call_performed") is False
        and manifest.get("market_data_downloaded") is False
        and manifest.get("backtest_performed") is False
        and manifest.get("strategy_promotion_performed") is False
    )
    safety = manifest.get("raw_payload_retention_allowed") is False and manifest.get("secret_values_disclosed") is False
    approval_gate = manifest.get("separate_probe_approval_required") is True
    rotation = manifest.get("credential_rotation_required") is True
    budget = manifest.get("max_first_probe_symbols") == 1 and manifest.get("max_first_probe_provider_calls") == 1
    _add_check(checks, "manifest_status_spec_only", status_ok and decision_ok, f"status={manifest.get('status')}; decision={manifest.get('decision')}")
    _add_check(checks, "manifest_no_execution_flags", no_execution, f"no_execution={no_execution}")
    _add_check(checks, "manifest_safety_flags", safety, f"safety={safety}")
    _add_check(checks, "manifest_separate_probe_approval_required", approval_gate, f"approval={manifest.get('separate_probe_approval_required')}")
    _add_check(checks, "manifest_credential_rotation_required", rotation, f"credential_rotation_required={manifest.get('credential_rotation_required')}")
    _add_check(checks, "manifest_first_probe_budget_bounded", budget, f"symbols={manifest.get('max_first_probe_symbols')}; calls={manifest.get('max_first_probe_provider_calls')}")
    _add_check(checks, "manifest_env_var_declared", manifest.get("required_env_var") == "INTRINIO_API_KEY", f"required_env_var={manifest.get('required_env_var')}")


def _validate_terms(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"item", "status", "requirement"}
    missing_columns = sorted(required_columns - set(frame.columns))
    items = set(frame["item"].astype(str)) if not missing_columns else set()
    statuses = {str(row["item"]): str(row["status"]).lower() for _, row in frame.iterrows()} if not missing_columns else {}
    open_or_resolved_ok = all(statuses.get(item) in {"unresolved", "confirmed_by_provider", "resolved_for_derived_use_only"} for item in REQUIRED_TERMS_ITEMS)
    _add_check(checks, "terms_required_columns", not missing_columns, f"missing={missing_columns}")
    _add_check(checks, "terms_required_items", REQUIRED_TERMS_ITEMS.issubset(items), f"missing={sorted(REQUIRED_TERMS_ITEMS - items)}")
    _add_check(checks, "terms_items_open_or_resolved", open_or_resolved_ok, f"statuses={statuses}")


def _validate_questions(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"question_id", "question", "status"}
    missing_columns = sorted(required_columns - set(frame.columns))
    allowed_statuses = frame["status"].astype(str).str.lower().isin({"open", "answered"}).all() if not missing_columns else False
    _add_check(checks, "questions_required_columns", not missing_columns, f"missing={missing_columns}")
    _add_check(checks, "questions_open_or_answered_pre_query", bool(allowed_statuses), f"allowed_statuses={bool(allowed_statuses)}")
    _add_check(checks, "questions_minimum_count", len(frame) >= 6, f"count={len(frame)}")


def _validate_credentials(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"policy", "status", "requirement"}
    missing_columns = sorted(required_columns - set(frame.columns))
    policies = set(frame["policy"].astype(str)) if not missing_columns else set()
    rotation = frame[frame["policy"].astype(str).eq("prior_key_rotation")] if not missing_columns else pd.DataFrame()
    disclosure = frame[frame["policy"].astype(str).eq("credential_disclosure")] if not missing_columns else pd.DataFrame()
    _add_check(checks, "credential_required_columns", not missing_columns, f"missing={missing_columns}")
    _add_check(checks, "credential_required_policies", REQUIRED_CREDENTIAL_POLICIES.issubset(policies), f"missing={sorted(REQUIRED_CREDENTIAL_POLICIES - policies)}")
    _add_check(checks, "credential_rotation_required", len(rotation) == 1 and str(rotation.iloc[0]["status"]) == "required_before_query", f"rotation_rows={len(rotation)}")
    _add_check(checks, "credential_disclosure_forbidden", len(disclosure) == 1 and str(disclosure.iloc[0]["status"]) == "forbidden", f"disclosure_rows={len(disclosure)}")


def _validate_budget(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"budget_item", "value", "status"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "budget_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    values = {str(row["budget_item"]): str(row["value"]) for _, row in frame.iterrows()}
    statuses = {str(row["budget_item"]): str(row["status"]) for _, row in frame.iterrows()}
    _add_check(checks, "budget_first_probe_one_symbol", values.get("first_probe_symbols") == "1" and "blocked" in statuses.get("first_probe_symbols", ""), f"value={values.get('first_probe_symbols')}; status={statuses.get('first_probe_symbols')}")
    _add_check(checks, "budget_first_probe_one_call", values.get("first_probe_provider_calls") == "1" and "blocked" in statuses.get("first_probe_provider_calls", ""), f"value={values.get('first_probe_provider_calls')}; status={statuses.get('first_probe_provider_calls')}")
    _add_check(checks, "budget_raw_retention_false", values.get("raw_payload_retention") == "false", f"raw_payload_retention={values.get('raw_payload_retention')}")
    _add_check(checks, "budget_strategy_actions_forbidden", values.get("backtest") == "false" and values.get("strategy_promotion") == "false" and values.get("paper_live") == "false", f"backtest={values.get('backtest')}; strategy_promotion={values.get('strategy_promotion')}; paper_live={values.get('paper_live')}")


def _validate_blockers(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"blocker", "severity", "status", "resolution_required"}
    missing_columns = sorted(required_columns - set(frame.columns))
    blockers = set(frame["blocker"].astype(str)) if not missing_columns else set()
    statuses = {str(row["blocker"]): str(row["status"]).lower() for _, row in frame.iterrows()} if not missing_columns else {}
    critical = frame.loc[frame["severity"].astype(str).str.lower().eq("critical"), "blocker"].astype(str).tolist() if not missing_columns else []
    critical_unresolved = statuses.get("prior_key_exposed_in_chat") == "unresolved" and statuses.get("separate_probe_approval_missing") == "unresolved"
    allowed_statuses = all(status in {"unresolved", "resolved"} for status in statuses.values())
    _add_check(checks, "blockers_required_columns", not missing_columns, f"missing={missing_columns}")
    _add_check(checks, "blockers_required_items", REQUIRED_BLOCKERS.issubset(blockers), f"missing={sorted(REQUIRED_BLOCKERS - blockers)}")
    _add_check(checks, "blockers_statuses_unresolved_or_resolved", allowed_statuses, f"statuses={statuses}")
    _add_check(checks, "blockers_critical_probe_guards_present", {"prior_key_exposed_in_chat", "separate_probe_approval_missing"}.issubset(set(critical)), f"critical={critical}")
    _add_check(checks, "blockers_critical_probe_guards_unresolved", critical_unresolved, f"statuses={statuses}")


def _read_json(path: Path, checks: list[dict[str, str]]) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, f"json_readable:{path.name}", False, f"{path}: {exc}")
        return None
    _add_check(checks, f"json_readable:{path.name}", True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]]) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        _add_check(checks, f"csv_readable:{path.name}", False, f"{path}: {exc}")
        return None
    _add_check(checks, f"csv_readable:{path.name}", not frame.empty, f"rows={len(frame)}; columns={len(frame.columns)}")
    return frame


def _read_markdown(path: Path, checks: list[dict[str, str]]) -> None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        _add_check(checks, f"markdown_readable:{path.name}", False, f"{path}: {exc}")
        return
    _add_check(checks, f"markdown_readable:{path.name}", bool(text.strip()), f"chars={len(text)}")


def _add_check(checks: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": str(detail)})


if __name__ == "__main__":
    raise SystemExit(main())
