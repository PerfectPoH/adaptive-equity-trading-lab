from __future__ import annotations

import json
from pathlib import Path

from src.experiments.provider_evaluation_artifact_validator import main, validate_provider_evaluation_artifacts


REQUIRED_CSVS = [
    "provider_requirement_table.csv",
    "provider_event_audit_table.csv",
    "raw_responses_manifest.csv",
    "snapshot_hashes.csv",
]


def _valid_provider_eval_dir(tmp_path: Path) -> Path:
    eval_dir = tmp_path / "provider_eval"
    eval_dir.mkdir()
    manifest = {
        "provider_name": "Example Provider",
        "provider_slug": "example_provider",
        "account_type": "free_trial",
        "payment_authorized": False,
        "payment_cap_usd": 0,
        "execution_date": "2026-05-17",
        "operator": "local",
        "frozen_panel_report": "Report-Small-Cap-Data-Provider-Event-Panel-2026-05-17",
        "panel_expansion_report": "Report-Small-Cap-Data-Provider-Event-Panel-Expansion-2026-05-17",
        "terms_url": "https://example.com/terms",
        "license_storage_verdict": "yes",
        "data_retention_allowed": "yes",
        "dataset_names": ["example_prices"],
        "api_versions": ["v1"],
        "query_budget_estimate_usd": 0,
        "actual_query_cost_usd": 0,
        "provider_query_executed": True,
    }
    (eval_dir / "provider_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (eval_dir / "provider_requirement_table.csv").write_text(
        "requirement,status,notes\ndelisted_symbols,pass,ok\n",
        encoding="utf-8",
    )
    (eval_dir / "provider_event_audit_table.csv").write_text(
        "event_id,provider_name,provider_symbol_resolves,historical_identifier_stable,event_window_available,raw_ohlcv_available,adjusted_ohlcv_available,corporate_action_metadata_available,halt_or_suspension_visible,delisted_history_available,point_in_time_universe_supported,licensing_allows_research_storage,pipeline_integration_complexity,severity,verdict,notes\n"
        "DPE-001,Example Provider,yes,yes,yes,yes,yes,yes,not_applicable,yes,partial,yes,medium,low,pass,ok\n"
        "DPE-002,Example Provider,yes,yes,yes,yes,yes,yes,not_applicable,not_applicable,partial,yes,medium,low,pass,ok\n"
        "DPE-003,Example Provider,yes,yes,yes,yes,yes,not_applicable,partial,not_applicable,partial,yes,medium,medium,caveat,halt partial\n"
        "DPE-004,Example Provider,yes,yes,yes,yes,yes,partial,not_applicable,not_applicable,partial,yes,medium,medium,caveat,event join\n"
        "DPE-005,Example Provider,yes,yes,yes,yes,yes,yes,not_applicable,not_applicable,partial,yes,medium,low,pass,ok\n"
        "DPE-006,Example Provider,yes,yes,yes,yes,yes,yes,not_applicable,yes,partial,yes,medium,low,pass,ok\n"
        "DPE-007,Example Provider,yes,yes,yes,yes,yes,yes,not_applicable,not_applicable,partial,yes,medium,low,pass,ok\n"
        "DPE-008,Example Provider,yes,yes,yes,yes,yes,not_applicable,partial,not_applicable,partial,yes,medium,medium,caveat,halt partial\n"
        "DPE-009,Example Provider,yes,yes,yes,yes,yes,partial,not_applicable,not_applicable,partial,yes,medium,medium,caveat,event join\n"
        "DPE-010,Example Provider,yes,yes,yes,yes,yes,yes,not_applicable,not_applicable,partial,yes,medium,low,pass,ok\n",
        encoding="utf-8",
    )
    (eval_dir / "license_notes.md").write_text("# License\nStorage allowed.\n", encoding="utf-8")
    (eval_dir / "query_cost_estimate.md").write_text("# Cost\n0 USD.\n", encoding="utf-8")
    (eval_dir / "raw_responses_manifest.csv").write_text("event_id,path,sha256\nDPE-001,raw/dpe001.json,abc\n", encoding="utf-8")
    (eval_dir / "snapshot_hashes.csv").write_text("path,sha256\nprovider_manifest.json,abc\n", encoding="utf-8")
    (eval_dir / "provider_evaluation_summary.md").write_text("# Summary\nProvider evaluated.\n", encoding="utf-8")
    return eval_dir


def test_validate_provider_evaluation_artifacts_passes_valid_eval_dir(tmp_path: Path) -> None:
    eval_dir = _valid_provider_eval_dir(tmp_path)

    report = validate_provider_evaluation_artifacts(eval_dir)

    assert report["status"] == "pass"
    assert report["evaluation_dir"] == str(eval_dir)
    assert report["summary"]["failed"] == 0
    assert any(check["name"] == "manifest_required_fields" and check["status"] == "pass" for check in report["checks"])
    assert any(check["name"] == "event_panel_complete" and check["status"] == "pass" for check in report["checks"])


def test_validate_provider_evaluation_artifacts_fails_missing_required_file(tmp_path: Path) -> None:
    eval_dir = _valid_provider_eval_dir(tmp_path)
    (eval_dir / "provider_event_audit_table.csv").unlink()

    report = validate_provider_evaluation_artifacts(eval_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "required_file:provider_event_audit_table.csv" and check["status"] == "fail" for check in report["checks"])


def test_validate_provider_evaluation_artifacts_fails_manifest_with_payment_authorized(tmp_path: Path) -> None:
    eval_dir = _valid_provider_eval_dir(tmp_path)
    manifest_path = eval_dir / "provider_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["payment_authorized"] = True
    manifest["payment_cap_usd"] = 125
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_provider_evaluation_artifacts(eval_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_payment_authorized" and check["status"] == "fail" for check in report["checks"])


def test_validate_provider_evaluation_artifacts_fails_incomplete_frozen_panel(tmp_path: Path) -> None:
    eval_dir = _valid_provider_eval_dir(tmp_path)
    event_table = eval_dir / "provider_event_audit_table.csv"
    rows = event_table.read_text(encoding="utf-8").splitlines()
    event_table.write_text("\n".join(rows[:-1]) + "\n", encoding="utf-8")

    report = validate_provider_evaluation_artifacts(eval_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "event_panel_complete" and check["status"] == "fail" for check in report["checks"])


def test_validate_provider_evaluation_artifacts_fails_missing_required_event_columns(tmp_path: Path) -> None:
    eval_dir = _valid_provider_eval_dir(tmp_path)
    (eval_dir / "provider_event_audit_table.csv").write_text("event_id,provider_name\nDPE-001,Example Provider\n", encoding="utf-8")

    report = validate_provider_evaluation_artifacts(eval_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "event_audit_required_columns" and check["status"] == "fail" for check in report["checks"])


def test_provider_evaluation_artifact_validator_cli_exit_codes(tmp_path: Path) -> None:
    eval_dir = _valid_provider_eval_dir(tmp_path)

    assert main(["--evaluation-dir", str(eval_dir)]) == 0

    (eval_dir / "provider_manifest.json").unlink()

    assert main(["--evaluation-dir", str(eval_dir)]) == 1
