import json
from pathlib import Path

import pandas as pd

from src.experiments.candidate_009_regime_momentum import (
    generate_candidate_009_trades,
    run_candidate_009_regime_momentum,
)


def _frame(start: float, drift: float, periods: int = 180) -> pd.DataFrame:
    index = pd.bdate_range("2025-01-01", periods=periods)
    close = pd.Series([start * (1.0 + drift * i / periods) for i in range(periods)], index=index)
    return pd.DataFrame({"Open": close, "High": close * 1.01, "Low": close * 0.99, "Close": close, "Volume": 1_000_000}, index=index)


def _write_dataset(root: Path) -> None:
    root.mkdir()
    frames = {
        "AAA": _frame(10, 0.30),
        "BBB": _frame(10, 0.20),
        "CCC": _frame(10, -0.10),
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
                "status": "APPROVED_ONE_POST_AUTOPSY_REGIME_MOMENTUM_BACKTEST_DIAGNOSTIC_ONLY",
                "linked_dataset": str(dataset),
                "linked_autopsy": "autopsy.json",
                "allowed_backtest_count": 1,
                "post_autopsy_same_panel": True,
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
                    "routes": {"RECOVERY_BOUNCE": {"momentum_60d": 1.0}, "DRAWDOWN_STRESS": {"momentum_60d": 1.0}},
                    "sleeves": {
                        "momentum_60d": {
                            "lookback_days": 30,
                            "holding_days": 10,
                            "top_k": 2,
                            "rank_direction": "highest_return",
                        }
                    },
                    "disabled_sleeves": {"mean_reversion_5d": "disabled"},
                },
                "robustness_gates": {
                    "min_oos_trades": 1,
                    "require_positive_oos_net": True,
                    "require_positive_ex_top3_oos_net": False,
                    "require_oos_beats_spy": False,
                    "require_oos_beats_iwm": False,
                },
            }
        ),
        encoding="utf-8",
    )


def test_generate_candidate_009_trades_only_uses_allowed_regimes() -> None:
    frames = {"AAA": _frame(10, 0.3), "BBB": _frame(10, 0.2), "CCC": _frame(10, -0.1)}
    symbols = ["AAA", "BBB", "CCC"]
    regime_map = pd.DataFrame(
        [
            {"date": date.date().isoformat(), "regime_label": "RECOVERY_BOUNCE" if i % 2 == 0 else "RISK_OFF"}
            for i, date in enumerate(pd.bdate_range("2025-01-01", periods=180))
        ]
    )
    contract = {
        "rebalance_every_n_trading_days": 20,
        "cost_bps_round_trip": 500,
        "tradability": {"min_price_asof": 1.0, "min_trailing_20d_median_turnover": 1000000.0, "min_history_rows": 30},
        "routes": {"RECOVERY_BOUNCE": {"momentum_60d": 1.0}},
        "sleeves": {"momentum_60d": {"lookback_days": 30, "holding_days": 10, "top_k": 2, "rank_direction": "highest_return"}},
    }

    trades = generate_candidate_009_trades(symbols, frames, regime_map, contract)

    assert trades
    assert {trade["sleeve"] for trade in trades} == {"momentum_60d"}
    assert {trade["regime_label"] for trade in trades} == {"RECOVERY_BOUNCE"}


def test_run_candidate_009_regime_momentum_is_diagnostic_only(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    gate = tmp_path / "gate"
    output = tmp_path / "out"
    _write_dataset(dataset)
    _gate(gate, dataset)

    result = run_candidate_009_regime_momentum(gate_dir=gate, output_dir=output)

    assert result["provider_query_performed"] is False
    assert result["market_data_download_performed"] is False
    assert result["parameter_sweep_performed"] is False
    assert result["promotion_allowed"] is False
    assert result["post_autopsy_same_panel"] is True
    assert "mean_reversion_5d" not in set(pd.read_csv(output / "trade_log.csv").get("sleeve", []))
    assert (output / "final_decision.json").exists()
