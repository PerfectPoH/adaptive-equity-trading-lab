from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import src.experiments.lab_final_status_pack_001 as pack


def test_collect_decision_files_extracts_core_governance_fields(tmp_path: Path) -> None:
    run_dir = tmp_path / "RUN-A"
    run_dir.mkdir()
    (run_dir / "final_decision.json").write_text(
        json.dumps(
            {
                "trial_id": "TRIAL-A",
                "run_id": "RUN-A",
                "decision": "ARCHIVE_CURRENT_FORM",
                "promotion_allowed": False,
                "provider_query_performed": False,
                "backtest_performed": True,
                "short_selling_performed": False,
            }
        ),
        encoding="utf-8",
    )

    rows = pack.collect_decision_rows(tmp_path)

    assert rows == [
        {
            "trial_id": "TRIAL-A",
            "run_id": "RUN-A",
            "decision": "ARCHIVE_CURRENT_FORM",
            "promotion_allowed": False,
            "provider_query_performed": False,
            "backtest_performed": True,
            "short_selling_performed": False,
            "source_file": str(run_dir / "final_decision.json"),
        }
    ]


def test_summarize_research_phase_marks_smallcap_free_data_paused() -> None:
    decisions = [
        {"decision": "ACTIVE_ONLY_MOMENTUM_SMOKE_ROBUSTNESS_COMPLETE_NO_PROMOTION", "promotion_allowed": False},
        {"decision": "POLYGON_DELISTED_LISTING_DATE_SUPPORT_BLOCKED", "promotion_allowed": False},
        {"decision": "TRANSITION_FIVE_POINT_BATCH_COMPLETE_NO_STRATEGY", "promotion_allowed": False},
    ]

    summary = pack.summarize_research_phase(decisions)

    assert summary["smallcap_free_data_directional_research_status"] == "PAUSED"
    assert summary["promoted_strategy_count"] == 0
    assert summary["final_policy"] == "RISK_REGIME_ENGINE_ONLY"
    assert "survivorship_or_pit_blocker" in summary["primary_blockers"]


def test_build_risk_regime_operating_rules_blocks_directional_alpha_and_allows_diagnostics() -> None:
    transition = {
        "smallcap_free_data_directional_research_allowed": False,
        "smallcap_microstructure_diagnostic_allowed": True,
        "etf_largecap_risk_regime_lab_allowed": True,
    }
    five_point = {
        "decision": "TRANSITION_FIVE_POINT_BATCH_COMPLETE_NO_STRATEGY",
        "promotion_allowed": False,
        "provider_query_performed": False,
    }

    rules = pack.build_risk_regime_operating_rules(transition, five_point)

    assert rules["mode"] == "RISK_REGIME_ENGINE"
    assert rules["forbidden_actions"]["smallcap_free_data_directional_alpha"] is True
    assert rules["allowed_actions"]["etf_largecap_risk_regime_diagnostics"] is True
    assert rules["promotion_allowed"] is False


def test_render_dashboard_contains_three_sections() -> None:
    html = pack.render_dashboard_html(
        phase_summary={"final_policy": "RISK_REGIME_ENGINE_ONLY", "promoted_strategy_count": 0},
        operating_rules={"mode": "RISK_REGIME_ENGINE", "promotion_allowed": False},
        ledger_rows=[
            {"trial_id": "A", "decision": "ARCHIVE", "promotion_allowed": False},
            {"trial_id": "B", "decision": "BLOCKED", "promotion_allowed": False},
        ],
    )

    assert "Research Phase Closure" in html
    assert "Risk/Regime Operating Rules" in html
    assert "Final Research Ledger" in html
    assert "RISK_REGIME_ENGINE_ONLY" in html


def test_run_lab_final_status_pack_writes_outputs(tmp_path: Path) -> None:
    execution_outputs = tmp_path / "execution_outputs"
    execution_outputs.mkdir()
    for name, decision in {
        "A": "ACTIVE_ONLY_MOMENTUM_SMOKE_ROBUSTNESS_COMPLETE_NO_PROMOTION",
        "B": "POLYGON_DELISTED_LISTING_DATE_SUPPORT_BLOCKED",
        "C": "TRANSITION_FIVE_POINT_BATCH_COMPLETE_NO_STRATEGY",
    }.items():
        run_dir = execution_outputs / name
        run_dir.mkdir()
        (run_dir / "final_decision.json").write_text(
            json.dumps(
                {
                    "trial_id": f"TRIAL-{name}",
                    "run_id": name,
                    "decision": decision,
                    "promotion_allowed": False,
                    "provider_query_performed": False,
                    "backtest_performed": False,
                    "short_selling_performed": False,
                }
            ),
            encoding="utf-8",
        )
    transition = tmp_path / "transition.json"
    transition.write_text(
        json.dumps(
            {
                "smallcap_free_data_directional_research_allowed": False,
                "smallcap_microstructure_diagnostic_allowed": True,
                "etf_largecap_risk_regime_lab_allowed": True,
            }
        ),
        encoding="utf-8",
    )
    five_point = tmp_path / "five_point.json"
    five_point.write_text(json.dumps({"decision": "TRANSITION_FIVE_POINT_BATCH_COMPLETE_NO_STRATEGY", "promotion_allowed": False}), encoding="utf-8")

    decision = pack.run_lab_final_status_pack_001(
        execution_outputs_dir=execution_outputs,
        transition_decision_path=transition,
        five_point_decision_path=five_point,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    validation = pack.validate_lab_final_status_pack_output(tmp_path / "out")

    assert validation["status"] == "pass"
    assert decision["decision"] == "LAB_FINAL_STATUS_PACK_COMPLETE"
    assert decision["completed_points"] == 3
    assert decision["promotion_allowed"] is False
    assert (tmp_path / "out" / "research_phase_closure_ledger.csv").is_file()
    assert (tmp_path / "out" / "risk_regime_operating_rules.json").is_file()
    assert (tmp_path / "out" / "lab_status_dashboard.html").is_file()


def test_research_ledger_csv_can_be_read_by_pandas(tmp_path: Path) -> None:
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    pack.write_research_ledger_csv(
        output_dir / "ledger.csv",
        [{"trial_id": "A", "run_id": "R", "decision": "D", "promotion_allowed": False}],
    )

    frame = pd.read_csv(output_dir / "ledger.csv")

    assert frame.loc[0, "trial_id"] == "A"
    assert frame.loc[0, "promotion_allowed"] is False or frame.loc[0, "promotion_allowed"] == 0
