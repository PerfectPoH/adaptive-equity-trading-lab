from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from src.experiments.candidate_004_regime_attribution import build_market_regime_map, map_trades_to_regimes


RUN_ID = "CANDIDATE-008-AUTOPSY-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_008_autopsy_gate_20260606")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID


def attach_security_master(trades: pd.DataFrame, security_master: pd.DataFrame) -> pd.DataFrame:
    master = security_master[["symbol", "universe_status", "is_delisted"]].copy()
    master["symbol"] = master["symbol"].astype(str)
    master["is_delisted"] = master["is_delisted"].astype(bool)
    joined = trades.copy()
    joined["symbol"] = joined["symbol"].astype(str)
    joined = joined.merge(master, on="symbol", how="left", validate="many_to_one")
    joined["universe_status"] = joined["universe_status"].fillna("unknown")
    joined["is_delisted"] = joined["is_delisted"].fillna(False).astype(bool)
    return joined


def summarize_failure_attribution(mapped: pd.DataFrame) -> dict[str, Any]:
    data = mapped.copy()
    for column in ("gross_return", "cost_return", "net_return", "weighted_net_return"):
        data[column] = pd.to_numeric(data[column], errors="coerce").fillna(0.0)
    summaries = {
        "by_sleeve": _summary_rows(data, ["sleeve"]),
        "by_sleeve_split": _summary_rows(data, ["sleeve", "split"]),
        "by_regime": _summary_rows(data, ["regime_label"]),
        "by_sleeve_regime": _summary_rows(data, ["sleeve", "regime_label"]),
        "by_universe": _summary_rows(data, ["universe_status"]),
        "by_universe_sleeve": _summary_rows(data, ["universe_status", "sleeve"]),
        "by_symbol": _summary_rows(data, ["symbol"]),
        "cost_drag": _cost_drag(data),
    }
    summaries["recommendations"] = _recommendations(summaries)
    return summaries


def run_candidate_008_autopsy(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    trade_log_path = Path(gate["linked_trade_log"])
    dataset_dir = Path(gate["linked_dataset"])
    trades = pd.read_csv(trade_log_path)
    security_master = pd.read_csv(dataset_dir / "security_master.csv")
    prices = pd.read_csv(dataset_dir / "prices.csv")
    regime_map = _build_regime_map_from_prices(prices)
    mapped = map_trades_to_regimes(trades, regime_map)
    mapped = attach_security_master(mapped, security_master)
    summary = summarize_failure_attribution(mapped)
    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "CANDIDATE_008_AUTOPSY_COMPLETE_NO_BACKTEST",
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "linked_trade_log": str(trade_log_path),
        "linked_dataset": str(dataset_dir),
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "strategy_backtest_performed": False,
        "kronos_inference_performed": False,
        "portfolio_search_performed": False,
        "parameter_sweep_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "summary": summary,
        "next_allowed_action": "Use this autopsy to draft, not run, a separate regime-routing hypothesis.",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "trade_regime_autopsy.csv", mapped)
    _write_csv(output_dir / "market_regime_map.csv", regime_map)
    for name in (
        "by_sleeve",
        "by_sleeve_split",
        "by_regime",
        "by_sleeve_regime",
        "by_universe",
        "by_universe_sleeve",
        "by_symbol",
    ):
        _write_csv(output_dir / f"summary_{name}.csv", pd.DataFrame(summary[name]))
    _write_json(output_dir / "candidate_008_autopsy_result.json", result)
    _write_json(output_dir / "final_decision.json", _final_decision(result))
    (output_dir / "candidate_008_autopsy_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _build_regime_map_from_prices(prices: pd.DataFrame) -> pd.DataFrame:
    frames: dict[str, pd.DataFrame] = {}
    for symbol in ("SPY", "IWM"):
        group = prices[prices["symbol"].astype(str).eq(symbol)].copy()
        group["date"] = pd.to_datetime(group["date"])
        group = group.sort_values("date").set_index("date")
        frames[symbol] = pd.DataFrame(
            {
                "Open": pd.to_numeric(group["open"], errors="coerce"),
                "High": pd.to_numeric(group["high"], errors="coerce"),
                "Low": pd.to_numeric(group["low"], errors="coerce"),
                "Close": pd.to_numeric(group["close"], errors="coerce"),
                "Volume": pd.to_numeric(group["volume"], errors="coerce"),
            }
        ).dropna()
    return build_market_regime_map(frames["SPY"], frames["IWM"])


def _summary_rows(frame: pd.DataFrame, keys: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if frame.empty:
        return rows
    for key_values, group in frame.groupby(keys, dropna=False):
        if not isinstance(key_values, tuple):
            key_values = (key_values,)
        row = {key: value for key, value in zip(keys, key_values)}
        gross_sum = float(group["gross_return"].sum())
        net_sum = float(group["net_return"].sum())
        weighted_sum = float(group["weighted_net_return"].sum())
        row.update(
            {
                "trade_count": int(len(group)),
                "gross_return_sum": gross_sum,
                "net_return_sum": net_sum,
                "weighted_net_return_sum": weighted_sum,
                "median_net_return": float(group["net_return"].median()),
                "win_rate": float((group["net_return"] > 0).mean()),
                "cost_return_sum": float(group["cost_return"].sum()),
                "best_symbol": _best_symbol(group),
                "worst_symbol": _worst_symbol(group),
            }
        )
        rows.append(row)
    return sorted(rows, key=lambda row: tuple(str(row.get(key, "")) for key in keys))


def _cost_drag(frame: pd.DataFrame) -> dict[str, Any]:
    weighted_cost = frame["cost_return"] * frame.get("per_trade_weight", 1.0)
    gross_weighted = frame["gross_return"] * frame.get("per_trade_weight", 1.0)
    return {
        "trade_count": int(len(frame)),
        "gross_weighted_sum": float(gross_weighted.sum()),
        "weighted_cost_sum": float(weighted_cost.sum()),
        "weighted_net_sum": float(frame["weighted_net_return"].sum()),
        "cost_to_gross_ratio": float(weighted_cost.sum() / gross_weighted.sum()) if float(gross_weighted.sum()) > 0 else None,
    }


def _recommendations(summary: dict[str, Any]) -> list[dict[str, str]]:
    recs: list[dict[str, str]] = []
    for row in summary["by_sleeve"]:
        if row["weighted_net_return_sum"] <= 0:
            recs.append(
                {
                    "scope": f"sleeve:{row['sleeve']}",
                    "finding": "Sleeve has non-positive weighted contribution.",
                    "suggested_action": "Do not route capital to this sleeve without a separate preregistered regime filter.",
                }
            )
    for row in summary["by_universe"]:
        if row["weighted_net_return_sum"] <= 0:
            recs.append(
                {
                    "scope": f"universe:{row['universe_status']}",
                    "finding": "Universe bucket has non-positive weighted contribution.",
                    "suggested_action": "Inspect whether tradability or delisting timing requires a stricter as-of filter.",
                }
            )
    cost = summary["cost_drag"]
    if cost["gross_weighted_sum"] > 0 and cost["weighted_net_sum"] <= 0:
        recs.append(
            {
                "scope": "cost_drag",
                "finding": "Gross edge exists but costs consume the diagnostic portfolio.",
                "suggested_action": "Any next hypothesis must justify maker/limit execution or larger gross moves before backtesting.",
            }
        )
    return recs


def _best_symbol(group: pd.DataFrame) -> str | None:
    by_symbol = group.groupby("symbol")["weighted_net_return"].sum().sort_values(ascending=False)
    return str(by_symbol.index[0]) if len(by_symbol) else None


def _worst_symbol(group: pd.DataFrame) -> str | None:
    by_symbol = group.groupby("symbol")["weighted_net_return"].sum().sort_values(ascending=True)
    return str(by_symbol.index[0]) if len(by_symbol) else None


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_CANDIDATE_008_AUTOPSY_ATTRIBUTION_ONLY":
        raise RuntimeError("Candidate 008 autopsy gate is not approved.")
    for key in (
        "provider_query_allowed",
        "market_data_download_allowed",
        "strategy_backtest_allowed",
        "kronos_inference_allowed",
        "portfolio_search_allowed",
        "parameter_sweep_allowed",
        "promotion_allowed",
        "paper_trading_allowed",
        "live_trading_allowed",
    ):
        if gate.get(key):
            raise RuntimeError(f"Gate unexpectedly allows {key}.")


def _final_decision(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result["decision"],
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "strategy_backtest_performed": False,
        "kronos_inference_performed": False,
        "portfolio_search_performed": False,
        "parameter_sweep_performed": False,
        "promotion_allowed": False,
        "next_allowed_action": result["next_allowed_action"],
    }


def _markdown_report(result: dict[str, Any]) -> str:
    summary = result["summary"]
    lines = [
        "# Candidate 008 Autopsy 001",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: read-only attribution. No provider query, no new backtest, no promotion.",
        "",
        "## Sleeve Attribution",
        "",
    ]
    for row in summary["by_sleeve"]:
        lines.append(
            f"- `{row['sleeve']}`: trades `{row['trade_count']}`, weighted net `{row['weighted_net_return_sum']}`, win rate `{row['win_rate']}`"
        )
    lines.extend(["", "## Universe Attribution", ""])
    for row in summary["by_universe"]:
        lines.append(
            f"- `{row['universe_status']}`: trades `{row['trade_count']}`, weighted net `{row['weighted_net_return_sum']}`, win rate `{row['win_rate']}`"
        )
    lines.extend(["", "## Cost Drag", ""])
    cost = summary["cost_drag"]
    lines.append(f"- Gross weighted sum: `{cost['gross_weighted_sum']}`")
    lines.append(f"- Weighted cost sum: `{cost['weighted_cost_sum']}`")
    lines.append(f"- Weighted net sum: `{cost['weighted_net_sum']}`")
    lines.extend(["", "## Recommendations", ""])
    for rec in summary["recommendations"]:
        lines.append(f"- `{rec['scope']}`: {rec['suggested_action']}")
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    if frame.empty:
        frame.to_csv(path, index=False)
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(frame.columns))
        writer.writeheader()
        writer.writerows(frame.to_dict(orient="records"))


if __name__ == "__main__":
    run_candidate_008_autopsy()
