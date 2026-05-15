from __future__ import annotations

from src.backtest.small_cap_execution import SmallCapExecutionConfig
from src.backtest.small_cap_portfolio_backtester import SmallCapPortfolioBacktestConfig
from src.risk.market_regime_guardrail import MarketRegimeGuardrailConfig
from src.scanner.small_cap_swing_scanner import SmallCapSwingScannerConfig

from experiments.configs import nctrl_scaffolding


def test_nctrl_scaffolding_freezes_baseline_universe() -> None:
    assert nctrl_scaffolding.BASELINE_SYMBOLS == ("AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "AMZN", "GOOGL", "SPY", "QQQ")
    metadata = nctrl_scaffolding.build_static_metadata()
    assert metadata["symbol"].tolist() == list(nctrl_scaffolding.BASELINE_SYMBOLS)
    assert metadata.loc[metadata["symbol"].isin(["SPY", "QQQ"]), "is_etf"].eq(True).all()


def test_nctrl_scaffolding_only_changes_universe_scope() -> None:
    universe = nctrl_scaffolding.RUN_CONFIG.candidate_export.universe
    assert universe.max_market_cap == 10_000_000_000_000
    assert universe.exclude_etfs is False
    assert universe.min_market_cap == 0
    assert nctrl_scaffolding.RUN_CONFIG.candidate_export.scanner == SmallCapSwingScannerConfig()
    assert nctrl_scaffolding.RUN_CONFIG.candidate_export.execution == SmallCapExecutionConfig()
    assert nctrl_scaffolding.RUN_CONFIG.candidate_export.regime == MarketRegimeGuardrailConfig()
    assert nctrl_scaffolding.RUN_CONFIG.portfolio == SmallCapPortfolioBacktestConfig()


def test_nctrl_scaffolding_manifest_extras_are_not_trial_accounting() -> None:
    assert nctrl_scaffolding.EXTRAS["purpose"] == "nctrl_scaffolding_check"
    assert nctrl_scaffolding.EXTRAS["research_item"] == "RESEARCH-046"
    assert nctrl_scaffolding.EXTRAS["not_a_trial"] is True
    assert nctrl_scaffolding.CONFIG_SOURCE == "experiments/configs/nctrl_scaffolding.py"
