from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.polygon_listing_date_coverage_continuation_001 as probe
from src.experiments.polygon_listing_date_coverage_continuation_validator import (
    validate_polygon_listing_date_coverage_continuation_gate,
)


SPEC_DIR = Path("experiments/provider_aware_research/polygon_listing_date_coverage_continuation_20260524")


def test_polygon_listing_date_coverage_continuation_gate_passes_real_spec() -> None:
    report = validate_polygon_listing_date_coverage_continuation_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "POLYGON_LISTING_DATE_COVERAGE_CONTINUATION_GATE_PASS"


def test_polygon_listing_date_coverage_continuation_gate_fails_if_delay_removed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "probe_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["min_seconds_between_calls"] = 0
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_polygon_listing_date_coverage_continuation_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "rate_limit_delay" and check["status"] == "fail" for check in report["checks"])


def test_assess_continuation_passes_when_all_remaining_have_list_dates() -> None:
    payloads = [
        {"results": {"ticker": ticker, "primary_exchange": "XNAS", "type": "CS", "active": True, "list_date": "2020-01-01", "cik": ticker}}
        for ticker in ["AAL", "AAME", "AAMI", "AAOI", "AAON"]
    ]

    assessment = probe.assess_continuation_listing_date_coverage(payloads, expected_tickers=["AAL", "AAME", "AAMI", "AAOI", "AAON"])

    assert assessment["continuation_passed"] is True
    assert assessment["provider_success_count"] == 5
    assert assessment["list_date_present_count"] == 5
    assert assessment["broad_universe_backtest_allowed"] is False


def test_run_continuation_writes_clean_artifacts_without_sleep_in_tests(tmp_path: Path, monkeypatch) -> None:
    tickers = ["AAL", "AAME", "AAMI", "AAOI", "AAON"]
    monkeypatch.setattr(probe, "_load_polygon_api_key", lambda: "test-key")
    monkeypatch.setattr(probe, "_sleep_between_calls", lambda seconds: None)
    monkeypatch.setattr(
        probe,
        "_fetch_polygon_ticker_details",
        lambda api_key, ticker: {
            "results": {
                "ticker": ticker,
                "primary_exchange": "XNAS",
                "type": "CS",
                "active": True,
                "list_date": "2020-01-01",
                "cik": ticker,
            }
        },
    )

    decision = probe.run_polygon_listing_date_coverage_continuation_001(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = probe.validate_polygon_listing_date_coverage_continuation_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "POLYGON_LISTING_DATE_COVERAGE_CONTINUATION_PASS"
    assert decision["provider_call_count"] == len(tickers)
    assert decision["backtest_performed"] is False
