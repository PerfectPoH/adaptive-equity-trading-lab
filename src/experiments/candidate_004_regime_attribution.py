from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "CANDIDATE-004-REGIME-ATTRIBUTION-DIAGNOSTIC-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_004_regime_attribution_gate_20260602")
DESIGN_DIR = Path("experiments/provider_aware_research/candidate_004_regime_routed_portfolio_design_20260602")
SECOND_BACKTEST_DIR = Path("experiments/provider_aware_research/execution_outputs/NORGATE-CANDIDATE-003-SECOND-BACKTEST-001")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID


@dataclass(frozen=True)
class RegimeFeatures:
    spy_close: float
    iwm_close: float
    spy_sma_10: float | None
    iwm_sma_10: float | None
    spy_sma_60: float | None
    iwm_sma_60: float | None
    spy_vol_20: float | None
    iwm_vol_20: float | None
    spy_vol_60_median: float | None
    iwm_vol_60_median: float | None
    spy_drawdown_60: float | None
    iwm_drawdown_60: float | None


def build_market_regime_map(spy_frame: pd.DataFrame, iwm_frame: pd.DataFrame) -> pd.DataFrame:
    spy = _prepare_benchmark(spy_frame, "spy")
    iwm = _prepare_benchmark(iwm_frame, "iwm")
    merged = spy.join(iwm, how="inner").dropna(subset=["spy_close", "iwm_close"]).sort_index()
    if merged.empty:
        return pd.DataFrame(columns=["date", "regime_label"])

    stress_seen = False
    recovery_streak = 0
    labels: list[str] = []
    for _, row in merged.iterrows():
        features = RegimeFeatures(
            spy_close=float(row["spy_close"]),
            iwm_close=float(row["iwm_close"]),
            spy_sma_10=_maybe_float(row.get("spy_sma_10")),
            iwm_sma_10=_maybe_float(row.get("iwm_sma_10")),
            spy_sma_60=_maybe_float(row.get("spy_sma_60")),
            iwm_sma_60=_maybe_float(row.get("iwm_sma_60")),
            spy_vol_20=_maybe_float(row.get("spy_vol_20")),
            iwm_vol_20=_maybe_float(row.get("iwm_vol_20")),
            spy_vol_60_median=_maybe_float(row.get("spy_vol_60_median")),
            iwm_vol_60_median=_maybe_float(row.get("iwm_vol_60_median")),
            spy_drawdown_60=_maybe_float(row.get("spy_drawdown_60")),
            iwm_drawdown_60=_maybe_float(row.get("iwm_drawdown_60")),
        )
        label, stress_seen, recovery_streak = classify_regime(features, stress_seen=stress_seen, recovery_streak=recovery_streak)
        labels.append(label)

    merged.index.name = "date"
    out = merged.reset_index()
    out["date"] = pd.to_datetime(out["date"]).dt.date.astype(str)
    out["regime_label"] = labels
    return out[
        [
            "date",
            "regime_label",
            "spy_close",
            "iwm_close",
            "spy_sma_60",
            "iwm_sma_60",
            "spy_vol_20",
            "iwm_vol_20",
            "spy_drawdown_60",
            "iwm_drawdown_60",
        ]
    ]


def classify_regime(features: RegimeFeatures, *, stress_seen: bool, recovery_streak: int) -> tuple[str, bool, int]:
    if _missing_core(features):
        return "INSUFFICIENT_HISTORY", stress_seen, 0

    stress = bool((features.spy_drawdown_60 or 0.0) <= -0.08 or (features.iwm_drawdown_60 or 0.0) <= -0.08)
    if stress:
        return "DRAWDOWN_STRESS", True, 0

    above_10 = bool(
        features.spy_sma_10 is not None
        and features.iwm_sma_10 is not None
        and features.spy_close > features.spy_sma_10
        and features.iwm_close > features.iwm_sma_10
    )
    next_recovery_streak = recovery_streak + 1 if stress_seen and above_10 else 0
    if stress_seen and next_recovery_streak >= 3:
        return "RECOVERY_BOUNCE", True, next_recovery_streak

    spy_above_60 = features.spy_close > (features.spy_sma_60 or features.spy_close)
    iwm_above_60 = features.iwm_close > (features.iwm_sma_60 or features.iwm_close)
    high_vol = bool(
        (features.spy_vol_20 or 0.0) > (features.spy_vol_60_median or 0.0)
        or (features.iwm_vol_20 or 0.0) > (features.iwm_vol_60_median or 0.0)
    )
    in_range = bool(
        abs(features.spy_close / (features.spy_sma_60 or features.spy_close) - 1.0) <= 0.03
        and abs(features.iwm_close / (features.iwm_sma_60 or features.iwm_close) - 1.0) <= 0.03
    )

    if not spy_above_60 and not iwm_above_60:
        return "RISK_OFF", stress_seen, next_recovery_streak
    if spy_above_60 and iwm_above_60:
        return ("TREND_UP_HIGH_VOL" if high_vol else "TREND_UP_LOW_VOL"), stress_seen, next_recovery_streak
    if in_range:
        return ("RANGE_HIGH_VOL" if high_vol else "RANGE_LOW_VOL"), stress_seen, next_recovery_streak
    return "MIXED_TRANSITION", stress_seen, next_recovery_streak


def map_trades_to_regimes(trades: pd.DataFrame, regime_map: pd.DataFrame) -> pd.DataFrame:
    if trades.empty:
        return pd.DataFrame()
    regime_index = regime_map.set_index("date").to_dict(orient="index")
    mapped_rows: list[dict[str, Any]] = []
    for row in trades.to_dict(orient="records"):
        signal_date = str(row.get("signal_date") or row.get("entry_date"))
        regime = regime_index.get(signal_date)
        if regime is None:
            label = "UNMAPPED"
        else:
            label = str(regime["regime_label"])
        mapped = dict(row)
        mapped["regime_label"] = label
        mapped_rows.append(mapped)
    return pd.DataFrame(mapped_rows)


def summarize_attribution(mapped: pd.DataFrame) -> dict[str, Any]:
    if mapped.empty:
        return {
            "total_mapped_trades": 0,
            "summary_by_regime": [],
            "summary_by_sleeve_regime": [],
            "recommendations": [],
        }

    mapped = mapped.copy()
    for column in ["net_return", "weighted_net_return"]:
        mapped[column] = pd.to_numeric(mapped[column], errors="coerce").fillna(0.0)

    by_regime = _summary_rows(mapped, ["regime_label"])
    by_sleeve_regime = _summary_rows(mapped, ["sleeve", "regime_label"])
    by_component_regime = _summary_rows(mapped, ["component_id", "component_template", "regime_label"])
    recommendations = _build_recommendations(by_sleeve_regime)
    return {
        "total_mapped_trades": int(len(mapped)),
        "regime_count": int(mapped["regime_label"].nunique()),
        "summary_by_regime": by_regime,
        "summary_by_sleeve_regime": by_sleeve_regime,
        "summary_by_component_regime": by_component_regime,
        "recommendations": recommendations,
    }


def run_candidate_004_regime_attribution_diagnostic(
    *,
    output_dir: Path = OUTPUT_DIR,
    gate_dir: Path = GATE_DIR,
    design_dir: Path = DESIGN_DIR,
    second_backtest_dir: Path = SECOND_BACKTEST_DIR,
    benchmark_frames: dict[str, pd.DataFrame] | None = None,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    taxonomy = _read_json(design_dir / "regime_taxonomy.json")
    if gate.get("status") != "APPROVED_ATTRIBUTION_ONLY_NO_BACKTEST":
        raise RuntimeError("Candidate 004 attribution gate is not approved.")
    if gate.get("portfolio_backtest_allowed") is not False:
        raise RuntimeError("Attribution gate must not allow portfolio backtests.")

    provider_query_performed = False
    if benchmark_frames is None:
        benchmark_frames = _load_norgate_benchmarks()
        provider_query_performed = True

    regime_map = build_market_regime_map(benchmark_frames["SPY"], benchmark_frames["IWM"])
    trades = pd.read_csv(second_backtest_dir / "trade_log.csv")
    mapped = map_trades_to_regimes(trades, regime_map)
    summary = summarize_attribution(mapped)

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "market_regime_map.csv", regime_map)
    _write_csv(output_dir / "trade_regime_attribution.csv", mapped)
    _write_csv(output_dir / "summary_by_regime.csv", pd.DataFrame(summary["summary_by_regime"]))
    _write_csv(output_dir / "summary_by_sleeve_regime.csv", pd.DataFrame(summary["summary_by_sleeve_regime"]))
    _write_csv(output_dir / "summary_by_component_regime.csv", pd.DataFrame(summary["summary_by_component_regime"]))

    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "CANDIDATE_004_REGIME_ATTRIBUTION_COMPLETE_NO_BACKTEST",
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "linked_taxonomy": str(design_dir / "regime_taxonomy.json"),
        "linked_candidate_003_backtest": str(second_backtest_dir / "norgate_candidate_003_second_backtest_result.json"),
        "provider_query_performed": provider_query_performed,
        "provider_query_scope": ["SPY", "IWM"] if provider_query_performed else [],
        "market_data_download_performed": False,
        "portfolio_backtest_performed": False,
        "parameter_sweep_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "taxonomy_id": taxonomy.get("taxonomy_id"),
        "summary": summary,
        "next_allowed_action": "review_candidate_004_regime_attribution_before_backtest_gate",
    }
    _write_json(output_dir / "regime_attribution_result.json", result)
    _write_json(output_dir / "final_decision.json", _final_decision(result))
    (output_dir / "regime_attribution_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _prepare_benchmark(frame: pd.DataFrame, prefix: str) -> pd.DataFrame:
    data = frame.copy()
    data.index = pd.to_datetime(data.index).tz_localize(None).normalize()
    close = pd.to_numeric(data["Close"], errors="coerce")
    returns = close.pct_change()
    out = pd.DataFrame(index=data.index)
    out[f"{prefix}_close"] = close
    out[f"{prefix}_sma_10"] = close.rolling(10).mean()
    out[f"{prefix}_sma_60"] = close.rolling(60).mean()
    out[f"{prefix}_vol_20"] = returns.rolling(20).std()
    out[f"{prefix}_vol_60_median"] = returns.rolling(60).std().rolling(60).median()
    out[f"{prefix}_drawdown_60"] = (close / close.rolling(60).max()) - 1.0
    return out


def _summary_rows(frame: pd.DataFrame, keys: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key_values, group in frame.groupby(keys, dropna=False):
        if not isinstance(key_values, tuple):
            key_values = (key_values,)
        row = {key: value for key, value in zip(keys, key_values)}
        row.update(
            {
                "trade_count": int(len(group)),
                "weighted_net_return_sum": float(group["weighted_net_return"].sum()),
                "median_net_return": float(group["net_return"].median()),
                "win_rate": float((group["net_return"] > 0).mean()),
                "best_symbol": str(group.groupby("symbol")["weighted_net_return"].sum().sort_values(ascending=False).index[0]),
            }
        )
        rows.append(row)
    return sorted(rows, key=lambda item: (str(item.get("sleeve", "")), str(item.get("regime_label", ""))))


def _build_recommendations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    for row in rows:
        sleeve = str(row.get("sleeve", ""))
        regime = str(row.get("regime_label", ""))
        trades = int(row.get("trade_count", 0))
        net_sum = float(row.get("weighted_net_return_sum", 0.0))
        win_rate = float(row.get("win_rate", 0.0))
        if trades < 5:
            action = "INSUFFICIENT_SAMPLE_KEEP_DIAGNOSTIC_ONLY"
        elif net_sum > 0 and win_rate >= 0.5:
            action = "CANDIDATE_ALLOWED_SLEEVE"
        elif net_sum > 0:
            action = "POSITIVE_BUT_WEAK_DISTRIBUTION_REQUIRE_CAP_OR_CONFIRMATION"
        else:
            action = "BLOCK_OR_ROUTE_TO_CASH"
        recommendations.append(
            {
                "sleeve": sleeve,
                "regime_label": regime,
                "trade_count": trades,
                "weighted_net_return_sum": net_sum,
                "win_rate": win_rate,
                "suggested_candidate_004_action": action,
            }
        )
    return recommendations


def _load_norgate_benchmarks() -> dict[str, pd.DataFrame]:
    import norgatedata

    frames: dict[str, pd.DataFrame] = {}
    for symbol in ("SPY", "IWM"):
        frame = norgatedata.price_timeseries(symbol, timeseriesformat="pandas-dataframe")
        if frame is None or frame.empty:
            raise RuntimeError(f"Norgate benchmark frame unavailable for {symbol}")
        frame = frame.copy()
        frame.index = pd.to_datetime(frame.index).tz_localize(None).normalize()
        frames[symbol] = frame.sort_index()
    return frames


def _missing_core(features: RegimeFeatures) -> bool:
    required = [
        features.spy_sma_60,
        features.iwm_sma_60,
        features.spy_vol_20,
        features.iwm_vol_20,
        features.spy_vol_60_median,
        features.iwm_vol_60_median,
        features.spy_drawdown_60,
        features.iwm_drawdown_60,
    ]
    return any(value is None for value in required)


def _maybe_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    if frame.empty:
        path.write_text("", encoding="utf-8")
        return
    frame.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def _final_decision(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result["decision"],
        "provider_query_performed": result["provider_query_performed"],
        "market_data_download_performed": False,
        "portfolio_backtest_performed": False,
        "parameter_sweep_performed": False,
        "promotion_allowed": False,
        "next_allowed_action": result["next_allowed_action"],
    }


def _markdown_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# Candidate 004 Regime Attribution Diagnostic 001",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: attribution only. No Candidate 004 backtest, no parameter sweep, no promotion.",
        "",
        "## Accounting",
        "",
        f"- Provider query performed: `{result['provider_query_performed']}` (scope: SPY/IWM only).",
        "- Market-data download performed: `False`.",
        "- Portfolio backtest performed: `False`.",
        "- Promotion allowed: `False`.",
        "",
        "## Summary",
        "",
        f"- Mapped trades: `{summary['total_mapped_trades']}`.",
        f"- Regime labels observed: `{summary['regime_count']}`.",
        "",
        "## Sleeve / Regime Actions",
        "",
    ]
    for row in summary["recommendations"]:
        lines.append(
            "- "
            f"{row['sleeve']} / {row['regime_label']}: "
            f"trades={row['trade_count']} "
            f"weighted_net={row['weighted_net_return_sum']:.6f} "
            f"win_rate={row['win_rate']:.3f} "
            f"action=`{row['suggested_candidate_004_action']}`"
        )
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "`review_candidate_004_regime_attribution_before_backtest_gate`",
        ]
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    run_candidate_004_regime_attribution_diagnostic()
