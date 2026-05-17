from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from src.analysis.nctrl_property_report import NctrlPropertyCheckResult, PropertyStatus
from src.analysis.small_cap_portfolio_diagnostics import build_portfolio_outlier_breakdown

FROZEN_NCTRL_UNIVERSE = ["AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "AMZN", "GOOGL", "SPY", "QQQ"]
REQUIRED_BENCHMARKS = {"cash_flat", "iwm_proxy", "equal_weight_universe", "random_entry_baseline", "ticker_holding_window"}


@dataclass
class NctrlPropertyEvaluationInput:
    output_dir: Path
    artifact_paths: dict[str, Path]
    run_manifest: dict[str, Any]
    candidate_export: pd.DataFrame
    benchmark_report: pd.DataFrame
    trade_log: pd.DataFrame
    portfolio_summary: dict[str, Any]
    portfolio_outlier_breakdown: dict[str, Any]
    bootstrap_random_baseline: dict[str, Any]
    random_entry_sign_flip_report: dict[str, Any]
    risk_fraction: float
    cash_ledger_fixture_tests_passed: bool


def evaluate_nctrl_trial_properties(inputs: NctrlPropertyEvaluationInput) -> tuple[list[NctrlPropertyCheckResult], PropertyStatus]:
    checks = [
        _check_p1_artifacts(inputs),
        _check_p2_manifest(inputs),
        _check_p3_risk_fraction(inputs),
        _check_p4_cash_ledger(inputs),
        _check_p5_bootstrap(inputs),
        _check_p6_random_entry(inputs),
        _check_p7_ex_topn(inputs),
        _check_p8_benchmarks(inputs),
    ]
    total_trades = int(inputs.portfolio_summary.get("total_trades", 0) or 0)
    if total_trades < 30:
        return checks, "insufficient_evidence"
    if any(check.status == "fail" for check in checks):
        return checks, "fail"
    if any(check.status == "insufficient_evidence" for check in checks):
        return checks, "insufficient_evidence"
    return checks, "pass"


def _check_p1_artifacts(inputs: NctrlPropertyEvaluationInput) -> NctrlPropertyCheckResult:
    missing = [name for name, path in inputs.artifact_paths.items() if not Path(path).exists() or Path(path).stat().st_size == 0]
    status: PropertyStatus = "fail" if missing else "pass"
    evidence = f"missing_or_empty={missing}" if missing else f"artifacts={len(inputs.artifact_paths)}"
    return NctrlPropertyCheckResult("P1", status, evidence, "end-to-end artifact presence")


def _check_p2_manifest(inputs: NctrlPropertyEvaluationInput) -> NctrlPropertyCheckResult:
    accounting = inputs.run_manifest.get("trial_accounting", {}) if isinstance(inputs.run_manifest, dict) else {}
    period = inputs.run_manifest.get("period", {}) if isinstance(inputs.run_manifest, dict) else {}
    universe = inputs.run_manifest.get("universe", []) if isinstance(inputs.run_manifest, dict) else []
    passed = (
        isinstance(accounting, dict)
        and accounting.get("trial_id") == "TRIAL-NCTRL-001"
        and bool(inputs.run_manifest.get("config_hash"))
        and list(universe) == FROZEN_NCTRL_UNIVERSE
        and period.get("start") == "2024-01-02"
        and _period_end_matches_candidate_window(period.get("end"), inputs.candidate_export)
    )
    status: PropertyStatus = "pass" if passed else "fail"
    evidence = f"trial_id={accounting.get('trial_id')}; config_hash={inputs.run_manifest.get('config_hash')}; period={period}"
    return NctrlPropertyCheckResult("P2", status, evidence, "manifest identity and frozen universe")


def _period_end_matches_candidate_window(period_end: object, candidate_export: pd.DataFrame) -> bool:
    if str(period_end) in {"2024-12-31", "2024-12-30"}:
        return True
    if candidate_export.empty or "as_of" not in candidate_export.columns:
        return False
    dates = pd.to_datetime(candidate_export["as_of"], errors="coerce").dropna()
    if dates.empty:
        return False
    return str(period_end) == dates.dt.normalize().max().date().isoformat()


def _check_p3_risk_fraction(inputs: NctrlPropertyEvaluationInput) -> NctrlPropertyCheckResult:
    passed = math.isclose(float(inputs.risk_fraction), 0.01, rel_tol=0.0, abs_tol=1e-12)
    return NctrlPropertyCheckResult("P3", "pass" if passed else "fail", f"risk_fraction={inputs.risk_fraction}", "risk sizing regression gate")


def _check_p4_cash_ledger(inputs: NctrlPropertyEvaluationInput) -> NctrlPropertyCheckResult:
    return NctrlPropertyCheckResult(
        "P4",
        "pass" if inputs.cash_ledger_fixture_tests_passed else "fail",
        f"cash_ledger_fixture_tests_passed={inputs.cash_ledger_fixture_tests_passed}",
        "fixture gate before trial interpretation",
    )


def _check_p5_bootstrap(inputs: NctrlPropertyEvaluationInput) -> NctrlPropertyCheckResult:
    report = inputs.bootstrap_random_baseline
    required = ["mean_return", "median_return", "std_return", "p05_return", "p95_return", "observations_per_simulation_min", "observations_per_simulation_max"]
    finite = all(_finite(report.get(key)) for key in required)
    passed = report.get("simulations") == 1000 and report.get("base_seed") == 700 and finite
    evidence = f"simulations={report.get('simulations')}; base_seed={report.get('base_seed')}; mean_return={report.get('mean_return')}; p05={report.get('p05_return')}; p95={report.get('p95_return')}"
    return NctrlPropertyCheckResult("P5", "pass" if passed else "fail", evidence, "distribution-aware random baseline")


def _check_p6_random_entry(inputs: NctrlPropertyEvaluationInput) -> NctrlPropertyCheckResult:
    report = inputs.random_entry_sign_flip_report
    frequency = report.get("sign_flip_excluding_top_3_frequency")
    passed = (
        int(report.get("simulations", 0) or 0) > 0
        and int(report.get("valid_simulations", 0) or 0) > 0
        and bool(report.get("preserves_execution_mechanics"))
        and _finite(frequency)
        and 0.0 < float(frequency) < 1.0
    )
    evidence = f"simulations={report.get('simulations')}; valid={report.get('valid_simulations')}; sign_flip_excluding_top_3_frequency={frequency}"
    return NctrlPropertyCheckResult("P6", "pass" if passed else "fail", evidence, "random-entry ex-outlier sanity")


def _check_p7_ex_topn(inputs: NctrlPropertyEvaluationInput) -> NctrlPropertyCheckResult:
    computed = build_portfolio_outlier_breakdown(inputs.trade_log, initial_cash=_numeric_or_none(inputs.portfolio_summary.get("initial_cash")))
    keys = ["total_pnl", "pnl_excluding_top_1", "pnl_excluding_top_3", "sign_flip_excluding_top_1", "sign_flip_excluding_top_3"]
    mismatches = [key for key in keys if not _same_value(computed.get(key), inputs.portfolio_outlier_breakdown.get(key))]
    status: PropertyStatus = "fail" if mismatches else "pass"
    evidence = f"mismatches={mismatches}" if mismatches else "outlier arithmetic reconciles"
    return NctrlPropertyCheckResult("P7", status, evidence, "ex-topN arithmetic property")


def _check_p8_benchmarks(inputs: NctrlPropertyEvaluationInput) -> NctrlPropertyCheckResult:
    report = inputs.benchmark_report
    if report.empty or "benchmark" not in report.columns or "return" not in report.columns or "observations" not in report.columns:
        return NctrlPropertyCheckResult("P8", "fail", "benchmark schema missing", "benchmark numerical sanity")
    present = set(report["benchmark"].astype(str))
    missing = sorted(REQUIRED_BENCHMARKS - present)
    impossible = []
    for _, row in report.iterrows():
        value = pd.to_numeric(pd.Series([row.get("return")]), errors="coerce").iat[0]
        observations = int(pd.to_numeric(pd.Series([row.get("observations")]), errors="coerce").fillna(0).iat[0])
        if observations > 0 and not _finite(value):
            impossible.append(str(row.get("benchmark")))
    passed = not missing and not impossible
    evidence = f"missing={missing}; nonfinite_with_observations={impossible}"
    return NctrlPropertyCheckResult("P8", "pass" if passed else "fail", evidence, "benchmark numerical sanity")


def _finite(value: object) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _numeric_or_none(value: object) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def _same_value(left: object, right: object) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return bool(left) == bool(right)
    try:
        left_float = float(left)
        right_float = float(right)
    except (TypeError, ValueError):
        return left == right
    if math.isnan(left_float) and math.isnan(right_float):
        return True
    return math.isclose(left_float, right_float, rel_tol=1e-9, abs_tol=1e-9)
