from __future__ import annotations

import json
from pathlib import Path

from src.experiments.post_run_validation_gate_validator import main, validate_post_run_gate


def _valid_run_dir(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    manifest = {
        "run_id": "run_test",
        "config_hash": "abc123",
        "config": {
            "portfolio": {
                "execution": {
                    "max_position_dollar_volume_fraction": 0.01,
                    "impact_participation_cap": 0.20,
                    "impact_coefficient_bps": 50.0,
                }
            }
        },
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (run_dir / "portfolio_trade_log.csv").write_text(
        "\n".join(
            [
                "symbol,signal_date,entry_date,exit_date,entry_reference_price,entry_price,position_size,position_notional,max_liquidity_notional,estimated_cost_pct,impact_cost_pct,pnl,return_pct,cash_after_entry,cash_after_exit",
                "AAA,2024-01-01,2024-01-02,2024-01-03,10.0,10.101,100,1010.1,10000.0,0.0101,0.0001,25.0,0.02475,98989.9,100025.0",
                "BBB,2024-01-04,2024-01-05,2024-01-06,20.0,20.202,50,1010.1,10000.0,0.0101,0.0001,-15.0,-0.01485,99014.9,100010.0",
            ]
        ),
        encoding="utf-8",
    )
    (run_dir / "portfolio_summary.csv").write_text(
        "initial_cash,ending_cash,total_pnl,return_pct,total_trades,total_rejections\n100000.0,100010.0,10.0,0.0001,2,0\n",
        encoding="utf-8",
    )
    (run_dir / "portfolio_outlier_breakdown.csv").write_text(
        "outlier_concentration_alert,sign_flip_excluding_top_3,pnl_excluding_top_3\nFalse,False,10.0\n",
        encoding="utf-8",
    )
    (run_dir / "benchmark_report.csv").write_text("benchmark,return\ncash_flat,0.0\n", encoding="utf-8")
    return run_dir


def test_post_run_gate_passes_valid_run_dir(tmp_path: Path) -> None:
    run_dir = _valid_run_dir(tmp_path)

    report = validate_post_run_gate(run_dir)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "POST_RUN_VALIDATION_PASS"
    assert report["summary"]["failed"] == 0


def test_post_run_gate_fails_missing_trade_log_column(tmp_path: Path) -> None:
    run_dir = _valid_run_dir(tmp_path)
    text = (run_dir / "portfolio_trade_log.csv").read_text(encoding="utf-8")
    (run_dir / "portfolio_trade_log.csv").write_text(text.replace(",impact_cost_pct", ""), encoding="utf-8")

    report = validate_post_run_gate(run_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "trade_log_required_columns" and check["status"] == "fail" for check in report["checks"])


def test_post_run_gate_fails_position_above_liquidity_cap(tmp_path: Path) -> None:
    run_dir = _valid_run_dir(tmp_path)
    text = (run_dir / "portfolio_trade_log.csv").read_text(encoding="utf-8")
    (run_dir / "portfolio_trade_log.csv").write_text(text.replace("1010.1,10000.0", "12000.0,10000.0", 1), encoding="utf-8")

    report = validate_post_run_gate(run_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "position_notional_within_liquidity_cap" and check["status"] == "fail" for check in report["checks"])


def test_post_run_gate_fails_if_summary_pnl_does_not_match_trade_log(tmp_path: Path) -> None:
    run_dir = _valid_run_dir(tmp_path)
    (run_dir / "portfolio_summary.csv").write_text(
        "initial_cash,ending_cash,total_pnl,return_pct,total_trades,total_rejections\n100000.0,100999.0,999.0,0.00999,2,0\n",
        encoding="utf-8",
    )

    report = validate_post_run_gate(run_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "summary_pnl_matches_trade_log" and check["status"] == "fail" for check in report["checks"])


def test_post_run_gate_cli_exit_codes(tmp_path: Path) -> None:
    run_dir = _valid_run_dir(tmp_path)

    assert main(["--run-dir", str(run_dir)]) == 0

    (run_dir / "portfolio_outlier_breakdown.csv").unlink()

    assert main(["--run-dir", str(run_dir)]) == 1
