from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd

from src.experiments.dollar_bar_diagnostic import build_dollar_bars


RUN_ID = "DOLLARBAR-MICROREV-RUN-001"
TRIAL_ID = "TRIAL-DOLLARBAR-MICROREV-001"
ROOT = Path("experiments/provider_aware_research")
SOURCE_DIR = ROOT / "data_inputs" / "gaprev_mini_panel_databento_intraday_probe_20260521"
CONTRACT_DIR = ROOT / "static_dollarbar_data_layer_contract_20260521"
EMA_REJECTION_DIR = ROOT / "dollarbar_ema_rejection_20260521"
PREREG_DIR = ROOT / "dollarbar_microrev_preregistration_20260521"
OUTPUT_DIR = ROOT / "execution_outputs" / RUN_ID
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-DollarBar-MicroRev-Trial-2026-05-21.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-21-codex-dollarbar-microrev-trial.md")


@dataclass(frozen=True)
class MicroRevParams:
    shock_z_threshold: float = -1.5
    rolling_window_bars: int = 20
    min_rolling_observations: int = 10
    hold_bars: int = 3
    round_trip_cost_bps: float = 500.0
    min_trade_count_for_promotion: int = 30
    min_net_return_sum_for_promotion: float = 0.0
    min_positive_net_trade_rate: float = 0.50


def run_dollarbar_microrev_protocol(source_dir: str | Path = SOURCE_DIR) -> dict[str, Any]:
    _ensure_dirs()
    params = MicroRevParams()
    bars_files = sorted(Path(source_dir).glob("*/bars.csv"))
    contract = write_static_data_layer_contract(bars_files)
    ema_rejection = write_ema_rejection_register()
    prereg = write_microrev_preregistration(params, bars_files)
    panel = [evaluate_microrev_file(path, params) for path in bars_files]
    _write_csv(OUTPUT_DIR / "microrev_panel.csv", list(panel[0].keys()) if panel else [], panel)
    summary = summarize_microrev_panel(panel, params)
    _write_json(OUTPUT_DIR / "microrev_summary.json", summary)
    final_decision = write_final_decision(contract, ema_rejection, prereg, summary)
    write_vault_report(final_decision, summary, panel)
    return final_decision


def write_static_data_layer_contract(bars_files: list[Path]) -> dict[str, Any]:
    manifest = {
        "status": "STATIC_DOLLARBAR_DATA_LAYER_CANONICAL",
        "contract_id": "CONTRACT-STATIC-DOLLARBAR-001",
        "source": "Report-Dollar-Bar-Diagnostic-2026-05-21 and rejected EMA validation",
        "allowed_transform": "static_average_dollar_bucket",
        "target_bucket_formula": "sum(close * volume) / time_bar_count",
        "forbidden_transforms": ["rolling_ema_dollar_bucket", "pnl_selected_bucket", "strategy_return_selected_bucket"],
        "input_file_count": len(bars_files),
        "provider_query_performed": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
    }
    _write_json(CONTRACT_DIR / "static_dollarbar_contract_manifest.json", manifest)
    _write_csv(
        CONTRACT_DIR / "input_panel.csv",
        ["bars_path"],
        [{"bars_path": str(path)} for path in bars_files],
    )
    _write_csv(
        CONTRACT_DIR / "blocked_actions.csv",
        ["action", "status", "reason"],
        [
            {"action": "select_bucket_from_pnl", "status": "blocked", "reason": "Static bucket is a data-layer rule."},
            {"action": "use_ema_bucket", "status": "blocked", "reason": "EMA transform failed preregistered validation."},
            {"action": "paper_trading", "status": "blocked", "reason": "Data-layer contract is not a strategy."},
            {"action": "live_trading", "status": "blocked", "reason": "Data-layer contract is not a strategy."},
        ],
    )
    return manifest


def write_ema_rejection_register() -> dict[str, Any]:
    prior_decision_path = ROOT / "dollarbar_transform_validation_20260521" / "final_decision.json"
    prior = json.loads(prior_decision_path.read_text(encoding="utf-8")) if prior_decision_path.exists() else {}
    manifest = {
        "status": "EMA_DOLLARBAR_TRANSFORM_REJECTED_AND_BLOCKED",
        "rejection_id": "REJECT-EMA-DOLLARBAR-001",
        "prior_decision": prior.get("decision", "missing_prior_decision"),
        "prior_coverage_rate": prior.get("coverage_rate"),
        "prior_median_stability_score_delta": prior.get("median_stability_score_delta"),
        "future_use_policy": "blocked_until_new_preregistration_with_new_data_or_theory",
        "provider_query_performed": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
    }
    _write_json(EMA_REJECTION_DIR / "ema_rejection_manifest.json", manifest)
    _write_csv(
        EMA_REJECTION_DIR / "blocked_actions.csv",
        ["action", "status", "reason"],
        [
            {"action": "use_ema_in_microrev", "status": "blocked", "reason": "Rejected by validation."},
            {"action": "retune_ema_span", "status": "blocked", "reason": "Would be post-hoc tuning."},
            {"action": "compare_ema_by_pnl", "status": "blocked", "reason": "PnL was forbidden in transform validation."},
        ],
    )
    return manifest


def write_microrev_preregistration(params: MicroRevParams, bars_files: list[Path]) -> dict[str, Any]:
    manifest = {
        "status": "PREREGISTERED_EXISTING_PANEL_ONLY",
        "preregistration_id": "PREREG-DOLLARBAR-MICROREV-001",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "input_panel": "existing_gaprev_mini_panel_databento_intraday_probe_20260521",
        "bar_transform": "static_average_dollar_bucket",
        "direction": "long_only_micro_reversion_after_negative_dollarbar_shock",
        "parameters": params.__dict__,
        "promotion_rule": "trade_count>=30 and net_return_sum>0 and positive_net_trade_rate>=0.50",
        "provider_query_performed": False,
        "parameter_sweep_performed": False,
        "oos_claim_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "input_file_count": len(bars_files),
    }
    _write_json(PREREG_DIR / "microrev_preregistration_manifest.json", manifest)
    _write_csv(
        PREREG_DIR / "parameter_freeze.csv",
        ["parameter", "value", "status"],
        [{"parameter": key, "value": value, "status": "frozen"} for key, value in params.__dict__.items()],
    )
    _write_csv(
        PREREG_DIR / "blocked_actions.csv",
        ["action", "status", "reason"],
        [
            {"action": "parameter_sweep", "status": "blocked", "reason": "One frozen parameter set only."},
            {"action": "provider_query", "status": "blocked", "reason": "Existing panel only."},
            {"action": "strategy_promotion", "status": "blocked", "reason": "Requires final gate pass."},
        ],
    )
    return manifest


def evaluate_microrev_file(path: str | Path, params: MicroRevParams) -> dict[str, Any]:
    bars_path = Path(path)
    frame = pd.read_csv(bars_path)
    required = {"symbol", "timestamp", "open", "high", "low", "close", "volume"}
    missing = sorted(required - set(frame.columns))
    base: dict[str, Any] = {
        "source": bars_path.parent.name,
        "bars_path": str(bars_path),
        "status": "blocked",
        "symbol": "",
        "time_bar_count": 0,
        "dollar_bar_count": 0,
        "trade_count": 0,
        "gross_return_sum": 0.0,
        "net_return_sum": 0.0,
        "positive_net_trade_count": 0,
        "reason": "",
    }
    if missing:
        return {**base, "reason": f"missing_columns:{','.join(missing)}"}
    frame = frame.sort_values("timestamp").reset_index(drop=True)
    frame = frame[(frame["close"].astype(float) > 0) & (frame["volume"].astype(float) >= 0)].copy()
    if frame.empty:
        return {**base, "reason": "empty_after_sanity_filter"}
    frame["dollar_value"] = frame["close"].astype(float) * frame["volume"].astype(float)
    target = float(frame["dollar_value"].sum()) / len(frame)
    dollar_bars = build_dollar_bars(frame, target)
    trades = simulate_microrev_trades(dollar_bars, params)
    gross = [trade["gross_return"] for trade in trades]
    net = [trade["net_return"] for trade in trades]
    return {
        **base,
        "status": "evaluated",
        "symbol": str(frame["symbol"].iloc[0]),
        "time_bar_count": len(frame),
        "dollar_bar_count": len(dollar_bars),
        "target_dollar_bucket": round(target, 6),
        "trade_count": len(trades),
        "gross_return_sum": round(sum(gross), 10),
        "net_return_sum": round(sum(net), 10),
        "positive_net_trade_count": sum(1 for value in net if value > 0),
        "median_net_return": round(median(net), 10) if net else "",
        "reason": "evaluated_existing_panel_static_dollarbars",
    }


def simulate_microrev_trades(dollar_bars: list[dict[str, Any]], params: MicroRevParams) -> list[dict[str, Any]]:
    closes = [float(row["close"]) for row in dollar_bars]
    returns = [(current / previous) - 1.0 for previous, current in zip(closes, closes[1:]) if previous > 0]
    trades: list[dict[str, Any]] = []
    for return_index, value in enumerate(returns):
        if return_index < params.min_rolling_observations:
            continue
        window = returns[max(0, return_index - params.rolling_window_bars) : return_index]
        if len(window) < params.min_rolling_observations:
            continue
        sigma = _pstdev(window)
        if sigma <= 0:
            continue
        z_score = (value - (sum(window) / len(window))) / sigma
        if z_score > params.shock_z_threshold:
            continue
        entry_bar_index = return_index + 1
        exit_bar_index = entry_bar_index + params.hold_bars
        if exit_bar_index >= len(dollar_bars):
            continue
        entry_price = float(dollar_bars[entry_bar_index]["close"])
        exit_price = float(dollar_bars[exit_bar_index]["close"])
        gross_return = exit_price / entry_price - 1.0
        net_return = gross_return - params.round_trip_cost_bps / 10000.0
        trades.append(
            {
                "entry_index": entry_bar_index,
                "exit_index": exit_bar_index,
                "shock_z_score": z_score,
                "gross_return": gross_return,
                "net_return": net_return,
            }
        )
    return trades


def summarize_microrev_panel(panel: list[dict[str, Any]], params: MicroRevParams) -> dict[str, Any]:
    evaluated = [row for row in panel if row["status"] == "evaluated"]
    total_trades = sum(int(row["trade_count"]) for row in evaluated)
    net_sum = sum(float(row["net_return_sum"]) for row in evaluated)
    gross_sum = sum(float(row["gross_return_sum"]) for row in evaluated)
    positive = sum(int(row["positive_net_trade_count"]) for row in evaluated)
    positive_rate = positive / total_trades if total_trades else 0.0
    blockers: list[str] = []
    if total_trades < params.min_trade_count_for_promotion:
        blockers.append("trade_count_below_30")
    if net_sum <= params.min_net_return_sum_for_promotion:
        blockers.append("net_return_not_positive_after_500bps")
    if positive_rate < params.min_positive_net_trade_rate:
        blockers.append("positive_net_trade_rate_below_50pct")
    return {
        "status": "evaluated_existing_panel",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "evaluated_file_count": len(evaluated),
        "trade_count": total_trades,
        "gross_return_sum": round(gross_sum, 10),
        "net_return_sum": round(net_sum, 10),
        "positive_net_trade_count": positive,
        "positive_net_trade_rate": round(positive_rate, 6),
        "round_trip_cost_bps": params.round_trip_cost_bps,
        "promotion_allowed": not blockers,
        "promotion_blockers": blockers,
        "provider_query_performed": False,
        "parameter_sweep_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
    }


def write_final_decision(
    contract: dict[str, Any],
    ema_rejection: dict[str, Any],
    prereg: dict[str, Any],
    summary: dict[str, Any],
) -> dict[str, Any]:
    decision = {
        "status": "complete",
        "decision": "DOLLARBAR_MICROREV_ARCHIVE_CURRENT_FORM" if not summary["promotion_allowed"] else "DOLLARBAR_MICROREV_RESEARCH_CANDIDATE_ONLY",
        "trial_id": TRIAL_ID,
        "run_id": RUN_ID,
        "points_completed": {
            "1_static_dollarbar_data_layer_contract": contract["status"],
            "2_ema_transform_blocked": ema_rejection["status"],
            "3_microrev_preregistration": prereg["status"],
            "4_static_dollarbar_microrev_probe": summary["status"],
            "5_final_decision": "NO_PROMOTION" if not summary["promotion_allowed"] else "RESEARCH_CANDIDATE_ONLY",
        },
        "evaluated_file_count": summary["evaluated_file_count"],
        "trade_count": summary["trade_count"],
        "gross_return_sum": summary["gross_return_sum"],
        "net_return_sum": summary["net_return_sum"],
        "positive_net_trade_rate": summary["positive_net_trade_rate"],
        "round_trip_cost_bps": summary["round_trip_cost_bps"],
        "promotion_allowed": False,
        "promotion_blockers": summary["promotion_blockers"] or ["research_candidate_not_promotable_without_fresh_prereg_oos"],
        "provider_query_performed": False,
        "backtest_performed_on_existing_panel": True,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }
    _write_json(OUTPUT_DIR / "final_decision.json", decision)
    return decision


def validate_dollarbar_microrev_protocol(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, Any]] = []
    required = ["microrev_panel.csv", "microrev_summary.json", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    _check(checks, "contract_exists", (CONTRACT_DIR / "static_dollarbar_contract_manifest.json").is_file(), str(CONTRACT_DIR))
    _check(checks, "ema_rejection_exists", (EMA_REJECTION_DIR / "ema_rejection_manifest.json").is_file(), str(EMA_REJECTION_DIR))
    _check(checks, "prereg_exists", (PREREG_DIR / "microrev_preregistration_manifest.json").is_file(), str(PREREG_DIR))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    panel = _read_csv(path / "microrev_panel.csv")
    summary = json.loads((path / "microrev_summary.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    forbidden_columns = {"sharpe", "dsr", "paper_signal", "live_signal"}
    columns = set(panel[0].keys()) if panel else set()
    _check(checks, "panel_non_empty", len(panel) > 0, f"rows={len(panel)}")
    _check(checks, "forbidden_columns_absent", not (columns & forbidden_columns), f"present={sorted(columns & forbidden_columns)}")
    _check(checks, "no_provider_query", summary.get("provider_query_performed") is False and decision.get("provider_query_performed") is False, str(summary))
    _check(checks, "cost_realism_500bps", float(summary.get("round_trip_cost_bps", 0.0)) == 500.0, str(summary.get("round_trip_cost_bps")))
    _check(checks, "promotion_not_allowed", decision.get("promotion_allowed") is False, str(decision))
    _check(checks, "all_five_points_recorded", len(decision.get("points_completed", {})) == 5, str(decision.get("points_completed")))
    return _report(checks)


def write_vault_report(decision: dict[str, Any], summary: dict[str, Any], panel: list[dict[str, Any]]) -> None:
    rows = "\n".join(
        f"- {row['source']} {row['symbol']} trades={row['trade_count']} gross={row['gross_return_sum']} net={row['net_return_sum']}"
        for row in panel
    )
    text = (
        "# Report DollarBar MicroRev Trial - 2026-05-21\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Five-Step Run\n\n"
        + "\n".join(f"- {step}: {status}" for step, status in decision["points_completed"].items())
        + "\n\n"
        "## Result\n\n"
        f"- Evaluated files: {summary['evaluated_file_count']}\n"
        f"- Trades: {summary['trade_count']}\n"
        f"- Gross return sum: {summary['gross_return_sum']}\n"
        f"- Net return sum after 500 bps: {summary['net_return_sum']}\n"
        f"- Positive net trade rate: {summary['positive_net_trade_rate']}\n"
        f"- Promotion blockers: {', '.join(decision['promotion_blockers'])}\n\n"
        "## Panel\n\n"
        f"{rows}\n\n"
        "## Interpretation\n\n"
        "Static dollar-bars remain a canonical data-layer representation, but this micro-reversion rule is not promoted. "
        "The run used only existing intraday artifacts and did not query providers, sweep parameters, paper trade, live trade, or promote a strategy.\n"
    )
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run static dollar-bar MicroRev five-step protocol.")
    parser.add_argument("--source-dir", default=str(SOURCE_DIR))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_dollarbar_microrev_protocol(args.source_dir)
    report = validate_dollarbar_microrev_protocol()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _ensure_dirs() -> None:
    for path in [CONTRACT_DIR, EMA_REJECTION_DIR, PREREG_DIR, OUTPUT_DIR, VAULT_REPORT.parent, VAULT_DEVLOG.parent]:
        path.mkdir(parents=True, exist_ok=True)


def _pstdev(values: list[float]) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((value - mean) ** 2 for value in values) / len(values))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _check(checks: list[dict[str, Any]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "DOLLARBAR_MICROREV_PROTOCOL_PASS" if failed == 0 else "DOLLARBAR_MICROREV_PROTOCOL_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
