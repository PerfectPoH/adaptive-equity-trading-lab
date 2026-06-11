from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.experiments.stream_extension import (
    Recipe,
    detect_entries,
    extend_components,
    load_ledger,
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


def _component(panel: pd.DataFrame, n_base: int = 100) -> dict:
    rows = [{"period": str(d.date()), "net_return": 0.001} for d in panel.index[:n_base]]
    return {
        "component_id": "C1", "strategy_name": "Factory Momentum 20d 100bps",
        "template": "Momentum", "cost_bps": 100, "inline_returns": rows,
        "trade_list_path": "", "equity_curve_path": "",
        "factory_manifest": {"holding_period_days": 20, "cost_bps": 100},
        "factory_preview": {"trade_rows": [{"symbol": "X"}]},
    }


def test_detect_entries_only_after_freeze_and_causal() -> None:
    panel = _panel()
    freeze = panel.index[400]
    entries = detect_entries(panel, Recipe("Momentum", 20, 100, ("X",)), freeze=freeze)
    assert entries and all(pd.Timestamp(e["entry_date"]) > freeze for e in entries)
    mutated = panel.copy()
    mutated.iloc[-30:, mutated.columns.get_loc("Close")] *= 2.0
    early = [e for e in entries if pd.Timestamp(e["entry_date"]) < panel.index[-60]]
    early_mutated = [e for e in detect_entries(mutated, Recipe("Momentum", 20, 100, ("X",)), freeze=freeze)
                     if pd.Timestamp(e["entry_date"]) < panel.index[-60]]
    assert early == early_mutated


def _freeze_and_cut(panel: pd.DataFrame) -> tuple[pd.Timestamp, int]:
    """Sceglie freeze e taglio cosi' che ESISTA un'entry post-freeze non maturabile."""
    freeze = panel.index[400]
    entries = detect_entries(panel, Recipe("Momentum", 20, 100, ("X",)), freeze=freeze)
    assert entries, "il sintetico deve produrre entry post-freeze"
    first_pos = int(panel.index.searchsorted(pd.Timestamp(entries[0]["entry_date"])))
    return freeze, first_pos + 5  # entry rilevabile ma holding-20 non maturabile


def test_ledger_persists_entries_and_matures_later(tmp_path: Path) -> None:
    panel = _panel()
    freeze, cut = _freeze_and_cut(panel)
    ledger_path = tmp_path / "ledger.json"
    comp = _component(panel)
    short = panel.iloc[:cut]  # primo run: l'entry non puo' maturare (holding 20)
    ext1, cov1 = extend_components([comp], {"X": short}, {"X": "ok"}, freeze=freeze, ledger_path=ledger_path)
    led = load_ledger(ledger_path)
    assert led["C1"], "entry persistite al primo run"
    open_before = sum(1 for r in led["C1"] if r["status"] == "open")
    assert open_before >= 1
    # secondo run con piu' dati: le pendenti maturano, nessuna entry duplicata
    ext2, cov2 = extend_components([comp], {"X": panel}, {"X": "ok"}, freeze=freeze, ledger_path=ledger_path)
    led2 = load_ledger(ledger_path)
    assert len(led2["C1"]) >= len(led["C1"])
    keys = [(r["symbol"], r["entry_date"]) for r in led2["C1"]]
    assert len(keys) == len(set(keys)), "nessun duplicato nel ledger"
    closed_after = sum(1 for r in led2["C1"] if r["status"] == "closed")
    assert closed_after >= open_before or open_before == 0


def test_stale_symbol_closes_at_last_close_and_vanished_at_total_loss(tmp_path: Path) -> None:
    panel = _panel()
    freeze, cut = _freeze_and_cut(panel)
    ledger_path = tmp_path / "ledger.json"
    comp = _component(panel)
    # primo run: crea entry open
    extend_components([comp], {"X": panel.iloc[:cut]}, {"X": "ok"}, freeze=freeze, ledger_path=ledger_path)
    led = load_ledger(ledger_path)
    assert any(r["status"] == "open" for r in led["C1"])
    # secondo run: simbolo STALE -> le open chiudono all'ultimo close (realizzate)
    ext, cov = extend_components([comp], {"X": panel.iloc[:cut]}, {"X": "stale"}, freeze=freeze, ledger_path=ledger_path)
    led2 = load_ledger(ledger_path)
    assert all(r["status"] == "closed" for r in led2["C1"])
    assert any(r.get("exit_reason") == "delisted_last_close" for r in led2["C1"])
    assert cov["delisting_closures"] >= 1
    # terzo scenario: simbolo SPARITO -> -100%
    ledger_path2 = tmp_path / "ledger2.json"
    extend_components([comp], {"X": panel.iloc[:cut]}, {"X": "ok"}, freeze=freeze, ledger_path=ledger_path2)
    ext3, cov3 = extend_components([comp], {}, {"X": "no_data"}, freeze=freeze, ledger_path=ledger_path2)
    led3 = load_ledger(ledger_path2)
    vanished = [r for r in led3["C1"] if r.get("exit_reason") == "symbol_vanished_total_loss"]
    assert vanished and all(r["net_return"] <= -1.0 for r in vanished)
