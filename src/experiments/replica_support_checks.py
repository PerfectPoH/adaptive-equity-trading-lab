"""Controlli di supporto alla replica (audit round 3).

1. SEAM CHECK (una tantum): le regole causali dell'estensione, applicate alla
   finestra di overlap (2026-01-02 -> 2026-05-08) sui panel yfinance, quante
   delle entry dello stream CONGELATO (panel Databento) ritrovano? Misura la
   cucitura tra fonti: overlap basso = parte del movimento mensile e' artefatto
   di fonte dati, da leggere nei report.
2. REGIME REFRESH: rigenera regime_history dal panel SPY fresco con il
   classifier deterministico causale (tiene viva la diagnostica timing).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.experiments.stream_extension import component_recipe, detect_entries, refresh_panel  # noqa: E402

OVERLAP_START = pd.Timestamp("2026-01-02")
OVERLAP_END = pd.Timestamp("2026-05-08")


def seam_check(components: list[dict], panels: dict[str, pd.DataFrame]) -> dict:
    from src.experiments.workbench_portfolio_engine import _component_return_series

    rows = []
    for component in components:
        recipe = component_recipe(component)
        if recipe is None:
            continue
        frozen = _component_return_series(component)
        frozen_dates = {
            str(pd.Timestamp(p).date())
            for p in frozen.index
            if OVERLAP_START <= pd.Timestamp(p) <= OVERLAP_END
        }
        causal_dates: set[str] = set()
        for symbol in recipe.symbols:
            panel = panels.get(symbol)
            if panel is None:
                continue
            window = panel[panel.index <= OVERLAP_END]
            for e in detect_entries(window, recipe, freeze=OVERLAP_START):
                causal_dates.add(e["entry_date"])
        if not frozen_dates and not causal_dates:
            continue
        inter = frozen_dates & causal_dates
        rows.append(
            {
                "component_id": str(component.get("component_id"))[:24],
                "strategy": str(component.get("strategy_name"))[:40],
                "frozen_entries": len(frozen_dates),
                "causal_entries": len(causal_dates),
                "overlap": len(inter),
                "overlap_pct_of_frozen": round(len(inter) / len(frozen_dates), 3) if frozen_dates else None,
            }
        )
    total_frozen = sum(r["frozen_entries"] for r in rows)
    total_overlap = sum(r["overlap"] for r in rows)
    return {
        "window": f"{OVERLAP_START.date()} -> {OVERLAP_END.date()}",
        "components_checked": len(rows),
        "total_frozen_entries": total_frozen,
        "total_overlap": total_overlap,
        "overlap_ratio": round(total_overlap / total_frozen, 3) if total_frozen else None,
        "per_component": rows,
        "interpretation": (
            "Overlap alto = la cucitura Databento->yfinance e' coerente; basso = "
            "il movimento mensile va letto anche come artefatto di fonte/regole."
        ),
    }


def refresh_regime_history(panels: dict[str, pd.DataFrame]) -> str:
    from src.risk.index_regime_classifier import IndexRegimeConfig, classify_index_regime

    spy = panels.get("SPY")
    if spy is None or len(spy) < 300:
        return "SPY_PANEL_INSUFFICIENT"
    classified = classify_index_regime(spy, close_column="Close", config=IndexRegimeConfig())
    out = Path("experiments/runs") / f"regime_index_refresh_{datetime.now().strftime('%Y%m%d')}"
    out.mkdir(parents=True, exist_ok=True)
    classified.reset_index().rename(columns={"index": "date", "Date": "date"}).to_csv(out / "regime_history.csv", index=False)
    return str(out / "regime_history.csv")


def main() -> int:
    from dashboard.lab_dashboard_data import build_strategy_factory_components, load_portfolio_lab_components

    components = load_portfolio_lab_components(limit=60) + build_strategy_factory_components(max_variants=48)
    symbols: set[str] = set()
    for component in components:
        recipe = component_recipe(component)
        if recipe:
            symbols.update(recipe.symbols)
    symbols.add("SPY")
    panels, _status = refresh_panel(symbols)
    result = seam_check(components, panels)
    out_dir = Path("experiments/runs") / f"seam_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "seam_check.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    regime_path = refresh_regime_history(panels)
    print("SEAM CHECK:", json.dumps({k: result[k] for k in ("window", "components_checked", "total_frozen_entries", "total_overlap", "overlap_ratio")}, indent=1))
    print("REGIME HISTORY REFRESH:", regime_path)
    print("ARTIFACTS:", out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
