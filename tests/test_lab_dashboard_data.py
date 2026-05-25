from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from dashboard.lab_dashboard_data import (
    STRATEGY_PROFILES,
    WORKBENCH_TEMPLATES,
    build_workbench_manifest,
    build_strategy_chart_story,
    classify_strategy_status,
    governance_metrics,
    load_dashboard_payload,
    project_capability_rows,
    project_lifecycle_rows,
    strategy_detail,
    strategy_rows,
)


def test_strategy_catalog_covers_core_research_tracks() -> None:
    keys = {profile.key for profile in STRATEGY_PROFILES}

    assert {"xmom", "gaprev", "sec8k", "pead", "lowvol", "form4", "dollarbar", "regime"}.issubset(keys)
    assert all(len(profile.demonstration) >= 5 for profile in STRATEGY_PROFILES)


def test_strategy_rows_groups_ledger_decisions_by_strategy_family() -> None:
    ledger = pd.DataFrame(
        [
            {"trial_id": "TRIAL-LOWVOL-TRADABILITY-001", "run_id": "LOWVOL", "decision": "LOWVOL_TRADABILITY_ARCHIVE_CURRENT_FORM", "promotion_allowed": False},
            {"trial_id": "TRIAL-SEC8K-DIRECTION-001", "run_id": "SEC8K", "decision": "SEC8K_TAPE_ORACLE_ARCHIVE_CURRENT_FORM", "promotion_allowed": False},
            {"trial_id": "PEAD", "run_id": "PROBE", "decision": "BLOCKED_ALPHAVANTAGE_SOURCE_INSUFFICIENT", "promotion_allowed": False},
        ]
    )

    rows = strategy_rows(ledger).set_index("key")

    assert rows.loc["lowvol", "status"] == "ARCHIVED"
    assert rows.loc["sec8k", "runs"] == 1
    assert rows.loc["pead", "status"] == "BLOCKED"


def test_strategy_detail_exposes_demonstration_graph_edges() -> None:
    ledger = pd.DataFrame(
        [{"trial_id": "TRIAL-GAPREV-001", "run_id": "GAPREV", "decision": "TECHNICAL_CONTROLLED_RUN_COMPLETE__NO_PROMOTION", "promotion_allowed": False}]
    )

    detail = strategy_detail("gaprev", ledger)

    assert detail["profile"].name == "GapRev RTH Reversion"
    assert len(detail["flow_edges"]) == len(detail["flow_nodes"]) - 1
    assert detail["status"] == "ARCHIVED"


def test_classify_strategy_status_prioritizes_promotion_then_blockers() -> None:
    assert classify_strategy_status(["ANYTHING"], promoted=True) == "PROMOTED"
    assert classify_strategy_status(["BLOCKED_ALPHAVANTAGE_SOURCE_INSUFFICIENT"], promoted=False) == "BLOCKED"
    assert classify_strategy_status(["LOWVOL_TRADABILITY_ARCHIVE_CURRENT_FORM"], promoted=False) == "ARCHIVED"
    assert classify_strategy_status([], promoted=False) == "NOT RUN"


def test_load_dashboard_payload_reads_final_status_artifacts(tmp_path: Path) -> None:
    final_dir = tmp_path / "experiments/provider_aware_research/execution_outputs/LAB-FINAL-STATUS-PACK-RUN-001"
    five_dir = tmp_path / "experiments/provider_aware_research/execution_outputs/TRANSITION-FIVE-POINT-BATCH-RUN-001"
    final_dir.mkdir(parents=True)
    five_dir.mkdir(parents=True)
    pd.DataFrame([{"trial_id": "A", "decision": "ARCHIVE", "promotion_allowed": False}]).to_csv(final_dir / "research_phase_closure_ledger.csv", index=False)
    (final_dir / "research_phase_summary.json").write_text(json.dumps({"decision_count": 1, "promoted_strategy_count": 0, "final_policy": "RISK_REGIME_ENGINE_ONLY"}), encoding="utf-8")
    (final_dir / "risk_regime_operating_rules.json").write_text(json.dumps({"mode": "RISK_REGIME_ENGINE"}), encoding="utf-8")
    (final_dir / "final_decision.json").write_text(json.dumps({"completed_points": 3}), encoding="utf-8")
    for filename in [
        "etf_largecap_regime_map.csv",
        "portfolio_allocation_smoke.csv",
        "smallcap_microstructure_diagnostic.csv",
        "data_upgrade_decision_matrix.csv",
    ]:
        pd.DataFrame([{"x": 1}]).to_csv(five_dir / filename, index=False)

    payload = load_dashboard_payload(tmp_path)
    metrics = governance_metrics(payload)

    assert metrics["decision_count"] == 1
    assert metrics["final_policy"] == "RISK_REGIME_ENGINE_ONLY"
    assert not payload["ledger"].empty


def test_project_capabilities_include_future_strategy_builder_as_planned() -> None:
    rows = project_capability_rows()

    assert "Future UX" in set(rows["area"])
    assert "planned" in set(rows["state"])


def test_project_lifecycle_documents_research_arc() -> None:
    rows = project_lifecycle_rows()

    assert len(rows) >= 6
    assert {"phase", "idea_source", "what_happened", "lesson"}.issubset(rows.columns)
    assert any(rows["phase"].str.contains("Momentum", case=False))
    assert any(rows["lesson"].str.contains("data", case=False))


def test_build_workbench_manifest_starts_unpromoted_and_gate_first() -> None:
    manifest = build_workbench_manifest(
        name="My gap probe",
        template="Mean Reversion",
        universe="small-cap active-only sandbox",
        holding_period_days=3,
        cost_bps=500,
        allow_provider_query=False,
    )

    assert "Mean Reversion" in WORKBENCH_TEMPLATES
    assert manifest["strategy_name"] == "My gap probe"
    assert manifest["promotion_allowed"] is False
    assert manifest["provider_query_allowed"] is False
    assert manifest["first_gate"] == "cost_realism_gate"
    assert "pre-run gate" in manifest["next_step"]


def test_build_strategy_chart_story_uses_real_ohlc_window(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv"
    pd.DataFrame(
        [
            {"symbol": "AEHR", "date": "2026-01-01", "open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2, "volume": 1000},
            {"symbol": "AEHR", "date": "2026-01-02", "open": 10.2, "high": 11.0, "low": 10.1, "close": 10.8, "volume": 2000},
            {"symbol": "AEHR", "date": "2026-01-05", "open": 10.8, "high": 11.2, "low": 10.0, "close": 10.1, "volume": 3000},
            {"symbol": "AEHR", "date": "2026-01-06", "open": 10.1, "high": 10.4, "low": 9.9, "close": 10.0, "volume": 1500},
        ]
    ).to_csv(prices, index=False)

    story = build_strategy_chart_story("xmom", price_file=prices)

    assert story["symbol"] == "AEHR"
    assert {"date", "open", "high", "low", "close", "volume"}.issubset(story["prices"].columns)
    assert len(story["markers"]) >= 2
    assert any(marker["kind"] == "buy" for marker in story["markers"])
    assert story["title"]
