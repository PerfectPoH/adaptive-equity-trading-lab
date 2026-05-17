from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from experiments.configs.nctrl_trial_001 import RUN_ID, build_static_metadata, run_nctrl_trial_001, write_nctrl_trial_001_property_report_from_artifacts


def _ohlcv(start: float) -> pd.DataFrame:
    index = pd.bdate_range("2023-01-03", periods=280)
    close = pd.Series([start + i * 0.1 for i in range(280)], index=index)
    return pd.DataFrame(
        {
            "Open": close - 0.01,
            "High": close + 0.2,
            "Low": close - 0.2,
            "Close": close,
            "Volume": [1_000_000] * 280,
        },
        index=index,
    )


def test_nctrl_trial_static_metadata_uses_frozen_universe() -> None:
    metadata = build_static_metadata()

    assert metadata["symbol"].tolist() == ["AAPL", "MSFT", "NVDA", "AMD", "TSLA", "META", "AMZN", "GOOGL", "SPY", "QQQ"]
    assert bool(metadata.loc[metadata["symbol"].eq("SPY"), "is_etf"].iloc[0]) is True


def test_run_nctrl_trial_001_writes_trial_accounting_and_property_reports(tmp_path: Path) -> None:
    def fake_downloader(symbol: str, start: str, end: str | None = None) -> pd.DataFrame:
        return _ohlcv(200.0 if symbol in {"IWM", "^VIX"} else 100.0)

    result = run_nctrl_trial_001(output_dir=tmp_path, downloader=fake_downloader, random_simulations=5, bootstrap_simulations=5)

    assert result["run_result"]["run_manifest"]["trial_accounting"]["trial_id"] == "TRIAL-NCTRL-001"
    assert result["run_result"]["run_manifest"]["run_id"] == RUN_ID
    assert result["property_report"]["trial_id"] == "TRIAL-NCTRL-001"
    assert [row["property"] for row in result["property_report"]["properties"]] == ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]
    assert next(row for row in result["property_report"]["properties"] if row["property"] == "P1")["status"] == "pass"
    assert (tmp_path / "property_check_report.md").exists()
    assert (tmp_path / "property_check_report.json").exists()
    assert (tmp_path / "bootstrap_random_baseline.json").exists()
    assert (tmp_path / "random_entry_sign_flip_report.json").exists()
    payload = json.loads((tmp_path / "property_check_report.json").read_text(encoding="utf-8"))
    assert payload == result["property_report"]

    rebuilt = write_nctrl_trial_001_property_report_from_artifacts(tmp_path)
    assert rebuilt["trial_id"] == "TRIAL-NCTRL-001"
    assert next(row for row in rebuilt["properties"] if row["property"] == "P1")["status"] == "pass"
