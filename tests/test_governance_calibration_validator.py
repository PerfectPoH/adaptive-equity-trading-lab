from __future__ import annotations

import json
from pathlib import Path

from src.experiments.governance_calibration_validator import main, validate_governance_calibration


def _valid_artifact(tmp_path: Path) -> Path:
    artifact = tmp_path / "calibration"
    artifact.mkdir()
    manifest = {
        "status": "SPEC_ONLY_NOT_EXECUTED",
        "decision": "GOVERNANCE_CALIBRATION_FALSIFIABILITY_DEFINED_NOT_RUN",
        "scope": "calibration",
        "purpose": "falsifiability",
        "no_provider_query": True,
        "no_backtest": True,
        "no_strategy_promotion": True,
        "required_tables": ["constraint_taxonomy.csv"],
    }
    (artifact / "governance_calibration_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (artifact / "constraint_taxonomy.csv").write_text(
        "constraint,constraint_type,may_block_execution,may_block_positive_result,rationale\n"
        "no_raw_payload_retention,hard_governance,yes,no,governance only\n"
        "primary_metric_predeclared,hard_research_process,yes,no,process only\n"
        "minimum_gap_threshold,research_design,no,yes,can affect result\n",
        encoding="utf-8",
    )
    (artifact / "falsifiability_checks.csv").write_text(
        "check_id,check,required,pass_condition,interpretation\n"
        "FAL-001,At least one allowed execution path exists after approval/preflight,yes,path exists,not impossible\n"
        "FAL-002,Positive and negative empirical outcomes are both representable,yes,both outcomes,system is falsifiable\n"
        "FAL-003,Performance thresholds are not embedded in provider validators,yes,no thresholds,validators do not force failure\n"
        "FAL-004,Research-design parameters can change via new preregistration,yes,new preregistration,learning remains possible\n"
        "FAL-005,At least one synthetic compliant artifact could pass validators without real alpha,yes,governance only,not alpha\n",
        encoding="utf-8",
    )
    (artifact / "allowed_research_flexibility.csv").write_text(
        "flexibility_item,allowed,mechanism,guardrail\n"
        "new_signal_hypothesis,yes,new preregistration,trial budget applies\n"
        "feature_set_change,yes,new preregistration,no mutation\n"
        "parameter_change,yes,new preregistration,counted\n",
        encoding="utf-8",
    )
    (artifact / "overconstraint_red_flags.csv").write_text(
        "red_flag,severity,meaning,required_response\n"
        "no_execution_path_even_with_approval,critical,impossible,revise/process-fix before research\n"
        "validators_require_positive_return,critical,performance leak,remove performance requirement from validator\n"
        "trial_budget_zero,critical,no test,set finite nonzero budget\n",
        encoding="utf-8",
    )
    (artifact / "calibration_decision_policy.csv").write_text(
        "decision,condition,action\n"
        "calibrated,all pass,continue to dry-run preflight spec\n"
        "overconstrained,critical red flag,revise governance before execution\n"
        "needs_review,high red flag,manual review before execution\n"
        "not_alpha_evidence,governance pass only,do not claim performance\n",
        encoding="utf-8",
    )
    (artifact / "governance_calibration_summary.md").write_text("# Summary\nSpec only.\n", encoding="utf-8")
    return artifact


def test_validate_governance_calibration_passes_valid_artifact(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)

    report = validate_governance_calibration(artifact)

    assert report["status"] == "pass"
    assert report["summary"]["failed"] == 0
    assert any(check["name"] == "taxonomy_hard_constraints_not_performance_requirements" and check["status"] == "pass" for check in report["checks"])
    assert any(check["name"] == "falsifiability_positive_and_negative_outcomes" and check["status"] == "pass" for check in report["checks"])


def test_validate_governance_calibration_fails_if_hard_constraint_blocks_positive_result(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)
    (artifact / "constraint_taxonomy.csv").write_text(
        "constraint,constraint_type,may_block_execution,may_block_positive_result,rationale\n"
        "no_raw_payload_retention,hard_governance,yes,yes,performance leak\n"
        "minimum_gap_threshold,research_design,no,yes,can affect result\n",
        encoding="utf-8",
    )

    report = validate_governance_calibration(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "taxonomy_hard_constraints_not_performance_requirements" and check["status"] == "fail" for check in report["checks"])


def test_validate_governance_calibration_fails_without_positive_negative_outcomes(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)
    (artifact / "falsifiability_checks.csv").write_text(
        "check_id,check,required,pass_condition,interpretation\n"
        "FAL-001,At least one allowed execution path exists after approval/preflight,yes,path exists,not impossible\n"
        "FAL-003,Performance thresholds are not embedded in provider validators,yes,no thresholds,validators do not force failure\n"
        "FAL-004,Research-design parameters can change via new preregistration,yes,new preregistration,learning remains possible\n"
        "FAL-005,At least one synthetic compliant artifact could pass validators without real alpha,yes,governance only,not alpha\n",
        encoding="utf-8",
    )

    report = validate_governance_calibration(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "falsifiability_required_checks" and check["status"] == "fail" for check in report["checks"])
    assert any(check["name"] == "falsifiability_positive_and_negative_outcomes" and check["status"] == "fail" for check in report["checks"])


def test_validate_governance_calibration_fails_without_research_flexibility(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)
    (artifact / "allowed_research_flexibility.csv").write_text(
        "flexibility_item,allowed,mechanism,guardrail\n"
        "parameter_change,no,permanently forbidden,no mutation\n",
        encoding="utf-8",
    )

    report = validate_governance_calibration(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "flexibility_items_allowed" and check["status"] == "fail" for check in report["checks"])
    assert any(check["name"] == "flexibility_new_preregistration_path_exists" and check["status"] == "fail" for check in report["checks"])


def test_governance_calibration_validator_cli_exit_codes(tmp_path: Path) -> None:
    artifact = _valid_artifact(tmp_path)

    assert main(["--artifact-dir", str(artifact)]) == 0

    (artifact / "governance_calibration_manifest.json").unlink()

    assert main(["--artifact-dir", str(artifact)]) == 1
