from __future__ import annotations

from pathlib import Path

from src.experiments.gaprev_intraday_data_contract_validator import (
    main,
    validate_gaprev_intraday_data_contract,
)


CONTRACT_DIR = Path("experiments/provider_aware_research/gap_down_reversion_intraday_data_contract_gate_20260521")


def test_gaprev_intraday_data_contract_passes_real_artifact() -> None:
    report = validate_gaprev_intraday_data_contract(CONTRACT_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "GAPREV_INTRADAY_DATA_CONTRACT_PASS"
    assert report["summary"]["failed"] == 0


def test_gaprev_intraday_data_contract_fails_if_provider_selected(tmp_path: Path) -> None:
    contract = _copy_contract(tmp_path)
    manifest = contract / "intraday_data_contract_manifest.json"
    manifest.write_text(manifest.read_text(encoding="utf-8").replace('"provider_selected": false', '"provider_selected": true'), encoding="utf-8")

    report = validate_gaprev_intraday_data_contract(contract)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution_flags" and check["status"] == "fail" for check in report["checks"])


def test_gaprev_intraday_data_contract_fails_if_core_bar_field_not_required(tmp_path: Path) -> None:
    contract = _copy_contract(tmp_path)
    schema = contract / "bar_schema_requirements.csv"
    schema.write_text(schema.read_text(encoding="utf-8").replace("volume,yes", "volume,no"), encoding="utf-8")

    report = validate_gaprev_intraday_data_contract(contract)

    assert report["status"] == "fail"
    assert any(check["name"] == "schema_core_fields_required" and check["status"] == "fail" for check in report["checks"])


def test_gaprev_intraday_data_contract_fails_if_backtest_unblocked(tmp_path: Path) -> None:
    contract = _copy_contract(tmp_path)
    blocked = contract / "blocked_actions.csv"
    blocked.write_text(blocked.read_text(encoding="utf-8").replace("execute_backtest,blocked", "execute_backtest,allowed"), encoding="utf-8")

    report = validate_gaprev_intraday_data_contract(contract)

    assert report["status"] == "fail"
    assert any(check["name"] == "blocked_all_blocked" and check["status"] == "fail" for check in report["checks"])


def test_gaprev_intraday_data_contract_cli_exit_codes(tmp_path: Path) -> None:
    contract = _copy_contract(tmp_path)
    assert main(["--contract-dir", str(contract)]) == 0

    (contract / "calendar_and_session_policy.csv").unlink()

    assert main(["--contract-dir", str(contract)]) == 1


def _copy_contract(tmp_path: Path) -> Path:
    target = tmp_path / "contract"
    target.mkdir()
    for item in CONTRACT_DIR.iterdir():
        target.joinpath(item.name).write_bytes(item.read_bytes())
    return target
