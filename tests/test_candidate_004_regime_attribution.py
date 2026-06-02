from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.experiments.candidate_004_regime_attribution import (
    build_market_regime_map,
    map_trades_to_regimes,
    run_candidate_004_regime_attribution_diagnostic,
)


def _benchmark_frame(start: float, step: float, periods: int = 140) -> pd.DataFrame:
    index = pd.bdate_range("2025-01-01", periods=periods)
    close = pd.Series([start + step * i for i in range(periods)], index=index)
    return pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": 1_000_000,
        },
        index=index,
    )


def test_market_regime_map_labels_trend_up_low_vol() -> None:
    spy = _benchmark_frame(100.0, 0.2)
    iwm = _benchmark_frame(80.0, 0.15)

    regimes = build_market_regime_map(spy, iwm)

    assert not regimes.empty
    assert regimes.iloc[-1]["regime_label"] == "TREND_UP_LOW_VOL"


def test_market_regime_map_handles_named_norgate_date_index() -> None:
    spy = _benchmark_frame(100.0, 0.2)
    iwm = _benchmark_frame(80.0, 0.15)
    spy.index.name = "Date"
    iwm.index.name = "Date"

    regimes = build_market_regime_map(spy, iwm)

    assert "date" in regimes.columns
    assert regimes["date"].str.match(r"\d{4}-\d{2}-\d{2}").all()


def test_trade_mapping_uses_signal_date_regime() -> None:
    regimes = pd.DataFrame(
        [
            {"date": "2025-03-03", "regime_label": "RISK_OFF"},
            {"date": "2025-03-04", "regime_label": "TREND_UP_LOW_VOL"},
        ]
    )
    trades = pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "sleeve": "Momentum",
                "signal_date": "2025-03-03",
                "entry_date": "2025-03-04",
                "net_return": 0.10,
                "weighted_net_return": 0.025,
                "component_id": "component-a",
                "component_template": "Momentum",
            }
        ]
    )

    mapped = map_trades_to_regimes(trades, regimes)

    assert mapped.iloc[0]["regime_label"] == "RISK_OFF"


def test_run_candidate_004_regime_attribution_remains_diagnostic_only(tmp_path: Path) -> None:
    gate_dir = tmp_path / "gate"
    design_dir = tmp_path / "design"
    backtest_dir = tmp_path / "candidate003"
    output_dir = tmp_path / "out"
    gate_dir.mkdir()
    design_dir.mkdir()
    backtest_dir.mkdir()
    (gate_dir / "gate_manifest.json").write_text(
        json.dumps(
            {
                "status": "APPROVED_ATTRIBUTION_ONLY_NO_BACKTEST",
                "portfolio_backtest_allowed": False,
            }
        ),
        encoding="utf-8",
    )
    (design_dir / "regime_taxonomy.json").write_text(json.dumps({"taxonomy_id": "TAXONOMY"}), encoding="utf-8")
    pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "sleeve": "Momentum",
                "signal_date": "2025-04-10",
                "entry_date": "2025-04-11",
                "exit_date": "2025-05-01",
                "gross_return": 0.12,
                "net_return": 0.11,
                "weighted_net_return": 0.0275,
                "component_id": "component-a",
                "component_template": "Momentum",
            }
        ]
    ).to_csv(backtest_dir / "trade_log.csv", index=False)
    (backtest_dir / "norgate_candidate_003_second_backtest_result.json").write_text("{}", encoding="utf-8")

    result = run_candidate_004_regime_attribution_diagnostic(
        output_dir=output_dir,
        gate_dir=gate_dir,
        design_dir=design_dir,
        second_backtest_dir=backtest_dir,
        benchmark_frames={"SPY": _benchmark_frame(100.0, 0.2), "IWM": _benchmark_frame(80.0, 0.15)},
    )

    assert result["decision"] == "CANDIDATE_004_REGIME_ATTRIBUTION_COMPLETE_NO_BACKTEST"
    assert result["portfolio_backtest_performed"] is False
    assert result["provider_query_performed"] is False
    final = json.loads((output_dir / "final_decision.json").read_text(encoding="utf-8"))
    assert final["promotion_allowed"] is False
    assert (output_dir / "trade_regime_attribution.csv").is_file()
