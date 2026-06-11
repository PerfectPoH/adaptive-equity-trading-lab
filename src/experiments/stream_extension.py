"""RISK-044: estensione CAUSALE degli stream componenti per la replica mensile.

Architettura post-audit (round 3, 2026-06-11):

  ENTRY LEDGER persistente (`experiments/replica_ledger/ledger.json`):
    - alla prima rilevazione un'entry viene PERSISTITA (data, simbolo, prezzo);
    - i run successivi maturano SOLO le uscite dal ledger, mai rigenerano
      entry passate (immune al re-aggiustamento yfinance dell'intera storia);
    - se il ricalcolo odierno non conferma un'entry del ledger -> warning
      `data_revision_warnings` (rivelatore di revisioni della fonte dati).

  REGOLA DELISTING preregistrata (un simbolo che sparisce produce un'uscita
  REALIZZATA, mai un trade svanito):
    - panel TERMINALE (ultimo dato piu' vecchio di 7 giorni rispetto al resto
      del panel): i trade aperti oltre l'ultimo dato chiudono all'ULTIMO CLOSE;
    - simbolo SPARITO del tutto (nessun dato scaricabile): chiusura a -100%.

  Soglie causali rolling 252d con shift(1); il pre-freeze vive nel componente
  congelato e non viene mai toccato.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import pandas as pd

FREEZE_DATE = pd.Timestamp("2026-05-08")
PANEL_DIR = Path("data/snapshots/replica_panel")
LEDGER_PATH = Path("experiments/replica_ledger/ledger.json")
QUANTILE_WINDOW = 252
STALE_DAYS = 7
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


def _download_with_retry(symbol: str, *, attempts: int = 3, pause_seconds: float = 1.5) -> pd.DataFrame:
    """Download con retry: un hiccup di rete non deve sembrare un delisting."""

    import time

    import yfinance as yf

    for attempt in range(attempts):
        try:
            frame = yf.download(symbol, start="2024-01-01", auto_adjust=True, progress=False)
            if isinstance(frame.columns, pd.MultiIndex):
                frame.columns = frame.columns.get_level_values(0)
            if not frame.empty:
                return frame[["Open", "High", "Low", "Close", "Volume"]].dropna()
        except Exception:
            pass
        if attempt < attempts - 1:
            time.sleep(pause_seconds * (attempt + 1))
    return pd.DataFrame()


def refresh_panel(
    symbols: set[str], *, panel_dir: Path = PANEL_DIR, max_age_days: int = 1
) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    """Scarica/riusa i pannelli. Status in {"ok", "stale", "no_data"}.

    Emendamento 003: un download vuoto NON e' prova di delisting.
    - retry con backoff + pausa 0.4s tra simboli (anti rate-limit);
    - su download vuoto con cache esistente (di qualunque eta') si usa la
      cache con status "stale": i pendenti chiudono all'ultimo close;
    - "no_data" resta solo per simboli MAI scaricati con successo.
    """

    import time

    panel_dir.mkdir(parents=True, exist_ok=True)
    panels: dict[str, pd.DataFrame] = {}
    status: dict[str, str] = {}
    cache_fallback: set[str] = set()
    for symbol in sorted(symbols):
        if DELISTED_MARKER.search(symbol):
            status[symbol] = "no_data"
            continue
        path = panel_dir / f"{symbol}.csv"
        fresh = path.exists() and (time.time() - path.stat().st_mtime) < max_age_days * 86400
        if fresh:
            frame = pd.read_csv(path, parse_dates=["Date"]).set_index("Date")
        else:
            frame = _download_with_retry(symbol)
            time.sleep(0.4)
            if frame.empty:
                if path.exists():
                    frame = pd.read_csv(path, parse_dates=["Date"]).set_index("Date")
                    cache_fallback.add(symbol)
                else:
                    status[symbol] = "no_data"
                    continue
            else:
                frame.to_csv(path)
        if len(frame) >= QUANTILE_WINDOW // 2 + 25:
            panels[symbol] = frame
            status[symbol] = "ok"
        else:
            status[symbol] = "no_data"
    if panels:
        global_last = max(frame.index.max() for frame in panels.values())
        for symbol, frame in panels.items():
            if (global_last - frame.index.max()).days > STALE_DAYS:
                status[symbol] = "stale"
    for symbol in cache_fallback:
        if status.get(symbol) == "ok":
            status[symbol] = "stale"
    return panels, status


def detect_entries(panel: pd.DataFrame, recipe: Recipe, *, freeze: pd.Timestamp = FREEZE_DATE) -> list[dict[str, Any]]:
    """Entry candidate post-freeze (data, prezzo al close). Nessuna maturazione qui."""

    signal = CAUSAL_SIGNALS[recipe.template](panel)
    step = max(5, recipe.holding // 2)
    entries: list[dict[str, Any]] = []
    last_pos = -10**9
    closes = panel["Close"].astype(float)
    for pos, date in enumerate(panel.index):
        if date <= freeze or not bool(signal.iloc[pos]):
            continue
        if pos - last_pos < step:
            continue
        entries.append({"entry_date": str(pd.Timestamp(date).date()), "entry_price": float(closes.iloc[pos])})
        last_pos = pos
    return entries


# ---------------------------------------------------------------------------
# ledger
# ---------------------------------------------------------------------------

def load_ledger(path: Path = LEDGER_PATH) -> dict[str, list[dict[str, Any]]]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def save_ledger(ledger: dict[str, list[dict[str, Any]]], path: Path = LEDGER_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=1, sort_keys=True), encoding="utf-8")


def _mature_entry(
    entry: dict[str, Any],
    panel: pd.DataFrame | None,
    symbol_status: str,
    holding: int,
    cost: float,
) -> None:
    """Matura un'entry del ledger IN PLACE secondo la regola preregistrata.

    Emendamento 003: "no_data" mette in QUARANTENA (`suspect_vanished`);
    la chiusura a -100% scatta solo alla SECONDA conferma consecutiva.
    Nel ramo data_revision la maturazione usa la prima barra >= entry date
    (prezzo di entry sempre dal ledger), cosi' nessuna entry resta open
    per sempre quando il panel copre entry+holding.
    """

    entry_price = float(entry["entry_price"])
    if symbol_status == "no_data" or panel is None:
        if entry.get("suspect_vanished"):
            # seconda conferma consecutiva: perdita totale realizzata
            entry["status"] = "closed"
            entry["exit_reason"] = "symbol_vanished_total_loss"
            entry["net_return"] = round(-1.0 - cost, 6)
        else:
            entry["suspect_vanished"] = True  # quarantena: resta open
        return
    entry.pop("suspect_vanished", None)  # il simbolo e' tornato: fine quarantena
    dates = panel.index
    entry_ts = pd.Timestamp(entry["entry_date"])
    anchor = int(dates.searchsorted(entry_ts))
    if anchor >= len(dates):
        # entry oltre l'ultimo dato disponibile
        if symbol_status == "stale":
            last_close = float(panel["Close"].iloc[-1])
            entry["status"] = "closed"
            entry["exit_reason"] = "delisted_last_close"
            entry["net_return"] = round((last_close / entry_price - 1.0) - cost, 6)
        return
    if pd.Timestamp(dates[anchor]).date() != entry_ts.date():
        entry["data_revision"] = True  # la data esatta non esiste piu': revisione fonte
    exit_pos = anchor + holding
    if exit_pos < len(dates):
        exit_price = float(panel["Close"].iloc[exit_pos])
        entry["status"] = "closed"
        entry["exit_reason"] = "holding_timeout"
        entry["net_return"] = round((exit_price / entry_price - 1.0) - cost, 6)
    elif symbol_status == "stale":
        last_close = float(panel["Close"].iloc[-1])
        entry["status"] = "closed"
        entry["exit_reason"] = "delisted_last_close"
        entry["net_return"] = round((last_close / entry_price - 1.0) - cost, 6)
    # altrimenti resta open: maturera' in una replica futura


def extend_components(
    components: list[dict[str, Any]],
    panels: dict[str, pd.DataFrame],
    panel_status: dict[str, str],
    *,
    freeze: pd.Timestamp = FREEZE_DATE,
    ledger_path: Path = LEDGER_PATH,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Ledger-driven: nuove entry persistite alla prima rilevazione, uscite
    maturate dal ledger, passato mai rigenerato."""

    from src.experiments.workbench_portfolio_engine import _component_return_series

    ledger = load_ledger(ledger_path)
    extended: list[dict[str, Any]] = []
    coverage: dict[str, Any] = {
        "extendable": 0,
        "frozen": 0,
        "new_trades_closed": 0,
        "pending_open_trades": 0,
        "delisting_closures": 0,
        "suspect_vanished_quarantine": 0,
        "data_revision_warnings": 0,
        "reasons": {},
    }
    for component in components:
        recipe = component_recipe(component)
        if recipe is None:
            coverage["frozen"] += 1
            coverage["reasons"]["template_o_recipe_non_mappabile"] = (
                coverage["reasons"].get("template_o_recipe_non_mappabile", 0) + 1
            )
            extended.append(component)
            continue
        component_id = str(component.get("component_id"))
        rows = ledger.setdefault(component_id, [])
        known = {(r["symbol"], r["entry_date"]) for r in rows}
        cost = recipe.cost_bps / 10_000.0

        # 1) nuove entry: solo simboli con panel ok/stale, mai gia' nel ledger
        for symbol in recipe.symbols:
            panel = panels.get(symbol)
            if panel is None:
                continue
            for candidate in detect_entries(panel, recipe, freeze=freeze):
                key = (symbol, candidate["entry_date"])
                if key in known:
                    continue
                rows.append(
                    {
                        "symbol": symbol,
                        "entry_date": candidate["entry_date"],
                        "entry_price": candidate["entry_price"],
                        "holding": recipe.holding,
                        "status": "open",
                    }
                )
                known.add(key)

        # 1b) warning revisione dati: entry open del ledger non piu' confermate oggi
        todays = {
            (symbol, c["entry_date"])
            for symbol in recipe.symbols
            if symbol in panels
            for c in detect_entries(panels[symbol], recipe, freeze=freeze)
        }
        for row in rows:
            if row["status"] == "open" and (row["symbol"], row["entry_date"]) not in todays and not row.get("data_revision"):
                row["data_revision"] = True
                coverage["data_revision_warnings"] += 1

        # 2) maturazione dal ledger
        for row in rows:
            if row["status"] != "open":
                continue
            symbol = str(row["symbol"])
            _mature_entry(row, panels.get(symbol), panel_status.get(symbol, "no_data"), int(row["holding"]), cost)
            if row["status"] == "closed" and str(row.get("exit_reason", "")).startswith(("delisted", "symbol_vanished")):
                coverage["delisting_closures"] += 1
            if row["status"] == "open" and row.get("suspect_vanished"):
                coverage["suspect_vanished_quarantine"] += 1

        closed = [r for r in rows if r["status"] == "closed"]
        still_open = [r for r in rows if r["status"] == "open"]

        base_series = _component_return_series(component)
        base_rows = [{"period": str(p), "net_return": float(v)} for p, v in base_series.items()]
        clone = dict(component)
        clone["inline_returns"] = base_rows + sorted(
            ({"period": r["entry_date"], "net_return": float(r["net_return"])} for r in closed),
            key=lambda r: r["period"],
        )
        clone["trade_list_path"] = ""
        clone["equity_curve_path"] = ""
        clone["stream_extension"] = {
            "freeze_date": str(freeze.date()),
            "new_trades": len(closed),
            "pending_open_trades": len(still_open),
        }
        coverage["extendable"] += 1
        coverage["new_trades_closed"] += len(closed)
        coverage["pending_open_trades"] += len(still_open)
        extended.append(clone)

    save_ledger(ledger, ledger_path)
    return extended, coverage
