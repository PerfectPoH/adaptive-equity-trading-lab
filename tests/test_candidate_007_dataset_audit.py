import json
from pathlib import Path

import pandas as pd

from src.experiments.candidate_007_dataset_audit import (
    audit_candidate_007_dataset,
    run_candidate_007_dataset_audit,
)


def _write_dataset(root: Path, *, active: int = 3, delisted: int = 2, rows: int = 100) -> None:
    root.mkdir()
    symbols = [f"A{i:03d}" for i in range(active)] + [f"D{i:03d}" for i in range(delisted)] + ["SPY", "IWM"]
    master_rows = []
    price_rows = []
    dates = pd.bdate_range("2025-01-01", periods=rows)
    for symbol in symbols:
        is_delisted = symbol.startswith("D")
        status = "delisted" if is_delisted else ("benchmark" if symbol in {"SPY", "IWM"} else "active")
        master_rows.append(
            {
                "symbol": symbol,
                "universe_status": status,
                "is_delisted": is_delisted,
                "first_date": str(dates[0].date()),
                "last_date": str(dates[-1].date()),
                "row_count": rows,
                "provider": "Norgate Data",
            }
        )
        for i, date in enumerate(dates):
            close = 10.0 + i * 0.01
            price_rows.append(
                {
                    "symbol": symbol,
                    "date": str(date.date()),
                    "open": close,
                    "high": close * 1.01,
                    "low": close * 0.99,
                    "close": close,
                    "volume": 1_000_000,
                    "provider_dataset": "Norgate Data",
                }
            )
    pd.DataFrame(master_rows).to_csv(root / "security_master.csv", index=False)
    pd.DataFrame(price_rows).to_csv(root / "prices.csv", index=False)
    (root / "dataset_manifest.json").write_text(
        json.dumps(
            {
                "decision": "CANDIDATE_007_NORGATE_DATASET_COMPLETE_DATASET_READY_NO_PROMOTION",
                "survivorship_free_claim_allowed": True,
                "trial_limited": True,
                "blockers": [],
            }
        ),
        encoding="utf-8",
    )
    (root / "data_input_validation_report.json").write_text(
        json.dumps({"status": "pass", "gate_decision": "DATA_INPUT_VALIDATION_PASS"}),
        encoding="utf-8",
    )


def test_audit_candidate_007_dataset_marks_ready_when_thresholds_pass(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    _write_dataset(dataset, active=3, delisted=2, rows=100)

    result = audit_candidate_007_dataset(
        dataset,
        thresholds={
            "min_active_symbols": 3,
            "min_delisted_symbols": 2,
            "min_total_symbols": 5,
            "min_price_rows": 500,
            "min_median_rows_per_symbol": 90,
            "required_benchmarks": ["SPY", "IWM"],
        },
    )

    assert result["decision"] == "CANDIDATE_007_DATASET_AUDIT_READY_FOR_BACKTEST_SPEC"
    assert result["provider_query_performed"] is False
    assert result["strategy_backtest_performed"] is False
    assert result["coverage"]["active_symbols"] == 3
    assert result["coverage"]["delisted_symbols"] == 2
    assert result["readiness_blockers"] == []


def test_audit_candidate_007_dataset_blocks_missing_delisted(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    _write_dataset(dataset, active=3, delisted=0, rows=100)

    result = audit_candidate_007_dataset(
        dataset,
        thresholds={
            "min_active_symbols": 3,
            "min_delisted_symbols": 1,
            "min_total_symbols": 4,
            "min_price_rows": 300,
            "min_median_rows_per_symbol": 90,
            "required_benchmarks": ["SPY", "IWM"],
        },
    )

    assert result["decision"] == "CANDIDATE_007_DATASET_AUDIT_NOT_READY"
    assert "delisted_symbol_count_below_threshold" in result["readiness_blockers"]


def test_run_candidate_007_dataset_audit_writes_artifacts(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    gate = tmp_path / "gate"
    output = tmp_path / "out"
    _write_dataset(dataset, active=3, delisted=2, rows=100)
    gate.mkdir()
    (gate / "gate_manifest.json").write_text(
        json.dumps(
            {
                "status": "APPROVED_CANDIDATE_007_DATASET_AUDIT_ONLY",
                "linked_dataset": str(dataset),
                "provider_query_allowed": False,
                "market_data_download_allowed": False,
                "strategy_backtest_allowed": False,
                "kronos_inference_allowed": False,
                "portfolio_selection_allowed": False,
                "promotion_allowed": False,
                "readiness_thresholds": {
                    "min_active_symbols": 3,
                    "min_delisted_symbols": 2,
                    "min_total_symbols": 5,
                    "min_price_rows": 500,
                    "min_median_rows_per_symbol": 90,
                    "required_benchmarks": ["SPY", "IWM"],
                },
            }
        ),
        encoding="utf-8",
    )

    result = run_candidate_007_dataset_audit(gate_dir=gate, output_dir=output)

    assert result["decision"] == "CANDIDATE_007_DATASET_AUDIT_READY_FOR_BACKTEST_SPEC"
    assert (output / "candidate_007_dataset_audit_result.json").exists()
    assert (output / "coverage_by_universe.csv").exists()
    assert (output / "final_decision.json").exists()
