from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

import src.experiments.sec8k_tape_oracle_existing_intraday_backtest as bt
from src.experiments.sec8k_tape_oracle_existing_intraday_backtest import (
    discover_existing_intraday_cases,
    evaluate_case,
    run_existing_intraday_backtest,
    validate_existing_intraday_backtest,
)


def test_discover_existing_intraday_cases_only_keeps_sec8k_matches(tmp_path: Path) -> None:
    event_panel = pd.DataFrame(
        [
            {"symbol": "AAA", "reaction_session_date": "2026-01-05", "status": "event"},
            {"symbol": "BBB", "reaction_session_date": "2026-01-06", "status": "control"},
        ]
    )
    _write_case(tmp_path, "AAA_2026-01-05")
    _write_case(tmp_path, "BBB_2026-01-06")

    cases = discover_existing_intraday_cases(event_panel, tmp_path)

    assert len(cases) == 1
    assert cases[0]["symbol"] == "AAA"
    assert cases[0]["event_date"] == "2026-01-05"


def test_evaluate_case_generates_positive_oracle_trade_when_first15_tape_confirms(tmp_path: Path) -> None:
    bars = _synthetic_bars("AAA", "2026-01-02", "2026-01-05", event_positive=True)
    case_dir = tmp_path / "AAA_2026-01-05"
    case_dir.mkdir()
    bars.to_csv(case_dir / "bars.csv", index=False)

    result = evaluate_case({"symbol": "AAA", "event_date": "2026-01-05", "bars_path": str(case_dir / "bars.csv")})

    assert result["positive_oracle_candidate"] is True
    assert result["gross_return"] > 0
    assert result["net_return_after_500bps"] == pytest.approx(result["gross_return"] - 0.05)


def test_real_existing_intraday_backtest_runs_without_provider_query(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bt, "OUTPUT_DIR", tmp_path / "out")
    monkeypatch.setattr(bt, "VAULT_REPORT", tmp_path / "report.md")
    monkeypatch.setattr(bt, "VAULT_DEVLOG", tmp_path / "devlog.md")

    decision = run_existing_intraday_backtest(output_dir=tmp_path / "out")
    report = validate_existing_intraday_backtest(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["backtest_performed"] is True
    assert decision["provider_query_performed"] is False
    assert decision["market_data_downloaded"] is False
    assert decision["promotion_allowed"] is False


def test_validator_fails_if_summary_claims_provider_query(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bt, "OUTPUT_DIR", tmp_path / "out")
    monkeypatch.setattr(bt, "VAULT_REPORT", tmp_path / "report.md")
    monkeypatch.setattr(bt, "VAULT_DEVLOG", tmp_path / "devlog.md")
    run_existing_intraday_backtest(output_dir=tmp_path / "out")
    summary_path = tmp_path / "out" / "backtest_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    summary["provider_query_performed"] = True
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_existing_intraday_backtest(tmp_path / "out")

    assert report["status"] == "fail"
    assert any(check["name"] == "summary_no_provider_query" and check["status"] == "fail" for check in report["checks"])


def _write_case(root: Path, name: str) -> None:
    path = root / name
    path.mkdir()
    (path / "bars.csv").write_text("symbol,timestamp,open,high,low,close,volume\n", encoding="utf-8")


def _synthetic_bars(symbol: str, control_date: str, event_date: str, *, event_positive: bool) -> pd.DataFrame:
    rows = []
    for date, volume_scale in [(control_date, 1), (event_date, 10)]:
        for hour, minute in [(9, 30), (9, 44), (9, 46), (15, 55)]:
            price = 10.0
            if date == event_date and event_positive and (hour, minute) == (9, 44):
                price = 10.5
            if date == event_date and (hour, minute) == (15, 55):
                price = 11.0
            timestamp = pd.Timestamp(f"{date} {hour:02d}:{minute:02d}", tz="America/New_York").tz_convert("UTC").isoformat().replace("+00:00", "Z")
            rows.append(
                {
                    "symbol": symbol,
                    "timestamp": timestamp,
                    "open": price,
                    "high": price,
                    "low": price,
                    "close": price,
                    "volume": 100 * volume_scale,
                }
            )
    return pd.DataFrame(rows)
