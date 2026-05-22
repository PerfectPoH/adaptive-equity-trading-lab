from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

import src.experiments.sec_8k_event_timing_diagnostic as diag
from src.experiments.sec_8k_event_timing_diagnostic import (
    build_event_timing_panel,
    run_sec_8k_event_timing_diagnostic,
    summarize_event_timing_panel,
    validate_sec_8k_event_timing_diagnostic,
)


def test_build_event_timing_panel_marks_event_and_control_days() -> None:
    events = pd.DataFrame([{"reaction_session_date": "2026-02-02"}])
    prices = _prices()

    panel = build_event_timing_panel(events, prices, symbol="AAA", lookback_days=5)

    assert any(row["is_sec_8k_event_day"] is True for row in panel)
    assert any(row["is_sec_8k_event_day"] is False for row in panel)
    assert all("pnl" not in row for row in panel)


def test_summary_archives_when_event_count_too_small() -> None:
    rows = [
        {"is_sec_8k_event_day": True, "return_abs": 0.2, "volume_ratio_vs_20d_median": 3.0},
        {"is_sec_8k_event_day": False, "return_abs": 0.01, "volume_ratio_vs_20d_median": 1.0},
    ]

    summary = summarize_event_timing_panel(rows, symbol="AAA", lookback_days=20)

    assert summary["candidate_timing_signal_allowed"] is False
    assert "event_count_below_8" in summary["blockers"]


def test_real_sec_8k_event_timing_diagnostic_passes_validation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(diag, "ARTIFACT_DIR", tmp_path / "sec_timing")
    monkeypatch.setattr(diag, "VAULT_REPORT", tmp_path / "report.md")
    monkeypatch.setattr(diag, "VAULT_DEVLOG", tmp_path / "devlog.md")

    decision = run_sec_8k_event_timing_diagnostic()
    report = validate_sec_8k_event_timing_diagnostic(tmp_path / "sec_timing")

    assert decision["promotion_allowed"] is False
    assert decision["provider_query_performed"] is False
    assert report["status"] == "pass"


def test_validator_fails_if_promotion_allowed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(diag, "ARTIFACT_DIR", tmp_path / "sec_timing")
    monkeypatch.setattr(diag, "VAULT_REPORT", tmp_path / "report.md")
    monkeypatch.setattr(diag, "VAULT_DEVLOG", tmp_path / "devlog.md")
    run_sec_8k_event_timing_diagnostic()
    decision_path = tmp_path / "sec_timing" / "final_decision.json"
    decision_path.write_text(
        decision_path.read_text(encoding="utf-8").replace('"promotion_allowed": false', '"promotion_allowed": true'),
        encoding="utf-8",
    )

    report = validate_sec_8k_event_timing_diagnostic(tmp_path / "sec_timing")

    assert report["status"] == "fail"
    assert any(check["name"] == "decision_no_promotion" and check["status"] == "fail" for check in report["checks"])


def _prices() -> pd.DataFrame:
    rows = []
    for index in range(15):
        rows.append(
            {
                "symbol": "AAA",
                "date": f"2026-01-{27 + index:02d}" if index < 5 else f"2026-02-{index - 4:02d}",
                "open": 10.0,
                "high": 10.5,
                "low": 9.5,
                "close": 10.0 + index * 0.1,
                "volume": 1000 + index * 100,
                "provider_dataset": "UNIT.TEST",
            }
        )
    return pd.DataFrame(rows)
