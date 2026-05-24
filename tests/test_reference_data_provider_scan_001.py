from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.reference_data_provider_scan_001 as scan
from src.experiments.reference_data_provider_scan_validator import validate_reference_data_provider_scan_gate


SPEC_DIR = Path("experiments/provider_aware_research/reference_data_provider_scan_20260524")


def test_reference_data_provider_scan_gate_passes_real_spec() -> None:
    report = validate_reference_data_provider_scan_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "REFERENCE_DATA_PROVIDER_SCAN_GATE_PASS"


def test_reference_data_provider_scan_gate_fails_if_provider_query_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "scan_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provider_query_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_reference_data_provider_scan_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "provider_query_blocked" and check["status"] == "fail" for check in report["checks"])


def test_score_provider_matrix_ranks_provider_probe_candidates() -> None:
    rows = [
        {
            "provider": "Polygon",
            "pit_membership": "pass",
            "delisted_symbols": "pass",
            "exchange_metadata": "pass",
            "security_type_metadata": "pass",
            "pricing_status": "paid_low",
            "api_probe_feasible": "yes",
        },
        {
            "provider": "SEC company_tickers",
            "pit_membership": "fail",
            "delisted_symbols": "fail",
            "exchange_metadata": "fail",
            "security_type_metadata": "fail",
            "pricing_status": "free",
            "api_probe_feasible": "yes",
        },
    ]

    scored = scan.score_provider_candidates(rows)

    assert scored[0]["provider"] == "Polygon"
    assert scored[0]["gate_status"] == "PROBE_CANDIDATE"
    assert scored[1]["gate_status"] == "BLOCKED_REFERENCE_METADATA_INSUFFICIENT"


def test_run_reference_data_provider_scan_writes_artifacts(tmp_path: Path) -> None:
    decision = scan.run_reference_data_provider_scan_001(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = scan.validate_reference_data_provider_scan_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "REFERENCE_DATA_PROVIDER_SCAN_COMPLETE_PROBE_CANDIDATE_SELECTED"
    assert decision["recommended_next_probe_provider"] == "Polygon/Massive"
    assert decision["provider_query_performed"] is False
    assert decision["backtest_performed"] is False
    assert decision["promotion_allowed"] is False
