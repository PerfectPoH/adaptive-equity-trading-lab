from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.experiments import candidate_006_kronos_smoke as smoke


def _sample_ohlcv() -> pd.DataFrame:
    index = pd.bdate_range("2026-01-01", periods=35)
    return pd.DataFrame(
        {
            "Open": [100.0 + i * 0.1 for i in range(35)],
            "High": [100.4 + i * 0.1 for i in range(35)],
            "Low": [99.8 + i * 0.1 for i in range(35)],
            "Close": [100.2 + i * 0.1 for i in range(35)],
            "Volume": [1_000_000 + i * 1000 for i in range(35)],
        },
        index=index,
    )


def _gate(path: Path) -> None:
    path.mkdir()
    payload = {
        "status": "APPROVED_KRONOS_INFERENCE_SMOKE_ONLY",
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "allowed_models": {
            "tokenizer": "NeoQuasar/Kronos-Tokenizer-2k",
            "model": "NeoQuasar/Kronos-mini",
        },
        "runtime_constraints": {
            "device": "cpu",
            "max_symbols": 1,
            "lookback_rows": 32,
            "pred_len": 5,
            "sample_count": 1,
            "temperature": 1.0,
            "top_p": 0.9,
        },
    }
    (path / "gate_manifest.json").write_text(json.dumps(payload), encoding="utf-8")


def test_forecast_feature_summary_is_feature_only() -> None:
    input_frame = smoke.prepare_kronos_input_frame(_sample_ohlcv(), lookback_rows=32)
    future_index = pd.bdate_range(input_frame.index[-1] + pd.Timedelta(days=1), periods=5)
    forecast = pd.DataFrame(
        {
            "open": [104.0, 104.1, 104.2, 104.3, 104.4],
            "high": [104.5, 104.6, 104.7, 104.8, 104.9],
            "low": [103.7, 103.8, 103.9, 104.0, 104.1],
            "close": [104.1, 104.2, 104.3, 104.4, 104.5],
            "volume": [1.0] * 5,
            "amount": [104.0] * 5,
        },
        index=future_index,
    )

    features = smoke.summarize_kronos_forecast(input_frame, forecast)

    assert set(features) == set(smoke.KRONOS_SMOKE_FEATURES)
    assert features["kronos_probability_up"] == 1.0
    assert features["kronos_forecast_return_mean"] > 0


def test_smoke_run_writes_no_promotion_artifacts(monkeypatch, tmp_path: Path) -> None:
    gate_dir = tmp_path / "gate"
    _gate(gate_dir)

    def fake_predict(*, input_frame: pd.DataFrame, pred_len: int, **kwargs) -> pd.DataFrame:
        future_index = pd.bdate_range(input_frame.index[-1] + pd.Timedelta(days=1), periods=pred_len)
        last_close = float(input_frame["close"].iloc[-1])
        return pd.DataFrame(
            {
                "open": [last_close + 0.1] * pred_len,
                "high": [last_close + 0.3] * pred_len,
                "low": [last_close - 0.1] * pred_len,
                "close": [last_close + 0.2] * pred_len,
                "volume": [1.0] * pred_len,
                "amount": [last_close] * pred_len,
            },
            index=future_index,
        )

    monkeypatch.setattr(smoke, "_run_real_kronos_prediction", fake_predict)

    result = smoke.run_candidate_006_kronos_inference_smoke(
        gate_dir=gate_dir,
        output_dir=tmp_path / "out",
        sample_frame=_sample_ohlcv(),
        kronos_repo_dir=tmp_path / "kronos",
    )

    assert result["decision"] == "CANDIDATE_006_KRONOS_INFERENCE_SMOKE_COMPLETE_NO_BACKTEST"
    assert result["inference_performed"] is True
    assert result["portfolio_backtest_performed"] is False
    assert result["promotion_allowed"] is False
    assert result["financial_performance_claimed"] is False
    assert (tmp_path / "out" / "kronos_smoke_result.json").is_file()
    assert (tmp_path / "out" / "forecast_preview.csv").is_file()
