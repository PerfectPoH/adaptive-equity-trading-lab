from __future__ import annotations

import pandas as pd
from backtesting import Backtest, Strategy

from src.backtest.metrics import stats_to_summary


class PrecomputedSignalStrategy(Strategy):
    timeout_bars = 10
    initial_cash = 100_000.0

    def init(self) -> None:
        pass

    def next(self) -> None:
        self._close_timed_out_trades()
        if self.position:
            return

        signal = bool(self.data.signal[-1])
        execution_valid = bool(self.data.execution_valid[-1])
        if not signal or not execution_valid:
            return

        size = int(self.data.position_size[-1])
        if size <= 0:
            return

        entry_price = float(self.data.entry_price[-1])
        stop_loss = float(self.data.stop_loss[-1])
        take_profit = float(self.data.take_profit[-1])
        if not stop_loss < entry_price < take_profit:
            return

        # RISK-043: il rischio segue l'equity corrente, non i 100k iniziali.
        # La size precomputata incorpora gia' risk_fraction e distanza di stop:
        # la riscaliamo sull'equity corrente e la cappiamo al cash investibile.
        scaled = int(size * (float(self.equity) / float(self.initial_cash)))
        affordable = int((float(self.equity) * 0.99) / entry_price)
        size = max(0, min(scaled, affordable))
        if size <= 0:
            return

        # Use the precomputed next-open entry as a marketable limit so
        # backtesting.py validates contingent exits against the intended fill.
        self.buy(size=size, limit=entry_price, sl=stop_loss, tp=take_profit)

    def _close_timed_out_trades(self) -> None:
        if self.timeout_bars <= 0:
            return

        current_bar = len(self.data) - 1
        for trade in list(self.trades):
            # RISK-043: la label esce al Close di entry+timeout-1; chiudendo
            # un bar prima il fill avviene all'Open dello STESSO giorno del
            # Close della label (prima era l'Open del giorno successivo).
            if current_bar - trade.entry_bar >= self.timeout_bars - 2:
                trade.close()


def run_backtest(
    frame: pd.DataFrame,
    cash: float = 100_000,
    commission: float = 0.001,
    timeout_bars: int = 10,
) -> tuple[pd.Series, dict[str, float | bool]]:
    required = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "signal",
        "execution_valid",
        "position_size",
        "entry_price",
        "stop_loss",
        "take_profit",
    ]
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise ValueError(f"Backtest frame missing columns: {missing}")

    data = frame.copy().dropna(subset=["Open", "High", "Low", "Close", "Volume"])
    PrecomputedSignalStrategy.initial_cash = float(cash)
    bt = Backtest(
        data,
        PrecomputedSignalStrategy,
        cash=cash,
        commission=commission,
        trade_on_close=False,
        exclusive_orders=True,
        finalize_trades=True,
    )
    stats = bt.run(timeout_bars=timeout_bars)
    return stats, stats_to_summary(stats, data)
