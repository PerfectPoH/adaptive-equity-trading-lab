from __future__ import annotations

import json
import shutil
from pathlib import Path

from src.experiments.sec8k_directional_alpha_retirement_validator import (
    validate_sec8k_directional_alpha_retirement,
)


SPEC_DIR = Path("experiments/provider_aware_research/sec8k_directional_alpha_retirement_20260523")


def test_sec8k_directional_alpha_retirement_passes_real_artifact() -> None:
    report = validate_sec8k_directional_alpha_retirement(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "SEC8K_DIRECTIONAL_ALPHA_RETIRED_PASS"
    assert report["summary"]["failed"] == 0


def test_sec8k_directional_alpha_retirement_fails_if_long_only_trial_unblocked(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    manifest_path = spec / "retirement_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["future_sec8k_long_only_directional_trials_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_sec8k_directional_alpha_retirement(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "future_sec8k_long_only_trials_blocked" and check["status"] == "fail" for check in report["checks"])


def _copy_spec(tmp_path: Path) -> Path:
    target = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, target)
    return target
