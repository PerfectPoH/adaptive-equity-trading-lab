from __future__ import annotations

import argparse
import csv
import json
from math import sqrt
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd

from src.experiments.transition_five_point_batch_validator import validate_transition_five_point_batch_gate


RUN_ID = "TRANSITION-FIVE-POINT-BATCH-RUN-001"
TRIAL_ID = "TRANSITION-FIVE-POINT-BATCH-001"
SPEC_DIR = Path("experiments/provider_aware_research/transition_five_point_batch_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/TRANSITION-FIVE-POINT-BATCH-RUN-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Transition-Five-Point-Batch-001-2026-05-24.md")


def run_transition_five_point_batch_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
    snapshot_files: list[str | Path] | None = None,
    active_only_trade_panel: str | Path | None = None,
    robustness_decision_path: str | Path | None = None,
    delisted_decision_path: str | Path | None = None,
    smallcap_price_file: str | Path | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    preflight = validate_transition_five_point_batch_gate(spec_dir)
    _write_json(output / "preflight_report.json", preflight)
    if preflight["status"] != "pass":
        decision = _blocked_decision("PRE_RUN_GATE_FAILED")
        _write_json(output / "final_decision.json", decision)
        return decision

    manifest = _read_json(Path(spec_dir) / "batch_manifest.json")
    snapshots = [Path(item) for item in (snapshot_files or manifest["snapshot_files"])]
    trade_panel_path = Path(active_only_trade_panel or manifest["active_only_trade_panel"])
    robustness_path = Path(robustness_decision_path or manifest["active_only_robustness_decision"])
    delisted_path = Path(delisted_decision_path or manifest["delisted_listing_date_decision"])
    smallcap_prices_path = Path(smallcap_price_file or manifest["smallcap_price_file"])

    largecap_prices = load_local_snapshot_prices(snapshots)
    regimes = build_etf_largecap_regime_map(
        largecap_prices,
        lookback_days=int(manifest["lookback_days"]),
        volatility_window_days=int(manifest["volatility_window_days"]),
        drawdown_window_days=int(manifest["drawdown_window_days"]),
        annualized_vol_high_threshold=float(manifest["annualized_vol_high_threshold"]),
        drawdown_stress_threshold=float(manifest["drawdown_stress_threshold"]),
        trend_return_threshold=float(manifest["trend_return_threshold"]),
    )

    trades = _read_csv(trade_panel_path)
    robustness = _read_json(robustness_path)
    overlay = replay_archived_trade_risk_overlay(
        trades,
        robustness_decision=robustness,
        per_trade_loss_floor=float(manifest["risk_overlay_per_trade_loss_floor"]),
        stop_after_cumulative_loss=float(manifest["risk_overlay_stop_after_cumulative_loss"]),
    )

    allocation = build_portfolio_allocation_smoke(
        largecap_prices,
        volatility_window_days=int(manifest["allocation_volatility_window_days"]),
        max_weight=float(manifest["allocation_max_weight"]),
        minimum_symbols=int(manifest["minimum_allocation_symbols"]),
    )
    smallcap = build_smallcap_microstructure_diagnostic(
        pd.read_csv(smallcap_prices_path),
        liquidity_window_days=int(manifest["smallcap_liquidity_window_days"]),
    )
    data_matrix = build_data_upgrade_decision_matrix(
        delisted_decision=_read_json(delisted_path),
        robustness_decision=robustness,
        manifest=manifest,
    )

    _write_csv(output / "etf_largecap_regime_map.csv", _fieldnames(regimes), regimes)
    _write_json(output / "risk_overlay_replay.json", overlay)
    _write_csv(output / "portfolio_allocation_smoke.csv", _fieldnames(allocation), allocation)
    _write_csv(output / "smallcap_microstructure_diagnostic.csv", _fieldnames(smallcap), smallcap)
    _write_csv(output / "data_upgrade_decision_matrix.csv", _fieldnames(data_matrix), data_matrix)

    decision = _final_decision(regimes, overlay, allocation, smallcap, data_matrix)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), decision, overlay, data_matrix)
    return decision


def load_local_snapshot_prices(snapshot_files: list[str | Path]) -> pd.DataFrame:
    frames = []
    for path_like in snapshot_files:
        path = Path(path_like)
        frame = pd.read_csv(path)
        symbol = path.name.split("_", 1)[0].upper()
        normalized = pd.DataFrame(
            {
                "symbol": symbol,
                "date": pd.to_datetime(frame["Date"]).dt.date.astype(str),
                "open": frame["Open"].astype(float),
                "high": frame["High"].astype(float),
                "low": frame["Low"].astype(float),
                "close": frame["Close"].astype(float),
                "adj_close": frame["Adj Close"].astype(float) if "Adj Close" in frame.columns else frame["Close"].astype(float),
                "volume": frame["Volume"].astype(int),
                "source_file": str(path),
            }
        )
        frames.append(normalized)
    if not frames:
        return pd.DataFrame(columns=["symbol", "date", "open", "high", "low", "close", "adj_close", "volume", "source_file"])
    combined = pd.concat(frames, ignore_index=True)
    return combined.drop_duplicates(subset=["symbol", "date"], keep="first").sort_values(["symbol", "date"]).reset_index(drop=True)


def build_etf_largecap_regime_map(
    prices: pd.DataFrame,
    *,
    lookback_days: int,
    volatility_window_days: int,
    drawdown_window_days: int,
    annualized_vol_high_threshold: float,
    drawdown_stress_threshold: float,
    trend_return_threshold: float,
) -> list[dict[str, Any]]:
    frame = prices.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    rows: list[dict[str, Any]] = []
    for symbol, group in frame.sort_values(["symbol", "date"]).groupby("symbol"):
        group = group.sort_values("date").copy()
        close = group["close"].astype(float)
        returns = close.pct_change()
        lookback_return = close.pct_change(periods=lookback_days)
        annualized_vol = returns.rolling(volatility_window_days, min_periods=2).std(ddof=0) * sqrt(252)
        drawdown = close / close.rolling(drawdown_window_days, min_periods=2).max() - 1.0
        for offset, (_, row) in enumerate(group.iterrows()):
            ret = _finite_float(lookback_return.iloc[offset], 0.0)
            vol = _finite_float(annualized_vol.iloc[offset], 0.0)
            dd = _finite_float(drawdown.iloc[offset], 0.0)
            if offset < max(lookback_days, volatility_window_days):
                label = "INSUFFICIENT_HISTORY"
            elif dd <= drawdown_stress_threshold:
                label = "DRAWDOWN_STRESS"
            elif ret >= trend_return_threshold and vol <= annualized_vol_high_threshold:
                label = "TREND_UP_LOW_VOL"
            elif ret >= trend_return_threshold:
                label = "TREND_UP_HIGH_VOL"
            elif abs(ret) < trend_return_threshold:
                label = "RANGE_NORMAL"
            else:
                label = "TREND_DOWN_OR_CHOP"
            rows.append(
                {
                    "run_id": RUN_ID,
                    "trial_id": TRIAL_ID,
                    "symbol": str(symbol),
                    "date": pd.Timestamp(row["date"]).date().isoformat(),
                    "lookback_return": round(ret, 10),
                    "annualized_volatility": round(vol, 10),
                    "drawdown": round(dd, 10),
                    "regime_label": label,
                    "provider_query_performed": False,
                    "backtest_performed": False,
                    "promotion_allowed": False,
                }
            )
    return rows


def replay_archived_trade_risk_overlay(
    trades: list[dict[str, Any]],
    *,
    robustness_decision: dict[str, Any],
    per_trade_loss_floor: float,
    stop_after_cumulative_loss: float,
) -> dict[str, Any]:
    original_returns = [_trade_net_return(row) for row in trades]
    overlay_returns: list[float] = []
    cumulative = 0.0
    stopped = False
    for value in original_returns:
        if stopped:
            overlay_returns.append(0.0)
            continue
        clipped = max(value, per_trade_loss_floor)
        overlay_returns.append(clipped)
        cumulative += clipped
        if cumulative <= stop_after_cumulative_loss:
            stopped = True
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "trade_count": len(original_returns),
        "original_net_return_sum": round(sum(original_returns), 10),
        "overlay_net_return_sum": round(sum(overlay_returns), 10),
        "original_median_net_return": round(median(original_returns), 10) if original_returns else 0.0,
        "overlay_median_net_return": round(median(overlay_returns), 10) if overlay_returns else 0.0,
        "per_trade_loss_floor": per_trade_loss_floor,
        "stop_after_cumulative_loss": stop_after_cumulative_loss,
        "stopped_by_risk_rule": stopped,
        "fragility_block": bool(robustness_decision.get("top3_dependency_flag") or robustness_decision.get("sign_flip_ex_top3")),
        "provider_query_performed": False,
        "backtest_performed": False,
        "promotion_allowed": False,
    }


def build_portfolio_allocation_smoke(
    prices: pd.DataFrame,
    *,
    volatility_window_days: int,
    max_weight: float,
    minimum_symbols: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for symbol, group in prices.sort_values(["symbol", "date"]).groupby("symbol"):
        returns = group["close"].astype(float).pct_change().dropna()
        realized_vol = float(returns.tail(volatility_window_days).std(ddof=0) * sqrt(252)) if len(returns) >= 2 else 0.0
        inverse_vol = 1.0 / max(realized_vol, 0.01)
        rows.append({"symbol": str(symbol), "realized_volatility": realized_vol, "inverse_vol_score": inverse_vol})
    total = sum(float(row["inverse_vol_score"]) for row in rows) or 1.0
    capped = []
    for row in rows:
        raw = float(row["inverse_vol_score"]) / total
        capped.append(min(raw, max_weight))
    cap_total = sum(capped) or 1.0
    for row, weight in zip(rows, capped):
        row.update(
            {
                "diagnostic_weight": round(weight / cap_total, 10),
                "minimum_symbols_met": len(rows) >= minimum_symbols,
                "provider_query_performed": False,
                "backtest_performed": False,
                "promotion_allowed": False,
            }
        )
        row["realized_volatility"] = round(float(row["realized_volatility"]), 10)
        row["inverse_vol_score"] = round(float(row["inverse_vol_score"]), 10)
    return sorted(rows, key=lambda item: item["symbol"])


def build_smallcap_microstructure_diagnostic(prices: pd.DataFrame, *, liquidity_window_days: int) -> list[dict[str, Any]]:
    frame = prices.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    rows: list[dict[str, Any]] = []
    for symbol, group in frame.sort_values(["symbol", "date"]).groupby("symbol"):
        close = group["close"].astype(float)
        volume = group["volume"].astype(float)
        dollar_volume = close * volume
        spread_proxy = (group["high"].astype(float) - group["low"].astype(float)) / close.replace(0, pd.NA)
        returns = close.pct_change().abs()
        amihud = returns / dollar_volume.replace(0, pd.NA)
        rows.append(
            {
                "run_id": RUN_ID,
                "trial_id": TRIAL_ID,
                "symbol": str(symbol),
                "observations": int(len(group)),
                "median_dollar_volume": round(float(dollar_volume.tail(liquidity_window_days).median()), 4),
                "median_spread_proxy": round(_finite_float(spread_proxy.tail(liquidity_window_days).median(), 0.0), 10),
                "median_amihud_proxy": round(_finite_float(amihud.tail(liquidity_window_days).median(), 0.0), 16),
                "microstructure_only": True,
                "provider_query_performed": False,
                "backtest_performed": False,
                "promotion_allowed": False,
            }
        )
    return rows


def build_data_upgrade_decision_matrix(
    *,
    delisted_decision: dict[str, Any],
    robustness_decision: dict[str, Any],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "track": "smallcap_directional_free_data",
            "decision": "PAUSE",
            "reason": "active_only_survivorship_bias_and_top3_dependency",
            "evidence": f"top3_dependency={bool(robustness_decision.get('top3_dependency_flag'))}",
            "next_action": "do_not_reopen_without_survivorship_free_universe",
            "promotion_allowed": False,
        },
        {
            "track": "pit_universe_data",
            "decision": "BLOCKED",
            "reason": "delisted_listing_dates_unavailable_for_full_pit",
            "evidence": str(delisted_decision.get("decision", "")),
            "next_action": "commercial_reference_data_or_no_broad_smallcap_backtest",
            "promotion_allowed": False,
        },
        {
            "track": "etf_largecap_risk_regime_lab",
            "decision": "ALLOW_DIAGNOSTICS_ONLY",
            "reason": "local_historical_snapshots_available_without_provider_query",
            "evidence": f"snapshot_files={len(manifest.get('snapshot_files', []))}",
            "next_action": "risk_regime_diagnostics_only_until_separate_preregistration",
            "promotion_allowed": False,
        },
        {
            "track": "paid_data_purchase",
            "decision": "DEFER",
            "reason": "no_single_paid_feed_purchase_is_justified_by_current_failed_alpha_queue",
            "evidence": "PEAD_and_PIT_universe_require_commercial_data_but_no_strategy_promoted",
            "next_action": "buy_data_only_after_written_budget_gate",
            "promotion_allowed": False,
        },
    ]


def validate_transition_five_point_batch_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = [
        "preflight_report.json",
        "etf_largecap_regime_map.csv",
        "risk_overlay_replay.json",
        "portfolio_allocation_smoke.csv",
        "smallcap_microstructure_diagnostic.csv",
        "data_upgrade_decision_matrix.csv",
        "final_decision.json",
    ]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _validation_report(checks)
    decision = _read_json(path / "final_decision.json")
    _check(checks, "completed_five_points", decision.get("completed_points") == 5, str(decision.get("completed_points")))
    _check(checks, "provider_query_not_performed", decision.get("provider_query_performed") is False, str(decision.get("provider_query_performed")))
    _check(checks, "market_download_not_performed", decision.get("market_data_downloaded") is False, str(decision.get("market_data_downloaded")))
    _check(checks, "new_backtest_not_performed", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "short_selling_not_performed", decision.get("short_selling_performed") is False, str(decision.get("short_selling_performed")))
    _check(checks, "promotion_blocked", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    return _validation_report(checks)


def _final_decision(
    regimes: list[dict[str, Any]],
    overlay: dict[str, Any],
    allocation: list[dict[str, Any]],
    smallcap: list[dict[str, Any]],
    data_matrix: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "status": "complete",
        "decision": "TRANSITION_FIVE_POINT_BATCH_COMPLETE_NO_STRATEGY",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "completed_points": 5,
        "etf_largecap_regime_rows": len(regimes),
        "risk_overlay_trade_count": overlay["trade_count"],
        "portfolio_allocation_symbol_count": len(allocation),
        "smallcap_microstructure_symbol_count": len(smallcap),
        "data_upgrade_track_count": len(data_matrix),
        "provider_query_performed": False,
        "provider_call_count": 0,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
        "next_unblocked_step": "Use these artifacts to decide a future no-query risk diagnostic; do not treat this as alpha evidence.",
    }


def _blocked_decision(reason: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": "TRANSITION_FIVE_POINT_BATCH_BLOCKED",
        "reason": reason,
        "completed_points": 0,
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
    }


def _write_vault_report(path: Path, decision: dict[str, Any], overlay: dict[str, Any], data_matrix: list[dict[str, Any]]) -> None:
    lines = [
        "# Report Transition Five Point Batch 001 - 2026-05-24",
        "",
        f"Decision: `{decision['decision']}`",
        "",
        "## Scope",
        "",
        "Executed the five next-step diagnostics using existing local artifacts only. No provider query, market-data download, new strategy backtest, parameter sweep, short selling, paper/live trading, or promotion occurred.",
        "",
        "## Five Points",
        "",
        f"- ETF/large-cap regime rows: {decision['etf_largecap_regime_rows']}",
        f"- Risk overlay archived trades: {decision['risk_overlay_trade_count']}",
        f"- Portfolio allocation smoke symbols: {decision['portfolio_allocation_symbol_count']}",
        f"- Small-cap microstructure symbols: {decision['smallcap_microstructure_symbol_count']}",
        f"- Data upgrade tracks: {decision['data_upgrade_track_count']}",
        "",
        "## Risk Overlay",
        "",
        f"- Original archived net sum: {overlay['original_net_return_sum']}",
        f"- Overlay net sum: {overlay['overlay_net_return_sum']}",
        f"- Fragility block: {overlay['fragility_block']}",
        "",
        "## Data Decision",
        "",
    ]
    for row in data_matrix:
        lines.append(f"- {row['track']}: {row['decision']} - {row['reason']}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This batch moves the lab from directional small-cap alpha hunting toward risk/regime diagnostics. It preserves the research pause on free-data small-cap directional work and creates no tradable signal.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _trade_net_return(row: dict[str, Any]) -> float:
    for key in ["net_return_500bps", "net_return", "return_pct"]:
        if row.get(key) not in (None, ""):
            return _finite_float(row.get(key), 0.0)
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


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _validation_report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "TRANSITION_FIVE_POINT_BATCH_OUTPUT_PASS" if failed == 0 else "TRANSITION_FIVE_POINT_BATCH_OUTPUT_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run TRANSITION-FIVE-POINT-BATCH-001.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_transition_five_point_batch_001()
    report = validate_transition_five_point_batch_output()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
