from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.experiments.candidate_014_norgate_fresh_data_audit import (
    NorgateAuditAdapter,
    audit_norgate_fresh_data_coverage,
    run_candidate_014_norgate_fresh_data_audit,
)


class FakeNorgateAuditAdapter(NorgateAuditAdapter):
    def __init__(self, frames: dict[str, pd.DataFrame], symbols: dict[str, list[str]]) -> None:
        self.frames = frames
        self.symbols = symbols

    def database_symbols(self, database_name: str) -> list[str]:
        return self.symbols.get(database_name, [])

    def price_timeseries(self, symbol: str) -> pd.DataFrame:
        return self.frames[symbol]


def _frame(start: str, end: str) -> pd.DataFrame:
    index = pd.bdate_range(start, end)
    close = pd.Series(range(1, len(index) + 1), index=index, dtype="float64")
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
                "status": "APPROVED_NORGATE_LOCAL_FRESH_DATA_AUDIT_ONLY",
                "provider": "Norgate Data",
                "target_database_names": {"active": "US Equities", "delisted": "US Equities Delisted"},
                "benchmark_symbols": ["SPY", "IWM"],
                "limits": {
                    "active_sample_limit": 2,
                    "delisted_sample_limit": 1,
                    "min_history_years": 5,
                    "min_loaded_active_symbols": 2,
                    "min_loaded_delisted_symbols": 1,
                },
                "provider_query_allowed": True,
                "local_provider_only": True,
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


def test_audit_norgate_fresh_data_coverage_ready_when_history_and_delisted_exist() -> None:
    frames = {
        "AAA": _frame("2019-01-01", "2026-01-01"),
        "BBB": _frame("2019-01-01", "2026-01-01"),
        "DDD": _frame("2018-01-01", "2021-01-01"),
        "SPY": _frame("2019-01-01", "2026-01-01"),
        "IWM": _frame("2019-01-01", "2026-01-01"),
    }
    adapter = FakeNorgateAuditAdapter(frames, {"US Equities": ["AAA", "BBB"], "US Equities Delisted": ["DDD"]})

    result = audit_norgate_fresh_data_coverage(
        adapter,
        active_sample_limit=2,
        delisted_sample_limit=1,
        benchmark_symbols=["SPY", "IWM"],
        min_history_years=5,
        min_loaded_active_symbols=2,
        min_loaded_delisted_symbols=1,
    )

    assert result["decision"] == "CANDIDATE_014_NORGATE_FRESH_DATA_AUDIT_READY_FOR_FRESH_DATA_GATE"
    assert result["backtest_allowed"] is False
    assert result["coverage"]["max_history_years"] >= 5
    assert result["coverage"]["loaded_delisted_symbols"] == 1


def test_audit_norgate_fresh_data_coverage_blocks_trial_limited_history() -> None:
    frames = {
        "AAA": _frame("2024-01-01", "2026-01-01"),
        "DDD": _frame("2025-01-01", "2026-01-01"),
        "SPY": _frame("2024-01-01", "2026-01-01"),
        "IWM": _frame("2024-01-01", "2026-01-01"),
    }
    adapter = FakeNorgateAuditAdapter(frames, {"US Equities": ["AAA"], "US Equities Delisted": ["DDD"]})

    result = audit_norgate_fresh_data_coverage(
        adapter,
        active_sample_limit=2,
        delisted_sample_limit=2,
        benchmark_symbols=["SPY", "IWM"],
        min_history_years=5,
        min_loaded_active_symbols=1,
        min_loaded_delisted_symbols=1,
    )

    assert result["decision"] == "CANDIDATE_014_NORGATE_FRESH_DATA_AUDIT_BLOCKED"
    assert "history_span_below_5_years" in result["blockers"]


def test_run_candidate_014_honors_gate_and_writes_artifacts(tmp_path: Path) -> None:
    gate_dir = tmp_path / "gate"
    output_dir = tmp_path / "out"
    _gate(gate_dir)
    frames = {
        "AAA": _frame("2019-01-01", "2026-01-01"),
        "BBB": _frame("2019-01-01", "2026-01-01"),
        "DDD": _frame("2018-01-01", "2021-01-01"),
        "SPY": _frame("2019-01-01", "2026-01-01"),
        "IWM": _frame("2019-01-01", "2026-01-01"),
    }
    adapter = FakeNorgateAuditAdapter(frames, {"US Equities": ["AAA", "BBB"], "US Equities Delisted": ["DDD"]})

    result = run_candidate_014_norgate_fresh_data_audit(gate_dir=gate_dir, output_dir=output_dir, adapter=adapter)

    assert result["provider_query_performed"] is True
    assert result["strategy_backtest_performed"] is False
    assert result["promotion_allowed"] is False
    assert (output_dir / "norgate_fresh_data_audit_result.json").exists()
    assert (output_dir / "final_decision.json").exists()
