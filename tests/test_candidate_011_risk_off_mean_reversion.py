import json
from pathlib import Path

import pandas as pd

from src.experiments.candidate_011_risk_off_mean_reversion import (
    generate_candidate_011_trades,
    run_candidate_011_risk_off_mean_reversion,
)


def _frame(start: float, drift: float, periods: int = 180) -> pd.DataFrame:
    index = pd.bdate_range("2025-01-01", periods=periods)
    close = pd.Series([start * (1.0 + drift * i / periods) for i in range(periods)], index=index)
    shock = pd.Series([0.0 if i % 17 else -0.03 for i in range(periods)], index=index)
    close = close * (1.0 + shock)
    return pd.DataFrame({"Open": close, "High": close * 1.01, "Low": close * 0.99, "Close": close, "Volume": 1_000_000}, index=index)


def _write_dataset(root: Path) -> None:
    root.mkdir()
    frames = {
        "AAA": _frame(10, 0.15),
        "BBB": _frame(10, 0.05),
        "CCC": _frame(10, -0.10),
        "DDD": _frame(10, -0.20),
        "SPY": _frame(100, 0.03),
        "IWM": _frame(80, 0.02),
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
                "status": "APPROVED_ONE_RISK_OFF_MEAN_REVERSION_DIAGNOSTIC_ONLY",
                "linked_dataset": str(dataset),
                "allowed_backtest_count": 1,
                "same_dataset_as_discovery": True,
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
                    "allowed_regimes": ["RISK_OFF"],
                    "tradability": {
                        "min_price_asof": 1.0,
                        "min_trailing_20d_median_turnover": 1000000.0,
                        "min_history_rows": 30,
                    },
                    "sleeve": {
                        "name": "risk_off_mean_reversion_5d",
                        "lookback_days": 5,
                        "holding_days": 10,
                        "top_k": 3,
                        "rank_direction": "lowest_return",
                    },
                },
                "robustness_gates": {
                    "min_oos_trades": 1,
                    "require_positive_oos_net": True,
                    "require_positive_oos_median": True,
                    "require_oos_win_rate_at_least": 0.5,
                    "require_positive_ex_top3_oos_net": False,
                    "require_oos_beats_cash": True,
                    "require_oos_beats_spy": False,
                    "require_oos_beats_iwm": False,
                },
            }
        ),
        encoding="utf-8",
    )


def _regime_map() -> pd.DataFrame:
    dates = pd.bdate_range("2025-01-01", periods=180)
    return pd.DataFrame(
        [
            {"date": date.date().isoformat(), "regime_label": "RISK_OFF" if i % 2 == 0 else "RECOVERY_BOUNCE"}
            for i, date in enumerate(dates)
        ]
    )


def test_generate_candidate_011_trades_only_risk_off_mean_reversion() -> None:
    frames = {"AAA": _frame(10, 0.15), "BBB": _frame(10, 0.05), "CCC": _frame(10, -0.10), "DDD": _frame(10, -0.20)}
    symbols = sorted(frames)
    contract = json.loads(
        Path("experiments/provider_aware_research/candidate_011_risk_off_mean_reversion_gate_20260606/gate_manifest.json").read_text(
            encoding="utf-8"
        )
    )["strategy_contract"]
    contract["tradability"]["min_history_rows"] = 30
    contract["sleeve"]["top_k"] = 3

    trades = generate_candidate_011_trades(symbols, frames, _regime_map(), contract)

    assert trades
    assert {trade["regime_label"] for trade in trades} == {"RISK_OFF"}
    assert {trade["sleeve"] for trade in trades} == {"risk_off_mean_reversion_5d"}
    assert all(trade["provider_query_performed"] is False for trade in trades)


def test_run_candidate_011_is_fixed_non_promotable_diagnostic(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    gate = tmp_path / "gate"
    output = tmp_path / "out"
    _write_dataset(dataset)
    _gate(gate, dataset)

    result = run_candidate_011_risk_off_mean_reversion(gate_dir=gate, output_dir=output)

    assert result["provider_query_performed"] is False
    assert result["market_data_download_performed"] is False
    assert result["parameter_sweep_performed"] is False
    assert result["promotion_allowed"] is False
    assert result["same_dataset_as_discovery"] is True
    assert result["decision"] == "CANDIDATE_011_RISK_OFF_MEAN_REVERSION_ARCHIVE_NO_PROMOTION"
    assert (output / "trade_log.csv").exists()
    assert (output / "candidate_011_risk_off_mean_reversion_result.json").exists()
