from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

import src.experiments.regime_map_diagnostic_001 as diag
from src.experiments.regime_map_preregistration_validator import validate_regime_map_preregistration


SPEC_DIR = Path("experiments/provider_aware_research/regime_map_preregistration_20260524")


def test_regime_map_preregistration_passes_real_spec() -> None:
    report = validate_regime_map_preregistration(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "REGIME_MAP_PREREGISTRATION_PASS"


def test_regime_map_preregistration_fails_if_provider_query_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "preregistration_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["provider_query_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_regime_map_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "provider_query_blocked" and check["status"] == "fail" for check in report["checks"])


def test_build_daily_regime_map_classifies_observable_states() -> None:
    prices = _synthetic_prices()

    regimes = diag.build_daily_regime_map(
        prices,
        lookback_days=3,
        shock_abs_return_threshold=0.08,
        shock_volume_z_threshold=1.0,
        trend_return_threshold=0.03,
        quiet_abs_return_threshold=0.01,
    )

    labels = {(row["symbol"], row["date"]): row["regime_label"] for row in regimes}
    assert labels[("AEHR", "2025-01-08")] == "VOLATILITY_SHOCK"
    assert labels[("AEHR", "2025-01-09")] == "TREND_UP"
    assert labels[("CABA", "2025-01-09")] == "QUIET_RANGE"


def test_map_trade_logs_to_regimes_uses_signal_then_entry_date() -> None:
    regimes = [
        {"symbol": "AEHR", "date": "2025-01-08", "regime_label": "VOLATILITY_SHOCK"},
        {"symbol": "AEHR", "date": "2025-01-09", "regime_label": "TREND_UP"},
    ]
    trades = [
        {
            "run_id": "R1",
            "trial_id": "T1",
            "selected_symbol": "AEHR",
            "signal_date": "2025-01-08",
            "entry_date": "2025-01-09",
            "net_return": "-0.12",
        },
        {
            "run_id": "R2",
            "trial_id": "T2",
            "symbol": "AEHR",
            "entry_date": "2025-01-09",
            "net_return": "0.04",
        },
    ]

    mapped = diag.map_trade_logs_to_regimes(trades, regimes)

    assert mapped[0]["mapped_date"] == "2025-01-08"
    assert mapped[0]["regime_label"] == "VOLATILITY_SHOCK"
    assert mapped[1]["mapped_date"] == "2025-01-09"
    assert mapped[1]["regime_label"] == "TREND_UP"


def test_summarize_regime_attribution_reports_no_promotion() -> None:
    mapped = [
        {"source_run_id": "LOWVOL", "regime_label": "TREND_DOWN", "net_return": -0.2},
        {"source_run_id": "LOWVOL", "regime_label": "TREND_DOWN", "net_return": -0.1},
        {"source_run_id": "TAPE", "regime_label": "VOLATILITY_SHOCK", "net_return": 0.05},
    ]
    regime_rows = [
            {"symbol": "AEHR", "date": "2025-01-01", "regime_label": "TREND_DOWN"},
            {"symbol": "AEHR", "date": "2025-01-02", "regime_label": "VOLATILITY_SHOCK"},
    ]

    summary = diag.summarize_regime_diagnostic(regime_rows, mapped, minimum_mapped_trades=3)

    assert summary["decision"] == "REGIME_MAP_DIAGNOSTIC_COMPLETE_NO_STRATEGY"
    assert summary["promotion_allowed"] is False
    assert summary["provider_query_performed"] is False
    assert summary["backtest_performed"] is False
    assert summary["mapped_trade_count"] == 3


def test_run_regime_map_diagnostic_writes_artifacts(tmp_path: Path) -> None:
    prices = tmp_path / "prices.csv"
    _synthetic_prices().to_csv(prices, index=False)
    trade_log = tmp_path / "trade_log.csv"
    pd.DataFrame(
        [
            {
                "run_id": "LOWVOL-TEST",
                "trial_id": "T-LOWVOL",
                "selected_symbol": "AEHR",
                "signal_date": "2025-01-08",
                "entry_date": "2025-01-09",
                "net_return": -0.2,
            }
        ]
    ).to_csv(trade_log, index=False)

    decision = diag.run_regime_map_diagnostic_001(
        spec_dir=SPEC_DIR,
        price_file=prices,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
        trade_log_paths=[trade_log],
        minimum_mapped_trades=1,
    )
    report = diag.validate_regime_map_diagnostic_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["decision"] == "REGIME_MAP_DIAGNOSTIC_COMPLETE_NO_STRATEGY"
    assert decision["provider_query_performed"] is False
    assert decision["backtest_performed"] is False
    assert decision["promotion_allowed"] is False
    assert (tmp_path / "out" / "daily_regime_map.csv").is_file()
    assert (tmp_path / "out" / "trial_regime_attribution.csv").is_file()


def _synthetic_prices() -> pd.DataFrame:
    rows = []
    closes = {
        "AEHR": [10.0, 10.1, 10.0, 10.1, 10.0, 11.2, 11.5],
        "CABA": [5.0, 5.01, 5.0, 5.02, 5.01, 5.02, 5.01],
    }
    volumes = {
        "AEHR": [100_000, 110_000, 105_000, 100_000, 100_000, 500_000, 250_000],
        "CABA": [100_000, 99_000, 100_000, 101_000, 100_000, 99_000, 100_000],
    }
    for index in range(7):
        date = (pd.Timestamp("2025-01-01") + pd.offsets.BDay(index)).date().isoformat()
        for symbol in ("AEHR", "CABA"):
            close = closes[symbol][index]
            rows.append(
                {
                    "symbol": symbol,
                    "date": date,
                    "open": close * 0.99,
                    "high": close * 1.02,
                    "low": close * 0.98,
                    "close": close,
                    "volume": volumes[symbol][index],
                    "provider_dataset": "UNIT.TEST",
                }
            )
    return pd.DataFrame(rows)
