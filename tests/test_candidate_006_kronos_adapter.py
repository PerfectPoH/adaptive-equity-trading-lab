from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.experiments import candidate_006_kronos_adapter as kronos


def _sample_frame() -> pd.DataFrame:
    index = pd.bdate_range("2026-01-01", periods=3)
    return pd.DataFrame(
        {
            "Open": [10.0, 10.2, 10.4],
            "High": [10.3, 10.5, 10.7],
            "Low": [9.8, 10.0, 10.2],
            "Close": [10.1, 10.3, 10.5],
            "Volume": [1000, 1200, 1400],
            "Turnover": [10100, 12360, 14700],
        },
        index=index,
    )


def _gate(path: Path) -> None:
    path.mkdir()
    payload = {
        "status": "APPROVED_COMPATIBILITY_AUDIT_ONLY_NO_MODEL_DOWNLOAD",
        "repo_metadata_query_allowed": False,
        "model_download_allowed": False,
        "inference_allowed": False,
        "fine_tuning_allowed": False,
        "portfolio_backtest_allowed": False,
        "parameter_sweep_allowed": False,
        "promotion_allowed": False,
    }
    (path / "gate_manifest.json").write_text(json.dumps(payload), encoding="utf-8")


def test_normalize_ohlcv_for_kronos_maps_norgate_schema() -> None:
    normalized = kronos.normalize_ohlcv_for_kronos(_sample_frame())

    assert normalized.columns.tolist() == ["open", "high", "low", "close", "volume", "amount"]
    assert float(normalized.iloc[0]["amount"]) == 10100.0


def test_feature_contract_is_feature_generator_only() -> None:
    contract = kronos.build_kronos_feature_contract()

    assert contract["role"] == "feature_generator_only"
    assert "kronos_probability_up" in contract["allowed_features"]
    assert "fine-tuning on active-only survivorship-biased data" in contract["forbidden_uses"]


def test_compatibility_audit_remains_diagnostic_only(monkeypatch, tmp_path: Path) -> None:
    gate_dir = tmp_path / "gate"
    _gate(gate_dir)
    monkeypatch.setattr(kronos, "_git_ls_remote_check", lambda repo: {"status": "not_allowed", "head_count": 0})

    result = kronos.run_candidate_006_kronos_compatibility_audit(
        output_dir=tmp_path / "out",
        gate_dir=gate_dir,
        sample_frame=_sample_frame(),
    )

    assert result["decision"] == "CANDIDATE_006_KRONOS_COMPATIBILITY_AUDIT_COMPLETE_NO_MODEL_DOWNLOAD"
    assert result["model_download_performed"] is False
    assert result["inference_performed"] is False
    assert result["portfolio_backtest_performed"] is False
    assert result["promotion_allowed"] is False
    assert (tmp_path / "out" / "feature_contract.json").is_file()
