from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd

from src.experiments.regime_map_preregistration_validator import validate_regime_map_preregistration


RUN_ID = "REGIME-MAP-DIAGNOSTIC-001"
TRIAL_ID = "REGIME-MAP-001"
SPEC_DIR = Path("experiments/provider_aware_research/regime_map_preregistration_20260524")
PRICE_FILE = Path("experiments/provider_aware_research/data_inputs/databento_xmom_20260520/prices.csv")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/REGIME-MAP-DIAGNOSTIC-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Regime-Map-Diagnostic-001-2026-05-24.md")
DEFAULT_TRADE_LOGS = [
    Path("experiments/provider_aware_research/execution_outputs/LOWVOL-TRADABILITY-BACKTEST-001/trade_log.csv"),
    Path("experiments/provider_aware_research/execution_outputs/SEC8K-TAPE-ORACLE-CLEAN-RUN-002/backtest_results.csv"),
    Path("experiments/provider_aware_research/execution_outputs/FORM4-CLUSTER-BUYING-BACKTEST-002/trade_log.csv"),
]


def run_regime_map_diagnostic_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    price_file: str | Path = PRICE_FILE,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
    trade_log_paths: list[str | Path] | None = None,
    minimum_mapped_trades: int | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    prereg = validate_regime_map_preregistration(spec_dir)
    _write_json(output / "preflight_report.json", prereg)
    if prereg["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED")
        _write_json(output / "final_decision.json", decision)
        return decision

    manifest = json.loads((Path(spec_dir) / "preregistration_manifest.json").read_text(encoding="utf-8"))
    prices = pd.read_csv(price_file)
    regimes = build_daily_regime_map(
        prices,
        lookback_days=int(manifest["lookback_days"]),
        shock_abs_return_threshold=float(manifest["shock_abs_return_threshold"]),
        shock_volume_z_threshold=float(manifest["shock_volume_z_threshold"]),
        trend_return_threshold=float(manifest["trend_return_threshold"]),
        quiet_abs_return_threshold=float(manifest["quiet_abs_return_threshold"]),
        allowed_symbols=set(manifest["allowed_symbols"]),
        start_date=str(manifest["start_date"]),
        end_date=str(manifest["end_date"]),
    )
    trades = load_archived_trade_rows(trade_log_paths or DEFAULT_TRADE_LOGS)
    mapped = map_trade_logs_to_regimes(trades, regimes)
    summary = summarize_regime_diagnostic(
        regimes,
        mapped,
        minimum_mapped_trades=minimum_mapped_trades or int(manifest["minimum_mapped_trades"]),
    )
    decision = _final_decision(summary)
    _write_csv(output / "daily_regime_map.csv", _fieldnames(regimes), regimes)
    _write_csv(output / "trial_regime_attribution.csv", _fieldnames(mapped), mapped)
    _write_csv(output / "regime_summary.csv", _fieldnames(summary["regime_summary_rows"]), summary["regime_summary_rows"])
    _write_json(output / "diagnostic_summary.json", summary)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), summary, decision)
    return decision


def build_daily_regime_map(
    prices: pd.DataFrame,
    *,
    lookback_days: int,
    shock_abs_return_threshold: float,
    shock_volume_z_threshold: float,
    trend_return_threshold: float,
    quiet_abs_return_threshold: float,
    allowed_symbols: set[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict[str, Any]]:
    frame = prices.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    if allowed_symbols is not None:
        frame = frame[frame["symbol"].astype(str).isin(allowed_symbols)].copy()
    if start_date is not None:
        frame = frame[frame["date"] >= pd.Timestamp(start_date)].copy()
    if end_date is not None:
        frame = frame[frame["date"] <= pd.Timestamp(end_date)].copy()
    frame = frame.sort_values(["symbol", "date"]).reset_index(drop=True)
    rows: list[dict[str, Any]] = []
    for symbol, group in frame.groupby("symbol"):
        group = group.sort_values("date").copy()
        group["return_1d"] = group["close"].astype(float).pct_change()
        group["return_lookback"] = group["close"].astype(float).pct_change(periods=lookback_days)
        dollar_volume = group["close"].astype(float) * group["volume"].astype(float)
        rolling_mean = dollar_volume.rolling(lookback_days, min_periods=2).mean().shift(1)
        rolling_std = dollar_volume.rolling(lookback_days, min_periods=2).std(ddof=0).shift(1)
        group["dollar_volume"] = dollar_volume
        group["volume_z"] = (dollar_volume - rolling_mean) / rolling_std.replace(0, pd.NA)
        for _, row in group.iterrows():
            return_1d = _finite_float(row.get("return_1d"), 0.0)
            return_lookback = _finite_float(row.get("return_lookback"), 0.0)
            volume_z = _finite_float(row.get("volume_z"), 0.0)
            label = classify_regime_label(
                return_1d=return_1d,
                return_lookback=return_lookback,
                volume_z=volume_z,
                shock_abs_return_threshold=shock_abs_return_threshold,
                shock_volume_z_threshold=shock_volume_z_threshold,
                trend_return_threshold=trend_return_threshold,
                quiet_abs_return_threshold=quiet_abs_return_threshold,
            )
            rows.append(
                {
                    "run_id": RUN_ID,
                    "trial_id": TRIAL_ID,
                    "symbol": str(symbol),
                    "date": pd.Timestamp(row["date"]).date().isoformat(),
                    "return_1d": round(return_1d, 10),
                    "abs_return_1d": round(abs(return_1d), 10),
                    "return_lookback": round(return_lookback, 10),
                    "dollar_volume": round(float(row["dollar_volume"]), 4),
                    "volume_z": round(volume_z, 6),
                    "regime_label": label,
                    "provider_query_performed": False,
                    "backtest_performed": False,
                    "promotion_allowed": False,
                }
            )
    return rows


def classify_regime_label(
    *,
    return_1d: float,
    return_lookback: float,
    volume_z: float,
    shock_abs_return_threshold: float,
    shock_volume_z_threshold: float,
    trend_return_threshold: float,
    quiet_abs_return_threshold: float,
) -> str:
    if abs(return_1d) >= shock_abs_return_threshold or (abs(return_1d) >= quiet_abs_return_threshold and volume_z >= shock_volume_z_threshold):
        return "VOLATILITY_SHOCK"
    if return_lookback >= trend_return_threshold:
        return "TREND_UP"
    if return_lookback <= -trend_return_threshold:
        return "TREND_DOWN"
    if abs(return_1d) <= quiet_abs_return_threshold and abs(return_lookback) <= trend_return_threshold:
        return "QUIET_RANGE"
    return "MIXED_NORMAL"


def load_archived_trade_rows(paths: list[str | Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path_like in paths:
        path = Path(path_like)
        if not path.is_file() or path.stat().st_size == 0:
            continue
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                continue
            for row in reader:
                normalized = dict(row)
                normalized["source_file"] = str(path)
                rows.append(normalized)
    return rows


def map_trade_logs_to_regimes(trades: list[dict[str, Any]], regimes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    index = {(str(row["symbol"]), str(row["date"])): row for row in regimes}
    mapped: list[dict[str, Any]] = []
    for trade in trades:
        symbol = _symbol_from_trade(trade)
        mapped_date = str(trade.get("signal_date") or trade.get("entry_date") or trade.get("date") or "")
        if not symbol or not mapped_date:
            continue
        regime = index.get((symbol, mapped_date))
        if regime is None and trade.get("entry_date"):
            mapped_date = str(trade["entry_date"])
            regime = index.get((symbol, mapped_date))
        if regime is None:
            continue
        net_return = _return_from_trade(trade, "net_return")
        gross_return = _return_from_trade(trade, "gross_return")
        mapped.append(
            {
                "run_id": RUN_ID,
                "trial_id": TRIAL_ID,
                "source_run_id": str(trade.get("run_id") or trade.get("source_run_id") or ""),
                "source_trial_id": str(trade.get("trial_id") or ""),
                "source_file": str(trade.get("source_file") or ""),
                "symbol": symbol,
                "mapped_date": mapped_date,
                "entry_date": str(trade.get("entry_date") or ""),
                "exit_date": str(trade.get("exit_date") or ""),
                "regime_label": str(regime["regime_label"]),
                "net_return": round(net_return, 10),
                "gross_return": round(gross_return, 10),
                "provider_query_performed": False,
                "backtest_performed": False,
                "promotion_allowed": False,
            }
        )
    return mapped


def summarize_regime_diagnostic(regime_rows: list[dict[str, Any]], mapped_trades: list[dict[str, Any]], *, minimum_mapped_trades: int) -> dict[str, Any]:
    regime_counts: dict[str, int] = {}
    for row in regime_rows:
        label = str(row["regime_label"])
        regime_counts[label] = regime_counts.get(label, 0) + 1
    attribution: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in mapped_trades:
        key = (str(row.get("source_run_id", "")), str(row["regime_label"]))
        attribution.setdefault(key, []).append(row)
    summary_rows: list[dict[str, Any]] = []
    for (source_run_id, regime_label), rows in sorted(attribution.items()):
        net = [float(row["net_return"]) for row in rows]
        gross = [float(row.get("gross_return", row["net_return"])) for row in rows]
        summary_rows.append(
            {
                "source_run_id": source_run_id,
                "regime_label": regime_label,
                "trade_count": len(rows),
                "gross_return_sum": round(sum(gross), 10),
                "net_return_sum": round(sum(net), 10),
                "median_net_return": round(median(net), 10) if net else 0.0,
                "net_win_rate": round(sum(1 for value in net if value > 0) / len(net), 6) if net else 0.0,
                "promotion_allowed": False,
            }
        )
    blockers: list[str] = []
    if len(mapped_trades) < minimum_mapped_trades:
        blockers.append(f"mapped_trade_count_below_{minimum_mapped_trades}")
    return {
        "status": "diagnostic_complete_existing_artifacts_only",
        "decision": "REGIME_MAP_DIAGNOSTIC_COMPLETE_NO_STRATEGY",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "regime_day_count": len(regime_rows),
        "regime_counts": regime_counts,
        "mapped_trade_count": len(mapped_trades),
        "minimum_mapped_trades": minimum_mapped_trades,
        "regime_summary_rows": summary_rows,
        "blockers": blockers,
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
    }


def validate_regime_map_diagnostic_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["preflight_report.json", "daily_regime_map.csv", "trial_regime_attribution.csv", "regime_summary.csv", "diagnostic_summary.json", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _validation_report(checks)
    summary = json.loads((path / "diagnostic_summary.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    regimes = _read_csv(path / "daily_regime_map.csv")
    columns = set(regimes[0].keys()) if regimes else set()
    required_cols = {"symbol", "date", "return_1d", "return_lookback", "volume_z", "regime_label"}
    forbidden_cols = {"optimized_threshold", "paper_signal", "live_signal"}
    _check(checks, "regime_map_non_empty", len(regimes) > 0, f"rows={len(regimes)}")
    _check(checks, "required_columns_present", required_cols.issubset(columns), f"missing={sorted(required_cols - columns)}")
    _check(checks, "forbidden_columns_absent", not (columns & forbidden_cols), f"present={sorted(columns & forbidden_cols)}")
    _check(checks, "summary_no_provider_query", summary.get("provider_query_performed") is False, str(summary.get("provider_query_performed")))
    _check(checks, "summary_no_backtest", summary.get("backtest_performed") is False, str(summary.get("backtest_performed")))
    _check(checks, "decision_no_promotion", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    return _validation_report(checks)


def _final_decision(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "complete",
        "decision": summary["decision"],
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "regime_day_count": summary["regime_day_count"],
        "mapped_trade_count": summary["mapped_trade_count"],
        "blockers": summary["blockers"],
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
        "next_unblocked_step": "Use this attribution only to write a separate preregistration if a regime-specific hypothesis is visible.",
    }


def _blocked_decision(reason: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": "REGIME_MAP_DIAGNOSTIC_BLOCKED",
        "reason": reason,
        "provider_query_performed": False,
        "backtest_performed": False,
        "promotion_allowed": False,
    }


def _write_vault_report(path: Path, summary: dict[str, Any], decision: dict[str, Any]) -> None:
    lines = [
        "# Report Regime Map Diagnostic 001 - 2026-05-24",
        "",
        f"Decision: `{decision['decision']}`",
        "",
        "## Scope",
        "",
        "Existing daily OHLCV and archived trade logs only. No provider query, market-data download, new backtest, parameter sweep, short selling, paper/live trading, or promotion occurred.",
        "",
        "## Result",
        "",
        f"- Regime day count: {summary['regime_day_count']}",
        f"- Mapped trade count: {summary['mapped_trade_count']}",
        f"- Blockers: {', '.join(summary['blockers']) if summary['blockers'] else 'none'}",
        f"- Regime counts: {json.dumps(summary['regime_counts'], sort_keys=True)}",
        "",
        "## Attribution",
        "",
    ]
    for row in summary["regime_summary_rows"]:
        lines.append(
            f"- {row['source_run_id']} / {row['regime_label']}: trades={row['trade_count']} net_sum={row['net_return_sum']} median_net={row['median_net_return']} win_rate={row['net_win_rate']}"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This diagnostic maps archived failures to observable regimes. It does not rescue any strategy; it can only identify whether a future regime-conditioned preregistration is worth writing.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _symbol_from_trade(trade: dict[str, Any]) -> str:
    return str(trade.get("symbol") or trade.get("selected_symbol") or "").strip()


def _return_from_trade(trade: dict[str, Any], key: str) -> float:
    if trade.get(key) not in (None, ""):
        return _finite_float(trade.get(key), 0.0)
    if key == "net_return" and trade.get("gross_return") not in (None, ""):
        return _finite_float(trade.get("gross_return"), 0.0)
    if trade.get("return_pct") not in (None, ""):
        return _finite_float(trade.get("return_pct"), 0.0)
    return 0.0


def _finite_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if pd.notna(parsed) else default


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    return list(rows[0].keys()) if rows else []


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


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


def _validation_report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "REGIME_MAP_DIAGNOSTIC_OUTPUT_PASS" if failed == 0 else "REGIME_MAP_DIAGNOSTIC_OUTPUT_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run REGIME-MAP-001 diagnostic.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_regime_map_diagnostic_001()
    report = validate_regime_map_diagnostic_output()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
