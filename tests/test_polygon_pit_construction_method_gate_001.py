from __future__ import annotations

import json
import shutil
from pathlib import Path

import src.experiments.polygon_pit_construction_method_gate_001 as gate
from src.experiments.polygon_pit_construction_method_gate_validator import (
    validate_polygon_pit_construction_method_gate,
)


SPEC_DIR = Path("experiments/provider_aware_research/polygon_pit_construction_method_gate_20260524")


def test_polygon_pit_construction_method_gate_passes_real_spec() -> None:
    report = validate_polygon_pit_construction_method_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "POLYGON_PIT_CONSTRUCTION_METHOD_GATE_PASS"


def test_polygon_pit_construction_method_gate_fails_if_backtest_enabled(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "method_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["broad_universe_backtest_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_polygon_pit_construction_method_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "broad_backtest_blocked" and check["status"] == "fail" for check in report["checks"])


def test_is_member_asof_uses_listing_and_delisting_dates() -> None:
    assert gate.is_member_asof({"list_date": "2020-01-01", "delisted_date": ""}, "2024-01-02") is True
    assert gate.is_member_asof({"list_date": "2025-01-01", "delisted_date": ""}, "2024-01-02") is False
    assert gate.is_member_asof({"list_date": "2020-01-01", "delisted_date": "2023-12-31"}, "2024-01-02") is False
    assert gate.is_member_asof({"list_date": "2020-01-01", "delisted_date": "2024-01-02"}, "2024-01-02") is False


def test_build_pit_membership_sample_marks_active_and_delisted_members() -> None:
    listing_rows = [
        {"ticker": "LIVE", "list_date": "2020-01-01", "primary_exchange": "XNAS", "type": "CS", "active": "True", "cik": "1"},
        {"ticker": "NEW", "list_date": "2025-01-01", "primary_exchange": "XNAS", "type": "CS", "active": "True", "cik": "2"},
    ]
    delisted_rows = [
        {"ticker": "OLD", "list_date": "2010-01-01", "delisted_date": "2021-01-01", "primary_exchange": "XNYS", "type": "CS", "active": "False", "cik": "3"},
        {"ticker": "PASTLIVE", "list_date": "2010-01-01", "delisted_date": "2025-01-01", "primary_exchange": "XNYS", "type": "CS", "active": "False", "cik": "4"},
    ]

    rows = gate.build_pit_membership_sample(listing_rows, delisted_rows, as_of_dates=["2024-01-02"])

    members = {row["ticker"] for row in rows if row["as_of_date"] == "2024-01-02" and row["is_member"] == "True"}
    assert members == {"LIVE", "PASTLIVE"}


def test_build_pit_membership_sample_excludes_delisted_rows_without_listing_dates() -> None:
    rows = gate.build_pit_membership_sample(
        listing_rows=[],
        delisted_rows=[
            {"ticker": "UNKNOWN", "delisted_date": "2025-01-01", "primary_exchange": "XNAS", "type": "CS", "active": "False", "cik": "1"}
        ],
        as_of_dates=["2024-01-02"],
    )

    assert rows == []


def test_run_pit_construction_method_gate_writes_no_query_no_backtest_artifacts(tmp_path: Path) -> None:
    decision = gate.run_polygon_pit_construction_method_gate_001(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    report = gate.validate_polygon_pit_construction_method_gate_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "POLYGON_PIT_CONSTRUCTION_METHOD_APPROVED_PARTIAL_SAMPLE_ONLY"
    assert "delisted_listing_dates_unavailable_for_full_pit" in decision["broad_backtest_blockers"]
    assert decision["provider_query_performed"] is False
    assert decision["market_data_downloaded"] is False
    assert decision["backtest_performed"] is False
    assert decision["broad_universe_backtest_allowed"] is False
