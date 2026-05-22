from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd


RUN_ID = "AMIHUD-LIQUIDITY-TOXICITY-001"
TRIAL_ID = "TRIAL-LIQUIDITY-TOXICITY-DIAGNOSTIC-001"
ARTIFACT_DIR = Path("experiments/provider_aware_research/amihud_liquidity_toxicity_20260522")
TRADE_LOG = Path("experiments/runs/xmom_trial_001_20260520/portfolio_trade_log.csv")
PRICE_FILE = Path("experiments/provider_aware_research/data_inputs/databento_xmom_20260520/prices.csv")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Amihud-Liquidity-Toxicity-Diagnostic-2026-05-22.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-22-codex-amihud-liquidity-toxicity-diagnostic.md")


def run_amihud_liquidity_toxicity_diagnostic(
    trade_log: str | Path = TRADE_LOG,
    price_file: str | Path = PRICE_FILE,
    lookback_days: int = 20,
) -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    trades = pd.read_csv(trade_log)
    prices = pd.read_csv(price_file)
    diagnostics = [
        diagnose_trade_liquidity(row, prices, lookback_days=lookback_days)
        for _, row in trades.iterrows()
    ]
    diagnostics = [row for row in diagnostics if row["status"] == "evaluated"]
    diagnostics = assign_liquidity_buckets(diagnostics)
    _write_csv(ARTIFACT_DIR / "amihud_trade_panel.csv", list(diagnostics[0].keys()), diagnostics)
    _write_csv(
        ARTIFACT_DIR / "blocked_actions.csv",
        ["action", "status", "reason"],
        build_blocked_actions(),
    )
    summary = summarize_liquidity_toxicity(diagnostics, lookback_days)
    _write_json(ARTIFACT_DIR / "diagnostic_summary.json", summary)
    decision = write_final_decision(summary)
    write_vault_report(summary, decision, diagnostics)
    return decision


def diagnose_trade_liquidity(trade: pd.Series, prices: pd.DataFrame, lookback_days: int = 20) -> dict[str, Any]:
    symbol = str(trade["symbol"])
    signal_date = str(trade["signal_date"])
    pnl = float(trade["pnl"])
    symbol_prices = prices[prices["symbol"].astype(str).eq(symbol)].copy()
    if symbol_prices.empty:
        return {"status": "missing_symbol_prices", "symbol": symbol, "signal_date": signal_date}
    symbol_prices["date"] = pd.to_datetime(symbol_prices["date"])
    cutoff = pd.Timestamp(signal_date)
    window = symbol_prices[symbol_prices["date"] < cutoff].tail(lookback_days + 1).copy()
    if len(window) < lookback_days + 1:
        return {"status": "insufficient_lookback", "symbol": symbol, "signal_date": signal_date, "rows": len(window)}
    window["return"] = window["close"].astype(float).pct_change()
    window["dollar_volume"] = window["close"].astype(float) * window["volume"].astype(float)
    valid = window.dropna(subset=["return"])
    valid = valid[valid["dollar_volume"] > 0]
    if len(valid) < lookback_days:
        return {"status": "insufficient_valid_observations", "symbol": symbol, "signal_date": signal_date, "rows": len(valid)}
    amihud = (valid["return"].abs() / valid["dollar_volume"]).mean()
    return {
        "status": "evaluated",
        "symbol": symbol,
        "signal_date": signal_date,
        "entry_date": str(trade["entry_date"]),
        "exit_date": str(trade["exit_date"]),
        "lookback_days": lookback_days,
        "amihud_illiq_20d": round(float(amihud), 14),
        "avg_dollar_volume_20d": round(float(trade.get("avg_dollar_volume_20d", 0.0)), 6),
        "rolling_volatility_20d": round(float(trade.get("rolling_volatility_20d", 0.0)), 10),
        "pnl": round(pnl, 6),
        "return_pct": round(float(trade["return_pct"]), 10),
        "toxicity_label": "loser" if pnl <= 0 else "winner",
    }


def assign_liquidity_buckets(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    threshold = median(float(row["amihud_illiq_20d"]) for row in rows)
    output = []
    for row in rows:
        tagged = dict(row)
        tagged["amihud_median_threshold"] = round(threshold, 14)
        tagged["liquidity_bucket"] = "high_illiq" if float(row["amihud_illiq_20d"]) >= threshold else "low_illiq"
        output.append(tagged)
    return output


def summarize_liquidity_toxicity(rows: list[dict[str, Any]], lookback_days: int) -> dict[str, Any]:
    high = [row for row in rows if row["liquidity_bucket"] == "high_illiq"]
    low = [row for row in rows if row["liquidity_bucket"] == "low_illiq"]
    high_loser_rate = _loser_rate(high)
    low_loser_rate = _loser_rate(low)
    high_median_pnl = _median_pnl(high)
    low_median_pnl = _median_pnl(low)
    separation = high_loser_rate - low_loser_rate
    blockers: list[str] = []
    if len(rows) < 30:
        blockers.append("trade_count_below_30")
    if separation < 0.25:
        blockers.append("insufficient_loser_rate_separation")
    if high_median_pnl >= low_median_pnl:
        blockers.append("high_illiq_median_pnl_not_worse")
    decision = "LIQUIDITY_TOXICITY_FILTER_CANDIDATE_ONLY" if not blockers else "LIQUIDITY_TOXICITY_DIAGNOSTIC_ARCHIVE_CURRENT_FORM"
    return {
        "status": "diagnostic_complete_existing_artifacts_only",
        "decision": decision,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "lookback_days": lookback_days,
        "trade_count": len(rows),
        "high_illiq_count": len(high),
        "low_illiq_count": len(low),
        "high_illiq_loser_rate": round(high_loser_rate, 6),
        "low_illiq_loser_rate": round(low_loser_rate, 6),
        "loser_rate_separation": round(separation, 6),
        "high_illiq_median_pnl": round(high_median_pnl, 6),
        "low_illiq_median_pnl": round(low_median_pnl, 6),
        "promotion_allowed": False,
        "candidate_filter_allowed": not blockers,
        "blockers": blockers or ["candidate_filter_requires_separate_preregistration"],
        "provider_query_performed": False,
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
        "trade_count": summary["trade_count"],
        "candidate_filter_allowed": summary["candidate_filter_allowed"],
        "promotion_allowed": False,
        "blockers": summary["blockers"],
        "provider_query_performed": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "next_unblocked_step": "Only if candidate_filter_allowed is true: create separate preregistration before using liquidity as a filter.",
    }
    _write_json(ARTIFACT_DIR / "final_decision.json", decision)
    return decision


def validate_amihud_liquidity_toxicity_diagnostic(diag_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    path = Path(diag_dir)
    checks: list[dict[str, Any]] = []
    required = ["amihud_trade_panel.csv", "blocked_actions.csv", "diagnostic_summary.json", "final_decision.json"]
    _check(checks, "diagnostic_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    panel = _read_csv(path / "amihud_trade_panel.csv")
    blocked = _read_csv(path / "blocked_actions.csv")
    summary = json.loads((path / "diagnostic_summary.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    columns = set(panel[0].keys()) if panel else set()
    required_cols = {"symbol", "signal_date", "amihud_illiq_20d", "liquidity_bucket", "pnl", "toxicity_label"}
    forbidden_cols = {"strategy_return", "sharpe", "dsr", "optimized_threshold"}
    _check(checks, "panel_non_empty", len(panel) > 0, f"rows={len(panel)}")
    _check(checks, "required_columns_present", required_cols.issubset(columns), f"missing={sorted(required_cols - columns)}")
    _check(checks, "forbidden_columns_absent", not (columns & forbidden_cols), f"present={sorted(columns & forbidden_cols)}")
    _check(checks, "median_split_has_two_buckets", {row["liquidity_bucket"] for row in panel} == {"high_illiq", "low_illiq"}, "median split")
    _check(checks, "blocked_actions_all_blocked", all(row["status"] == "blocked" for row in blocked), "blocked actions")
    _check(checks, "summary_no_execution", summary.get("provider_query_performed") is False and summary.get("backtest_performed") is False, str(summary))
    _check(checks, "decision_no_promotion", decision.get("promotion_allowed") is False, str(decision))
    return _report(checks)


def write_vault_report(summary: dict[str, Any], decision: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    panel_rows = "\n".join(
        f"- {row['symbol']} {row['signal_date']} bucket={row['liquidity_bucket']} "
        f"amihud={row['amihud_illiq_20d']} pnl={row['pnl']} label={row['toxicity_label']}"
        for row in rows
    )
    text = (
        "# Report Amihud Liquidity Toxicity Diagnostic - 2026-05-22\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Diagnostic-only Amihud illiquidity analysis on existing XMOM trade and Databento daily price artifacts. "
        "No provider query, market-data download, new backtest, parameter sweep, paper/live trading or promotion was performed.\n\n"
        "## Result\n\n"
        f"- Trade count: {summary['trade_count']}\n"
        f"- High-ILLIQ loser rate: {summary['high_illiq_loser_rate']}\n"
        f"- Low-ILLIQ loser rate: {summary['low_illiq_loser_rate']}\n"
        f"- Loser-rate separation: {summary['loser_rate_separation']}\n"
        f"- High-ILLIQ median PnL: {summary['high_illiq_median_pnl']}\n"
        f"- Low-ILLIQ median PnL: {summary['low_illiq_median_pnl']}\n"
        f"- Blockers: {', '.join(summary['blockers'])}\n\n"
        "## Panel\n\n"
        f"{panel_rows}\n\n"
        "## Interpretation\n\n"
        "This diagnostic asks whether pre-entry Amihud illiquidity separates toxic trades from survivors. "
        "A positive diagnostic would still require a separate preregistration before any filter or strategy run.\n"
    )
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Amihud liquidity toxicity diagnostic on existing artifacts.")
    parser.add_argument("--trade-log", default=str(TRADE_LOG))
    parser.add_argument("--price-file", default=str(PRICE_FILE))
    parser.add_argument("--lookback-days", type=int, default=20)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_amihud_liquidity_toxicity_diagnostic(args.trade_log, args.price_file, args.lookback_days)
    report = validate_amihud_liquidity_toxicity_diagnostic()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def build_blocked_actions() -> list[list[Any]]:
    return [
        ["provider_query", "blocked", "Diagnostic uses existing XMOM Databento artifacts only."],
        ["run_backtest", "blocked", "No new strategy execution is authorized."],
        ["optimize_liquidity_threshold", "blocked", "Median split is diagnostic only, not a tuned threshold."],
        ["paper_trading", "blocked", "No strategy has passed preregistration and validation gates."],
        ["live_trading", "blocked", "No strategy is promotable."],
    ]


def _loser_rate(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if row["toxicity_label"] == "loser") / len(rows)


def _median_pnl(rows: list[dict[str, Any]]) -> float:
    if not rows:
        return 0.0
    return median(float(row["pnl"]) for row in rows)


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
        "gate_decision": "AMIHUD_LIQUIDITY_TOXICITY_DIAGNOSTIC_PASS" if failed == 0 else "AMIHUD_LIQUIDITY_TOXICITY_DIAGNOSTIC_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
