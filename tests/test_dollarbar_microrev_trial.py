from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

import src.experiments.dollarbar_microrev_trial as microrev
from src.experiments.dollar_bar_diagnostic import build_dollar_bars
from src.experiments.dollarbar_microrev_trial import (
    MicroRevParams,
    evaluate_microrev_file,
    run_dollarbar_microrev_protocol,
    simulate_microrev_trades,
    validate_dollarbar_microrev_protocol,
)


def test_simulate_microrev_trades_charges_500bps_cost() -> None:
    closes = [100 + index * 0.1 for index in range(25)]
    closes.extend([90.0, 91.0, 92.0, 93.0, 94.0])
    dollar_bars = [{"close": close} for close in closes]

    trades = simulate_microrev_trades(dollar_bars, MicroRevParams())

    assert trades
    first = trades[0]
    assert first["net_return"] == first["gross_return"] - 0.05


def test_evaluate_microrev_file_uses_static_dollarbar_bucket(tmp_path: Path) -> None:
    event_dir = tmp_path / "AAA_2026-01-02"
    event_dir.mkdir()
    bars = _sample_bars()
    bars.to_csv(event_dir / "bars.csv", index=False)
    frame = bars.sort_values("timestamp").reset_index(drop=True).copy()
    frame["dollar_value"] = frame["close"] * frame["volume"]
    expected_count = len(build_dollar_bars(frame, float(frame["dollar_value"].sum()) / len(frame)))

    result = evaluate_microrev_file(event_dir / "bars.csv", MicroRevParams())

    assert result["status"] == "evaluated"
    assert result["dollar_bar_count"] == expected_count
    assert result["target_dollar_bucket"] > 0


def test_full_microrev_protocol_records_five_points_and_blocks_provider_query(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _redirect_artifacts(tmp_path, monkeypatch)

    source = tmp_path / "panel"
    for idx in range(2):
        event_dir = source / f"AAA_{idx}"
        event_dir.mkdir(parents=True)
        _sample_bars(symbol=f"AAA{idx}").to_csv(event_dir / "bars.csv", index=False)

    decision = run_dollarbar_microrev_protocol(source)
    validation = validate_dollarbar_microrev_protocol()

    assert validation["status"] == "pass"
    assert len(decision["points_completed"]) == 5
    assert decision["provider_query_performed"] is False
    assert decision["promotion_allowed"] is False


def _redirect_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(microrev, "CONTRACT_DIR", tmp_path / "contract")
    monkeypatch.setattr(microrev, "EMA_REJECTION_DIR", tmp_path / "ema_rejection")
    monkeypatch.setattr(microrev, "PREREG_DIR", tmp_path / "prereg")
    monkeypatch.setattr(microrev, "OUTPUT_DIR", tmp_path / "output")
    monkeypatch.setattr(microrev, "VAULT_REPORT", tmp_path / "vault_report.md")
    monkeypatch.setattr(microrev, "VAULT_DEVLOG", tmp_path / "vault_devlog.md")


def _sample_bars(symbol: str = "AAA") -> pd.DataFrame:
    rows = []
    for index in range(80):
        close = 100.0 + index * 0.05
        if index == 45:
            close = 92.0
        elif 46 <= index <= 50:
            close = 92.0 + (index - 45) * 0.7
        rows.append(
            {
                "symbol": symbol,
                "timestamp": f"2026-01-02T14:{index % 60:02d}:00Z",
                "open": close - 0.05,
                "high": close + 0.2,
                "low": close - 0.2,
                "close": close,
                "volume": 1000 + index * 10,
            }
        )
    return pd.DataFrame(rows)
