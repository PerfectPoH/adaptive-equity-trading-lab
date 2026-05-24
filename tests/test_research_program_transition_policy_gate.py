from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.research_program_transition_policy_gate as gate
from src.experiments.research_program_transition_policy_gate_validator import (
    validate_research_program_transition_policy_gate,
)


SPEC_DIR = Path("experiments/provider_aware_research/research_program_transition_policy_gate_20260524")


def test_research_program_transition_policy_gate_passes_real_spec() -> None:
    report = validate_research_program_transition_policy_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "RESEARCH_PROGRAM_TRANSITION_POLICY_GATE_PASS"


def test_transition_policy_gate_fails_if_smallcap_directional_research_reopened(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "policy_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["smallcap_free_data_directional_research_status"] = "ACTIVE"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_research_program_transition_policy_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "smallcap_directional_paused" and check["status"] == "fail" for check in report["checks"])


def test_evaluate_transition_policy_routes_research_tracks_without_promotion() -> None:
    active_only = {"decision": "POLYGON_ACTIVE_ONLY_EXPLORATORY_RESEARCH_ALLOWED_NO_PROMOTION"}
    robustness = {"top3_dependency_flag": True, "sign_flip_ex_top3": True}
    delisted = {"decision": "POLYGON_DELISTED_LISTING_DATE_SUPPORT_BLOCKED"}

    decision = gate.evaluate_research_program_transition_policy(active_only, robustness, delisted)

    assert decision["decision"] == "RESEARCH_PROGRAM_TRANSITION_ACTIVE"
    assert decision["smallcap_free_data_directional_research_allowed"] is False
    assert decision["smallcap_microstructure_diagnostic_allowed"] is True
    assert decision["etf_largecap_risk_regime_lab_allowed"] is True
    assert decision["strategy_promotion_allowed"] is False
    assert "delisted_listing_dates_unavailable_for_full_pit" in decision["primary_data_blockers"]


def test_run_transition_policy_writes_no_query_no_backtest_artifacts(tmp_path: Path) -> None:
    decision = gate.run_research_program_transition_policy_gate(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = gate.validate_research_program_transition_policy_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["provider_query_performed"] is False
    assert decision["market_data_downloaded"] is False
    assert decision["backtest_performed"] is False
    assert decision["strategy_promotion_allowed"] is False
