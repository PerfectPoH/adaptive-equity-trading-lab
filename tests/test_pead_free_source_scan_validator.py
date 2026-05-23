from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.experiments.pead_free_source_scan_validator import validate_pead_free_source_scan


SCAN_DIR = Path("experiments/provider_aware_research/pead_free_source_scan_20260523")


def test_pead_free_source_scan_passes_real_artifact() -> None:
    report = validate_pead_free_source_scan(SCAN_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "PEAD_FREE_SOURCE_SCAN_PASS"
    assert report["provider_query_performed"] is False
    assert report["summary"]["failed"] == 0


def test_pead_free_source_scan_fails_if_query_authorized(tmp_path: Path) -> None:
    scan = _copy_scan(tmp_path)
    manifest_path = scan / "source_scan_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provider_query_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_pead_free_source_scan(scan)

    assert report["status"] == "fail"
    assert any(check["name"] == "provider_query_blocked" and check["status"] == "fail" for check in report["checks"])


def test_pead_free_source_scan_fails_if_candidate_without_consensus_is_selected(tmp_path: Path) -> None:
    scan = _copy_scan(tmp_path)
    candidates = scan / "candidate_sources.csv"
    candidates.write_text(
        candidates.read_text(encoding="utf-8").replace(
            "SEC EDGAR Companyfacts,rejected",
            "SEC EDGAR Companyfacts,selected",
        ),
        encoding="utf-8",
    )

    report = validate_pead_free_source_scan(scan)

    assert report["status"] == "fail"
    assert any(check["name"] == "selected_candidate_has_required_capabilities" and check["status"] == "fail" for check in report["checks"])


def test_pead_free_source_scan_fails_if_more_than_one_probe_selected(tmp_path: Path) -> None:
    scan = _copy_scan(tmp_path)
    candidates = scan / "candidate_sources.csv"
    candidates.write_text(
        candidates.read_text(encoding="utf-8").replace(
            "Yahoo Finance unofficial,rejected",
            "Yahoo Finance unofficial,selected",
        ),
        encoding="utf-8",
    )

    report = validate_pead_free_source_scan(scan)

    assert report["status"] == "fail"
    assert any(check["name"] == "exactly_one_next_probe_selected" and check["status"] == "fail" for check in report["checks"])


def _copy_scan(tmp_path: Path) -> Path:
    target = tmp_path / "scan"
    shutil.copytree(SCAN_DIR, target)
    return target
