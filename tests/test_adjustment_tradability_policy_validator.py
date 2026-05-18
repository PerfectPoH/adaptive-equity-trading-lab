from __future__ import annotations

import json
from pathlib import Path

from src.experiments.adjustment_tradability_policy_validator import main, validate_adjustment_tradability_policy


def _valid_policy_dir(tmp_path: Path) -> Path:
    policy_dir = tmp_path / "policy"
    policy_dir.mkdir()
    manifest = {
        "status": "SPEC_ONLY_NOT_EXECUTED",
        "decision": "ADJUSTMENT_TRADABILITY_POLICY_REQUIRED_BEFORE_PERFORMANCE_RESEARCH",
        "scope": "Provider-aware small-cap research track",
        "purpose": "Define policy gates.",
        "no_provider_query": True,
        "no_backtest": True,
        "no_strategy_promotion": True,
        "required_policy_tables": ["adjustment_tradability_policy.csv"],
    }
    (policy_dir / "adjustment_tradability_policy_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (policy_dir / "adjustment_tradability_policy.csv").write_text(
        "policy_area,current_status,allowed_for_diagnostics,allowed_for_performance,required_before_performance,notes\n"
        "price_adjustment,raw_or_unknown_caveated,yes,no,validated adjustment,notes\n"
        "corporate_actions,crosscheck_only,yes,no,corporate action source,notes\n"
        "halt_tradability,unknown_blocked,limited,no,halt source,notes\n"
        "PIT_universe,frozen_sample_only,yes,no,PIT source,notes\n"
        "licensing_retention,derived_only,yes,conditional,raw license,notes\n"
        "provider_quality_warnings,must_capture_as_caveat,yes,conditional,warning capture,notes\n",
        encoding="utf-8",
    )
    (policy_dir / "policy_stop_conditions.csv").write_text(
        "stop_condition,severity,blocked_work,resolution_required\n"
        "adjustment_policy_unknown_and_performance_requested,critical,backtest,validate adjustment\n"
        "corporate_action_source_missing_for_adjusted_claim,critical,claim,add source\n"
        "halt_tradability_unknown_for_small_cap_execution,critical,paper,add source\n"
        "PIT_universe_missing_for_universe_claim,critical,universe claim,add PIT\n"
        "raw_retention_required_without_license,critical,raw storage,get license\n"
        "provider_quality_warning_ignored,high,promotion,capture warning\n",
        encoding="utf-8",
    )
    (policy_dir / "policy_enforcement_matrix.csv").write_text(
        "research_stage,policy_required,minimum_policy_status,promotion_allowed\n"
        "data_quality_diagnostic,yes,diagnostic_caveats_declared,no\n"
        "fixed_signal_replay,yes,diagnostic_caveats_declared,no\n"
        "new_signal_research,yes,trial_accounting_and_policy_caveats_declared,no\n"
        "portfolio_backtest,yes,performance_policy_gate_passed,no_until_separate_promotion_gate\n"
        "OOS,yes,in_sample_provider_aware_track_passed_and_policy_gate_passed,no_until_separate_promotion_gate\n"
        "paper_live,yes,all_policy_gates_passed_and_promotion_gate_passed,conditional\n",
        encoding="utf-8",
    )
    (policy_dir / "adjustment_tradability_policy_summary.md").write_text("# Summary\nPolicy complete.\n", encoding="utf-8")
    return policy_dir


def test_validate_adjustment_tradability_policy_passes_valid_policy(tmp_path: Path) -> None:
    policy_dir = _valid_policy_dir(tmp_path)

    report = validate_adjustment_tradability_policy(policy_dir)

    assert report["status"] == "pass"
    assert report["policy_dir"] == str(policy_dir)
    assert report["summary"]["failed"] == 0
    assert any(check["name"] == "policy_required_areas" and check["status"] == "pass" for check in report["checks"])
    assert any(check["name"] == "enforcement_promotion_not_silently_allowed" and check["status"] == "pass" for check in report["checks"])


def test_validate_adjustment_tradability_policy_fails_missing_required_file(tmp_path: Path) -> None:
    policy_dir = _valid_policy_dir(tmp_path)
    (policy_dir / "policy_stop_conditions.csv").unlink()

    report = validate_adjustment_tradability_policy(policy_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "required_file:policy_stop_conditions.csv" and check["status"] == "fail" for check in report["checks"])


def test_validate_adjustment_tradability_policy_fails_missing_policy_area(tmp_path: Path) -> None:
    policy_dir = _valid_policy_dir(tmp_path)
    (policy_dir / "adjustment_tradability_policy.csv").write_text(
        "policy_area,current_status,allowed_for_diagnostics,allowed_for_performance,required_before_performance,notes\n"
        "price_adjustment,raw,yes,no,validated adjustment,notes\n",
        encoding="utf-8",
    )

    report = validate_adjustment_tradability_policy(policy_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "policy_required_areas" and check["status"] == "fail" for check in report["checks"])


def test_validate_adjustment_tradability_policy_fails_execution_flags(tmp_path: Path) -> None:
    policy_dir = _valid_policy_dir(tmp_path)
    manifest_path = policy_dir / "adjustment_tradability_policy_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["no_strategy_promotion"] = False
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_adjustment_tradability_policy(policy_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution_flags" and check["status"] == "fail" for check in report["checks"])


def test_adjustment_tradability_policy_validator_cli_exit_codes(tmp_path: Path) -> None:
    policy_dir = _valid_policy_dir(tmp_path)

    assert main(["--policy-dir", str(policy_dir)]) == 0

    (policy_dir / "adjustment_tradability_policy_manifest.json").unlink()

    assert main(["--policy-dir", str(policy_dir)]) == 1
