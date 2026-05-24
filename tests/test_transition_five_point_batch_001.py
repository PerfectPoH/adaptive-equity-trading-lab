from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

import src.experiments.transition_five_point_batch_001 as batch
from src.experiments.transition_five_point_batch_validator import (
    validate_transition_five_point_batch_gate,
)


SPEC_DIR = Path("experiments/provider_aware_research/transition_five_point_batch_20260524")


def test_transition_five_point_batch_gate_passes_real_spec() -> None:
    report = validate_transition_five_point_batch_gate(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "TRANSITION_FIVE_POINT_BATCH_GATE_PASS"


def test_transition_five_point_batch_gate_fails_if_query_or_promotion_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "batch_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provider_query_allowed"] = True
    manifest["promotion_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_transition_five_point_batch_gate(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "provider_query_blocked" and check["status"] == "fail" for check in report["checks"])
    assert any(check["name"] == "promotion_blocked" and check["status"] == "fail" for check in report["checks"])


def test_normalize_local_snapshot_prices_adds_symbol_and_standard_columns(tmp_path: Path) -> None:
    snapshot = tmp_path / "SPY_2026-05-08.csv"
    pd.DataFrame(
        [
            {
                "Date": "2026-01-02",
                "Open": 100.0,
                "High": 102.0,
                "Low": 99.0,
                "Close": 101.0,
                "Adj Close": 100.5,
                "Volume": 1_000_000,
            }
        ]
    ).to_csv(snapshot, index=False)

    prices = batch.load_local_snapshot_prices([snapshot])

    assert prices.to_dict("records") == [
        {
            "symbol": "SPY",
            "date": "2026-01-02",
            "open": 100.0,
            "high": 102.0,
            "low": 99.0,
            "close": 101.0,
            "adj_close": 100.5,
            "volume": 1_000_000,
            "source_file": str(snapshot),
        }
    ]


def test_largecap_regime_map_classifies_drawdown_and_uptrend() -> None:
    prices = _synthetic_largecap_prices()

    regimes = batch.build_etf_largecap_regime_map(
        prices,
        lookback_days=3,
        volatility_window_days=3,
        drawdown_window_days=5,
        annualized_vol_high_threshold=0.45,
        drawdown_stress_threshold=-0.15,
        trend_return_threshold=0.03,
    )

    labels = {(row["symbol"], row["date"]): row["regime_label"] for row in regimes}
    assert labels[("SPY", "2026-01-08")] == "TREND_UP_LOW_VOL"
    assert labels[("TSLA", "2026-01-08")] == "DRAWDOWN_STRESS"


def test_risk_overlay_replay_blocks_fragile_active_only_momentum() -> None:
    trades = [
        {"net_return_500bps": "1.0"},
        {"net_return_500bps": "-0.2"},
        {"net_return_500bps": "-0.1"},
    ]
    robustness = {"top3_dependency_flag": True, "sign_flip_ex_top3": True}

    overlay = batch.replay_archived_trade_risk_overlay(
        trades,
        robustness_decision=robustness,
        per_trade_loss_floor=-0.15,
        stop_after_cumulative_loss=-0.25,
    )

    assert overlay["trade_count"] == 3
    assert overlay["fragility_block"] is True
    assert overlay["promotion_allowed"] is False
    assert overlay["overlay_net_return_sum"] > overlay["original_net_return_sum"]


def test_run_transition_five_point_batch_writes_all_five_artifacts(tmp_path: Path) -> None:
    snapshot = tmp_path / "SPY_2026-05-08.csv"
    _synthetic_largecap_prices().query("symbol == 'SPY'").rename(
        columns={
            "date": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )[["Date", "Open", "High", "Low", "Close", "Volume"]].to_csv(snapshot, index=False)
    trade_panel = tmp_path / "trade_panel.csv"
    pd.DataFrame(
        [
            {"symbol": "AEHR", "net_return_500bps": -0.10},
            {"symbol": "ARRY", "net_return_500bps": 0.20},
        ]
    ).to_csv(trade_panel, index=False)
    smallcap_prices = tmp_path / "smallcap_prices.csv"
    _synthetic_smallcap_prices().to_csv(smallcap_prices, index=False)
    robustness = tmp_path / "robustness.json"
    robustness.write_text(json.dumps({"top3_dependency_flag": True, "sign_flip_ex_top3": True}), encoding="utf-8")
    delisted = tmp_path / "delisted.json"
    delisted.write_text(json.dumps({"decision": "POLYGON_DELISTED_LISTING_DATE_SUPPORT_BLOCKED"}), encoding="utf-8")

    decision = batch.run_transition_five_point_batch_001(
        spec_dir=SPEC_DIR,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
        snapshot_files=[snapshot],
        active_only_trade_panel=trade_panel,
        robustness_decision_path=robustness,
        delisted_decision_path=delisted,
        smallcap_price_file=smallcap_prices,
    )
    report = batch.validate_transition_five_point_batch_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "TRANSITION_FIVE_POINT_BATCH_COMPLETE_NO_STRATEGY"
    assert decision["completed_points"] == 5
    assert decision["provider_query_performed"] is False
    assert decision["backtest_performed"] is False
    assert decision["promotion_allowed"] is False
    for filename in [
        "etf_largecap_regime_map.csv",
        "risk_overlay_replay.json",
        "portfolio_allocation_smoke.csv",
        "smallcap_microstructure_diagnostic.csv",
        "data_upgrade_decision_matrix.csv",
    ]:
        assert (tmp_path / "out" / filename).is_file()


def _synthetic_largecap_prices() -> pd.DataFrame:
    rows = []
    spy = [100.0, 101.0, 102.0, 103.0, 104.0, 106.0]
    tsla = [100.0, 101.0, 98.0, 90.0, 84.0, 82.0]
    for index, date in enumerate(pd.bdate_range("2026-01-01", periods=6)):
        for symbol, closes in {"SPY": spy, "TSLA": tsla}.items():
            close = closes[index]
            rows.append(
                {
                    "symbol": symbol,
                    "date": date.date().isoformat(),
                    "open": close * 0.99,
                    "high": close * 1.01,
                    "low": close * 0.98,
                    "close": close,
                    "volume": 1_000_000 + index,
                }
            )
    return pd.DataFrame(rows)


def _synthetic_smallcap_prices() -> pd.DataFrame:
    rows = []
    for index, date in enumerate(pd.bdate_range("2026-01-01", periods=8)):
        for symbol in ["AEHR", "CABA"]:
            close = 10 + index if symbol == "AEHR" else 10 - index * 0.2
            volume = 100_000 + index * 20_000
            rows.append(
                {
                    "symbol": symbol,
                    "date": date.date().isoformat(),
                    "open": close * 0.99,
                    "high": close * 1.02,
                    "low": close * 0.98,
                    "close": close,
                    "volume": volume,
                }
            )
    return pd.DataFrame(rows)
