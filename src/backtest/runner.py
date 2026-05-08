from __future__ import annotations

import pandas as pd
from backtesting import Backtest, Strategy

from src.backtest.metrics import stats_to_summary


class PrecomputedSignalStrategy(Strategy):
    def init(self) -> None:
        pass

    def next(self) -> None:
        if self.position:
            return

        signal = bool(self.data.signal[-1])
        execution_valid = bool(self.data.execution_valid[-1])
        if not signal or not execution_valid:
            return

        size = int(self.data.position_size[-1])
        if size <= 0:
            return

        stop_loss = float(self.data.stop_loss[-1])
        take_profit = float(self.data.take_profit[-1])
        if not stop_loss < float(self.data.entry_price[-1]) < take_profit:
            return

        self.buy(size=size, sl=stop_loss, tp=take_profit)


def run_backtest(
    frame: pd.DataFrame,
    cash: float = 100_000,
    commission: float = 0.001,
) -> tuple[pd.Series, dict[str, float | bool]]:
    required = ["Open", "High", "Low", "Close", "Volume", "signal", "execution_valid", "position_size"]
    missing = [col for col in required if col not in frame.columns]
    if missing:
        raise ValueError(f"Backtest frame missing columns: {missing}")

    data = frame.copy().dropna(subset=["Open", "High", "Low", "Close", "Volume"])
    bt = Backtest(
        data,
        PrecomputedSignalStrategy,
        cash=cash,
        commission=commission,
        trade_on_close=False,
        exclusive_orders=True,
    )
    stats = bt.run()
    return stats, stats_to_summary(stats, data)
