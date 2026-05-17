from __future__ import annotations

import pandas as pd

from src.backtest.small_cap_execution import SmallCapExecutionConfig
from src.backtest.small_cap_portfolio_backtester import SmallCapPortfolioBacktestConfig, run_small_cap_portfolio_backtest
from src.experiments.nctrl_random_entry_simulator import (
    NctrlRandomEntrySimulatorConfig,
    build_nctrl_random_entry_candidate_export,
)


def _frames() -> dict[str, pd.DataFrame]:
    index = pd.bdate_range("2024-01-01", periods=6)
    base = pd.DataFrame(
        {
            "Open": [10.0, 10.1, 10.2, 10.3, 10.4, 10.5],
            "High": [10.2, 10.3, 10.4, 10.5, 10.6, 10.7],
            "Low": [9.8, 9.9, 10.0, 10.1, 10.2, 10.3],
            "Close": [10.0, 10.1, 10.2, 10.3, 10.4, 10.5],
            "Volume": [1_000_000] * 6,
            "atr": [0.5] * 6,
            "avg_dollar_volume_20d": [2_000_000.0] * 6,
            "relative_volume_20d": [2.0] * 6,
            "open_to_close_return": [0.01] * 6,
            "iwm_close": [220.0] * 6,
            "iwm_ema_200": [200.0] * 6,
        },
        index=index,
    )
    second = base.copy()
    second["Close"] = [20.0, 20.1, 20.2, 20.3, 20.4, 20.5]
    second["Open"] = [20.0, 20.1, 20.2, 20.3, 20.4, 20.5]
    third = base.copy()
    third["Close"] = [30.0, 30.1, 30.2, 30.3, 30.4, 30.5]
    third["Open"] = [30.0, 30.1, 30.2, 30.3, 30.4, 30.5]
    return {"AAA": base, "BBB": second, "CCC": third}


def test_nctrl_random_entry_candidate_export_is_deterministic_and_schema_compatible() -> None:
    frames = _frames()
    as_of_dates = ["2024-01-02", "2024-01-03", "2024-01-04"]
    config = NctrlRandomEntrySimulatorConfig(seed=701, candidates_per_day=2)

    first = build_nctrl_random_entry_candidate_export(frames, as_of_dates, config=config)
    second = build_nctrl_random_entry_candidate_export(frames, as_of_dates, config=config)

    assert first.equals(second)
    assert first["as_of"].tolist() == ["2024-01-02", "2024-01-02", "2024-01-03", "2024-01-03", "2024-01-04", "2024-01-04"]
    assert first["operational_candidate"].tolist() == [True] * 6
    assert first["small_cap_setup"].unique().tolist() == ["nctrl_random_entry"]
    assert first["small_cap_scanner_pass"].tolist() == [True] * 6
    assert set(first["symbol"]).issubset({"AAA", "BBB", "CCC"})
    assert first["small_cap_scanner_score"].between(0.0, 1.0).all()


def test_nctrl_random_entry_simulator_preserves_portfolio_execution_mechanics() -> None:
    candidates = build_nctrl_random_entry_candidate_export(
        _frames(),
        ["2024-01-02", "2024-01-03"],
        config=NctrlRandomEntrySimulatorConfig(seed=702, candidates_per_day=1),
    )
    portfolio_config = SmallCapPortfolioBacktestConfig(
        initial_cash=20_000.0,
        holding_period_bars=1,
        max_concurrent_positions=1,
        execution=SmallCapExecutionConfig(
            spread_bps=0.0,
            slippage_bps=0.0,
            risk_fraction=0.5,
            max_position_dollar_volume_fraction=0.001,
            min_trade_notional=100.0,
        ),
    )

    result = run_small_cap_portfolio_backtest(candidates, _frames(), config=portfolio_config)

    assert result.summary["total_trades"] >= 1
    assert set(result.trade_log["small_cap_setup"]) == {"nctrl_random_entry"}
    assert (result.trade_log["position_notional"] <= 2_000.0).all()
    assert "missing_price_path" not in result.rejection_summary


def test_nctrl_random_entry_config_defaults_are_fixed_for_trial_infrastructure() -> None:
    default = NctrlRandomEntrySimulatorConfig()

    assert default.seed == 701
    assert default.candidates_per_day == 1
    assert default.setup_label == "nctrl_random_entry"
