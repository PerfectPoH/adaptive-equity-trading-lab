from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.experiments import candidate_006_kronos_batch_features as batch


def _gate(path: Path) -> None:
    path.mkdir()
    payload = {
        "status": "APPROVED_KRONOS_BATCH_FEATURE_GENERATION_ONLY",
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "runtime_constraints": {
            "device": "cpu",
            "max_symbol_date_pairs": 3,
            "lookback_rows": 4,
            "pred_len": 2,
            "sample_count": 1,
            "temperature": 1.0,
            "top_p": 0.9,
        },
        "allowed_models": {
            "tokenizer": "NeoQuasar/Kronos-Tokenizer-2k",
            "model": "NeoQuasar/Kronos-mini",
        },
    }
    (path / "gate_manifest.json").write_text(json.dumps(payload), encoding="utf-8")


def _frame() -> pd.DataFrame:
    index = pd.bdate_range("2026-01-01", periods=8)
    return pd.DataFrame(
        {
            "Open": [10 + i for i in range(8)],
            "High": [10.5 + i for i in range(8)],
            "Low": [9.5 + i for i in range(8)],
            "Close": [10.2 + i for i in range(8)],
            "Volume": [1000 + i for i in range(8)],
        },
        index=index,
    )


def test_frozen_signal_pairs_ignore_realized_return_columns() -> None:
    trades = pd.DataFrame(
        [
            {"symbol": "AAA", "signal_date": "2026-01-06", "net_return": 99.0},
            {"symbol": "AAA", "signal_date": "2026-01-06", "net_return": -99.0},
            {"symbol": "BBB", "signal_date": "2026-01-07", "weighted_net_return": 42.0},
        ]
    )

    pairs = batch.frozen_symbol_date_pairs(trades, max_pairs=10)

    assert pairs == [("AAA", "2026-01-06"), ("BBB", "2026-01-07")]


def test_batch_feature_run_writes_feature_rows_without_backtest(monkeypatch, tmp_path: Path) -> None:
    gate_dir = tmp_path / "gate"
    _gate(gate_dir)
    trade_log = tmp_path / "trade_log.csv"
    pd.DataFrame(
        [
            {"symbol": "AAA", "signal_date": "2026-01-08", "net_return": 1.23},
            {"symbol": "BBB", "signal_date": "2026-01-08", "gross_return": -4.56},
        ]
    ).to_csv(trade_log, index=False)
    frames = {"AAA": _frame(), "BBB": _frame()}

    def fake_predictor(input_frame: pd.DataFrame, pred_len: int) -> pd.DataFrame:
        future_index = pd.bdate_range(input_frame.index[-1] + pd.Timedelta(days=1), periods=pred_len)
        last_close = float(input_frame["close"].iloc[-1])
        return pd.DataFrame(
            {
                "open": [last_close + 0.1] * pred_len,
                "high": [last_close + 0.2] * pred_len,
                "low": [last_close - 0.1] * pred_len,
                "close": [last_close + 0.15] * pred_len,
                "volume": [1.0] * pred_len,
                "amount": [last_close] * pred_len,
            },
            index=future_index,
        )

    result = batch.run_candidate_006_kronos_batch_feature_generation(
        gate_dir=gate_dir,
        output_dir=tmp_path / "out",
        trade_log_path=trade_log,
        frames=frames,
        predictor=fake_predictor,
    )

    assert result["decision"] == "CANDIDATE_006_KRONOS_BATCH_FEATURE_GENERATION_COMPLETE"
    assert result["portfolio_backtest_performed"] is False
    assert result["threshold_optimization_performed"] is False
    assert result["promotion_allowed"] is False
    assert result["coverage"]["feature_rows"] == 2
    feature_rows = pd.read_csv(tmp_path / "out" / "kronos_batch_features.csv")
    assert feature_rows["symbol"].tolist() == ["AAA", "BBB"]
    assert "net_return" not in feature_rows.columns
    assert (tmp_path / "out" / "final_decision.json").is_file()
