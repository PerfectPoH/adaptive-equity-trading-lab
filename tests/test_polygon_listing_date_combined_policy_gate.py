from __future__ import annotations

import json
from pathlib import Path

import src.experiments.polygon_listing_date_combined_policy_gate as gate


def test_combined_listing_date_policy_passes_when_all_sample_tickers_have_dates(tmp_path: Path) -> None:
    first = tmp_path / "first.csv"
    second = tmp_path / "second.csv"
    first.write_text(
        "ticker,primary_exchange,type,active,list_date,cik,raw_payload_retained\n"
        "A,XNYS,CS,True,1999-11-18,1,False\n"
        "AA,XNYS,CS,True,2016-10-18,2,False\n",
        encoding="utf-8",
    )
    second.write_text(
        "ticker,primary_exchange,type,active,list_date,cik,raw_payload_retained\n"
        "AAL,XNAS,CS,True,1972-06-01,3,False\n",
        encoding="utf-8",
    )

    report = gate.assess_combined_listing_date_policy([first, second], expected_min_count=3)

    assert report["decision"] == "POLYGON_LISTING_DATE_SAMPLE_COVERAGE_PASS_NO_PIT_UNIVERSE"
    assert report["sample_ticker_count"] == 3
    assert report["list_date_present_count"] == 3
    assert report["provider_query_performed"] is False
    assert report["broad_universe_backtest_allowed"] is False


def test_combined_listing_date_policy_blocks_missing_dates(tmp_path: Path) -> None:
    sample = tmp_path / "sample.csv"
    sample.write_text(
        "ticker,primary_exchange,type,active,list_date,cik,raw_payload_retained\n"
        "A,XNYS,CS,True,,1,False\n",
        encoding="utf-8",
    )

    report = gate.assess_combined_listing_date_policy([sample], expected_min_count=1)

    assert report["decision"] == "POLYGON_LISTING_DATE_SAMPLE_COVERAGE_BLOCKED"
    assert "missing_list_dates_in_combined_sample" in report["blockers"]


def test_run_combined_listing_date_policy_gate_writes_clean_no_query_artifacts(tmp_path: Path) -> None:
    decision = gate.run_polygon_listing_date_combined_policy_gate(
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )
    output_report = gate.validate_polygon_listing_date_combined_policy_gate_output(tmp_path / "out")

    assert output_report["status"] == "pass"
    assert decision["provider_query_performed"] is False
    assert decision["backtest_performed"] is False
    assert decision["broad_universe_backtest_allowed"] is False
    assert decision["strategy_promotion_performed"] is False
    assert (tmp_path / "report.md").is_file()
