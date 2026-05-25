from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.experiments.delisted_data_source_gate_validator import main, validate_delisted_data_source_gate


SPEC_DIR = Path("experiments/provider_aware_research/delisted_data_source_gate_20260525")


def test_delisted_data_source_gate_passes_real_spec() -> None:
    report = validate_delisted_data_source_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "DELISTED_DATA_SOURCE_GATE_READY_NOT_EXECUTABLE"
    assert any(check["name"] == "candidate_matrix_has_admissible_source" and check["status"] == "pass" for check in report["checks"])


def test_delisted_data_source_gate_fails_if_execution_is_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "gate"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "delisted_data_source_gate_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["backtest_allowed"] = True
    manifest["market_data_download_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_delisted_data_source_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution_flags" and check["status"] == "fail" for check in report["checks"])


def test_delisted_data_source_gate_requires_survivorship_free_price_source(tmp_path: Path) -> None:
    spec = tmp_path / "gate"
    shutil.copytree(SPEC_DIR, spec)
    matrix_path = spec / "candidate_source_matrix.csv"
    text = matrix_path.read_text(encoding="utf-8")
    text = text.replace(",pass,pass,pass,pass,pass,pass,pass,admissible,", ",pass,fail,pass,pass,pass,pass,pass,blocked,")
    matrix_path.write_text(text, encoding="utf-8")

    report = validate_delisted_data_source_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "candidate_matrix_has_admissible_source" and check["status"] == "fail" for check in report["checks"])


def test_delisted_data_source_gate_cli_exit_codes() -> None:
    assert main(["--spec-dir", str(SPEC_DIR)]) == 0
