from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.polygon_delisted_survivorship_audit_001 as audit
from src.experiments.polygon_delisted_survivorship_audit_validator import validate_polygon_delisted_survivorship_audit_gate


SPEC_DIR = Path("experiments/provider_aware_research/polygon_delisted_survivorship_audit_20260524")


def _row(ticker: str, delisted: str = "2024-01-02T05:00:00Z", security_type: str = "CS") -> dict[str, object]:
    return {
        "ticker": ticker,
        "market": "stocks",
        "locale": "us",
        "primary_exchange": "XNAS",
        "type": security_type,
        "active": False,
        "delisted_utc": delisted,
        "cik": "0000000000",
    }


def test_polygon_delisted_survivorship_audit_gate_passes_real_spec() -> None:
    report = validate_polygon_delisted_survivorship_audit_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "POLYGON_DELISTED_SURVIVORSHIP_AUDIT_GATE_PASS"


def test_polygon_delisted_survivorship_audit_gate_fails_if_backtest_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "audit_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["backtest_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_polygon_delisted_survivorship_audit_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "backtest_blocked" and check["status"] == "fail" for check in report["checks"])


def test_assess_delisted_payload_passes_metadata_support_but_not_pit_universe() -> None:
    rows = [_row(f"D{i:04d}") for i in range(350)]

    assessment = audit.assess_polygon_delisted_payload({"results": rows})

    assert assessment["record_count"] == 350
    assert assessment["delisted_common_stock_count"] == 350
    assert assessment["passes_delisted_metadata_support"] is True
    assert assessment["pit_universe_backtest_authorized"] is False
    assert assessment["requires_pit_membership_construction"] is True


def test_assess_delisted_payload_blocks_when_delisted_dates_missing() -> None:
    rows = [_row(f"D{i:04d}", delisted="") for i in range(350)]

    assessment = audit.assess_polygon_delisted_payload({"results": rows})

    assert assessment["passes_delisted_metadata_support"] is False
    assert "delisted_date_coverage_below_0_95" in assessment["blockers"]


def test_run_delisted_audit_writes_clean_artifacts(tmp_path: Path, monkeypatch) -> None:
    rows = [_row(f"D{i:04d}") for i in range(320)]
    monkeypatch.setattr(audit, "_load_polygon_api_key", lambda: "test-key")
    monkeypatch.setattr(audit, "_fetch_polygon_inactive_tickers", lambda api_key, limit: {"results": rows, "status": "OK"})

    decision = audit.run_polygon_delisted_survivorship_audit_001(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = audit.validate_polygon_delisted_survivorship_audit_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "POLYGON_DELISTED_METADATA_SUPPORT_PASS"
    assert decision["backtest_performed"] is False
    assert decision["pit_universe_backtest_authorized"] is False
