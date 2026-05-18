from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "trial_accounting_preregistration_manifest.json",
    "preregistration_schema.csv",
    "preregistration_template.csv",
    "trial_budget_policy.csv",
    "decision_thresholds.csv",
    "trial_ledger_template.csv",
    "research_stage_enforcement.csv",
    "trial_accounting_preregistration_summary.md",
]

REQUIRED_MANIFEST_FIELDS = [
    "status",
    "decision",
    "scope",
    "purpose",
    "no_provider_query",
    "no_backtest",
    "no_strategy_promotion",
    "required_tables",
]

REQUIRED_PREREGISTRATION_FIELDS = [
    "preregistration_id",
    "research_question",
    "hypothesis",
    "provider_contract_id",
    "adjustment_tradability_policy_id",
    "sample_definition",
    "in_sample_window",
    "holdout_window",
    "features_allowed",
    "parameters_allowed",
    "primary_metric",
    "secondary_metrics",
    "trial_budget_id",
    "stop_go_threshold_id",
    "forbidden_changes_after_execution",
    "raw_data_retention_policy",
]

REQUIRED_STAGES = [
    "data_quality_diagnostic",
    "fixed_signal_replay",
    "new_signal_research",
    "portfolio_backtest",
    "OOS",
    "paper_live",
]

BLOCKED_TEMPLATE_VALUES = {"", "unknown", "tbd", "todo", "n/a"}


def validate_trial_accounting_preregistration(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(path / "trial_accounting_preregistration_manifest.json", checks, "manifest_json")
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)

    schema = _read_csv(path / "preregistration_schema.csv", checks, "csv_readable:preregistration_schema.csv")
    template = _read_csv(path / "preregistration_template.csv", checks, "csv_readable:preregistration_template.csv")
    budget = _read_csv(path / "trial_budget_policy.csv", checks, "csv_readable:trial_budget_policy.csv")
    thresholds = _read_csv(path / "decision_thresholds.csv", checks, "csv_readable:decision_thresholds.csv")
    ledger = _read_csv(path / "trial_ledger_template.csv", checks, "csv_readable:trial_ledger_template.csv")
    enforcement = _read_csv(path / "research_stage_enforcement.csv", checks, "csv_readable:research_stage_enforcement.csv")
    _read_text_file(path / "trial_accounting_preregistration_summary.md", checks, "markdown_readable:trial_accounting_preregistration_summary.md")

    if schema is not None:
        _validate_schema(schema, checks)
    if template is not None:
        _validate_template(template, checks)
    if budget is not None:
        _validate_budget(budget, checks)
    if thresholds is not None:
        _validate_thresholds(thresholds, checks)
    if ledger is not None:
        _validate_ledger(ledger, checks)
    if enforcement is not None:
        _validate_enforcement(enforcement, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_trial_accounting_preregistration(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate trial accounting and preregistration artifacts.")
    parser.add_argument("--spec-dir", required=True, help="Trial accounting/preregistration spec directory to validate.")
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing = [field for field in REQUIRED_MANIFEST_FIELDS if field not in manifest]
    tables_ok = isinstance(manifest.get("required_tables"), list) and bool(manifest.get("required_tables"))
    no_provider_query_ok = manifest.get("no_provider_query") is True
    no_backtest_ok = manifest.get("no_backtest") is True
    no_strategy_promotion_ok = manifest.get("no_strategy_promotion") is True
    _add_check(checks, "manifest_required_fields", not missing and tables_ok, f"missing={missing}; required_tables_ok={tables_ok}")
    _add_check(
        checks,
        "manifest_no_execution_flags",
        no_provider_query_ok and no_backtest_ok and no_strategy_promotion_ok,
        f"no_provider_query={manifest.get('no_provider_query')}; no_backtest={manifest.get('no_backtest')}; no_strategy_promotion={manifest.get('no_strategy_promotion')}",
    )


def _validate_schema(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"field", "required", "allowed_or_format", "description"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "schema_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    fields = {str(value) for value in frame["field"].dropna().tolist()}
    missing_fields = [field for field in REQUIRED_PREREGISTRATION_FIELDS if field not in fields]
    _add_check(checks, "schema_required_preregistration_fields", not missing_fields, f"missing={missing_fields}")


def _validate_template(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    missing_columns = [field for field in REQUIRED_PREREGISTRATION_FIELDS if field not in frame.columns]
    _add_check(checks, "template_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    _add_check(checks, "template_single_preregistration_row", len(frame) == 1, f"rows={len(frame)}")
    if frame.empty:
        return
    row = frame.iloc[0]
    blocked_values = []
    for field in REQUIRED_PREREGISTRATION_FIELDS:
        value = str(row.get(field, "")).strip().lower()
        if value in BLOCKED_TEMPLATE_VALUES:
            blocked_values.append(field)
    _add_check(checks, "template_required_values_populated", not blocked_values, f"blocked_or_empty={blocked_values}")


def _validate_budget(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"trial_budget_id", "stage", "max_trials", "what_counts_as_trial", "reset_allowed", "notes"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "budget_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    stages = {str(value) for value in frame["stage"].dropna().tolist()}
    required_budget_stages = {"new_signal_research", "portfolio_backtest", "OOS", "paper_live"}
    missing_stages = sorted(required_budget_stages - stages)
    reset_blocked = frame["reset_allowed"].astype(str).str.lower().eq("no").all()
    max_trials_positive = pd.to_numeric(frame["max_trials"], errors="coerce").ge(1).all()
    _add_check(checks, "budget_required_stages", not missing_stages, f"missing={missing_stages}")
    _add_check(checks, "budget_reset_blocked", bool(reset_blocked), f"reset_blocked={bool(reset_blocked)}")
    _add_check(checks, "budget_max_trials_positive", bool(max_trials_positive), f"max_trials_positive={bool(max_trials_positive)}")


def _validate_thresholds(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"threshold_id", "stage", "primary_metric", "go_condition", "stop_condition", "caveat_condition"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "thresholds_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    stages = {str(value) for value in frame["stage"].dropna().tolist()}
    required_threshold_stages = {"new_signal_research", "portfolio_backtest", "OOS"}
    missing_stages = sorted(required_threshold_stages - stages)
    _add_check(checks, "thresholds_required_stages", not missing_stages, f"missing={missing_stages}")


def _validate_ledger(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"trial_id", "preregistration_id", "stage", "executed_at", "code_commit", "artifact_dir", "trial_number", "within_budget", "result_status", "decision", "notes"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "ledger_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    _add_check(checks, "ledger_template_not_executed", frame["result_status"].astype(str).str.lower().eq("not_executed").all(), "template rows must be not_executed")


def _validate_enforcement(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"research_stage", "preregistration_required", "trial_ledger_required", "trial_budget_required", "promotion_allowed"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "enforcement_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    stages = {str(value) for value in frame["research_stage"].dropna().tolist()}
    missing_stages = [stage for stage in REQUIRED_STAGES if stage not in stages]
    post_diagnostic = frame[frame["research_stage"].isin(["new_signal_research", "portfolio_backtest", "OOS", "paper_live"])]
    required_after_diagnostics = (
        post_diagnostic["preregistration_required"].astype(str).str.lower().eq("yes").all()
        and post_diagnostic["trial_ledger_required"].astype(str).str.lower().eq("yes").all()
        and post_diagnostic["trial_budget_required"].astype(str).str.lower().eq("yes").all()
    )
    promotion_values = frame["promotion_allowed"].astype(str).str.lower().tolist()
    promotion_not_silently_allowed = all(value in {"no", "no_until_separate_promotion_gate", "conditional"} for value in promotion_values)
    _add_check(checks, "enforcement_required_stages", not missing_stages, f"missing={missing_stages}")
    _add_check(checks, "enforcement_required_after_diagnostics", bool(required_after_diagnostics), f"required_after_diagnostics={bool(required_after_diagnostics)}")
    _add_check(checks, "enforcement_promotion_not_silently_allowed", promotion_not_silently_allowed, f"promotion_allowed={promotion_values}")


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
        "spec_dir": str(path),
        "status": "pass" if not failed else "fail",
        "summary": {"total": len(checks), "failed": len(failed), "passed": len(checks) - len(failed)},
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
