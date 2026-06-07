from __future__ import annotations

import json
from pathlib import Path

from src.experiments.candidate_015_data_mesh_provider_scan import (
    PROVIDER_REQUIREMENTS,
    build_data_mesh_provider_scan,
    persist_candidate_015_data_mesh_provider_scan,
    run_candidate_015_data_mesh_provider_scan,
)


def _gate(gate_dir: Path) -> None:
    gate_dir.mkdir()
    (gate_dir / "gate_manifest.json").write_text(
        json.dumps(
            {
                "status": "APPROVED_DATA_MESH_PROVIDER_SCAN_NO_QUERY",
                "provider_query_allowed": False,
                "market_data_download_allowed": False,
                "raw_payload_retention_allowed": False,
                "dataset_build_allowed": False,
                "backtest_allowed": False,
                "promotion_allowed": False,
                "paper_trading_allowed": False,
                "live_trading_allowed": False,
            }
        ),
        encoding="utf-8",
    )


def test_build_data_mesh_provider_scan_keeps_paid_single_provider_paths_admissible() -> None:
    scan = build_data_mesh_provider_scan()
    rows = {row["provider"]: row for row in scan["provider_matrix"]}

    assert rows["Norgate Data Full US Stocks Platinum"]["status"] == "ADMISSIBLE_IF_SUBSCRIBED"
    assert rows["CRSP/WRDS"]["status"] == "ADMISSIBLE_IF_ACCESS_GRANTED"
    assert "candidate_012_true_backtest" in rows["Norgate Data Full US Stocks Platinum"]["can_unlock"]
    assert scan["decision"] == "DATA_MESH_PROVIDER_SCAN_COMPLETE_NO_QUERY"
    assert scan["provider_query_performed"] is False


def test_build_data_mesh_provider_scan_blocks_free_mesh_from_backtest_until_micro_probes_pass() -> None:
    scan = build_data_mesh_provider_scan()
    free_mesh = next(row for row in scan["provider_matrix"] if row["provider"] == "Hybrid Free Data Mesh")

    assert free_mesh["status"] == "REQUIRES_MICRO_PROBES"
    assert free_mesh["candidate_012_backtest_allowed"] is False
    assert "identity_reconciliation_unverified" in free_mesh["blockers"]
    assert "corporate_action_policy_unverified" in free_mesh["blockers"]
    assert scan["final_decision"]["backtest_allowed"] is False


def test_probe_plan_has_known_cases_for_identity_delisting_and_corporate_actions() -> None:
    scan = build_data_mesh_provider_scan()
    cases = {case["case_id"]: case for case in scan["micro_probe_plan"]}

    assert {"ACTIVE_BASELINE_AAPL", "SPLIT_AAPL_2020", "TICKER_CHANGE_FB_META", "DELISTING_BBBY"}.issubset(cases)
    assert cases["DELISTING_BBBY"]["purpose"] == "Verify delisted price continuity and terminal date handling."
    assert len(PROVIDER_REQUIREMENTS) >= 10


def test_run_candidate_015_honors_no_query_gate_and_writes_artifacts(tmp_path: Path) -> None:
    gate_dir = tmp_path / "gate"
    output_dir = tmp_path / "out"
    _gate(gate_dir)

    result = run_candidate_015_data_mesh_provider_scan(gate_dir=gate_dir, output_dir=output_dir)

    assert result["provider_query_performed"] is False
    assert result["backtest_performed"] is False
    assert result["promotion_allowed"] is False
    assert (output_dir / "data_mesh_provider_scan.json").exists()
    assert (output_dir / "final_decision.json").exists()
    assert (output_dir / "data_mesh_provider_scan_report.md").exists()


def test_persist_candidate_015_writes_vault_note(tmp_path: Path) -> None:
    scan = build_data_mesh_provider_scan()
    paths = persist_candidate_015_data_mesh_provider_scan(
        scan,
        output_dir=tmp_path / "out",
        vault_note_path=tmp_path / "vault" / "note.md",
    )

    assert paths["vault_note"].exists()
    note = paths["vault_note"].read_text(encoding="utf-8")
    assert "Hybrid Free Data Mesh" in note
    assert "micro-probe" in note
