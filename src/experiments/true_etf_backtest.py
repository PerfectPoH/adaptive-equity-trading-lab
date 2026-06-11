"""TRIAL-TRUE-ETF-001: true backtest capital-aware su universo ammissibile.

Spec congelata + Emendamento 001 in vault/01-Feature/TRIAL-TRUE-ETF-001-Spec.md.
Regole CAUSALI (soglie rolling), entry al next open, cash accounting reale,
costi 100 bps round-trip, difesa del regime classifier all'entry.
Diagnostico: nessuna promozione automatica.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

from src.risk.index_regime_classifier import IndexRegimeConfig, classify_index_regime
from src.validation.deflated_sharpe import deflated_sharpe_ratio_from_returns

ETF_UNIVERSE = ["SPY", "QQQ", "IWM", "XLF", "XLK", "XLE", "XLV", "XLI", "XLP", "XLU", "XLY", "XLB"]
LARGECAP_UNIVERSE = ["AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "AMZN", "GOOGL"]


@dataclass(frozen=True)
class TrueEtfConfig:
    oos_start: str = "2024-01-01"
    quantile_window: int = 252
    momentum_quantile: float = 0.90
    meanrev_quantile: float = 0.10
    dollarbar_quantile: float = 0.90
    holdings: tuple[int, ...] = (90, 180)
    cost_bps_round_trip: float = 100.0
    position_fraction: float = 0.10
    max_positions: int = 10
    initial_equity: float = 100_000.0
    defense_high_vol: float = 0.25
    defense_trend_down: float = 0.50
    min_oos_trades: int = 100
    dsr_trial_count: float = 2.0
    dsr_sharpe_std: float = 0.30


@dataclass
class _Position:
    symbol: str
    rule: str
    entry_date: pd.Timestamp
    entry_price: float
    shares: float
    notional: float
    exit_due: pd.Timestamp
    exposure_scale: float


def causal_signals(prices: pd.DataFrame, cfg: TrueEtfConfig) -> pd.DataFrame:
    """Segnali causali per simbolo: True quando la regola scatta al close di t."""

    close = prices["Close"].astype(float)
    volume = prices["Volume"].astype(float)
    r21 = close.pct_change(21)
    r2 = close.pct_change(2)
    r1 = close.pct_change()
    dv_change = (close * volume).pct_change()
    q = cfg.quantile_window
    mom_threshold = r21.rolling(q, min_periods=q // 2).quantile(cfg.momentum_quantile).shift(1)
    rev_threshold = r2.rolling(q, min_periods=q // 2).quantile(cfg.meanrev_quantile).shift(1)
    db_threshold = dv_change.rolling(q, min_periods=q // 2).quantile(cfg.dollarbar_quantile).shift(1)
    return pd.DataFrame(
        {
            "momentum": (r21 >= mom_threshold) & mom_threshold.notna(),
            "meanrev": (r2 <= rev_threshold) & rev_threshold.notna(),
            "dollarbar": (dv_change >= db_threshold) & db_threshold.notna() & (r1 < 0),
        },
        index=prices.index,
    )


def defense_exposure(regimes: pd.Series, cfg: TrueEtfConfig) -> pd.Series:
    mapping = {"HIGH_VOL": cfg.defense_high_vol, "TREND_DOWN": cfg.defense_trend_down}
    return regimes.map(lambda r: mapping.get(str(r), 1.0)).astype(float)


def run_true_etf_backtest(
    panels: dict[str, pd.DataFrame],
    spy_for_regime: pd.DataFrame,
    cfg: TrueEtfConfig | None = None,
    *,
    apply_defense: bool = True,
    cost_multiplier: float = 1.0,
) -> dict[str, Any]:
    """Simulazione capital-aware: un'unica linea di equity, cash reale."""

    config = cfg or TrueEtfConfig()
    classified = classify_index_regime(spy_for_regime, close_column="Close", config=IndexRegimeConfig())
    exposure_by_date = defense_exposure(classified["regime"], config) if apply_defense else pd.Series(1.0, index=classified.index)

    signals = {s: causal_signals(p, config) for s, p in panels.items()}
    all_dates = sorted(set().union(*[set(p.index) for p in panels.values()]))
    cost_rate = (config.cost_bps_round_trip / 10_000.0) * cost_multiplier

    cash = config.initial_equity
    positions: list[_Position] = []
    trades: list[dict[str, Any]] = []
    equity_rows: list[dict[str, Any]] = []
    pending_entries: list[dict[str, Any]] = []

    for date in all_dates:
        date = pd.Timestamp(date)
        # 1. uscite dovute (al prezzo di apertura di oggi)
        still_open: list[_Position] = []
        for pos in positions:
            panel = panels[pos.symbol]
            if date >= pos.exit_due and date in panel.index:
                exit_price = float(panel.loc[date, "Open"])
                proceeds = pos.shares * exit_price
                cost = pos.notional * (cost_rate / 2.0) + proceeds * (cost_rate / 2.0)
                cash += proceeds - proceeds * (cost_rate / 2.0)
                trades.append(
                    {
                        "symbol": pos.symbol,
                        "rule": pos.rule,
                        "entry_date": str(pos.entry_date.date()),
                        "exit_date": str(date.date()),
                        "net_return": (exit_price / pos.entry_price - 1.0) - cost_rate,
                        "pnl": proceeds - pos.notional - cost,
                        "exposure_scale": pos.exposure_scale,
                    }
                )
            else:
                still_open.append(pos)
        positions = still_open
        # 2. entry pianificate ieri, eseguite all'open di oggi
        for plan in pending_entries:
            symbol = plan["symbol"]
            panel = panels[symbol]
            if date not in panel.index or len(positions) >= config.max_positions:
                continue
            equity_mark = cash + sum(p.shares * float(panels[p.symbol].loc[date, "Open"]) for p in positions if date in panels[p.symbol].index)
            scale = float(plan["exposure_scale"])
            notional = equity_mark * config.position_fraction * scale
            entry_price = float(panel.loc[date, "Open"])
            entry_cost = notional * (cost_rate / 2.0)
            if notional <= 0 or cash < notional + entry_cost:
                continue
            cash -= notional + entry_cost
            holding = int(plan["holding"])
            future = panel.index[panel.index > date]
            exit_due = future[min(holding, len(future) - 1)] if len(future) else date
            positions.append(
                _Position(symbol, plan["rule"], date, entry_price, notional / entry_price, notional, pd.Timestamp(exit_due), scale)
            )
        pending_entries = []
        # 3. segnali al close di oggi -> entry domani
        if date in exposure_by_date.index:
            scale_today = float(exposure_by_date.loc[date]) if pd.notna(exposure_by_date.loc[date]) else 1.0
        else:
            scale_today = 1.0
        held = {p.symbol for p in positions}
        for symbol, sig in signals.items():
            if symbol in held or date not in sig.index:
                continue
            row = sig.loc[date]
            for rule, holding in (("momentum", config.holdings[1]), ("meanrev", config.holdings[1]), ("dollarbar", config.holdings[1])):
                if bool(row[rule]):
                    pending_entries.append({"symbol": symbol, "rule": f"{rule}_{holding}d", "holding": holding, "exposure_scale": scale_today})
                    break
        # 4. mark-to-market al close
        marked = cash
        for pos in positions:
            panel = panels[pos.symbol]
            price = float(panel.loc[date, "Close"]) if date in panel.index else pos.entry_price
            marked += pos.shares * price
        equity_rows.append({"date": str(date.date()), "equity": marked, "open_positions": len(positions), "cash": cash})

    equity = pd.DataFrame(equity_rows).set_index("date")
    equity.index = pd.to_datetime(equity.index)
    return {"equity": equity, "trades": pd.DataFrame(trades), "config": config}


def evaluate_oos_gates(
    result: dict[str, Any],
    result_double_costs: dict[str, Any],
    spy_panel: pd.DataFrame,
    cfg: TrueEtfConfig,
) -> dict[str, Any]:
    equity = result["equity"]
    oos = equity[equity.index >= pd.Timestamp(cfg.oos_start)]
    base = float(oos["equity"].iloc[0])
    curve = oos["equity"] / base
    returns = curve.pct_change().fillna(0.0)
    drawdown = curve / curve.cummax() - 1.0
    total = float(curve.iloc[-1] - 1.0)
    max_dd = float(drawdown.min())

    spy = spy_panel[spy_panel.index >= pd.Timestamp(cfg.oos_start)]["Close"].astype(float)
    spy_curve = spy / spy.iloc[0]
    spy_total = float(spy_curve.iloc[-1] - 1.0)
    spy_dd = float((spy_curve / spy_curve.cummax() - 1.0).min())

    trades = result["trades"]
    trades["exit_ts"] = pd.to_datetime(trades["exit_date"])
    oos_trades = trades[trades["exit_ts"] >= pd.Timestamp(cfg.oos_start)]
    top3 = oos_trades.nlargest(3, "pnl")
    pnl_ex_top3 = float(oos_trades["pnl"].sum() - top3["pnl"].sum())
    sign_flip = (float(oos_trades["pnl"].sum()) > 0) != (pnl_ex_top3 > 0) if len(oos_trades) else True

    dsr = deflated_sharpe_ratio_from_returns(
        returns.to_numpy(), trial_count=cfg.dsr_trial_count, sharpe_std=cfg.dsr_sharpe_std, confidence_threshold=0.95
    )

    eq2 = result_double_costs["equity"]
    oos2 = eq2[eq2.index >= pd.Timestamp(cfg.oos_start)]
    total_double = float(oos2["equity"].iloc[-1] / oos2["equity"].iloc[0] - 1.0)

    ratio = total / abs(max_dd) if max_dd < 0 else float("inf")
    spy_ratio = spy_total / abs(spy_dd) if spy_dd < 0 else float("inf")
    gates = {
        "G1_positive_and_beats_spy_risk_adjusted": total > 0 and ratio > spy_ratio,
        "G2_no_sign_flip_ex_top3": not sign_flip,
        "G3_dsr_pass": bool(dsr.passed),
        "G4_min_trades": len(oos_trades) >= cfg.min_oos_trades,
        "G5_survives_double_costs": total_double > 0,
    }
    return {
        "trial_id": "TRIAL-TRUE-ETF-001",
        "oos": {
            "total_return": round(total, 6),
            "max_drawdown": round(max_dd, 6),
            "return_over_dd": round(ratio, 4),
            "spy_total_return": round(spy_total, 6),
            "spy_max_drawdown": round(spy_dd, 6),
            "spy_return_over_dd": round(spy_ratio, 4),
            "trade_count": int(len(oos_trades)),
            "pnl_ex_top3": round(pnl_ex_top3, 2),
            "total_return_double_costs": round(total_double, 6),
        },
        "statistical_gate": {
            "observed_sharpe_daily": round(dsr.observed_sharpe, 6),
            "dsr": round(dsr.dsr, 6),
            "dsr_passed": bool(dsr.passed),
        },
        "gates": gates,
        "verdict": "TRUE_ETF_" + ("PASS_ALL_GATES" if all(gates.values()) else "FAIL__" + "_".join(k.split("_")[0] for k, v in gates.items() if not v)),
        "promotion_allowed": False,
    }
