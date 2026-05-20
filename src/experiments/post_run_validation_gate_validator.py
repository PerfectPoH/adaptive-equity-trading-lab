from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_FILES = [
    "run_manifest.json",
    "portfolio_trade_log.csv",
    "portfolio_summary.csv",
    "portfolio_outlier_breakdown.csv",
    "benchmark_report.csv",
]

REQUIRED_TRADE_COLUMNS = {
    "symbol",
    "signal_date",
    "entry_date",
    "exit_date",
    "entry_reference_price",
    "entry_price",
    "position_size",
    "position_notional",
    "max_liquidity_notional",
    "estimated_cost_pct",
    "impact_cost_pct",
    "pnl",
    "return_pct",
    "cash_after_entry",
    "cash_after_exit",
}

SUMMARY_COLUMNS = {"initial_cash", "ending_cash", "total_pnl", "return_pct", "total_trades"}
OUTLIER_COLUMNS = {"outlier_concentration_alert", "sign_flip_excluding_top_3", "pnl_excluding_top_3"}


def validate_post_run_gate(run_dir: str | Path) -> dict[str, Any]:
    run_path = Path(run_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "run_dir_exists", run_path.exists() and run_path.is_dir(), str(run_path))
    if not run_path.exists() or not run_path.is_dir():
        return _report(run_path, checks)

    for filename in REQUIRED_FILES:
        file_path = run_path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(run_path / "run_manifest.json", checks, "manifest_json")
    trade_log = _read_csv(run_path / "portfolio_trade_log.csv", checks, "csv_readable:portfolio_trade_log.csv")
    summary = _read_csv(run_path / "portfolio_summary.csv", checks, "csv_readable:portfolio_summary.csv")
    outliers = _read_csv(run_path / "portfolio_outlier_breakdown.csv", checks, "csv_readable:portfolio_outlier_breakdown.csv")
    _read_csv(run_path / "benchmark_report.csv", checks, "csv_readable:benchmark_report.csv")

    execution_config = _execution_config(manifest if isinstance(manifest, dict) else {})
    _validate_manifest_execution_config(execution_config, checks)

    if trade_log is not None:
        _validate_trade_log_schema(trade_log, checks)
        if execution_config:
            _validate_execution_guardrails(trade_log, execution_config, checks)
    if summary is not None:
        _validate_summary_schema(summary, checks)
    if outliers is not None:
        _validate_outlier_schema(outliers, checks)
    if trade_log is not None and summary is not None:
        _validate_summary_matches_trade_log(trade_log, summary, checks)

    return _report(run_path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_post_run_gate(args.run_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate post-run execution and accounting invariants for a completed research run.")
    parser.add_argument("--run-dir", required=True, help="Completed run artifact directory.")
    return parser


def _execution_config(manifest: dict[str, Any]) -> dict[str, Any]:
    config = manifest.get("config")
    if not isinstance(config, dict):
        return {}
    portfolio = config.get("portfolio")
    if isinstance(portfolio, dict) and isinstance(portfolio.get("execution"), dict):
        return dict(portfolio["execution"])
    candidate_export = config.get("candidate_export")
    if isinstance(candidate_export, dict) and isinstance(candidate_export.get("execution"), dict):
        return dict(candidate_export["execution"])
    return {}


def _validate_manifest_execution_config(execution_config: dict[str, Any], checks: list[dict[str, str]]) -> None:
    required = {"max_position_dollar_volume_fraction", "impact_participation_cap", "impact_coefficient_bps"}
    missing = sorted(required - set(execution_config.keys()))
    values_ok = True
    for key in required - set(missing):
        value = _safe_float(execution_config.get(key))
        values_ok = values_ok and value is not None and value > 0
    _add_check(checks, "manifest_execution_config", not missing and values_ok, f"missing={missing}; values_ok={values_ok}")


def _validate_trade_log_schema(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    missing = sorted(REQUIRED_TRADE_COLUMNS - set(frame.columns))
    _add_check(checks, "trade_log_required_columns", not missing, f"missing={missing}; rows={len(frame)}")
    _add_check(checks, "trade_log_non_empty", not frame.empty, f"rows={len(frame)}")


def _validate_execution_guardrails(frame: pd.DataFrame, execution_config: dict[str, Any], checks: list[dict[str, str]]) -> None:
    required_missing = REQUIRED_TRADE_COLUMNS - set(frame.columns)
    if required_missing or frame.empty:
        _add_check(checks, "execution_guardrails_evaluable", False, f"missing={sorted(required_missing)}; rows={len(frame)}")
        return

    max_liquidity_fraction = float(execution_config["max_position_dollar_volume_fraction"])
    impact_cap = float(execution_config["impact_participation_cap"])

    position_notional = pd.to_numeric(frame["position_notional"], errors="coerce")
    max_liquidity_notional = pd.to_numeric(frame["max_liquidity_notional"], errors="coerce")
    position_size = pd.to_numeric(frame["position_size"], errors="coerce")
    estimated_cost = pd.to_numeric(frame["estimated_cost_pct"], errors="coerce")
    impact_cost = pd.to_numeric(frame["impact_cost_pct"], errors="coerce")
    entry_reference = pd.to_numeric(frame["entry_reference_price"], errors="coerce")
    entry_price = pd.to_numeric(frame["entry_price"], errors="coerce")
    adv_notional = max_liquidity_notional / max_liquidity_fraction
    participation = position_notional / adv_notional

    finite_core = _series_finite(position_notional) & _series_finite(max_liquidity_notional) & _series_finite(participation)
    _add_check(checks, "trade_numeric_fields_finite", bool(finite_core.all()), f"bad_rows={int((~finite_core).sum())}")
    _add_check(checks, "position_size_positive", bool((position_size > 0).all()), f"min={position_size.min()}")
    _add_check(checks, "position_notional_positive", bool((position_notional > 0).all()), f"min={position_notional.min()}")
    _add_check(
        checks,
        "position_notional_within_liquidity_cap",
        bool((position_notional <= max_liquidity_notional + 1e-6).all()),
        f"max_excess={float((position_notional - max_liquidity_notional).max())}",
    )
    _add_check(
        checks,
        "participation_within_configured_fraction",
        bool((participation <= max_liquidity_fraction + 1e-12).all()),
        f"max_participation={float(participation.max())}; cap={max_liquidity_fraction}",
    )
    _add_check(
        checks,
        "impact_participation_below_hard_cap",
        bool((participation < impact_cap).all()),
        f"max_participation={float(participation.max())}; hard_cap={impact_cap}",
    )
    _add_check(checks, "impact_cost_non_negative", bool((impact_cost >= 0).all()), f"min={impact_cost.min()}")
    _add_check(
        checks,
        "estimated_cost_covers_impact_cost",
        bool((estimated_cost + 1e-12 >= impact_cost).all()),
        f"min_margin={float((estimated_cost - impact_cost).min())}",
    )
    _add_check(
        checks,
        "long_entry_price_not_below_reference_after_costs",
        bool((entry_price + 1e-9 >= entry_reference).all()),
        f"min_margin={float((entry_price - entry_reference).min())}",
    )


def _validate_summary_schema(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    missing = sorted(SUMMARY_COLUMNS - set(frame.columns))
    one_row = len(frame) == 1
    _add_check(checks, "summary_required_columns", not missing and one_row, f"missing={missing}; rows={len(frame)}")


def _validate_outlier_schema(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    missing = sorted(OUTLIER_COLUMNS - set(frame.columns))
    _add_check(checks, "outlier_required_columns", not missing and len(frame) == 1, f"missing={missing}; rows={len(frame)}")


def _validate_summary_matches_trade_log(trade_log: pd.DataFrame, summary: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    if trade_log.empty or summary.empty or not {"pnl"}.issubset(trade_log.columns) or not SUMMARY_COLUMNS.issubset(summary.columns):
        _add_check(checks, "summary_trade_log_reconciliation_evaluable", False, "missing pnl/summary columns or empty frame")
        return
    pnl_sum = float(pd.to_numeric(trade_log["pnl"], errors="coerce").sum())
    summary_row = summary.iloc[0]
    total_pnl = float(summary_row["total_pnl"])
    initial_cash = float(summary_row["initial_cash"])
    return_pct = float(summary_row["return_pct"])
    total_trades = int(summary_row["total_trades"])
    pnl_matches = math.isclose(pnl_sum, total_pnl, rel_tol=1e-9, abs_tol=1e-6)
    return_matches = math.isclose(return_pct, total_pnl / initial_cash, rel_tol=1e-9, abs_tol=1e-9) if initial_cash else False
    count_matches = total_trades == len(trade_log)
    _add_check(checks, "summary_pnl_matches_trade_log", pnl_matches, f"trade_log_pnl={pnl_sum}; summary_pnl={total_pnl}")
    _add_check(checks, "summary_return_matches_pnl_over_initial_cash", return_matches, f"return_pct={return_pct}; total_pnl={total_pnl}; initial_cash={initial_cash}")
    _add_check(checks, "summary_trade_count_matches_trade_log", count_matches, f"summary_total_trades={total_trades}; trade_log_rows={len(trade_log)}")


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


def _series_finite(series: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(series, errors="coerce")
    return numeric.notna() & numeric.map(math.isfinite)


def _safe_float(value: Any) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _add_check(checks: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": str(detail)})


def _report(run_path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = [check for check in checks if check["status"] == "fail"]
    return {
        "run_dir": str(run_path),
        "status": "pass" if not failed else "fail",
        "gate_decision": "POST_RUN_VALIDATION_PASS" if not failed else "POST_RUN_VALIDATION_FAIL",
        "summary": {"total": len(checks), "failed": len(failed), "passed": len(checks) - len(failed)},
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
