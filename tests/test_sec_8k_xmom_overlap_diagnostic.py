from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

import src.experiments.sec_8k_xmom_overlap_diagnostic as diag
from src.experiments.sec_8k_xmom_overlap_diagnostic import (
    build_overlap_panel,
    nearest_event_overlap,
    run_sec8k_xmom_overlap_diagnostic,
    summarize_overlap_panel,
    validate_sec8k_xmom_overlap_diagnostic,
)


def test_nearest_event_overlap_uses_trading_day_distance() -> None:
    calendar = ["2026-01-02", "2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08"]

    overlap = nearest_event_overlap(
        calendar=calendar,
        event_dates=["2026-01-06"],
        signal_date="2026-01-02",
        entry_date="2026-01-05",
        exit_date="2026-01-08",
        window_days=1,
    )

    assert overlap["overlaps_sec8k_window"] is True
    assert overlap["nearest_event_date"] == "2026-01-06"
    assert overlap["nearest_event_anchor"] == "entry"
    assert overlap["nearest_event_distance_trading_days"] == -1


def test_build_overlap_panel_marks_top3_winners_without_direction_columns() -> None:
    panel = build_overlap_panel(_trades(), _prices(), _events(), window_days=2)

    assert len(panel) == 4
    assert sum(1 for row in panel if row["is_top3_winner"] is True) == 3
    assert any(row["symbol"] == "AAA" and row["overlaps_sec8k_window"] is True for row in panel)
    assert all("sharpe" not in row and "dsr" not in row for row in panel)


def test_summary_supports_explanation_only_when_top_winners_cluster_near_8k() -> None:
    rows = [
        _row(100.0, True, True),
        _row(80.0, True, True),
        _row(50.0, True, True),
        _row(-10.0, False, False),
        _row(-20.0, False, False),
    ]

    summary = summarize_overlap_panel(rows, window_days=5)

    assert summary["decision"] == "SEC8K_XMOM_OVERLAP_SUPPORTS_CATALYST_EXPLANATION"
    assert summary["promotion_allowed"] is False
    assert summary["blockers"] == ["trade_count_below_30"]


def test_real_overlap_diagnostic_writes_artifacts_and_passes_validation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(diag, "ARTIFACT_DIR", tmp_path / "overlap")
    monkeypatch.setattr(diag, "VAULT_REPORT", tmp_path / "report.md")
    monkeypatch.setattr(diag, "VAULT_DEVLOG", tmp_path / "devlog.md")

    decision = run_sec8k_xmom_overlap_diagnostic()
    report = validate_sec8k_xmom_overlap_diagnostic(tmp_path / "overlap")

    assert report["status"] == "pass"
    assert decision["promotion_allowed"] is False
    assert decision["provider_query_performed"] is False
    assert (tmp_path / "overlap" / "sec8k_xmom_overlap_panel.csv").is_file()


def test_validator_fails_if_backtest_marked_performed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(diag, "ARTIFACT_DIR", tmp_path / "overlap")
    monkeypatch.setattr(diag, "VAULT_REPORT", tmp_path / "report.md")
    monkeypatch.setattr(diag, "VAULT_DEVLOG", tmp_path / "devlog.md")
    run_sec8k_xmom_overlap_diagnostic()
    summary_path = tmp_path / "overlap" / "diagnostic_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["backtest_performed"] = True
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_sec8k_xmom_overlap_diagnostic(tmp_path / "overlap")

    assert report["status"] == "fail"
    assert any(check["name"] == "summary_no_execution" and check["status"] == "fail" for check in report["checks"])


def _trades() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "AAA", "signal_date": "2026-01-02", "entry_date": "2026-01-05", "exit_date": "2026-01-08", "pnl": 100.0, "return_pct": 0.1},
            {"symbol": "AAA", "signal_date": "2026-01-09", "entry_date": "2026-01-12", "exit_date": "2026-01-13", "pnl": 50.0, "return_pct": 0.05},
            {"symbol": "BBB", "signal_date": "2026-01-02", "entry_date": "2026-01-05", "exit_date": "2026-01-06", "pnl": 25.0, "return_pct": 0.02},
            {"symbol": "BBB", "signal_date": "2026-01-09", "entry_date": "2026-01-12", "exit_date": "2026-01-13", "pnl": -30.0, "return_pct": -0.03},
        ]
    )


def _prices() -> pd.DataFrame:
    rows = []
    for symbol in ["AAA", "BBB"]:
        for day in ["2026-01-02", "2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08", "2026-01-09", "2026-01-12", "2026-01-13"]:
            rows.append({"symbol": symbol, "date": day, "open": 10.0, "high": 10.2, "low": 9.8, "close": 10.0, "volume": 1000})
    return pd.DataFrame(rows)


def _events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "AAA", "status": "event", "reaction_session_date": "2026-01-06"},
            {"symbol": "BBB", "status": "control", "reaction_session_date": "2026-01-06"},
        ]
    )


def _row(pnl: float, overlap: bool, top3: bool) -> dict[str, object]:
    return {
        "pnl": pnl,
        "winner_label": "winner" if pnl > 0 else "loser",
        "overlaps_sec8k_window": overlap,
        "is_top3_winner": top3,
    }
