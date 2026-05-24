from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.polygon_delisted_listing_date_probe_001 as probe
from src.experiments.polygon_delisted_listing_date_probe_validator import (
    validate_polygon_delisted_listing_date_probe_gate,
)


SPEC_DIR = Path("experiments/provider_aware_research/polygon_delisted_listing_date_probe_20260524")


def test_delisted_listing_date_probe_gate_passes_real_spec() -> None:
    report = validate_polygon_delisted_listing_date_probe_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "POLYGON_DELISTED_LISTING_DATE_PROBE_GATE_PASS"


def test_delisted_listing_date_probe_gate_fails_if_backtest_enabled(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "probe_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["backtest_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_polygon_delisted_listing_date_probe_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "backtest_blocked" and check["status"] == "fail" for check in report["checks"])


def test_assess_delisted_listing_date_payloads_passes_when_coverage_high() -> None:
    payloads = [
        {"results": {"ticker": ticker, "primary_exchange": "XNAS", "type": "CS", "active": False, "list_date": "2010-01-01", "delisted_utc": "2020-01-01T00:00:00Z", "cik": ticker}}
        for ticker in ["AABA", "AAC", "AACQ", "AACT", "AAGR"]
    ]

    assessment = probe.assess_delisted_listing_date_payloads(payloads, expected_tickers=["AABA", "AAC", "AACQ", "AACT", "AAGR"])

    assert assessment["delisted_listing_date_support_passed"] is True
    assert assessment["provider_success_count"] == 5
    assert assessment["list_date_present_count"] == 5
    assert assessment["broad_universe_backtest_allowed"] is False


def test_run_delisted_listing_date_probe_writes_clean_artifacts(tmp_path: Path, monkeypatch) -> None:
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
                "active": False,
                "list_date": "2010-01-01",
                "delisted_utc": "2020-01-01T00:00:00Z",
                "cik": ticker,
            }
        },
    )

    decision = probe.run_polygon_delisted_listing_date_probe_001(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = probe.validate_polygon_delisted_listing_date_probe_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "POLYGON_DELISTED_LISTING_DATE_SUPPORT_PASS"
    assert decision["provider_call_count"] == 5
    assert decision["market_data_downloaded"] is False
    assert decision["backtest_performed"] is False
