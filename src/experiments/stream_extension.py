"""RISK-044: estensione CAUSALE degli stream componenti per la replica mensile.

Gli stream del pool sono congelati al 2026-05-08. Questo modulo li estende
con dati freschi (yfinance, autorizzato dall'owner) generando i NUOVI trade
solo dopo il freeze, con soglie rolling causali - il passato non viene MAI
ricalcolato. I componenti non estendibili (template non mappato, simboli
delisted, dati mancanti) restano congelati e vengono dichiarati nel coverage.

Regole causali per template (analoghe a true_etf_backtest, quantile rolling
252d con shift(1)):
  Momentum                  : r21 >= q90
  Mean Reversion            : r2  <= q10
  Dollar-Bar Microstructure : pct-change dollar volume >= q90 in giorno negativo
  LowVol Tradability        : vol 5d <= q10

Contabilita' identica alla factory: entry al Close del giorno segnale, exit
al Close dopo `holding` barre, net = gross - cost_bps/10000, spaziatura
minima tra entry per simbolo = max(5, holding // 2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pandas as pd

FREEZE_DATE = pd.Timestamp("2026-05-08")
PANEL_DIR = Path("data/snapshots/replica_panel")
QUANTILE_WINDOW = 252
DELISTED_MARKER = re.compile(r"-\d{6}$")
NAME_RECIPE = re.compile(r"Factory (?P<template>.+?) (?P<holding>\d+)d (?P<cost>\d+)bps")


@dataclass(frozen=True)
class Recipe:
    template: str
    holding: int
    cost_bps: int
    symbols: tuple[str, ...]


def _r21_signal(panel: pd.DataFrame) -> pd.Series:
    r21 = panel["Close"].pct_change(21)
    threshold = r21.rolling(QUANTILE_WINDOW, min_periods=QUANTILE_WINDOW // 2).quantile(0.90).shift(1)
    return (r21 >= threshold) & threshold.notna()


def _r2_signal(panel: pd.DataFrame) -> pd.Series:
    r2 = panel["Close"].pct_change(2)
    threshold = r2.rolling(QUANTILE_WINDOW, min_periods=QUANTILE_WINDOW // 2).quantile(0.10).shift(1)
    return (r2 <= threshold) & threshold.notna()


def _dollarbar_signal(panel: pd.DataFrame) -> pd.Series:
    dv = (panel["Close"] * panel["Volume"]).pct_change()
    threshold = dv.rolling(QUANTILE_WINDOW, min_periods=QUANTILE_WINDOW // 2).quantile(0.90).shift(1)
    return (dv >= threshold) & threshold.notna() & (panel["Close"].pct_change() < 0)


def _lowvol_signal(panel: pd.DataFrame) -> pd.Series:
    vol = panel["Close"].pct_change().rolling(5).std()
    threshold = vol.rolling(QUANTILE_WINDOW, min_periods=QUANTILE_WINDOW // 2).quantile(0.10).shift(1)
    return (vol <= threshold) & threshold.notna()


CAUSAL_SIGNALS: dict[str, Callable[[pd.DataFrame], pd.Series]] = {
    "Momentum": _r21_signal,
    "Mean Reversion": _r2_signal,
    "GapRev RTH Reversion": _r2_signal,
    "Dollar-Bar Microstructure": _dollarbar_signal,
    "LowVol Tradability": _lowvol_signal,
}


def component_recipe(component: dict[str, Any]) -> Recipe | None:
    """Estrae (template, holding, costi, simboli) da nome/manifest/trade list."""

    name = str(component.get("strategy_name", ""))
    template = str(component.get("template", ""))
    manifest = component.get("factory_manifest") or {}
    match = NAME_RECIPE.search(name)
    holding = int(manifest.get("holding_period_days") or (match.group("holding") if match else 0) or 0)
    cost = int(manifest.get("cost_bps") or component.get("cost_bps") or (match.group("cost") if match else 0) or 0)
    if template not in CAUSAL_SIGNALS or holding <= 0:
        return None
    symbols: set[str] = set()
    trade_path = str(component.get("trade_list_path") or "")
    if trade_path and Path(trade_path).exists():
        trades = pd.read_csv(trade_path)
        if "symbol" in trades.columns:
            symbols = set(trades["symbol"].astype(str))
    if not symbols:
        preview = component.get("factory_preview") or {}
        rows = preview.get("trade_rows", []) or []
        symbols = {str(r.get("symbol")) for r in rows if isinstance(r, dict) and r.get("symbol")}
    if not symbols:
        return None
    return Recipe(template, holding, cost, tuple(sorted(symbols)))


def refresh_panel(symbols: set[str], *, panel_dir: Path = PANEL_DIR, max_age_days: int = 1) -> dict[str, pd.DataFrame]:
    """Scarica/riusa i pannelli OHLCV (yfinance auto-adjusted, simboli vivi)."""

    import time

    import yfinance as yf

    panel_dir.mkdir(parents=True, exist_ok=True)
    panels: dict[str, pd.DataFrame] = {}
    for symbol in sorted(symbols):
        if DELISTED_MARKER.search(symbol):
            continue
        path = panel_dir / f"{symbol}.csv"
        fresh = path.exists() and (time.time() - path.stat().st_mtime) < max_age_days * 86400
        if fresh:
            frame = pd.read_csv(path, parse_dates=["Date"]).set_index("Date")
        else:
            frame = yf.download(symbol, start="2024-01-01", auto_adjust=True, progress=False)
            if isinstance(frame.columns, pd.MultiIndex):
                frame.columns = frame.columns.get_level_values(0)
            if frame.empty:
                continue
            frame = frame[["Open", "High", "Low", "Close", "Volume"]].dropna()
            frame.to_csv(path)
        if len(frame) >= QUANTILE_WINDOW // 2 + 25:
            panels[symbol] = frame
    return panels


def causal_trades_after_freeze(
    panel: pd.DataFrame,
    recipe: Recipe,
    *,
    freeze: pd.Timestamp = FREEZE_DATE,
) -> list[dict[str, Any]]:
    """Nuovi trade SOLO dopo il freeze, soglie causali, contabilita' factory."""

    signal = CAUSAL_SIGNALS[recipe.template](panel)
    cost = recipe.cost_bps / 10_000.0
    step = max(5, recipe.holding // 2)
    closes = panel["Close"].astype(float)
    dates = panel.index
    trades: list[dict[str, Any]] = []
    pending = 0
    last_entry_pos = -10**9
    for pos, date in enumerate(dates):
        if date <= freeze or not bool(signal.iloc[pos]):
            continue
        if pos - last_entry_pos < step:
            continue
        exit_pos = pos + recipe.holding
        if exit_pos >= len(dates):
            pending += 1
            last_entry_pos = pos  # l'entry e' avvenuta: blocca la spaziatura
            continue  # chiusura nelle repliche future, mai restating
        entry = float(closes.iloc[pos])
        exit_price = float(closes.iloc[exit_pos])
        if entry <= 0:
            continue
        trades.append(
            {
                "period": str(pd.Timestamp(date).date()),
                "net_return": round((exit_price / entry - 1.0) - cost, 6),
            }
        )
        last_entry_pos = pos
    return trades, pending


def extend_components(
    components: list[dict[str, Any]],
    panels: dict[str, pd.DataFrame],
    *,
    freeze: pd.Timestamp = FREEZE_DATE,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Clona i componenti aggiungendo i trade post-freeze. Mai toccato il passato."""

    from src.experiments.workbench_portfolio_engine import _component_return_series

    extended: list[dict[str, Any]] = []
    coverage = {"extendable": 0, "frozen": 0, "new_trades": 0, "pending_open_trades": 0, "reasons": {}}
    for component in components:
        recipe = component_recipe(component)
        if recipe is None:
            reason = "template_o_recipe_non_mappabile"
        else:
            alive = [s for s in recipe.symbols if s in panels]
            dead = [s for s in recipe.symbols if DELISTED_MARKER.search(s)]
            missing = [s for s in recipe.symbols if s not in panels and not DELISTED_MARKER.search(s)]
            reason = "" if alive else "nessun_simbolo_con_dati"
        if recipe is None or reason:
            coverage["frozen"] += 1
            coverage["reasons"][reason] = coverage["reasons"].get(reason, 0) + 1
            extended.append(component)
            continue
        new_trades: list[dict[str, Any]] = []
        pending_total = 0
        for symbol in alive:
            closed, pending = causal_trades_after_freeze(panels[symbol], recipe, freeze=freeze)
            new_trades.extend(closed)
            pending_total += pending
        base_series = _component_return_series(component)
        base_rows = [
            {"period": str(period), "net_return": float(value)} for period, value in base_series.items()
        ]
        clone = dict(component)
        clone["inline_returns"] = base_rows + sorted(new_trades, key=lambda r: r["period"])
        clone["trade_list_path"] = ""
        clone["equity_curve_path"] = ""
        clone["stream_extension"] = {
            "freeze_date": str(freeze.date()),
            "new_trades": len(new_trades),
            "pending_open_trades": pending_total,
            "alive_symbols": len(alive),
            "dead_symbols": len(dead),
            "missing_symbols": len(missing),
        }
        coverage["extendable"] += 1
        coverage["new_trades"] += len(new_trades)
        coverage["pending_open_trades"] += pending_total
        extended.append(clone)
    return extended, coverage
