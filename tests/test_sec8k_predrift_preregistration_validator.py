from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.experiments.sec8k_predrift_preregistration_validator import validate_sec8k_predrift_preregistration


SPEC_DIR = Path("experiments/provider_aware_research/sec8k_predrift_preregistration_20260523")


def test_sec8k_predrift_preregistration_passes_real_spec() -> None:
    report = validate_sec8k_predrift_preregistration(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "SEC8K_PREDRIFT_PREREGISTRATION_PASS"
    assert report["summary"]["failed"] == 0


def test_sec8k_predrift_preregistration_fails_if_provider_query_allowed(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    manifest_path = spec / "preregistration_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provider_query_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_sec8k_predrift_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "provider_query_blocked" and check["status"] == "fail" for check in report["checks"])


def test_sec8k_predrift_preregistration_fails_if_mini_panel_reuse_allowed(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    manifest_path = spec / "preregistration_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["invalidated_run_usage"] = "allowed"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_sec8k_predrift_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "invalidated_run_blocked" and check["status"] == "fail" for check in report["checks"])


def _copy_spec(tmp_path: Path) -> Path:
    target = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, target)
    return target
