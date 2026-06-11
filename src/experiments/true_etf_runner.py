"""Runner TRIAL-TRUE-ETF-001: download autorizzato + backtest + gate."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import sys

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.experiments.true_etf_backtest import (  # noqa: E402
    ETF_UNIVERSE,
    LARGECAP_UNIVERSE,
    TrueEtfConfig,
    evaluate_oos_gates,
    run_true_etf_backtest,
)

DATA_DIR = Path("data/snapshots/true_etf_001")


def download_universe() -> dict[str, pd.DataFrame]:
    import yfinance as yf

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    panels: dict[str, pd.DataFrame] = {}
    symbols = [*ETF_UNIVERSE, *LARGECAP_UNIVERSE]
    for symbol in symbols:
        path = DATA_DIR / f"{symbol}.csv"
        if path.exists():
            frame = pd.read_csv(path, parse_dates=["Date"]).set_index("Date")
        else:
            frame = yf.download(symbol, start="2018-01-01", auto_adjust=True, progress=False)
            if isinstance(frame.columns, pd.MultiIndex):
                frame.columns = frame.columns.get_level_values(0)
            frame = frame[["Open", "High", "Low", "Close", "Volume"]].dropna()
            frame.to_csv(path)
        if len(frame) > 500:
            panels[symbol] = frame
        print(f"  {symbol}: {len(frame)} bar, {frame.index.min().date()} -> {frame.index.max().date()}", flush=True)
    return panels


def main() -> int:
    print("FASE A: download universo autorizzato (yfinance, auto-adjusted)...", flush=True)
    panels = download_universe()
    spy = panels["SPY"]
    cfg = TrueEtfConfig()
    print("FASE B: backtest capital-aware (costi base e raddoppiati)...", flush=True)
    base = run_true_etf_backtest(panels, spy, cfg, apply_defense=True)
    double = run_true_etf_backtest(panels, spy, cfg, apply_defense=True, cost_multiplier=2.0)
    undefended = run_true_etf_backtest(panels, spy, cfg, apply_defense=False)
    gates = evaluate_oos_gates(base, double, spy, cfg)

    eq_u = undefended["equity"]
    oos_u = eq_u[eq_u.index >= pd.Timestamp(cfg.oos_start)]
    curve_u = oos_u["equity"] / oos_u["equity"].iloc[0]
    gates["undefended_reference"] = {
        "total_return": round(float(curve_u.iloc[-1] - 1.0), 6),
        "max_drawdown": round(float((curve_u / curve_u.cummax() - 1.0).min()), 6),
    }

    out_dir = Path("experiments/runs") / f"true_etf_001_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    out_dir.mkdir(parents=True, exist_ok=True)
    base["equity"].to_csv(out_dir / "equity_curve.csv")
    base["trades"].to_csv(out_dir / "trade_log.csv", index=False)
    (out_dir / "gates_result.json").write_text(json.dumps(gates, indent=2, default=str), encoding="utf-8")
    print("ARTIFACTS:", out_dir)
    print("VERDICT:", gates["verdict"])
    print(json.dumps({k: gates[k] for k in ("oos", "statistical_gate", "gates", "undefended_reference")}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
