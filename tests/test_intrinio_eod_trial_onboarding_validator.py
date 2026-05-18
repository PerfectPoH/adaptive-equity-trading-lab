from __future__ import annotations

import json
from pathlib import Path

from src.experiments.intrinio_eod_trial_onboarding_validator import main, validate_intrinio_eod_trial_onboarding


def _write_valid_gate(root: Path) -> Path:
    artifact = root / "intrinio_gate"
    artifact.mkdir()
    (artifact / "intrinio_eod_trial_onboarding_manifest.json").write_text(json.dumps({
        "status": "SPEC_ONLY_INTRINIO_TRIAL_ACTIVE_NOT_QUERIED",
        "decision": "INTRINIO_EOD_TRIAL_ONBOARDING_DEFINED_NOT_EXECUTED",
        "required_env_var": "INTRINIO_API_KEY",
        "provider_query_performed": False,
        "network_call_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "raw_payload_retention_allowed": False,
        "secret_values_disclosed": False,
        "separate_probe_approval_required": True,
        "credential_rotation_required": True,
        "max_first_probe_symbols": 1,
        "max_first_probe_provider_calls": 1,
    }), encoding="utf-8")
    (artifact / "intrinio_trial_terms_checklist.csv").write_text(
        "item,status,requirement\n"
        "trial_active,confirmed_by_provider,trial enabled\n"
        "eod_one_year_history,confirmed_by_provider,one year EOD\n"
        "us_small_cap_coverage,unresolved,confirm\n"
        "delisted_symbol_coverage,unresolved,confirm\n"
        "adjustment_policy,unresolved,confirm\n"
        "raw_retention_rights,unresolved,confirm\n"
        "rate_limits,unresolved,confirm\n"
        "endpoint_selection,unresolved,confirm\n",
        encoding="utf-8",
    )
    (artifact / "intrinio_eod_endpoint_questions.csv").write_text(
        "question_id,question,status\n"
        "Q1,endpoint?,open\nQ2,adjusted?,open\nQ3,small cap?,open\nQ4,delisted?,open\nQ5,retention?,open\nQ6,rate limits?,open\n",
        encoding="utf-8",
    )
    (artifact / "intrinio_credential_policy.csv").write_text(
        "policy,status,requirement\n"
        "credential_source,env_file_or_environment_only,INTRINIO_API_KEY only\n"
        "credential_disclosure,forbidden,no disclosure\n"
        "prior_key_rotation,required_before_query,rotate key\n"
        "credential_preflight,required_before_query,presence only\n"
        "account_page_access,user_only,user retrieves keys\n",
        encoding="utf-8",
    )
    (artifact / "intrinio_probe_budget.csv").write_text(
        "budget_item,value,status\n"
        "first_probe_symbols,1,blocked_until_separate_approval\n"
        "first_probe_provider_calls,1,blocked_until_separate_approval\n"
        "raw_payload_retention,false,required\n"
        "output_raw_response_path,RAW_RESPONSE_RETENTION_NOT_ENABLED,required\n"
        "derived_artifacts,row_count|field_names|payload_sha256|summary_metrics,allowed_if_terms_confirmed\n"
        "backtest,false,forbidden\n"
        "strategy_promotion,false,forbidden\n"
        "paper_live,false,forbidden\n",
        encoding="utf-8",
    )
    (artifact / "intrinio_blocker_register.csv").write_text(
        "blocker,severity,status,resolution_required\n"
        "prior_key_exposed_in_chat,critical,unresolved,rotate key\n"
        "terms_for_derived_artifacts_unknown,high,unresolved,confirm terms\n"
        "endpoint_not_confirmed,high,unresolved,confirm endpoint\n"
        "rate_limits_unknown,medium,unresolved,confirm limits\n"
        "separate_probe_approval_missing,critical,unresolved,approve one probe\n"
        "output_directory_not_created,medium,unresolved,create output\n"
        "trial_ledger_entry_not_created,medium,unresolved,create ledger\n",
        encoding="utf-8",
    )
    (artifact / "intrinio_eod_trial_onboarding_summary.md").write_text("# Summary\n", encoding="utf-8")
    return artifact


def test_validate_intrinio_eod_trial_onboarding_passes_valid_gate(tmp_path: Path) -> None:
    report = validate_intrinio_eod_trial_onboarding(_write_valid_gate(tmp_path))

    assert report["status"] == "pass"
    assert report["provider_query_performed"] is False
    assert report["network_call_performed"] is False
    assert report["secret_values_disclosed"] is False
    assert report["summary"]["failed"] == 0


def test_validate_intrinio_eod_trial_onboarding_requires_no_execution_flags(tmp_path: Path) -> None:
    artifact = _write_valid_gate(tmp_path)
    manifest_path = artifact / "intrinio_eod_trial_onboarding_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["network_call_performed"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_intrinio_eod_trial_onboarding(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution_flags" and check["status"] == "fail" for check in report["checks"])


def test_validate_intrinio_eod_trial_onboarding_requires_credential_rotation_blocker(tmp_path: Path) -> None:
    artifact = _write_valid_gate(tmp_path)
    text = (artifact / "intrinio_blocker_register.csv").read_text(encoding="utf-8")
    (artifact / "intrinio_blocker_register.csv").write_text(text.replace("prior_key_exposed_in_chat", "other_blocker"), encoding="utf-8")

    report = validate_intrinio_eod_trial_onboarding(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "blockers_required_items" and check["status"] == "fail" for check in report["checks"])


def test_validate_intrinio_eod_trial_onboarding_requires_one_call_probe_budget(tmp_path: Path) -> None:
    artifact = _write_valid_gate(tmp_path)
    text = (artifact / "intrinio_probe_budget.csv").read_text(encoding="utf-8")
    (artifact / "intrinio_probe_budget.csv").write_text(text.replace("first_probe_provider_calls,1", "first_probe_provider_calls,2"), encoding="utf-8")

    report = validate_intrinio_eod_trial_onboarding(artifact)

    assert report["status"] == "fail"
    assert any(check["name"] == "budget_first_probe_one_call" and check["status"] == "fail" for check in report["checks"])


def test_main_exits_zero_for_valid_gate(tmp_path: Path, capsys) -> None:
    artifact = _write_valid_gate(tmp_path)

    code = main(["--artifact-dir", str(artifact)])

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert code == 0
    assert report["decision"] == "INTRINIO_EOD_TRIAL_ONBOARDING_GATE_VALID"


def test_validate_intrinio_eod_trial_onboarding_accepts_answered_provider_questions(tmp_path: Path) -> None:
    artifact = _write_valid_gate(tmp_path)
    manifest_path = artifact / "intrinio_eod_trial_onboarding_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "SPEC_ONLY_INTRINIO_TRIAL_INFO_RESOLVED_NOT_QUERIED"
    manifest["decision"] = "INTRINIO_EOD_TRIAL_READY_FOR_ONE_PROBE_PREPARATION_NOT_APPROVED"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    (artifact / "intrinio_trial_terms_checklist.csv").write_text(
        "item,status,requirement\n"
        "trial_active,confirmed_by_provider,trial enabled\n"
        "eod_one_year_history,confirmed_by_provider,one year EOD\n"
        "us_small_cap_coverage,confirmed_by_provider,yes\n"
        "delisted_symbol_coverage,confirmed_by_provider,yes\n"
        "adjustment_policy,confirmed_by_provider,both\n"
        "raw_retention_rights,resolved_for_derived_use_only,derived only\n"
        "rate_limits,confirmed_by_provider,2k/min\n"
        "endpoint_selection,confirmed_by_provider,docs provided\n",
        encoding="utf-8",
    )
    (artifact / "intrinio_eod_endpoint_questions.csv").write_text(
        "question_id,question,status,provider_answer\n"
        "Q1,endpoint?,answered,docs\nQ2,adjusted?,answered,both\nQ3,small cap?,answered,yes\nQ4,delisted?,answered,yes\nQ5,retention?,answered,derived only\nQ6,rate limits?,answered,2k/min\n",
        encoding="utf-8",
    )
    (artifact / "intrinio_blocker_register.csv").write_text(
        "blocker,severity,status,resolution_required\n"
        "prior_key_exposed_in_chat,critical,unresolved,rotate key\n"
        "terms_for_derived_artifacts_unknown,high,resolved,derived only\n"
        "endpoint_not_confirmed,high,resolved,docs\n"
        "rate_limits_unknown,medium,resolved,2k/min\n"
        "separate_probe_approval_missing,critical,unresolved,approve one probe\n"
        "output_directory_not_created,medium,unresolved,create output\n"
        "trial_ledger_entry_not_created,medium,unresolved,create ledger\n",
        encoding="utf-8",
    )

    report = validate_intrinio_eod_trial_onboarding(artifact)

    assert report["status"] == "pass"
    assert any(check["name"] == "blockers_critical_probe_guards_unresolved" and check["status"] == "pass" for check in report["checks"])

