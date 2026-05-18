from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.validation.purged_temporal_split_embargo_validator import (
    PurgedTemporalSplitConfig,
    build_synthetic_labeled_panel,
    main,
    validate_purged_temporal_split_embargo,
)


def test_validate_purged_temporal_split_embargo_passes_on_synthetic_panel() -> None:
    report = validate_purged_temporal_split_embargo()

    assert report["research_id"] == "RESEARCH-062"
    assert report["status"] == "pass"
    assert report["provider_query_performed"] is False
    assert report["market_data_downloaded"] is False
    assert report["backtest_performed"] is False
    assert report["strategy_promotion_performed"] is False
    assert report["summary"]["failed"] == 0


def test_synthetic_panel_contains_multiple_symbols_without_external_data() -> None:
    frame = build_synthetic_labeled_panel(PurgedTemporalSplitConfig(symbols=("AAA", "BBB", "CCC", "DDD")))

    assert sorted(frame["symbol"].unique()) == ["AAA", "BBB", "CCC", "DDD"]
    assert frame["synthetic_fixture"].eq(True).all()
    assert frame.index.min() == pd.Timestamp("2022-12-01")


def test_validate_purged_temporal_split_embargo_records_embargo_and_purge_checks() -> None:
    report = validate_purged_temporal_split_embargo(PurgedTemporalSplitConfig(label_horizon_bars=4, embargo_days=3))
    checks = {check["name"]: check["status"] for check in report["checks"]}

    assert checks["validation_embargo_respected"] == "pass"
    assert checks["test_embargo_respected"] == "pass"
    assert checks["train_label_horizon_purged_by_symbol"] == "pass"
    assert checks["validation_label_horizon_purged_by_symbol"] == "pass"


def test_validate_purged_temporal_split_embargo_rejects_negative_embargo() -> None:
    with pytest.raises(ValueError, match="embargo_days must be non-negative"):
        validate_purged_temporal_split_embargo(PurgedTemporalSplitConfig(embargo_days=-1))


def test_main_writes_output_json(tmp_path: Path, capsys) -> None:
    output_json = tmp_path / "research_062_report.json"

    code = main(["--output-json", str(output_json)])

    captured = capsys.readouterr()
    stdout_report = json.loads(captured.out)
    file_report = json.loads(output_json.read_text(encoding="utf-8"))
    assert code == 0
    assert stdout_report["status"] == "pass"
    assert file_report["decision"] == "PURGED_TEMPORAL_SPLIT_EMBARGO_VALIDATED"
