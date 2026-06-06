from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.experiments.candidate_007_norgate_dataset_builder import (
    NorgateLikeAdapter,
    build_candidate_007_dataset,
    run_candidate_007_norgate_dataset_builder,
    validate_candidate_007_dataset,
)


class FakeNorgateAdapter(NorgateLikeAdapter):
    def __init__(self, frames: dict[str, pd.DataFrame], symbols: dict[str, list[str]]) -> None:
        self.frames = frames
        self.symbols = symbols

    def database_symbols(self, database_name: str) -> list[str]:
        return self.symbols.get(database_name, [])

    def price_timeseries(self, symbol: str) -> pd.DataFrame:
        return self.frames[symbol]


def _frame(start: float, periods: int = 120) -> pd.DataFrame:
    index = pd.bdate_range("2025-01-01", periods=periods)
    close = pd.Series([start + i * 0.1 for i in range(periods)], index=index)
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


def _gate(gate_dir: Path) -> None:
    gate_dir.mkdir()
    (gate_dir / "gate_manifest.json").write_text(
        json.dumps(
            {
                "status": "APPROVED_NORGATE_SURVIVORSHIP_FREE_PANEL_BUILD_ONLY",
                "target_database_names": {"active": "US Equities", "delisted": "US Equities Delisted"},
                "benchmark_symbols": ["SPY", "IWM"],
                "limits": {"active_symbol_limit": 2, "delisted_symbol_limit": 2, "min_rows": 90},
                "provider_query_allowed": True,
                "internet_market_data_download_allowed": False,
                "strategy_backtest_allowed": False,
                "kronos_inference_allowed": False,
                "portfolio_selection_allowed": False,
                "promotion_allowed": False,
                "paper_trading_allowed": False,
                "live_trading_allowed": False,
            }
        ),
        encoding="utf-8",
    )


def test_build_candidate_007_dataset_exports_active_delisted_and_benchmarks(tmp_path: Path) -> None:
    frames = {"AAA": _frame(10), "BBB": _frame(20), "DDD": _frame(5), "SPY": _frame(400), "IWM": _frame(200)}
    adapter = FakeNorgateAdapter(
        frames,
        {"US Equities": ["AAA", "BBB"], "US Equities Delisted": ["DDD"]},
    )

    result = build_candidate_007_dataset(
        adapter,
        output_dir=tmp_path,
        active_limit=2,
        delisted_limit=2,
        min_rows=90,
        benchmark_symbols=["SPY", "IWM"],
    )

    assert result["decision"] == "CANDIDATE_007_NORGATE_DATASET_COMPLETE_DATASET_READY_NO_PROMOTION"
    assert result["run_id"] == tmp_path.name
    assert result["symbol_counts"]["active"] == 2
    assert result["symbol_counts"]["delisted"] == 1
    assert (tmp_path / "prices.csv").exists()
    assert (tmp_path / "security_master.csv").exists()
    assert "prices.csv" in result["file_hashes"]
    prices = pd.read_csv(tmp_path / "prices.csv")
    assert set(prices["symbol"]) == {"AAA", "BBB", "DDD", "SPY", "IWM"}
    validation = validate_candidate_007_dataset(tmp_path)
    assert validation["gate_decision"] == "DATA_INPUT_VALIDATION_PASS"
    manifest = json.loads((tmp_path / "dataset_manifest.json").read_text(encoding="utf-8"))
    assert manifest["dataset_id"] == tmp_path.name


def test_build_candidate_007_dataset_blocks_without_delisted_sample(tmp_path: Path) -> None:
    frames = {"AAA": _frame(10), "SPY": _frame(400), "IWM": _frame(200)}
    adapter = FakeNorgateAdapter(frames, {"US Equities": ["AAA"], "US Equities Delisted": []})

    result = build_candidate_007_dataset(
        adapter,
        output_dir=tmp_path,
        active_limit=2,
        delisted_limit=2,
        min_rows=90,
        benchmark_symbols=["SPY", "IWM"],
    )

    assert result["decision"] == "CANDIDATE_007_NORGATE_DATASET_BLOCKED"
    assert "delisted_symbol_sample_missing" in result["blockers"]
    assert result["survivorship_free_claim_allowed"] is False


def test_run_candidate_007_norgate_dataset_builder_honors_gate_and_writes_final_decision(tmp_path: Path) -> None:
    gate_dir = tmp_path / "gate"
    output_dir = tmp_path / "out"
    _gate(gate_dir)
    frames = {"AAA": _frame(10), "DDD": _frame(5), "SPY": _frame(400), "IWM": _frame(200)}
    adapter = FakeNorgateAdapter(frames, {"US Equities": ["AAA"], "US Equities Delisted": ["DDD"]})

    result = run_candidate_007_norgate_dataset_builder(gate_dir=gate_dir, output_dir=output_dir, adapter=adapter)

    assert result["strategy_backtest_performed"] is False
    assert result["kronos_inference_performed"] is False
    assert result["promotion_allowed"] is False
    assert (output_dir / "dataset_manifest.json").exists()
    assert (output_dir / "final_decision.json").exists()


def test_run_candidate_007_norgate_dataset_builder_accepts_rerun_gate_status(tmp_path: Path) -> None:
    gate_dir = tmp_path / "gate"
    output_dir = tmp_path / "out"
    _gate(gate_dir)
    manifest = json.loads((gate_dir / "gate_manifest.json").read_text(encoding="utf-8"))
    manifest["status"] = "APPROVED_NORGATE_SURVIVORSHIP_FREE_PANEL_RERUN_AFTER_VALIDATOR_TOLERANCE_FIX"
    (gate_dir / "gate_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    frames = {"AAA": _frame(10), "DDD": _frame(5), "SPY": _frame(400), "IWM": _frame(200)}
    adapter = FakeNorgateAdapter(frames, {"US Equities": ["AAA"], "US Equities Delisted": ["DDD"]})

    result = run_candidate_007_norgate_dataset_builder(gate_dir=gate_dir, output_dir=output_dir, adapter=adapter)

    assert result["decision"] == "CANDIDATE_007_NORGATE_DATASET_COMPLETE_DATASET_READY_NO_PROMOTION"


def test_validate_candidate_007_dataset_allows_tiny_ohlc_rounding_tolerance(tmp_path: Path) -> None:
    pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "date": "2025-04-30",
                "open": 22.678125,
                "high": 22.67813,
                "low": 22.67813,
                "close": 22.678125,
                "volume": 250001,
                "provider_dataset": "Norgate Data",
            }
        ]
    ).to_csv(tmp_path / "prices.csv", index=False)
    pd.DataFrame(
        [
            {
                "symbol": "AAA",
                "universe_status": "delisted",
                "is_delisted": True,
                "first_date": "2025-04-30",
                "last_date": "2025-04-30",
                "row_count": 1,
                "provider": "Norgate Data",
            },
            {
                "symbol": "BBB",
                "universe_status": "active",
                "is_delisted": False,
                "first_date": "2025-04-30",
                "last_date": "2025-04-30",
                "row_count": 1,
                "provider": "Norgate Data",
            },
        ]
    ).to_csv(tmp_path / "security_master.csv", index=False)

    validation = validate_candidate_007_dataset(tmp_path)

    assert validation["gate_decision"] == "DATA_INPUT_VALIDATION_PASS"
