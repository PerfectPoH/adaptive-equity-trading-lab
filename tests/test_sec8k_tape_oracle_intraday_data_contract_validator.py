from __future__ import annotations

from pathlib import Path

from src.experiments.sec8k_tape_oracle_intraday_data_contract_validator import (
    main,
    validate_sec8k_tape_oracle_intraday_data_contract,
)


CONTRACT_DIR = Path("experiments/provider_aware_research/sec8k_tape_oracle_intraday_data_contract_gate_20260522")


def test_sec8k_tape_oracle_intraday_data_contract_passes_real_artifact() -> None:
    report = validate_sec8k_tape_oracle_intraday_data_contract(CONTRACT_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "SEC8K_TAPE_ORACLE_INTRADAY_DATA_CONTRACT_PASS"
    assert report["summary"]["failed"] == 0


def test_sec8k_tape_oracle_intraday_data_contract_fails_if_provider_selected(tmp_path: Path) -> None:
    contract = _copy_contract(tmp_path)
    manifest = contract / "intraday_data_contract_manifest.json"
    manifest.write_text(manifest.read_text(encoding="utf-8").replace('"provider_selected": false', '"provider_selected": true'), encoding="utf-8")

    report = validate_sec8k_tape_oracle_intraday_data_contract(contract)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution_flags" and check["status"] == "fail" for check in report["checks"])


def test_sec8k_tape_oracle_intraday_data_contract_fails_if_oracle_window_changes(tmp_path: Path) -> None:
    contract = _copy_contract(tmp_path)
    oracle = contract / "oracle_window_policy.csv"
    oracle.write_text(oracle.read_text(encoding="utf-8").replace("oracle_end,required,09:45 America/New_York", "oracle_end,required,10:00 America/New_York"), encoding="utf-8")

    report = validate_sec8k_tape_oracle_intraday_data_contract(contract)

    assert report["status"] == "fail"
    assert any(check["name"] == "oracle_end_locked" and check["status"] == "fail" for check in report["checks"])


def test_sec8k_tape_oracle_intraday_data_contract_fails_if_cost_model_weakened(tmp_path: Path) -> None:
    contract = _copy_contract(tmp_path)
    costs = contract / "execution_cost_proxy_requirements.csv"
    costs.write_text(costs.read_text(encoding="utf-8").replace("cost_model_bps,required,500 bps round-trip minimum", "cost_model_bps,required,50 bps round-trip minimum"), encoding="utf-8")

    report = validate_sec8k_tape_oracle_intraday_data_contract(contract)

    assert report["status"] == "fail"
    assert any(check["name"] == "costs_500bps_required" and check["status"] == "fail" for check in report["checks"])


def test_sec8k_tape_oracle_intraday_data_contract_cli_exit_codes(tmp_path: Path) -> None:
    contract = _copy_contract(tmp_path)
    assert main(["--contract-dir", str(contract)]) == 0

    (contract / "oracle_window_policy.csv").unlink()

    assert main(["--contract-dir", str(contract)]) == 1


def _copy_contract(tmp_path: Path) -> Path:
    target = tmp_path / "contract"
    target.mkdir()
    for item in CONTRACT_DIR.iterdir():
        target.joinpath(item.name).write_bytes(item.read_bytes())
    return target
