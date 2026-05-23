from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd

from src.experiments.sec8k_predrift_preregistration_validator import (
    validate_sec8k_predrift_preregistration,
)


RUN_ID = "SEC8K-PREDRIFT-EXISTING-DAILY-DIAGNOSTIC-001"
TRIAL_ID = "SEC8K-PREDRIFT-001"
SPEC_DIR = Path("experiments/provider_aware_research/sec8k_predrift_preregistration_20260523")
EVENT_PANEL = Path("experiments/provider_aware_research/sec_8k_multisymbol_event_timing_diagnostic_20260522/sec_8k_multisymbol_event_panel.csv")
PRICE_FILE = Path("experiments/provider_aware_research/data_inputs/databento_xmom_20260520/prices.csv")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/SEC8K-PREDRIFT-EXISTING-DAILY-DIAGNOSTIC-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-SEC8K-Predrift-Existing-Daily-Diagnostic-2026-05-23.md")


def run_sec8k_predrift_existing_daily_diagnostic(
    *,
    spec_dir: str | Path = SPEC_DIR,
    event_panel_path: str | Path = EVENT_PANEL,
    price_file: str | Path = PRICE_FILE,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
    min_event_count: int | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    prereg = validate_sec8k_predrift_preregistration(spec_dir)
    _write_json(output / "preflight_report.json", prereg)
    if prereg["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED")
        _write_json(output / "final_decision.json", decision)
        return decision

    manifest = json.loads((Path(spec_dir) / "preregistration_manifest.json").read_text(encoding="utf-8"))
    events = pd.read_csv(event_panel_path)
    prices = pd.read_csv(price_file)
    panel = build_predrift_panel(
        events,
        prices,
        pre_window_days=int(manifest["pre_window_days"]),
        baseline_lookback_days=int(manifest["baseline_lookback_days"]),
    )
    summary = summarize_predrift_panel(panel, min_event_count=min_event_count or int(manifest["minimum_event_count"]))
    decision = _final_decision(summary)
    _write_csv(output / "predrift_panel.csv", list(panel[0].keys()) if panel else [], panel)
    _write_json(output / "diagnostic_summary.json", summary)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), summary, decision)
    return decision


def build_predrift_panel(
    events: pd.DataFrame,
    prices: pd.DataFrame,
    *,
    pre_window_days: int,
    baseline_lookback_days: int,
) -> list[dict[str, Any]]:
    event_dates_by_symbol: dict[str, set[str]] = {}
    for _, row in events.iterrows():
        if str(row.get("status")) != "event":
            continue
        event_dates_by_symbol.setdefault(str(row["symbol"]), set()).add(str(row["reaction_session_date"]))

    rows: list[dict[str, Any]] = []
    prices = prices.copy()
    prices["date"] = pd.to_datetime(prices["date"])
    for symbol, symbol_prices in prices.groupby("symbol"):
        symbol = str(symbol)
        if symbol not in event_dates_by_symbol:
            continue
        frame = symbol_prices.sort_values("date").reset_index(drop=True)
        event_dates = event_dates_by_symbol[symbol]
        for index in range(baseline_lookback_days + pre_window_days, len(frame)):
            event_date = frame.iloc[index]["date"].date().isoformat()
            is_event = event_date in event_dates
            pre_start = index - pre_window_days
            baseline_start = pre_start - baseline_lookback_days
            pre = frame.iloc[pre_start:index]
            baseline = frame.iloc[baseline_start:pre_start]
            if pre.empty or baseline.empty:
                continue
            start_close = float(pre.iloc[0]["close"])
            end_close = float(pre.iloc[-1]["close"])
            baseline_volumes = [float(value) for value in baseline["volume"].tolist() if float(value) > 0]
            if start_close <= 0 or not baseline_volumes:
                continue
            pre_volume_median = median(float(value) for value in pre["volume"].tolist())
            baseline_volume_median = median(baseline_volumes)
            pre_return = end_close / start_close - 1.0
            rows.append(
                {
                    "symbol": symbol,
                    "event_date": event_date,
                    "is_sec8k_event": bool(is_event),
                    "pre_window_start": frame.iloc[pre_start]["date"].date().isoformat(),
                    "pre_window_end": frame.iloc[index - 1]["date"].date().isoformat(),
                    "pre_window_days": pre_window_days,
                    "baseline_lookback_days": baseline_lookback_days,
                    "pre_window_return": round(pre_return, 10),
                    "pre_window_abs_return": round(abs(pre_return), 10),
                    "pre_window_volume_ratio": round(pre_volume_median / baseline_volume_median if baseline_volume_median > 0 else 0.0, 8),
                    "provider_query_performed": False,
                    "market_data_downloaded": False,
                    "source": "existing_sec8k_event_panel_and_existing_daily_databento_prices",
                }
            )
    return rows


def summarize_predrift_panel(rows: list[dict[str, Any]], *, min_event_count: int) -> dict[str, Any]:
    events = [row for row in rows if row["is_sec8k_event"] is True]
    controls = [row for row in rows if row["is_sec8k_event"] is False]
    event_signed = _median(events, "pre_window_return")
    control_signed = _median(controls, "pre_window_return")
    event_abs = _median(events, "pre_window_abs_return")
    control_abs = _median(controls, "pre_window_abs_return")
    event_volume = _median(events, "pre_window_volume_ratio")
    control_volume = _median(controls, "pre_window_volume_ratio")
    blockers: list[str] = []
    if len(events) < min_event_count:
        blockers.append(f"event_count_below_{min_event_count}")
    if event_signed <= control_signed:
        blockers.append("event_signed_predrift_not_above_control")
    if event_abs <= control_abs:
        blockers.append("event_abs_predrift_not_above_control")
    if event_volume <= control_volume:
        blockers.append("event_volume_predrift_not_above_control")
    decision = "SEC8K_PREDRIFT_CANDIDATE_ONLY_REQUIRES_SEPARATE_TRIAL" if not blockers else "SEC8K_PREDRIFT_ARCHIVE_CURRENT_FORM"
    return {
        "status": "complete",
        "decision": decision,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "event_count": len(events),
        "control_count": len(controls),
        "min_event_count": min_event_count,
        "event_median_pre_window_return": round(event_signed, 10),
        "control_median_pre_window_return": round(control_signed, 10),
        "signed_return_lift": round(event_signed - control_signed, 10),
        "event_median_pre_window_abs_return": round(event_abs, 10),
        "control_median_pre_window_abs_return": round(control_abs, 10),
        "abs_return_lift": round(event_abs - control_abs, 10),
        "event_median_pre_window_volume_ratio": round(event_volume, 8),
        "control_median_pre_window_volume_ratio": round(control_volume, 8),
        "volume_ratio_lift": round(event_volume - control_volume, 8),
        "candidate_allowed": not blockers,
        "promotion_allowed": False,
        "blockers": blockers or ["candidate_requires_separate_preregistration"],
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }


def validate_sec8k_predrift_existing_daily_diagnostic(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["preflight_report.json", "predrift_panel.csv", "diagnostic_summary.json", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _validation_report(checks)
    summary = json.loads((path / "diagnostic_summary.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    rows = _read_csv(path / "predrift_panel.csv")
    forbidden_cols = {"post_event_return", "trade_pnl", "optimized_threshold", "sweep_id"}
    columns = set(rows[0].keys()) if rows else set()
    _check(checks, "panel_non_empty", len(rows) > 0, f"rows={len(rows)}")
    _check(checks, "forbidden_columns_absent", not (columns & forbidden_cols), f"present={sorted(columns & forbidden_cols)}")
    _check(checks, "summary_no_provider_query", summary.get("provider_query_performed") is False, str(summary.get("provider_query_performed")))
    _check(checks, "summary_no_market_download", summary.get("market_data_downloaded") is False, str(summary.get("market_data_downloaded")))
    _check(checks, "summary_no_backtest", summary.get("backtest_performed") is False, str(summary.get("backtest_performed")))
    _check(checks, "decision_no_promotion", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    return _validation_report(checks)


def _final_decision(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "complete",
        "decision": summary["decision"],
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "event_count": summary["event_count"],
        "control_count": summary["control_count"],
        "candidate_allowed": summary["candidate_allowed"],
        "promotion_allowed": False,
        "blockers": summary["blockers"],
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }


def _blocked_decision(reason: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": "SEC8K_PREDRIFT_DIAGNOSTIC_BLOCKED",
        "reason": reason,
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "promotion_allowed": False,
    }


def _write_vault_report(path: Path, summary: dict[str, Any], decision: dict[str, Any]) -> None:
    text = (
        "# Report SEC8K Predrift Existing Daily Diagnostic - 2026-05-23\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Existing daily artifacts only. No provider query, market-data download, intraday query, parameter sweep, backtest, paper/live trading, or promotion occurred.\n\n"
        "## Result\n\n"
        f"- Event count: {summary['event_count']}\n"
        f"- Control count: {summary['control_count']}\n"
        f"- Event median pre-window return: {summary['event_median_pre_window_return']}\n"
        f"- Control median pre-window return: {summary['control_median_pre_window_return']}\n"
        f"- Signed return lift: {summary['signed_return_lift']}\n"
        f"- Event median pre-window abs return: {summary['event_median_pre_window_abs_return']}\n"
        f"- Control median pre-window abs return: {summary['control_median_pre_window_abs_return']}\n"
        f"- Abs return lift: {summary['abs_return_lift']}\n"
        f"- Event median pre-window volume ratio: {summary['event_median_pre_window_volume_ratio']}\n"
        f"- Control median pre-window volume ratio: {summary['control_median_pre_window_volume_ratio']}\n"
        f"- Volume ratio lift: {summary['volume_ratio_lift']}\n"
        f"- Blockers: {', '.join(summary['blockers'])}\n\n"
        "## Interpretation\n\n"
        "This diagnostic tests whether SEC 8-K Item 2.02 events are preceded by measurable daily drift. It is not a trading strategy and cannot promote without a separate trial.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _median(rows: list[dict[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in rows if row.get(key) not in {"", None}]
    return median(values) if values else 0.0


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _validation_report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "SEC8K_PREDRIFT_EXISTING_DAILY_DIAGNOSTIC_PASS" if failed == 0 else "SEC8K_PREDRIFT_EXISTING_DAILY_DIAGNOSTIC_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run SEC8K predrift existing daily diagnostic.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_sec8k_predrift_existing_daily_diagnostic()
    report = validate_sec8k_predrift_existing_daily_diagnostic()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
