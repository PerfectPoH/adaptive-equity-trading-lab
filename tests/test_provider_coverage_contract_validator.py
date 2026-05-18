from __future__ import annotations

import json
from pathlib import Path

from src.experiments.provider_coverage_contract_validator import main, validate_provider_coverage_contract


def _valid_contract_dir(tmp_path: Path) -> Path:
    contract_dir = tmp_path / "coverage_contract"
    contract_dir.mkdir()
    manifest = {
        "status": "SPEC_ONLY_NOT_EXECUTED",
        "decision": "PROVIDER_COVERAGE_CONTRACT_REQUIRED_BEFORE_STRATEGY_RUN",
        "scope": "Small-cap provider-aware research track",
        "purpose": "Require explicit coverage assumptions before execution.",
        "no_provider_query": True,
        "no_backtest": True,
        "required_for": ["new_signal_research", "portfolio_backtest"],
        "minimum_contract_tables": ["coverage_contract_template.csv"],
    }
    (contract_dir / "provider_coverage_contract_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (contract_dir / "coverage_contract_schema.csv").write_text(
        "field,required,allowed_or_format,description\n"
        "contract_id,yes,string,Unique identifier\n"
        "provider_combo,yes,string,Provider roles\n"
        "dataset_or_endpoint,yes,string,Dataset used\n"
        "coverage_start,yes,YYYY-MM-DD,Earliest date\n"
        "coverage_end,yes,YYYY-MM-DD or open,Latest date\n"
        "symbol_scope,yes,frozen_list,Symbol scope\n"
        "missingness_policy,yes,fail,Missingness handling\n"
        "adjustment_policy,yes,raw,Adjustment handling\n"
        "corporate_action_policy,yes,validated,Corporate actions\n"
        "halt_tradability_policy,yes,validated,Halt handling\n"
        "PIT_universe_policy,yes,validated,Point in time policy\n"
        "licensing_retention_policy,yes,derived_only,Retention policy\n"
        "provider_quality_warnings,yes,string,Warnings\n"
        "stop_conditions,yes,string,Stop conditions\n"
        "approved_uses,yes,string,Allowed uses\n"
        "blocked_uses,yes,string,Blocked uses\n",
        encoding="utf-8",
    )
    (contract_dir / "coverage_contract_template.csv").write_text(
        "contract_id,provider_combo,dataset_or_endpoint,coverage_start,coverage_end,symbol_scope,missingness_policy,adjustment_policy,corporate_action_policy,halt_tradability_policy,PIT_universe_policy,licensing_retention_policy,provider_quality_warnings,stop_conditions,approved_uses,blocked_uses\n"
        "TEST-CONTRACT,Databento+Polygon,EQUS.MINI,2023-03-28,open,frozen_list,drop_with_log,raw_or_unknown_caveated,crosscheck_only,unknown_blocked,frozen_sample_only,derived_only,warnings_logged,missing_required_window,diagnostics,promotion\n",
        encoding="utf-8",
    )
    (contract_dir / "coverage_validation_checklist.csv").write_text(
        "check,severity,pass_condition,failure_action\n"
        "coverage_dates_declared,critical,dates explicit,block\n"
        "symbol_scope_frozen,critical,symbols frozen,block\n"
        "missingness_policy_declared,critical,policy declared,block\n"
        "adjustment_policy_declared,critical,policy declared,block\n"
        "corporate_action_policy_declared,high,policy declared,caveat\n"
        "halt_tradability_policy_declared,high,policy declared,caveat\n"
        "PIT_universe_policy_declared,critical,policy declared,block\n"
        "licensing_policy_declared,critical,policy declared,block\n"
        "provider_warning_capture,high,warnings logged,block\n"
        "stop_conditions_declared,critical,conditions declared,block\n",
        encoding="utf-8",
    )
    (contract_dir / "coverage_contract_enforcement_policy.csv").write_text(
        "use_case,contract_required,minimum_status\n"
        "data_quality_audit,yes,coverage_contract_complete_with_caveats\n"
        "fixed_signal_replay,yes,coverage_contract_complete_with_caveats\n"
        "new_signal_research,yes,coverage_contract_complete_and_trial_accounting_declared\n"
        "portfolio_backtest,yes,performance_dataset_gate_passed\n"
        "OOS,yes,in_sample_provider_aware_track_completed\n"
        "paper_live_trading,yes,separate_promotion_gate_passed\n",
        encoding="utf-8",
    )
    (contract_dir / "provider_coverage_contract_summary.md").write_text("# Summary\nCoverage contract complete.\n", encoding="utf-8")
    return contract_dir


def test_validate_provider_coverage_contract_passes_valid_contract(tmp_path: Path) -> None:
    contract_dir = _valid_contract_dir(tmp_path)

    report = validate_provider_coverage_contract(contract_dir)

    assert report["status"] == "pass"
    assert report["contract_dir"] == str(contract_dir)
    assert report["summary"]["failed"] == 0
    assert any(check["name"] == "schema_required_contract_fields" and check["status"] == "pass" for check in report["checks"])
    assert any(check["name"] == "template_required_values_populated" and check["status"] == "pass" for check in report["checks"])


def test_validate_provider_coverage_contract_fails_missing_required_file(tmp_path: Path) -> None:
    contract_dir = _valid_contract_dir(tmp_path)
    (contract_dir / "coverage_contract_template.csv").unlink()

    report = validate_provider_coverage_contract(contract_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "required_file:coverage_contract_template.csv" and check["status"] == "fail" for check in report["checks"])


def test_validate_provider_coverage_contract_fails_missing_template_column(tmp_path: Path) -> None:
    contract_dir = _valid_contract_dir(tmp_path)
    (contract_dir / "coverage_contract_template.csv").write_text("contract_id,provider_combo\nTEST,Provider\n", encoding="utf-8")

    report = validate_provider_coverage_contract(contract_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "template_required_columns" and check["status"] == "fail" for check in report["checks"])


def test_validate_provider_coverage_contract_fails_execution_flags(tmp_path: Path) -> None:
    contract_dir = _valid_contract_dir(tmp_path)
    manifest_path = contract_dir / "provider_coverage_contract_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["no_backtest"] = False
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_provider_coverage_contract(contract_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution_flags" and check["status"] == "fail" for check in report["checks"])


def test_provider_coverage_contract_validator_cli_exit_codes(tmp_path: Path) -> None:
    contract_dir = _valid_contract_dir(tmp_path)

    assert main(["--contract-dir", str(contract_dir)]) == 0

    (contract_dir / "provider_coverage_contract_manifest.json").unlink()

    assert main(["--contract-dir", str(contract_dir)]) == 1
