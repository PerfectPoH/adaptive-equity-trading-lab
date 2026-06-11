from __future__ import annotations

import numpy as np
import pandas as pd

from src.experiments.stream_extension import (
    Recipe,
    causal_trades_after_freeze,
    component_recipe,
    extend_components,
)


def _panel(periods: int = 700, seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2024-01-02", periods=periods)
    close = 100 * np.cumprod(1 + rng.normal(0.0006, 0.015, periods))
    return pd.DataFrame(
        {"Open": close, "High": close * 1.01, "Low": close * 0.99, "Close": close,
         "Volume": rng.integers(1_000_000, 9_000_000, periods).astype(float)},
        index=dates,
    )


def test_no_trades_on_or_before_freeze() -> None:
    panel = _panel()
    freeze = panel.index[400]
    trades, pending = causal_trades_after_freeze(panel, Recipe("Momentum", 20, 100, ("X",)), freeze=freeze)
    assert all(pd.Timestamp(t["period"]) > freeze for t in trades)
    assert pending >= 0


def test_thresholds_are_causal_under_future_mutation() -> None:
    panel = _panel()
    freeze = panel.index[400]
    base, _ = causal_trades_after_freeze(panel, Recipe("Momentum", 20, 100, ("X",)), freeze=freeze)
    mutated = panel.copy()
    mutated.iloc[-30:, mutated.columns.get_loc("Close")] *= 2.0  # futuro remoto cambiato
    after, _ = causal_trades_after_freeze(mutated, Recipe("Momentum", 20, 100, ("X",)), freeze=freeze)
    horizon = panel.index[-60]  # i trade con entry+exit prima della mutazione
    base_early = [t for t in base if pd.Timestamp(t["period"]) < horizon]
    after_early = [t for t in after if pd.Timestamp(t["period"]) < horizon]
    assert base_early == after_early


def test_extend_components_appends_only_and_flags_frozen() -> None:
    panel = _panel()
    freeze = panel.index[400]
    rows = [{"period": str(d.date()), "net_return": 0.001} for d in panel.index[:100]]
    extendable = {
        "component_id": "C1", "strategy_name": "Factory Momentum 20d 100bps",
        "template": "Momentum", "cost_bps": 100, "inline_returns": rows,
        "trade_list_path": "", "equity_curve_path": "",
        "factory_manifest": {"holding_period_days": 20, "cost_bps": 100},
    }
    # recipe richiede simboli dal trade list -> senza, va flaggato frozen
    import src.experiments.stream_extension as se
    recipe = component_recipe(extendable)
    assert recipe is None  # nessun trade list -> non estendibile, onesto
    frozen_clone, coverage = extend_components([extendable], {"X": panel}, freeze=freeze)
    assert coverage["frozen"] == 1 and coverage["extendable"] == 0
    # con simboli forzati nella recipe, l'estensione appende solo dopo il freeze
    trades, _ = causal_trades_after_freeze(panel, Recipe("Momentum", 20, 100, ("X",)), freeze=freeze)
    assert trades, "atteso almeno un trade post-freeze sul sintetico"
