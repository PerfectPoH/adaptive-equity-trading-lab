from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.experiments.active_only_momentum_smoke_validator import validate_active_only_momentum_smoke_gate


RUN_ID = "ACTIVE-ONLY-MOMENTUM-SMOKE-RUN-001"
TRIAL_ID = "ACTIVE-ONLY-MOMENTUM-SMOKE-001"
SPEC_DIR = Path("experiments/provider_aware_research/active_only_momentum_smoke_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/ACTIVE-ONLY-MOMENTUM-SMOKE-RUN-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Active-Only-Momentum-Smoke-001-2026-05-24.md")


def run_active_only_momentum_smoke_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    preflight = validate_active_only_momentum_smoke_gate(spec_dir)
    _write_json(output / "preflight_report.json", preflight)
    if preflight["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED")
        _write_json(output / "final_decision.json", decision)
        return decision
    manifest = _read_json(Path(spec_dir) / "trial_manifest.json")
    trades = compute_monthly_top1_momentum_trades(
        Path(manifest["input_prices"]),
        symbols=list(manifest["symbols"]),
        lookback_days=int(manifest["lookback_days"]),
        hold_days=int(manifest["hold_days"]),
        rebalance_step_days=int(manifest["rebalance_step_days"]),
    )
    decision = _decision(trades, manifest)
    _write_csv(output / "trade_panel.csv", _fieldnames(trades), trades)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), decision)
    return decision


def compute_monthly_top1_momentum_trades(
    prices_path: str | Path,
    *,
    symbols: list[str],
    lookback_days: int,
    hold_days: int,
    rebalance_step_days: int,
) -> list[dict[str, Any]]:
    rows = _read_csv(Path(prices_path))
    by_symbol: dict[str, list[dict[str, Any]]] = {symbol: [] for symbol in symbols}
    for row in rows:
        symbol = row.get("symbol", "")
        if symbol in by_symbol:
            by_symbol[symbol].append(row)
    for symbol_rows in by_symbol.values():
        symbol_rows.sort(key=lambda row: row["date"])
    common_dates = sorted(set.intersection(*(set(row["date"] for row in by_symbol[symbol]) for symbol in symbols)))
    trades: list[dict[str, Any]] = []
    for index in range(lookback_days, max(lookback_days, len(common_dates) - hold_days), rebalance_step_days):
        signal_date = common_dates[index]
        exit_date = common_dates[index + hold_days]
        scores = []
        for symbol in symbols:
            series = {row["date"]: row for row in by_symbol[symbol]}
            start_close = float(series[common_dates[index - lookback_days]]["close"])
            signal_close = float(series[signal_date]["close"])
            score = signal_close / start_close - 1.0
            scores.append((score, symbol))
        score, winner = max(scores)
        series = {row["date"]: row for row in by_symbol[winner]}
        entry = float(series[signal_date]["close"])
        exit_ = float(series[exit_date]["close"])
        gross = exit_ / entry - 1.0
        trades.append(
            {
                "symbol": winner,
                "side": "long",
                "signal_date": signal_date,
                "exit_date": exit_date,
                "momentum_score": round(score, 8),
                "entry_close": round(entry, 6),
                "exit_close": round(exit_, 6),
                "gross_return": round(gross, 8),
                "net_return_500bps": round(gross - 0.05, 8),
                "active_only_survivorship_bias_declared": True,
                "promotion_allowed": False,
            }
        )
    return trades


def validate_active_only_momentum_smoke_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    for filename in ["preflight_report.json", "trade_panel.csv", "final_decision.json"]:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    decision = _read_json(path / "final_decision.json")
    trades = _read_csv(path / "trade_panel.csv")
    _check(checks, "provider_query_not_performed", decision.get("provider_query_performed") is False, str(decision.get("provider_query_performed")))
    _check(checks, "market_download_not_performed", decision.get("market_data_downloaded") is False, str(decision.get("market_data_downloaded")))
    _check(checks, "backtest_performed", decision.get("backtest_performed") is True, str(decision.get("backtest_performed")))
    _check(checks, "survivorship_claim_blocked", decision.get("survivorship_free_claim_allowed") is False, str(decision.get("survivorship_free_claim_allowed")))
    _check(checks, "promotion_blocked", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    _check(checks, "long_only", all(row.get("side") == "long" for row in trades), str(trades[:3]))
    return _report(checks)


def _decision(trades: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    gross = sum(float(trade["gross_return"]) for trade in trades)
    net = sum(float(trade["net_return_500bps"]) for trade in trades)
    wins = sum(1 for trade in trades if float(trade["net_return_500bps"]) > 0)
    return {
        "status": "complete",
        "decision": "ACTIVE_ONLY_MOMENTUM_SMOKE_COMPLETE_NO_PROMOTION",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "trade_count": len(trades),
        "gross_return_sum": round(gross, 8),
        "net_return_sum_500bps": round(net, 8),
        "net_win_count": wins,
        "net_win_rate": round(wins / len(trades), 6) if trades else 0.0,
        "cost_bps_round_trip": manifest["cost_bps_round_trip"],
        "provider_query_performed": False,
        "provider_call_count": 0,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": True,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "survivorship_free_claim_allowed": False,
        "active_only_survivorship_bias_declared": True,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
        "next_unblocked_step": "Inspect active-only smoke result only as exploratory evidence; no promotion is allowed.",
    }


def _blocked_decision(reason: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": reason,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "survivorship_free_claim_allowed": False,
    }


def _write_vault_report(path: Path, decision: dict[str, Any]) -> None:
    text = (
        "# Report Active-Only Momentum Smoke 001 - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Exploratory active-only momentum smoke test on archived Databento daily OHLCV. This result is survivorship-biased by construction and cannot promote a strategy.\n\n"
        "## Result\n\n"
        f"- Trades: {decision['trade_count']}\n"
        f"- Gross return sum: {decision['gross_return_sum']}\n"
        f"- Net return sum at 500 bps: {decision['net_return_sum_500bps']}\n"
        f"- Net win rate: {decision['net_win_rate']}\n"
        f"- Promotion allowed: {decision['promotion_allowed']}\n"
        f"- Survivorship-free claim allowed: {decision['survivorship_free_claim_allowed']}\n\n"
        "## Interpretation\n\n"
        "Use this only as a pipeline smoke test and active-only exploratory datapoint. It is not survivorship-free alpha evidence.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    return list(rows[0].keys()) if rows else []


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fieldnames:
            handle.write("\n")
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run active-only momentum smoke 001.")
    parser.add_argument("--spec-dir", default=str(SPEC_DIR))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--vault-report", default=str(VAULT_REPORT))
    parser.add_argument("--validate-output", action="store_true")
    args = parser.parse_args(argv)
    if args.validate_output:
        report = validate_active_only_momentum_smoke_output(args.output_dir)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1
    decision = run_active_only_momentum_smoke_001(
        spec_dir=args.spec_dir,
        output_dir=args.output_dir,
        vault_report=args.vault_report,
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
