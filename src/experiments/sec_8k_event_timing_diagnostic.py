from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd


RUN_ID = "SEC-8K-EVENT-TIMING-DIAGNOSTIC-001"
TRIAL_ID = "TRIAL-SEC-8K-TIMING-DIAGNOSTIC-001"
ROOT = Path("experiments/provider_aware_research")
EVENT_PANEL = ROOT / "pead_sec_event_source_gate_20260521" / "pead_sec_event_source_panel.csv"
PRICE_FILE = ROOT / "data_inputs" / "databento_xmom_20260520" / "prices.csv"
ARTIFACT_DIR = ROOT / "sec_8k_event_timing_diagnostic_20260522"
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-SEC-8K-Event-Timing-Diagnostic-2026-05-22.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-22-codex-sec-8k-event-timing-diagnostic.md")


def run_sec_8k_event_timing_diagnostic(
    event_panel: str | Path = EVENT_PANEL,
    price_file: str | Path = PRICE_FILE,
    symbol: str = "CRMD",
    lookback_days: int = 20,
) -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(event_panel)
    prices = pd.read_csv(price_file)
    panel = build_event_timing_panel(events, prices, symbol=symbol, lookback_days=lookback_days)
    _write_csv(ARTIFACT_DIR / "sec_8k_event_timing_panel.csv", list(panel[0].keys()) if panel else [], panel)
    _write_csv(ARTIFACT_DIR / "blocked_actions.csv", ["action", "status", "reason"], build_blocked_actions())
    summary = summarize_event_timing_panel(panel, symbol=symbol, lookback_days=lookback_days)
    _write_json(ARTIFACT_DIR / "diagnostic_summary.json", summary)
    decision = write_final_decision(summary)
    write_vault_report(summary, decision, panel)
    return decision


def build_event_timing_panel(events: pd.DataFrame, prices: pd.DataFrame, *, symbol: str, lookback_days: int) -> list[dict[str, Any]]:
    symbol_prices = prices[prices["symbol"].astype(str).eq(symbol)].copy()
    symbol_prices["date"] = pd.to_datetime(symbol_prices["date"])
    symbol_prices = symbol_prices.sort_values("date").reset_index(drop=True)
    event_dates = {
        pd.Timestamp(value).date().isoformat()
        for value in events.get("reaction_session_date", pd.Series(dtype=str)).dropna().astype(str)
    }
    rows: list[dict[str, Any]] = []
    for index, row in symbol_prices.iterrows():
        if index < lookback_days:
            continue
        current_date = row["date"].date().isoformat()
        lookback = symbol_prices.iloc[index - lookback_days : index].copy()
        if lookback.empty:
            continue
        close = float(row["close"])
        previous_close = float(symbol_prices.iloc[index - 1]["close"])
        if previous_close <= 0:
            continue
        volume = float(row["volume"])
        lookback_volume = [float(value) for value in lookback["volume"].tolist() if float(value) > 0]
        if not lookback_volume:
            continue
        median_volume = median(lookback_volume)
        rows.append(
            {
                "symbol": symbol,
                "date": current_date,
                "is_sec_8k_event_day": current_date in event_dates,
                "return_abs": round(abs(close / previous_close - 1.0), 10),
                "signed_return": round(close / previous_close - 1.0, 10),
                "volume": int(volume),
                "volume_ratio_vs_20d_median": round(volume / median_volume if median_volume > 0 else 0.0, 8),
                "lookback_days": lookback_days,
                "source": "existing_sec_event_panel_and_existing_databento_prices",
            }
        )
    return rows


def summarize_event_timing_panel(rows: list[dict[str, Any]], *, symbol: str, lookback_days: int) -> dict[str, Any]:
    events = [row for row in rows if row["is_sec_8k_event_day"] is True]
    controls = [row for row in rows if row["is_sec_8k_event_day"] is False]
    event_abs = _median_value(events, "return_abs")
    control_abs = _median_value(controls, "return_abs")
    event_volume = _median_value(events, "volume_ratio_vs_20d_median")
    control_volume = _median_value(controls, "volume_ratio_vs_20d_median")
    abs_lift = event_abs - control_abs
    volume_lift = event_volume - control_volume
    blockers: list[str] = []
    if len(events) < 8:
        blockers.append("event_count_below_8")
    if event_abs <= control_abs:
        blockers.append("event_abs_return_not_above_control")
    if event_volume <= control_volume:
        blockers.append("event_volume_ratio_not_above_control")
    decision = "SEC_8K_TIMING_DIAGNOSTIC_CANDIDATE_ONLY" if not blockers else "SEC_8K_TIMING_DIAGNOSTIC_ARCHIVE_CURRENT_FORM"
    return {
        "status": "diagnostic_complete_existing_artifacts_only",
        "decision": decision,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "symbol": symbol,
        "lookback_days": lookback_days,
        "event_day_count": len(events),
        "control_day_count": len(controls),
        "event_median_abs_return": round(event_abs, 10),
        "control_median_abs_return": round(control_abs, 10),
        "abs_return_lift": round(abs_lift, 10),
        "event_median_volume_ratio": round(event_volume, 8),
        "control_median_volume_ratio": round(control_volume, 8),
        "volume_ratio_lift": round(volume_lift, 8),
        "candidate_timing_signal_allowed": not blockers,
        "promotion_allowed": False,
        "blockers": blockers or ["candidate_requires_separate_preregistration_and_direction_source"],
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }


def write_final_decision(summary: dict[str, Any]) -> dict[str, Any]:
    decision = {
        "status": "complete",
        "decision": summary["decision"],
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "event_day_count": summary["event_day_count"],
        "control_day_count": summary["control_day_count"],
        "candidate_timing_signal_allowed": summary["candidate_timing_signal_allowed"],
        "promotion_allowed": False,
        "blockers": summary["blockers"],
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "next_unblocked_step": "Only if candidate_timing_signal_allowed is true: preregister a separate event-window study with an ex-ante direction source.",
    }
    _write_json(ARTIFACT_DIR / "final_decision.json", decision)
    return decision


def validate_sec_8k_event_timing_diagnostic(diag_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    path = Path(diag_dir)
    checks: list[dict[str, Any]] = []
    required = ["sec_8k_event_timing_panel.csv", "blocked_actions.csv", "diagnostic_summary.json", "final_decision.json"]
    _check(checks, "diagnostic_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    panel = _read_csv(path / "sec_8k_event_timing_panel.csv")
    blocked = _read_csv(path / "blocked_actions.csv")
    summary = json.loads((path / "diagnostic_summary.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    columns = set(panel[0].keys()) if panel else set()
    required_columns = {"symbol", "date", "is_sec_8k_event_day", "return_abs", "volume_ratio_vs_20d_median"}
    forbidden_columns = {"pnl", "sharpe", "dsr", "strategy_return", "optimized_threshold"}
    _check(checks, "panel_non_empty", len(panel) > 0, f"rows={len(panel)}")
    _check(checks, "required_columns_present", required_columns.issubset(columns), f"missing={sorted(required_columns - columns)}")
    _check(checks, "forbidden_columns_absent", not (columns & forbidden_columns), f"present={sorted(columns & forbidden_columns)}")
    _check(checks, "has_event_and_control_days", _has_both_classes(panel), "event/control")
    _check(checks, "blocked_actions_all_blocked", all(row["status"] == "blocked" for row in blocked), "blocked")
    _check(checks, "summary_no_execution", summary.get("provider_query_performed") is False and summary.get("backtest_performed") is False, str(summary))
    _check(checks, "decision_no_promotion", decision.get("promotion_allowed") is False, str(decision))
    return _report(checks)


def write_vault_report(summary: dict[str, Any], decision: dict[str, Any], panel: list[dict[str, Any]]) -> None:
    event_rows = "\n".join(
        f"- {row['date']} abs_return={row['return_abs']} volume_ratio={row['volume_ratio_vs_20d_median']}"
        for row in panel
        if row["is_sec_8k_event_day"] is True
    )
    text = (
        "# Report SEC 8-K Event Timing Diagnostic - 2026-05-22\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Diagnostic-only comparison of SEC 8-K Item 2.02 event days versus non-event days using existing SEC event artifacts and existing Databento daily prices. "
        "No provider query, market-data download, backtest, parameter sweep, paper/live trading or promotion was performed.\n\n"
        "## Result\n\n"
        f"- Event days: {summary['event_day_count']}\n"
        f"- Control days: {summary['control_day_count']}\n"
        f"- Event median absolute return: {summary['event_median_abs_return']}\n"
        f"- Control median absolute return: {summary['control_median_abs_return']}\n"
        f"- Absolute-return lift: {summary['abs_return_lift']}\n"
        f"- Event median volume ratio: {summary['event_median_volume_ratio']}\n"
        f"- Control median volume ratio: {summary['control_median_volume_ratio']}\n"
        f"- Volume-ratio lift: {summary['volume_ratio_lift']}\n"
        f"- Blockers: {', '.join(summary['blockers'])}\n\n"
        "## Event Days\n\n"
        f"{event_rows}\n\n"
        "## Interpretation\n\n"
        "This diagnostic tests only whether SEC acceptance timing marks distinguishable event windows. It does not infer earnings surprise or trade direction from future returns.\n"
    )
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run SEC 8-K event timing diagnostic on existing artifacts.")
    parser.add_argument("--event-panel", default=str(EVENT_PANEL))
    parser.add_argument("--price-file", default=str(PRICE_FILE))
    parser.add_argument("--symbol", default="CRMD")
    parser.add_argument("--lookback-days", type=int, default=20)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_sec_8k_event_timing_diagnostic(args.event_panel, args.price_file, args.symbol, args.lookback_days)
    report = validate_sec_8k_event_timing_diagnostic()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def build_blocked_actions() -> list[list[Any]]:
    return [
        ["provider_query", "blocked", "Diagnostic uses existing SEC and Databento artifacts only."],
        ["infer_direction_from_returns", "blocked", "Would turn event timing into look-ahead leakage."],
        ["run_backtest", "blocked", "This is an event-window diagnostic, not a strategy."],
        ["parameter_sweep", "blocked", "No optimized event-window thresholds."],
        ["paper_trading", "blocked", "No strategy has been promoted."],
        ["live_trading", "blocked", "No strategy has been promoted."],
    ]


def _median_value(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    return median(float(row[key]) for row in rows)


def _has_both_classes(rows: list[dict[str, str]]) -> bool:
    values = {str(row["is_sec_8k_event_day"]).lower() for row in rows}
    return "true" in values and "false" in values


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]] | list[list[Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        if rows and isinstance(rows[0], dict):
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)  # type: ignore[arg-type]
        else:
            writer = csv.writer(handle)
            writer.writerow(fieldnames)
            writer.writerows(rows)  # type: ignore[arg-type]


def _check(checks: list[dict[str, Any]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "SEC_8K_EVENT_TIMING_DIAGNOSTIC_PASS" if failed == 0 else "SEC_8K_EVENT_TIMING_DIAGNOSTIC_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
