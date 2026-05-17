from __future__ import annotations

from pathlib import Path

from src.analysis.nctrl_property_report import NctrlPropertyCheckResult, build_nctrl_property_check_report, write_nctrl_property_check_report_markdown


def test_build_nctrl_property_check_report_preserves_property_order_and_binary_status() -> None:
    checks = [
        NctrlPropertyCheckResult(property_id="P1", status="pass", evidence="closed_trades=32", notes="sample-size met"),
        NctrlPropertyCheckResult(property_id="P2", status="fail", evidence="strategy_gt_random=false", notes="negative control failed"),
    ]

    report = build_nctrl_property_check_report("TRIAL-NCTRL-001", checks)

    assert report["trial_id"] == "TRIAL-NCTRL-001"
    assert report["overall_status"] == "fail"
    assert report["properties"] == [
        {"property": "P1", "status": "pass", "evidence": "closed_trades=32", "notes": "sample-size met"},
        {"property": "P2", "status": "fail", "evidence": "strategy_gt_random=false", "notes": "negative control failed"},
    ]


def test_build_nctrl_property_check_report_marks_insufficient_evidence_without_passing() -> None:
    checks = [NctrlPropertyCheckResult(property_id="P1", status="insufficient_evidence", evidence="closed_trades=12", notes="< 30 stop rule")]

    report = build_nctrl_property_check_report("TRIAL-NCTRL-001", checks)

    assert report["overall_status"] == "insufficient_evidence"
    assert report["properties"][0]["status"] == "insufficient_evidence"


def test_write_nctrl_property_check_report_markdown_includes_required_table(tmp_path: Path) -> None:
    output_path = tmp_path / "nctrl_property_report.md"
    checks = [NctrlPropertyCheckResult(property_id="P4", status="pass", evidence="cash ledger fixtures green", notes="29 targeted tests")]

    report = write_nctrl_property_check_report_markdown("TRIAL-NCTRL-001", checks, output_path)

    content = output_path.read_text(encoding="utf-8")
    assert report["overall_status"] == "pass"
    assert "# TRIAL-NCTRL-001 Property Check Report" in content
    assert "| Property | Status | Evidence | Notes |" in content
    assert "| P4 | pass | cash ledger fixtures green | 29 targeted tests |" in content
