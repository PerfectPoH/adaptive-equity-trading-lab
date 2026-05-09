from __future__ import annotations

import pandas as pd

from src.risk.market_regime_guardrail import MarketRegimeGuardrailConfig, add_market_regime_guardrail_columns


def test_market_regime_guardrail_allows_signals_in_favorable_regime() -> None:
    frame = pd.DataFrame(
        {
            "signal": [True, False],
            "iwm_close": [210.0, 211.0],
            "iwm_ema_50": [200.0, 200.0],
            "vix_close": [18.0, 19.0],
        }
    )

    result = add_market_regime_guardrail_columns(frame)

    assert result["market_regime_trade_allowed"].tolist() == [True, True]
    assert result["signal"].tolist() == [True, False]
    assert result["market_regime_block_reason"].tolist() == ["", ""]


def test_market_regime_guardrail_blocks_signals_when_iwm_below_ema_50() -> None:
    frame = pd.DataFrame(
        {
            "signal": [True],
            "iwm_close": [195.0],
            "iwm_ema_50": [200.0],
            "vix_close": [18.0],
        }
    )

    result = add_market_regime_guardrail_columns(frame)

    assert result.iloc[0]["signal_before_market_regime_guardrail"] is True
    assert result.iloc[0]["signal"] is False
    assert result.iloc[0]["market_regime_trade_allowed"] is False
    assert result.iloc[0]["market_regime_block_reason"] == "iwm_below_ema_50"


def test_market_regime_guardrail_blocks_signals_when_vix_above_max() -> None:
    frame = pd.DataFrame(
        {
            "signal": [True],
            "iwm_close": [210.0],
            "iwm_ema_50": [200.0],
            "vix_close": [36.0],
        }
    )

    result = add_market_regime_guardrail_columns(frame)

    assert result.iloc[0]["signal"] is False
    assert result.iloc[0]["market_regime_block_reason"] == "vix_above_max"


def test_market_regime_guardrail_fails_closed_when_regime_data_missing() -> None:
    frame = pd.DataFrame({"signal": [True], "iwm_close": [210.0], "vix_close": [18.0]})

    result = add_market_regime_guardrail_columns(frame)

    assert result.iloc[0]["signal"] is False
    assert result.iloc[0]["market_regime_trade_allowed"] is False
    assert "missing_iwm_ema_50" in result.iloc[0]["market_regime_block_reason"]


def test_market_regime_guardrail_can_require_breadth_and_iwm_ema_200() -> None:
    frame = pd.DataFrame(
        {
            "signal": [True],
            "iwm_close": [210.0],
            "iwm_ema_50": [200.0],
            "iwm_ema_200": [220.0],
            "vix_close": [18.0],
            "small_cap_breadth": [0.45],
        }
    )
    config = MarketRegimeGuardrailConfig(require_iwm_above_ema_200=True, min_small_cap_breadth=0.50)

    result = add_market_regime_guardrail_columns(frame, config=config)

    reasons = result.iloc[0]["market_regime_block_reason"]
    assert result.iloc[0]["signal"] is False
    assert "iwm_below_ema_200" in reasons
    assert "breadth_below_min" in reasons
