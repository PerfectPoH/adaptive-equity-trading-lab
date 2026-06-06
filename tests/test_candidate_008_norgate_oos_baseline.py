import json
from pathlib import Path

import pandas as pd

from src.experiments.candidate_008_norgate_oos_baseline import (
    build_frames_from_candidate_007_dataset,
    generate_candidate_008_trades,
    run_candidate_008_norgate_oos_baseline,
)


def _write_dataset(root: Path) -> None:
    root.mkdir()
    dates = pd.bdate_range("2025-01-01", periods=160)
    price_rows = []
    master_rows = []
    specs = {
        "AAA": 0.20,
        "BBB": 0.10,
        "CCC": -0.05,
        "DDD": -0.10,
        "EEE": 0.03,
        "SPY": 0.05,
        "IWM": 0.04,
    }
    for symbol, drift in specs.items():
        status = "benchmark" if symbol in {"SPY", "IWM"} else ("delisted" if symbol == "DDD" else "active")
        master_rows.append(
            {
                "symbol": symbol,
                "universe_status": status,
                "is_delisted": status == "delisted",
                "first_date": str(dates[0].date()),
                "last_date": str(dates[-1].date()),
                "row_count": len(dates),
                "provider": "Norgate Data",
            }
        )
        for i, date in enumerate(dates):
            close = 10.0 * (1.0 + drift * i / len(dates))
            price_rows.append(
                {
                    "symbol": symbol,
                    "date": str(date.date()),
                    "open": close,
                    "high": close * 1.01,
                    "low": close * 0.99,
                    "close": close,
                    "volume": 1_000_000,
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
                "status": "APPROVED_ONE_NORGATE_OOS_BASELINE_BACKTEST_DIAGNOSTIC_ONLY",
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
                    "sleeves": {
                        "momentum_60d": {
                            "lookback_days": 30,
                            "holding_days": 10,
                            "top_k": 2,
                            "sleeve_weight": 0.5,
                            "rank_direction": "highest_return",
                        },
                        "mean_reversion_5d": {
                            "lookback_days": 5,
                            "holding_days": 5,
                            "top_k": 2,
                            "sleeve_weight": 0.5,
                            "rank_direction": "lowest_return",
                        },
                    },
                },
                "robustness_gates": {
                    "min_oos_trades": 2,
                    "require_positive_oos_net": True,
                    "require_positive_ex_top3_oos_net": True,
                    "require_oos_beats_spy": True,
                    "require_oos_beats_iwm": True,
                },
            }
        ),
        encoding="utf-8",
    )


def test_build_frames_from_candidate_007_dataset_excludes_benchmarks_from_symbol_list(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    _write_dataset(dataset)

    frames, symbols, benchmarks, master = build_frames_from_candidate_007_dataset(dataset)

    assert "SPY" not in symbols
    assert "IWM" not in symbols
    assert {"SPY", "IWM"}.issubset(benchmarks)
    assert "AAA" in frames
    assert not master.empty


def test_generate_candidate_008_trades_uses_asof_tradability_and_two_sleeves(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    _write_dataset(dataset)
    frames, symbols, _, _ = build_frames_from_candidate_007_dataset(dataset)
    contract = {
        "rebalance_every_n_trading_days": 20,
        "cost_bps_round_trip": 500,
        "tradability": {"min_price_asof": 1.0, "min_trailing_20d_median_turnover": 1000000.0, "min_history_rows": 30},
        "sleeves": {
            "momentum_60d": {"lookback_days": 30, "holding_days": 10, "top_k": 2, "sleeve_weight": 0.5, "rank_direction": "highest_return"},
            "mean_reversion_5d": {"lookback_days": 5, "holding_days": 5, "top_k": 2, "sleeve_weight": 0.5, "rank_direction": "lowest_return"},
        },
    }

    trades = generate_candidate_008_trades(symbols, frames, contract)

    assert trades
    assert {trade["sleeve"] for trade in trades} == {"momentum_60d", "mean_reversion_5d"}
    assert all(trade["provider_query_performed"] is False for trade in trades)


def test_run_candidate_008_norgate_oos_baseline_writes_no_promotion_artifacts(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    gate = tmp_path / "gate"
    output = tmp_path / "out"
    _write_dataset(dataset)
    _gate(gate, dataset)

    result = run_candidate_008_norgate_oos_baseline(gate_dir=gate, output_dir=output)

    assert result["decision"].startswith("CANDIDATE_008_NORGATE_OOS_BASELINE_")
    assert result["provider_query_performed"] is False
    assert result["market_data_download_performed"] is False
    assert result["parameter_sweep_performed"] is False
    assert result["promotion_allowed"] is False
    assert "oos" in result["summary_by_split"]
    assert (output / "trade_log.csv").exists()
    assert (output / "final_decision.json").exists()
