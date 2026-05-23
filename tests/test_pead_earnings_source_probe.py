from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.pead_earnings_source_probe_runner as runner
from src.experiments.pead_earnings_source_probe_gate_validator import validate_pead_earnings_source_probe_gate


SPEC_DIR = Path("experiments/provider_aware_research/pead_earnings_source_probe_gate_20260523")


def test_pead_earnings_source_probe_gate_passes_real_spec() -> None:
    report = validate_pead_earnings_source_probe_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "PEAD_EARNINGS_SOURCE_PROBE_GATE_PASS"


def test_pead_earnings_source_probe_gate_fails_if_backtest_allowed(tmp_path: Path) -> None:
    spec = _copy_spec(tmp_path)
    manifest_path = spec / "probe_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["backtest_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_pead_earnings_source_probe_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "backtest_blocked" and check["status"] == "fail" for check in report["checks"])


def test_pead_source_probe_blocks_without_api_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(runner, "_load_intrinio_api_key", lambda: "")

    decision = runner.run_pead_earnings_source_probe(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )

    assert decision["status"] == "blocked"
    assert decision["decision"] == "BLOCKED_EARNINGS_SOURCE_API_KEY_MISSING"
    assert decision["provider_query_performed"] is False


def test_pead_source_probe_detects_complete_payload_candidate(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(runner, "_load_intrinio_api_key", lambda: "test-key")
    monkeypatch.setattr(
        runner,
        "_fetch_json",
        lambda url: {
            "expected_earnings": [
                {
                    "ticker": "CRMD",
                    "expected_date": "2024-05-09",
                    "expected_8k_at": "2024-05-09T12:00:00Z",
                    "actual_eps": "0.10",
                    "consensus_eps": "0.01",
                    "updated_at": "2024-05-08T20:00:00Z",
                }
            ]
        },
    )

    decision = runner.run_pead_earnings_source_probe(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )

    assert decision["decision"] == "PEAD_SOURCE_CANDIDATE"
    assert decision["provider_query_performed"] is True
    assert decision["raw_payload_retained"] is False
    assert decision["backtest_performed"] is False


def test_pead_source_probe_blocks_payload_without_consensus(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(runner, "_load_intrinio_api_key", lambda: "test-key")
    monkeypatch.setattr(runner, "_fetch_json", lambda url: {"expected_earnings": [{"expected_date": "2024-05-09", "actual_eps": "0.10"}]})

    decision = runner.run_pead_earnings_source_probe(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )

    assert decision["decision"] == "BLOCKED_EARNINGS_SOURCE_INSUFFICIENT"
    assert "consensus_eps_missing" in decision["blockers"]


def _copy_spec(tmp_path: Path) -> Path:
    target = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, target)
    return target
