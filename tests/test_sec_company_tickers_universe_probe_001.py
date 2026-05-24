from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.sec_company_tickers_universe_probe_001 as probe
from src.experiments.sec_company_tickers_universe_probe_validator import validate_sec_company_tickers_universe_probe_gate


SPEC_DIR = Path("experiments/provider_aware_research/sec_company_tickers_universe_probe_20260524")


def test_sec_company_tickers_universe_probe_gate_passes_real_spec() -> None:
    report = validate_sec_company_tickers_universe_probe_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "SEC_COMPANY_TICKERS_UNIVERSE_PROBE_GATE_PASS"


def test_sec_company_tickers_universe_probe_gate_fails_if_backtest_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "probe_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["backtest_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_sec_company_tickers_universe_probe_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "backtest_blocked" and check["status"] == "fail" for check in report["checks"])


def test_assess_sec_company_tickers_payload_detects_current_only_metadata_gap() -> None:
    payload = {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
    }

    assessment = probe.assess_sec_company_tickers_payload(payload)

    assert assessment["record_count"] == 2
    assert assessment["has_ticker"] is True
    assert assessment["has_cik"] is True
    assert assessment["has_exchange"] is False
    assert assessment["has_security_type"] is False
    assert assessment["has_active_windows"] is False
    assert assessment["has_delisted_symbols"] is False
    assert assessment["passes_universe_gate_requirements"] is False
    assert "missing_point_in_time_membership" in assessment["blockers"]


def test_run_probe_writes_blocked_artifacts_with_monkeypatched_payload(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        probe,
        "_fetch_sec_company_tickers",
        lambda: {
            "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
            "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp"},
        },
    )

    decision = probe.run_sec_company_tickers_universe_probe_001(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = probe.validate_sec_company_tickers_universe_probe_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "SEC_COMPANY_TICKERS_UNIVERSE_SOURCE_BLOCKED_METADATA_INSUFFICIENT"
    assert decision["provider_query_performed"] is True
    assert decision["raw_payload_retained"] is False
    assert decision["backtest_performed"] is False
    assert (tmp_path / "out" / "derived_universe_sample.csv").is_file()
