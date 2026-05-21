from __future__ import annotations

import json
from pathlib import Path

from src.experiments.xmom_earnings_single_probe_explicit_approval_template_validator import (
    main,
    validate_xmom_earnings_single_probe_explicit_approval_template,
)


TEMPLATE_DIR = Path("experiments/provider_aware_research/xmom_earnings_single_probe_explicit_approval_template_20260521")


def test_explicit_approval_template_validator_passes_real_template() -> None:
    report = validate_xmom_earnings_single_probe_explicit_approval_template(TEMPLATE_DIR)

    assert report["status"] == "pass"
    assert report["decision"] == "XMOM_EARNINGS_SINGLE_PROBE_EXPLICIT_APPROVAL_TEMPLATE_PASS"
    assert report["approval_granted"] is False
    assert report["provider_query_performed"] is False
    assert report["summary"]["failed"] == 0


def test_explicit_approval_template_validator_fails_if_marked_granted(tmp_path: Path) -> None:
    template = _copy_template(tmp_path)
    manifest_path = template / "explicit_approval_template_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["status"] = "APPROVAL_GRANTED_FOR_SINGLE_PROBE_PREPARATION"
    manifest["approval_status"] = "granted"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_xmom_earnings_single_probe_explicit_approval_template(template)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_template_identity_not_granted" and check["status"] == "fail" for check in report["checks"])


def test_explicit_approval_template_validator_fails_if_provider_preselected(tmp_path: Path) -> None:
    template = _copy_template(tmp_path)
    manifest_path = template / "explicit_approval_template_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provider"] = "intrinio"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_xmom_earnings_single_probe_explicit_approval_template(template)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_provider_symbol_unresolved" and check["status"] == "fail" for check in report["checks"])


def test_explicit_approval_template_validator_fails_if_raw_payload_allowed(tmp_path: Path) -> None:
    template = _copy_template(tmp_path)
    manifest_path = template / "explicit_approval_template_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["raw_payload_retention_allowed"] = True
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_xmom_earnings_single_probe_explicit_approval_template(template)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution_or_raw_payload" and check["status"] == "fail" for check in report["checks"])


def test_explicit_approval_template_validator_fails_if_action_unblocked(tmp_path: Path) -> None:
    template = _copy_template(tmp_path)
    blocked = template / "blocked_until_approval.csv"
    blocked.write_text(
        blocked.read_text(encoding="utf-8").replace(
            "query_provider,blocked",
            "query_provider,allowed",
        ),
        encoding="utf-8",
    )

    report = validate_xmom_earnings_single_probe_explicit_approval_template(template)

    assert report["status"] == "fail"
    assert any(check["name"] == "blocked_all_actions_blocked" and check["status"] == "fail" for check in report["checks"])


def test_explicit_approval_template_validator_cli_exit_codes(tmp_path: Path) -> None:
    template = _copy_template(tmp_path)
    assert main(["--template-dir", str(template)]) == 0

    (template / "approval_fields_required.csv").unlink()

    assert main(["--template-dir", str(template)]) == 1


def _copy_template(tmp_path: Path) -> Path:
    target = tmp_path / "approval_template"
    target.mkdir()
    for item in TEMPLATE_DIR.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    return target
