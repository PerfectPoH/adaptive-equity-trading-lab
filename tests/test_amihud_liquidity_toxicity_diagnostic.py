from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

import src.experiments.amihud_liquidity_toxicity_diagnostic as diag
from src.experiments.amihud_liquidity_toxicity_diagnostic import (
    assign_liquidity_buckets,
    diagnose_trade_liquidity,
    run_amihud_liquidity_toxicity_diagnostic,
    summarize_liquidity_toxicity,
    validate_amihud_liquidity_toxicity_diagnostic,
)


def test_diagnose_trade_liquidity_calculates_pre_entry_amihud() -> None:
    prices = _price_frame("AAA", volume=1000)
    trade = pd.Series(
        {
            "symbol": "AAA",
            "signal_date": "2026-02-01",
            "entry_date": "2026-02-02",
            "exit_date": "2026-03-01",
            "pnl": -10.0,
            "return_pct": -0.01,
            "avg_dollar_volume_20d": 100000.0,
            "rolling_volatility_20d": 0.02,
        }
    )

    result = diagnose_trade_liquidity(trade, prices, lookback_days=20)

    assert result["status"] == "evaluated"
    assert result["amihud_illiq_20d"] > 0
    assert result["toxicity_label"] == "loser"


def test_assign_liquidity_buckets_uses_median_split() -> None:
    rows = [
        {"amihud_illiq_20d": 1.0, "pnl": 1.0, "toxicity_label": "winner"},
        {"amihud_illiq_20d": 2.0, "pnl": -1.0, "toxicity_label": "loser"},
        {"amihud_illiq_20d": 3.0, "pnl": -2.0, "toxicity_label": "loser"},
    ]

    tagged = assign_liquidity_buckets(rows)

    assert [row["liquidity_bucket"] for row in tagged] == ["low_illiq", "high_illiq", "high_illiq"]


def test_summary_blocks_when_trade_count_below_30_even_with_separation() -> None:
    rows = assign_liquidity_buckets(
        [
            {"amihud_illiq_20d": 1.0, "pnl": 10.0, "toxicity_label": "winner"},
            {"amihud_illiq_20d": 2.0, "pnl": -10.0, "toxicity_label": "loser"},
            {"amihud_illiq_20d": 3.0, "pnl": -20.0, "toxicity_label": "loser"},
        ]
    )

    summary = summarize_liquidity_toxicity(rows, lookback_days=20)

    assert summary["candidate_filter_allowed"] is False
    assert "trade_count_below_30" in summary["blockers"]


def test_real_amihud_diagnostic_passes_validation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(diag, "ARTIFACT_DIR", tmp_path / "amihud")
    monkeypatch.setattr(diag, "VAULT_REPORT", tmp_path / "report.md")
    monkeypatch.setattr(diag, "VAULT_DEVLOG", tmp_path / "devlog.md")

    decision = run_amihud_liquidity_toxicity_diagnostic()
    report = validate_amihud_liquidity_toxicity_diagnostic(tmp_path / "amihud")

    assert decision["promotion_allowed"] is False
    assert decision["provider_query_performed"] is False
    assert report["status"] == "pass"


def test_validator_fails_if_backtest_marked_performed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(diag, "ARTIFACT_DIR", tmp_path / "amihud")
    monkeypatch.setattr(diag, "VAULT_REPORT", tmp_path / "report.md")
    monkeypatch.setattr(diag, "VAULT_DEVLOG", tmp_path / "devlog.md")
    run_amihud_liquidity_toxicity_diagnostic()
    summary_path = tmp_path / "amihud" / "diagnostic_summary.json"
    summary_path.write_text(
        summary_path.read_text(encoding="utf-8").replace('"backtest_performed": false', '"backtest_performed": true'),
        encoding="utf-8",
    )

    report = validate_amihud_liquidity_toxicity_diagnostic(tmp_path / "amihud")

    assert report["status"] == "fail"
    assert any(check["name"] == "summary_no_execution" and check["status"] == "fail" for check in report["checks"])


def _price_frame(symbol: str, volume: int) -> pd.DataFrame:
    rows = []
    for index in range(25):
        close = 10.0 + index * 0.1
        rows.append(
            {
                "symbol": symbol,
                "date": f"2026-01-{index + 1:02d}",
                "open": close - 0.05,
                "high": close + 0.1,
                "low": close - 0.1,
                "close": close,
                "volume": volume,
                "provider_dataset": "UNIT.TEST",
            }
        )
    return pd.DataFrame(rows)
