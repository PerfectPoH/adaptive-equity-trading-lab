from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.polygon_listing_date_coverage_probe_001 as probe
from src.experiments.polygon_listing_date_coverage_probe_validator import (
    validate_polygon_listing_date_coverage_probe_gate,
)


SPEC_DIR = Path("experiments/provider_aware_research/polygon_listing_date_coverage_probe_20260524")


def test_polygon_listing_date_coverage_gate_passes_real_spec() -> None:
    report = validate_polygon_listing_date_coverage_probe_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "POLYGON_LISTING_DATE_COVERAGE_PROBE_GATE_PASS"


def test_polygon_listing_date_coverage_gate_fails_if_call_bound_expands(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "probe_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["expected_max_calls"] = 11
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_polygon_listing_date_coverage_probe_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "ten_call_bound" and check["status"] == "fail" for check in report["checks"])


def test_assess_listing_date_coverage_passes_when_coverage_high() -> None:
    payloads = [
        {"results": {"ticker": f"T{i}", "primary_exchange": "XNAS", "type": "CS", "active": True, "list_date": "2020-01-01", "cik": str(i)}}
        for i in range(8)
    ] + [
        {"results": {"ticker": "T8", "primary_exchange": "XNAS", "type": "CS", "active": True}},
        {"results": {"ticker": "T9", "primary_exchange": "XNAS", "type": "CS", "active": True, "list_date": "2021-01-01", "cik": "9"}},
    ]

    assessment = probe.assess_listing_date_coverage(payloads, expected_tickers=[f"T{i}" for i in range(10)])

    assert assessment["listing_date_coverage_passed"] is True
    assert assessment["detail_success_count"] == 10
    assert assessment["list_date_present_count"] == 9
    assert assessment["list_date_coverage"] == 0.9
    assert assessment["broad_universe_backtest_allowed"] is False


def test_assess_listing_date_coverage_blocks_when_coverage_low() -> None:
    payloads = [
        {"results": {"ticker": f"T{i}", "primary_exchange": "XNAS", "type": "CS", "active": True}}
        for i in range(10)
    ]

    assessment = probe.assess_listing_date_coverage(payloads, expected_tickers=[f"T{i}" for i in range(10)])

    assert assessment["listing_date_coverage_passed"] is False
    assert "list_date_coverage_below_0_80" in assessment["blockers"]


def test_run_polygon_listing_date_coverage_probe_writes_clean_artifacts(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(probe, "_load_polygon_api_key", lambda: "test-key")
    tickers = [f"T{i}" for i in range(10)]
    monkeypatch.setattr(probe, "_load_probe_tickers", lambda manifest: tickers)
    monkeypatch.setattr(
        probe,
        "_fetch_polygon_ticker_details",
        lambda api_key, ticker: {
            "results": {
                "ticker": ticker,
                "primary_exchange": "XNYS",
                "type": "CS",
                "active": True,
                "list_date": "1999-11-18",
                "cik": "0001090872",
            }
        },
    )

    decision = probe.run_polygon_listing_date_coverage_probe_001(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = probe.validate_polygon_listing_date_coverage_probe_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "POLYGON_LISTING_DATE_COVERAGE_SUPPORT_PASS"
    assert decision["provider_call_count"] == 10
    assert decision["backtest_performed"] is False
    assert decision["broad_universe_backtest_allowed"] is False
