from __future__ import annotations

import csv
import json
from pathlib import Path

import src.experiments.active_only_momentum_smoke_robustness_001 as robust


def test_assess_trade_panel_robustness_removes_top_three_net_returns(tmp_path: Path) -> None:
    panel = tmp_path / "trades.csv"
    with panel.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["symbol", "net_return_500bps"])
        writer.writeheader()
        for value in [1.0, 0.9, 0.8, -0.1, -0.2]:
            writer.writerow({"symbol": "AAA", "net_return_500bps": value})

    assessment = robust.assess_active_only_momentum_smoke_robustness(panel)

    assert assessment["trade_count"] == 5
    assert assessment["net_return_sum_500bps"] == 2.4
    assert assessment["net_return_ex_top3_500bps"] == -0.3
    assert assessment["sign_flip_ex_top3"] is True


def test_run_robustness_writes_no_query_no_promotion_artifacts(tmp_path: Path) -> None:
    decision = robust.run_active_only_momentum_smoke_robustness_001(
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = robust.validate_active_only_momentum_smoke_robustness_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["provider_query_performed"] is False
    assert decision["backtest_performed"] is False
    assert decision["promotion_allowed"] is False
    assert decision["survivorship_free_claim_allowed"] is False
