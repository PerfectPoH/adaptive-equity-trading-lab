from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "mini_panel_approval_gate_manifest.json",
    "mini_panel_candidates.csv",
    "mini_panel_query_plan.csv",
    "mini_panel_stop_rules.csv",
    "mini_panel_approval_checklist.csv",
    "mini_panel_approval_gate_summary.md",
]

REQUIRED_CANDIDATE_COLUMNS = {
    "panel_slot",
    "candidate_role",
    "reference_run",
    "symbol",
    "signal_date",
    "entry_date",
    "exit_date",
    "entry_price",
    "exit_price",
    "return_pct",
    "execution_status",
    "provider_query_allowed_without_new_approval",
}

REQUIRED_CHECKLIST_GATES = {
    "separate_user_approval",
    "output_directory",
    "trial_ledger_entries",
    "credential_presence",
    "single_candidate_limit_removed",
    "strategy_promotion",
}


def validate_mini_panel_approval_gate(artifact_dir: str | Path) -> dict[str, Any]:
    root = Path(artifact_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "artifact_dir_exists", root.exists() and root.is_dir(), str(root))
    for name in REQUIRED_FILES:
        _add_check(checks, f"required_file:{name}", (root / name).exists(), str(root / name))
    manifest = _read_json(root / "mini_panel_approval_gate_manifest.json", checks)
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)
    candidates = _read_csv(root / "mini_panel_candidates.csv", checks)
    query_plan = _read_csv(root / "mini_panel_query_plan.csv", checks)
    stop_rules = _read_csv(root / "mini_panel_stop_rules.csv", checks)
    checklist = _read_csv(root / "mini_panel_approval_checklist.csv", checks)
    _read_markdown(root / "mini_panel_approval_gate_summary.md", checks)
    if candidates is not None:
        _validate_candidates(candidates, checks)
    if query_plan is not None:
        _validate_query_plan(query_plan, checks)
    if stop_rules is not None:
        _validate_stop_rules(stop_rules, checks)
    if checklist is not None:
        _validate_checklist(checklist, checks)
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {"artifact_dir": str(root), "status": "pass" if failed == 0 else "fail", "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed}, "checks": checks}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate mini-panel approval gate artifact.")
    parser.add_argument("--artifact-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_mini_panel_approval_gate(args.artifact_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    safe_status = manifest.get("status") == "SPEC_ONLY_AWAITING_SEPARATE_APPROVAL"
    decision = manifest.get("decision") == "MINI_PANEL_DEFINED_NOT_EXECUTED"
    no_execution = (
        manifest.get("provider_query_performed") is False
        and manifest.get("backtest_performed") is False
        and manifest.get("strategy_promotion_performed") is False
    )
    count = int(manifest.get("candidate_count", 0))
    new_queries = int(manifest.get("new_provider_query_count_proposed", -1))
    approval_required = manifest.get("separate_approval_required") is True and manifest.get("approval_status") == "not_granted_for_mini_panel"
    raw_retention_blocked = manifest.get("raw_payload_retention_allowed") is False
    _add_check(checks, "manifest_spec_only_awaiting_approval", safe_status and decision, f"status={manifest.get('status')}; decision={manifest.get('decision')}")
    _add_check(checks, "manifest_candidate_count_3_to_5", 3 <= count <= 5, f"candidate_count={count}")
    _add_check(checks, "manifest_new_queries_bounded", 0 <= new_queries <= 4, f"new_queries={new_queries}")
    _add_check(checks, "manifest_separate_approval_required", approval_required, f"approval_status={manifest.get('approval_status')}")
    _add_check(checks, "manifest_no_execution", no_execution, f"no_execution={no_execution}")
    _add_check(checks, "manifest_raw_retention_blocked", raw_retention_blocked, f"raw_payload_retention_allowed={manifest.get('raw_payload_retention_allowed')}")


def _validate_candidates(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    missing_columns = sorted(REQUIRED_CANDIDATE_COLUMNS - set(frame.columns))
    _add_check(checks, "candidates_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    count = len(frame)
    anchor_count = int(frame["candidate_role"].astype(str).str.lower().eq("executed_anchor").sum())
    not_allowed = frame["provider_query_allowed_without_new_approval"].astype(str).str.lower().eq("no").all()
    proposed_not_executed = frame.loc[frame["candidate_role"].astype(str).str.lower().eq("proposed_new_query"), "execution_status"].astype(str).str.lower().eq("not_executed").all()
    symbols_present = frame["symbol"].astype(str).str.strip().ne("").all()
    _add_check(checks, "candidates_count_3_to_5", 3 <= count <= 5, f"count={count}")
    _add_check(checks, "candidates_one_executed_anchor", anchor_count == 1, f"anchor_count={anchor_count}")
    _add_check(checks, "candidates_new_queries_not_executed", bool(proposed_not_executed), f"proposed_not_executed={bool(proposed_not_executed)}")
    _add_check(checks, "candidates_no_query_without_new_approval", bool(not_allowed), f"not_allowed={bool(not_allowed)}")
    _add_check(checks, "candidates_symbols_present", bool(symbols_present), f"symbols_present={bool(symbols_present)}")


def _validate_query_plan(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"field", "value", "status"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "query_plan_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    fields = set(frame["field"].astype(str).tolist())
    required_fields = {"max_new_provider_queries", "databento_dataset", "databento_schema", "raw_payload_retention", "sleep_seconds_between_candidates", "output_dir", "trial_ledger_entries"}
    raw = frame[frame["field"].astype(str).eq("raw_payload_retention")]
    output = frame[frame["field"].astype(str).eq("output_dir")]
    ledger = frame[frame["field"].astype(str).eq("trial_ledger_entries")]
    _add_check(checks, "query_plan_required_fields", required_fields.issubset(fields), f"missing={sorted(required_fields - fields)}")
    _add_check(checks, "query_plan_raw_retention_false", len(raw) == 1 and str(raw.iloc[0]["value"]).lower() == "false", f"raw_rows={len(raw)}")
    _add_check(checks, "query_plan_output_not_created", len(output) == 1 and str(output.iloc[0]["status"]).lower() == "not_created", f"output_rows={len(output)}")
    _add_check(checks, "query_plan_ledger_blocked", len(ledger) == 1 and "blocked" in str(ledger.iloc[0]["status"]).lower(), f"ledger_rows={len(ledger)}")


def _validate_stop_rules(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"stop_rule", "trigger", "required_action"}
    missing_columns = sorted(required_columns - set(frame.columns))
    stop_actions = frame["required_action"].astype(str).str.lower().str.contains("stop").any() if not missing_columns else False
    _add_check(checks, "stop_rules_required_columns", not missing_columns, f"missing={missing_columns}")
    _add_check(checks, "stop_rules_include_stop_actions", bool(stop_actions), f"stop_actions={bool(stop_actions)}")


def _validate_checklist(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"gate", "status", "requirement"}
    missing_columns = sorted(required_columns - set(frame.columns))
    gates = set(frame["gate"].astype(str).tolist()) if not missing_columns else set()
    approval = frame[frame["gate"].astype(str).eq("separate_user_approval")] if not missing_columns else pd.DataFrame()
    promotion = frame[frame["gate"].astype(str).eq("strategy_promotion")] if not missing_columns else pd.DataFrame()
    _add_check(checks, "checklist_required_columns", not missing_columns, f"missing={missing_columns}")
    _add_check(checks, "checklist_required_gates", REQUIRED_CHECKLIST_GATES.issubset(gates), f"missing={sorted(REQUIRED_CHECKLIST_GATES - gates)}")
    _add_check(checks, "checklist_approval_not_granted", len(approval) == 1 and str(approval.iloc[0]["status"]).lower() == "not_granted", f"approval_rows={len(approval)}")
    _add_check(checks, "checklist_promotion_blocked", len(promotion) == 1 and str(promotion.iloc[0]["status"]).lower() == "blocked", f"promotion_rows={len(promotion)}")


def _read_json(path: Path, checks: list[dict[str, str]]) -> Any:
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
