from __future__ import annotations

import json
from pathlib import Path

from src.experiments.xmom_earnings_provider_selection_validator import (
    main,
    validate_xmom_earnings_provider_selection,
)


GATE_DIR = Path("experiments/provider_aware_research/xmom_earnings_provider_selection_gate_20260521")


def test_xmom_earnings_provider_selection_validator_passes_real_gate() -> None:
    report = validate_xmom_earnings_provider_selection(GATE_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "EARNINGS_PROVIDER_SELECTION_GATE_PASS"
    assert report["provider_query_performed"] is False
    assert report["extractor_implemented"] is False
    assert report["summary"]["failed"] == 0


def test_xmom_earnings_provider_selection_validator_fails_if_query_enabled(tmp_path: Path) -> None:
    gate_dir = _copy_gate(tmp_path)
    manifest_path = gate_dir / "earnings_provider_selection_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["no_provider_query"] = False
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    report = validate_xmom_earnings_provider_selection(gate_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "manifest_no_execution_or_query_flags" and check["status"] == "fail" for check in report["checks"])


def test_xmom_earnings_provider_selection_validator_fails_if_unspecified_allowed(tmp_path: Path) -> None:
    gate_dir = _copy_gate(tmp_path)
    policy = gate_dir / "coverage_quality_policy.csv"
    policy.write_text(
        policy.read_text(encoding="utf-8").replace(
            "dmt_policy,locked,purge,during-market releases excluded from ECDF discovery,purge_event",
            "dmt_policy,locked,allow,during-market releases excluded from ECDF discovery,purge_event",
        ),
        encoding="utf-8",
    )

    report = validate_xmom_earnings_provider_selection(gate_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "quality_reaction_session_policy" and check["status"] == "fail" for check in report["checks"])


def test_xmom_earnings_provider_selection_validator_fails_if_scope_widened(tmp_path: Path) -> None:
    gate_dir = _copy_gate(tmp_path)
    policy = gate_dir / "coverage_quality_policy.csv"
    policy.write_text(
        policy.read_text(encoding="utf-8").replace(
            "earnings_scope,locked,earnings_only",
            "earnings_scope,locked,universal_anomaly_days",
        ),
        encoding="utf-8",
    )

    report = validate_xmom_earnings_provider_selection(gate_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "quality_earnings_only_scope" and check["status"] == "fail" for check in report["checks"])


def test_xmom_earnings_provider_selection_validator_fails_if_primary_provider_preselected(tmp_path: Path) -> None:
    gate_dir = _copy_gate(tmp_path)
    roles = gate_dir / "candidate_provider_roles.csv"
    roles.write_text(
        roles.read_text(encoding="utf-8").replace(
            "primary_earnings_calendar,unselected",
            "primary_earnings_calendar,selected",
        ),
        encoding="utf-8",
    )

    report = validate_xmom_earnings_provider_selection(gate_dir)

    assert report["status"] == "fail"
    assert any(check["name"] == "roles_primary_not_preselected" and check["status"] == "fail" for check in report["checks"])


def test_xmom_earnings_provider_selection_validator_cli_exit_codes(tmp_path: Path) -> None:
    gate_dir = _copy_gate(tmp_path)
    assert main(["--gate-dir", str(gate_dir)]) == 0

    (gate_dir / "blocked_actions.csv").unlink()

    assert main(["--gate-dir", str(gate_dir)]) == 1


def _copy_gate(tmp_path: Path) -> Path:
    target = tmp_path / "earnings_provider_gate"
    target.mkdir()
    for item in GATE_DIR.iterdir():
        target.joinpath(item.name).write_text(item.read_text(encoding="utf-8"), encoding="utf-8")
    return target
