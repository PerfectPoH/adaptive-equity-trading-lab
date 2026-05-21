from __future__ import annotations

import json
from pathlib import Path

from src.experiments.xmom_earnings_single_probe_approval_validator import (
    main,
    validate_xmom_earnings_single_probe_approval,
)


ARTIFACT_DIR = Path("experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521")


def test_xmom_earnings_single_probe_approval_validator_passes_real_artifact() -> None:
    report = validate_xmom_earnings_single_probe_approval(ARTIFACT_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "EARNINGS_SINGLE_PROBE_APPROVAL_SPEC_PASS"
    assert report["provider_query_performed"] is False
    assert report["network_call_performed"] is False
    assert report["extractor_implemented"] is False
    assert report["summary"]["failed"] == 0


def test_xmom_earnings_single_probe_approval_validator_fails_if_approval_granted(tmp_path: Path) -> None:
    artifact_dir = _copy_artifact(tmp_path)
    manifest_path = artifact_dir / "single_probe_approval_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["approval_status"] = "granted"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_xmom_earnings_single_probe_approval(artifact_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_separate_approval_not_granted" and check["status"] == "fail" for check in report["checks"])


def test_xmom_earnings_single_probe_approval_validator_fails_if_query_performed(tmp_path: Path) -> None:
    artifact_dir = _copy_artifact(tmp_path)
    manifest_path = artifact_dir / "single_probe_approval_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provider_query_performed"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_xmom_earnings_single_probe_approval(artifact_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution_or_secret_flags" and check["status"] == "fail" for check in report["checks"])


def test_xmom_earnings_single_probe_approval_validator_fails_if_scope_preselects_symbol(tmp_path: Path) -> None:
    artifact_dir = _copy_artifact(tmp_path)
    scope = artifact_dir / "single_probe_scope.csv"
    scope.write_text(
        scope.read_text(encoding="utf-8").replace(
            "symbol,unselected,blocked_until_approval",
            "symbol,CRMD,blocked_until_approval",
        ),
        encoding="utf-8",
    )

    report = validate_xmom_earnings_single_probe_approval(artifact_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "scope_provider_and_symbol_unselected" and check["status"] == "fail" for check in report["checks"])


def test_xmom_earnings_single_probe_approval_validator_fails_if_max_calls_widened(tmp_path: Path) -> None:
    artifact_dir = _copy_artifact(tmp_path)
    scope = artifact_dir / "single_probe_scope.csv"
    scope.write_text(
        scope.read_text(encoding="utf-8").replace(
            "max_provider_calls,1,locked",
            "max_provider_calls,2,locked",
        ),
        encoding="utf-8",
    )

    report = validate_xmom_earnings_single_probe_approval(artifact_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "scope_max_provider_calls_one" and check["status"] == "fail" for check in report["checks"])


def test_xmom_earnings_single_probe_approval_validator_fails_if_raw_payload_allowed(tmp_path: Path) -> None:
    artifact_dir = _copy_artifact(tmp_path)
    schema = artifact_dir / "expected_probe_output_schema.csv"
    schema.write_text(
        schema.read_text(encoding="utf-8").replace(
            "raw_payload_saved,yes,false,not_secret",
            "raw_payload_saved,yes,true,not_secret",
        ),
        encoding="utf-8",
    )

    report = validate_xmom_earnings_single_probe_approval(artifact_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "output_schema_raw_payload_false" and check["status"] == "fail" for check in report["checks"])


def test_xmom_earnings_single_probe_approval_validator_fails_if_probe_unblocked(tmp_path: Path) -> None:
    artifact_dir = _copy_artifact(tmp_path)
    blocked = artifact_dir / "single_probe_blocked_actions.csv"
    blocked.write_text(
        blocked.read_text(encoding="utf-8").replace(
            "execute_probe,blocked",
            "execute_probe,allowed",
        ),
        encoding="utf-8",
    )

    report = validate_xmom_earnings_single_probe_approval(artifact_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "blocked_actions_all_blocked" and check["status"] == "fail" for check in report["checks"])


def test_xmom_earnings_single_probe_approval_validator_cli_exit_codes(tmp_path: Path) -> None:
    artifact_dir = _copy_artifact(tmp_path)
    assert main(["--artifact-dir", str(artifact_dir)]) == 0

    (artifact_dir / "single_probe_blocked_actions.csv").unlink()

    assert main(["--artifact-dir", str(artifact_dir)]) == 1


def _copy_artifact(tmp_path: Path) -> Path:
    target = tmp_path / "single_probe_approval"
    target.mkdir()
    for item in ARTIFACT_DIR.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    return target
