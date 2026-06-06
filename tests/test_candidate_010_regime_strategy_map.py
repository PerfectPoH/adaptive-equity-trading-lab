import json
from pathlib import Path

import pandas as pd

from src.experiments.candidate_010_regime_strategy_map import (
    generate_candidate_010_trades,
    run_candidate_010_regime_strategy_map,
)


def _frame(start: float, drift: float, periods: int = 180, volume: int = 1_000_000) -> pd.DataFrame:
    index = pd.bdate_range("2025-01-01", periods=periods)
    close = pd.Series([start * (1.0 + drift * i / periods) for i in range(periods)], index=index)
    wiggle = pd.Series([(i % 5 - 2) * 0.002 for i in range(periods)], index=index)
    close = close * (1.0 + wiggle)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": volume,
        },
        index=index,
    )


def _write_dataset(root: Path) -> None:
    root.mkdir()
    frames = {
        "AAA": _frame(10, 0.30),
        "BBB": _frame(10, 0.10),
        "CCC": _frame(10, -0.10),
        "DDD": _frame(10, -0.25),
        "EEE": _frame(10, 0.02),
        "SPY": _frame(100, 0.05),
        "IWM": _frame(80, 0.04),
    }
    price_rows = []
    master_rows = []
    for symbol, frame in frames.items():
        status = "benchmark" if symbol in {"SPY", "IWM"} else "active"
        master_rows.append({"symbol": symbol, "universe_status": status, "is_delisted": False})
        for date, row in frame.iterrows():
            price_rows.append(
                {
                    "symbol": symbol,
                    "date": date.date().isoformat(),
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"],
                    "provider_dataset": "Norgate Data",
                }
            )
    pd.DataFrame(price_rows).to_csv(root / "prices.csv", index=False)
    pd.DataFrame(master_rows).to_csv(root / "security_master.csv", index=False)


def _gate(gate_dir: Path, dataset: Path) -> None:
    gate_dir.mkdir()
    (gate_dir / "gate_manifest.json").write_text(
        json.dumps(
            {
                "status": "APPROVED_ONE_REGIME_STRATEGY_MAP_DIAGNOSTIC_ONLY",
                "linked_dataset": str(dataset),
                "allowed_backtest_count": 1,
                "provider_query_allowed": False,
                "market_data_download_allowed": False,
                "kronos_inference_allowed": False,
                "portfolio_search_allowed": False,
                "parameter_sweep_allowed": False,
                "promotion_allowed": False,
                "paper_trading_allowed": False,
                "live_trading_allowed": False,
                "oos_split": {"in_sample_end": "2025-04-30", "out_of_sample_start": "2025-05-01"},
                "strategy_contract": {
                    "rebalance_every_n_trading_days": 20,
                    "cost_bps_round_trip": 500,
                    "tradability": {
                        "min_price_asof": 1.0,
                        "min_trailing_20d_median_turnover": 1000000.0,
                        "min_history_rows": 30,
                    },
                    "families": {
                        "momentum_60d": {
                            "lookback_days": 30,
                            "holding_days": 10,
                            "top_k": 2,
                            "rank_direction": "highest_return",
                        },
                        "mean_reversion_5d": {
                            "lookback_days": 5,
                            "holding_days": 10,
                            "top_k": 2,
                            "rank_direction": "lowest_return",
                        },
                        "volatility_compression_20d": {
                            "volatility_window_days": 20,
                            "holding_days": 10,
                            "top_k": 2,
                            "rank_direction": "lowest_volatility",
                        },
                        "dollar_volume_shock_20d": {
                            "dollar_volume_window_days": 20,
                            "holding_days": 10,
                            "top_k": 2,
                            "rank_direction": "highest_dollar_volume_ratio",
                        },
                    },
                    "family_weights": {
                        "momentum_60d": 1.0,
                        "mean_reversion_5d": 1.0,
                        "volatility_compression_20d": 1.0,
                        "dollar_volume_shock_20d": 1.0,
                    },
                },
                "robustness_gates": {
                    "min_oos_trades_per_family_regime": 1,
                    "min_oos_weighted_net_sum": 0.0,
                    "min_oos_ex_top3_weighted_net_sum": 0.0,
                    "min_oos_win_rate": 0.5,
                },
                "ranking_policy": {
                    "allowed": True,
                    "scope": "descriptive_only",
                    "cannot_be_used_for_promotion": True,
                },
            }
        ),
        encoding="utf-8",
    )


def _regime_map() -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-01", periods=180)
    labels = ["RECOVERY_BOUNCE", "DRAWDOWN_STRESS", "TREND_UP_HIGH_VOL", "RISK_OFF"]
    return pd.DataFrame(
        [{"date": date.date().isoformat(), "regime_label": labels[i % len(labels)]} for i, date in enumerate(dates)]
    )


def test_generate_candidate_010_trades_emits_all_predeclared_families_without_route_selection() -> None:
    frames = {
        "AAA": _frame(10, 0.3),
        "BBB": _frame(10, 0.1),
        "CCC": _frame(10, -0.1),
        "DDD": _frame(10, -0.25),
        "EEE": _frame(10, 0.02),
    }
    symbols = sorted(frames)
    contract = json.loads(
        (Path("experiments/provider_aware_research/candidate_010_regime_strategy_map_gate_20260606/gate_manifest.json"))
        .read_text(encoding="utf-8")
    )["strategy_contract"]

    trades = generate_candidate_010_trades(symbols, frames, _regime_map(), contract)

    assert trades
    assert {trade["family"] for trade in trades} == set(contract["families"])
    assert all(trade["provider_query_performed"] is False for trade in trades)
    assert all(trade["selection_policy"] == "predeclared_family_map" for trade in trades)


def test_run_candidate_010_regime_strategy_map_is_non_promotable_diagnostic(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    gate = tmp_path / "gate"
    output = tmp_path / "out"
    _write_dataset(dataset)
    _gate(gate, dataset)

    result = run_candidate_010_regime_strategy_map(gate_dir=gate, output_dir=output)

    assert result["provider_query_performed"] is False
    assert result["market_data_download_performed"] is False
    assert result["portfolio_search_performed"] is False
    assert result["parameter_sweep_performed"] is False
    assert result["promotion_allowed"] is False
    assert result["ranking_scope"] == "descriptive_only"
    assert result["decision"] == "CANDIDATE_010_REGIME_STRATEGY_MAP_ARCHIVE_NO_PROMOTION"
    assert (output / "family_regime_summary.csv").exists()
    assert (output / "candidate_010_regime_strategy_map_result.json").exists()
