import json
from pathlib import Path

import pandas as pd

from src.experiments.candidate_008_autopsy import (
    attach_security_master,
    summarize_failure_attribution,
    run_candidate_008_autopsy,
)


def _trades() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "sleeve": "momentum_60d",
                "signal_date": "2025-01-10",
                "entry_date": "2025-01-13",
                "exit_date": "2025-01-31",
                "gross_return": 0.10,
                "cost_return": 0.05,
                "net_return": 0.05,
                "weighted_net_return": 0.005,
                "split": "oos",
            },
            {
                "symbol": "DDD",
                "sleeve": "mean_reversion_5d",
                "signal_date": "2025-01-10",
                "entry_date": "2025-01-13",
                "exit_date": "2025-01-24",
                "gross_return": -0.02,
                "cost_return": 0.05,
                "net_return": -0.07,
                "weighted_net_return": -0.007,
                "split": "oos",
            },
            {
                "symbol": "BBB",
                "sleeve": "mean_reversion_5d",
                "signal_date": "2025-01-20",
                "entry_date": "2025-01-21",
                "exit_date": "2025-02-03",
                "gross_return": 0.02,
                "cost_return": 0.05,
                "net_return": -0.03,
                "weighted_net_return": -0.003,
                "split": "is",
            },
        ]
    )


def _master() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "AAA", "universe_status": "active", "is_delisted": False},
            {"symbol": "BBB", "universe_status": "active", "is_delisted": False},
            {"symbol": "DDD", "universe_status": "delisted", "is_delisted": True},
        ]
    )


def test_attach_security_master_adds_universe_status() -> None:
    mapped = attach_security_master(_trades(), _master())

    assert mapped.loc[mapped["symbol"].eq("DDD"), "universe_status"].iloc[0] == "delisted"
    assert bool(mapped.loc[mapped["symbol"].eq("AAA"), "is_delisted"].iloc[0]) is False


def test_summarize_failure_attribution_identifies_cost_and_delisted_drag() -> None:
    mapped = attach_security_master(_trades(), _master())
    mapped["regime_label"] = ["TREND_UP_LOW_VOL", "DRAWDOWN_STRESS", "TREND_UP_LOW_VOL"]

    summary = summarize_failure_attribution(mapped)

    by_sleeve = {row["sleeve"]: row for row in summary["by_sleeve"]}
    by_universe = {row["universe_status"]: row for row in summary["by_universe"]}
    assert by_sleeve["mean_reversion_5d"]["weighted_net_return_sum"] < 0
    assert by_universe["delisted"]["weighted_net_return_sum"] < 0
    assert summary["cost_drag"]["weighted_cost_sum"] > 0
    assert summary["recommendations"]


def test_run_candidate_008_autopsy_writes_read_only_artifacts(tmp_path: Path) -> None:
    gate_dir = tmp_path / "gate"
    output_dir = tmp_path / "out"
    dataset_dir = tmp_path / "dataset"
    backtest_dir = tmp_path / "backtest"
    gate_dir.mkdir()
    dataset_dir.mkdir()
    backtest_dir.mkdir()
    _trades().to_csv(backtest_dir / "trade_log.csv", index=False)
    _master().to_csv(dataset_dir / "security_master.csv", index=False)
    prices = pd.DataFrame(
        {
            "symbol": ["SPY"] * 80 + ["IWM"] * 80,
            "date": list(pd.bdate_range("2024-11-01", periods=80).date.astype(str)) * 2,
            "open": [100.0] * 160,
            "high": [101.0] * 160,
            "low": [99.0] * 160,
            "close": [100.0 + i * 0.1 for i in range(80)] + [90.0 + i * 0.05 for i in range(80)],
            "volume": [1_000_000] * 160,
            "provider_dataset": ["Norgate Data"] * 160,
        }
    )
    prices.to_csv(dataset_dir / "prices.csv", index=False)
    (backtest_dir / "candidate_008_norgate_oos_baseline_result.json").write_text("{}", encoding="utf-8")
    (gate_dir / "gate_manifest.json").write_text(
        json.dumps(
            {
                "status": "APPROVED_CANDIDATE_008_AUTOPSY_ATTRIBUTION_ONLY",
                "linked_trade_log": str(backtest_dir / "trade_log.csv"),
                "linked_dataset": str(dataset_dir),
                "linked_candidate_008_result": str(backtest_dir / "candidate_008_norgate_oos_baseline_result.json"),
                "provider_query_allowed": False,
                "market_data_download_allowed": False,
                "strategy_backtest_allowed": False,
                "kronos_inference_allowed": False,
                "portfolio_search_allowed": False,
                "parameter_sweep_allowed": False,
                "promotion_allowed": False,
            }
        ),
        encoding="utf-8",
    )

    result = run_candidate_008_autopsy(gate_dir=gate_dir, output_dir=output_dir)

    assert result["decision"] == "CANDIDATE_008_AUTOPSY_COMPLETE_NO_BACKTEST"
    assert result["provider_query_performed"] is False
    assert result["strategy_backtest_performed"] is False
    assert (output_dir / "summary_by_sleeve.csv").exists()
    assert (output_dir / "final_decision.json").exists()
