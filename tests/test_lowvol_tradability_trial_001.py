from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

import src.experiments.lowvol_tradability_trial_001 as trial
from src.experiments.lowvol_tradability_preregistration_validator import validate_lowvol_tradability_preregistration


SPEC_DIR = Path("experiments/provider_aware_research/lowvol_tradability_preregistration_20260523")


def test_lowvol_tradability_preregistration_passes_real_spec() -> None:
    report = validate_lowvol_tradability_preregistration(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "LOWVOL_TRADABILITY_PREREGISTRATION_PASS"


def test_lowvol_tradability_preregistration_fails_if_provider_query_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "preregistration_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provider_query_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_lowvol_tradability_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "provider_query_blocked" and check["status"] == "fail" for check in report["checks"])


def test_build_lowvol_trades_uses_prior_data_and_selects_lowest_vol_tradable_symbol() -> None:
    prices = _synthetic_prices(days=90)

    trades = trial.build_lowvol_tradability_trades(
        prices,
        start_date="2026-03-05",
        end_date="2026-04-15",
        lookback_days=20,
        holding_days=5,
        rebalance_step_days=5,
        min_median_dollar_volume=100_000,
        min_price=1.0,
        round_trip_cost_bps=500,
    )

    assert trades
    assert {row["selected_symbol"] for row in trades} == {"AEHR"}
    assert all(row["provider_query_performed"] is False for row in trades)
    assert all(row["market_data_downloaded"] is False for row in trades)
    first = trades[0]
    assert first["signal_date"] < first["entry_date"] <= first["exit_date"]
    assert first["net_return"] == round(first["gross_return"] - 0.05, 10)


def test_summary_archives_when_costs_destroy_edge() -> None:
    trades = [
        {"gross_return": 0.01, "net_return": -0.04, "selected_symbol": "AAA"},
        {"gross_return": 0.02, "net_return": -0.03, "selected_symbol": "AAA"},
        {"gross_return": -0.01, "net_return": -0.06, "selected_symbol": "BBB"},
    ]

    summary = trial.summarize_lowvol_backtest(trades, minimum_trade_count=3)

    assert summary["decision"] == "LOWVOL_TRADABILITY_ARCHIVE_CURRENT_FORM"
    assert "net_return_not_positive_after_500bps" in summary["blockers"]
    assert summary["promotion_allowed"] is False


def test_trial_run_writes_backtest_artifacts(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv"
    _synthetic_prices(days=115, start="2024-10-01").to_csv(prices, index=False)

    decision = trial.run_lowvol_tradability_trial_001(
        spec_dir=SPEC_DIR,
        price_file=prices,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
        minimum_trade_count=3,
    )
    report = trial.validate_lowvol_tradability_trial_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["backtest_performed"] is True
    assert decision["provider_query_performed"] is False
    assert decision["promotion_allowed"] is False
    assert (tmp_path / "out" / "trade_log.csv").is_file()


def _synthetic_prices(days: int, start: str = "2026-01-01") -> pd.DataFrame:
    rows = []
    for index in range(days):
        date = (pd.Timestamp(start) + pd.offsets.BDay(index)).date().isoformat()
        for symbol, amplitude, drift, volume in (
            ("AEHR", 0.002, 0.001, 100_000),
            ("ARRY", 0.04, 0.001, 100_000),
            ("CABA", 0.001, 0.001, 100),
        ):
            close = 10.0 * (1.0 + drift * index + amplitude * ((index % 2) * 2 - 1))
            rows.append(
                {
                    "symbol": symbol,
                    "date": date,
                    "open": close * 0.999,
                    "high": close * 1.01,
                    "low": close * 0.99,
                    "close": close,
                    "volume": volume,
                    "provider_dataset": "UNIT.TEST",
                }
            )
    return pd.DataFrame(rows)
