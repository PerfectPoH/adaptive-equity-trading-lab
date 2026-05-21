from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.experiments.pead_sec_event_source_gate import build_sec_earnings_event_panel, run_pead_sec_event_source_gate, validate_pead_sec_event_source_gate


def test_build_sec_earnings_event_panel_maps_bmo_and_amc_reaction_sessions(tmp_path: Path) -> None:
    path = tmp_path / "summary.csv"
    pd.DataFrame(
        [
            {
                "accessionNumber": "a",
                "filingDate": "2026-01-02",
                "acceptanceDateTime": "2026-01-02T12:00:00.000Z",
                "items": "2.02,9.01",
                "classification": "BMO",
                "action": "allow_candidate",
                "reaction_session": "same_regular_session",
            },
            {
                "accessionNumber": "b",
                "filingDate": "2026-01-02",
                "acceptanceDateTime": "2026-01-02T22:00:00.000Z",
                "items": "2.02,9.01",
                "classification": "AMC",
                "action": "allow_candidate",
                "reaction_session": "next_regular_session",
            },
        ]
    ).to_csv(path, index=False)

    panel = build_sec_earnings_event_panel(path)

    assert panel["reaction_session_date"].tolist() == ["2026-01-02", "2026-01-05"]
    assert not panel["has_earnings_surprise_magnitude"].any()


def test_pead_sec_event_source_gate_blocks_without_surprise_magnitude() -> None:
    decision = run_pead_sec_event_source_gate()
    report = validate_pead_sec_event_source_gate()

    assert decision["decision"] == "BLOCKED_EARNINGS_SURPRISE_MAGNITUDE_UNAVAILABLE"
    assert decision["backtest_performed"] is False
    assert report["status"] == "pass"
