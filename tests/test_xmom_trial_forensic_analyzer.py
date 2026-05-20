from __future__ import annotations

import pandas as pd

from src.experiments.xmom_trial_forensic_analyzer import analyze_xmom_trial_forensics


def test_xmom_forensics_detects_top_trade_sign_flip(tmp_path) -> None:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    pd.DataFrame(
        [
            _trade("AAA", 200.0, 0.5),
            _trade("BBB", -80.0, -0.2),
            _trade("CCC", -50.0, -0.1),
        ]
    ).to_csv(run_dir / "portfolio_trade_log.csv", index=False)

    report = analyze_xmom_trial_forensics(run_dir, top_n=1)

    assert report["total_pnl"] == 70.0
    assert report["rest_pnl"] == -130.0
    assert report["sign_flip_excluding_top_n"] is True
    assert report["winner_count"] == 1
    assert report["loser_count"] == 2


def _trade(symbol: str, pnl: float, return_pct: float) -> dict[str, object]:
    return {
        "symbol": symbol,
        "signal_date": "2025-01-01",
        "entry_date": "2025-01-02",
        "exit_date": "2025-02-01",
        "position_notional": 1000.0,
        "pnl": pnl,
        "return_pct": return_pct,
        "momentum_3m": 0.1,
        "momentum_6m": 0.2,
        "momentum_12m": 0.3,
        "rank_aggregate_score": 0.2,
        "avg_dollar_volume_20d": 1_000_000.0,
        "rolling_volatility_20d": 0.05,
        "participation_rate": 0.01,
        "impact_bps": 2.0,
    }
