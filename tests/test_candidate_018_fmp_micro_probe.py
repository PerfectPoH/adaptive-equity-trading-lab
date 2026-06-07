from __future__ import annotations

import json
from pathlib import Path

from src.experiments.candidate_018_fmp_micro_probe import (
    FmpResponse,
    build_fmp_micro_probe_decision,
    run_candidate_018_fmp_micro_probe,
    summarize_delisted_payload,
    summarize_historical_payload,
)


class FakeFmpClient:
    def get_json(self, endpoint: str, params: dict[str, str]) -> FmpResponse:
        if endpoint == "/stable/delisted-companies":
            return FmpResponse(status_code=200, payload=[{"symbol": "BBBY", "delistedDate": "2023-05-03"}, {"symbol": "OLD"}])
        if endpoint == "/stable/historical-price-eod/full" and params.get("symbol") in {"AAPL", "SPY", "IWM", "BBBY"}:
            return FmpResponse(
                status_code=200,
                payload={
                    "symbol": params["symbol"],
                    "historical": [
                        {"date": "2020-08-31", "open": 1, "high": 2, "low": 1, "close": 2, "adjClose": 2, "volume": 100},
                        {"date": "2020-09-01", "open": 2, "high": 3, "low": 2, "close": 3, "adjClose": 3, "volume": 200},
                    ],
                },
            )
        return FmpResponse(status_code=404, payload={"error": "not found"})


def _gate(gate_dir: Path, env_path: Path) -> None:
    gate_dir.mkdir()
    (gate_dir / "gate_manifest.json").write_text(
        json.dumps(
            {
                "status": "APPROVED_FMP_DATA_MESH_MICRO_PROBE_ONLY",
                "api_key_source": "env-file",
                "env_file": str(env_path),
                "provider_query_allowed": True,
                "max_http_requests": 8,
                "raw_payload_retention_allowed": False,
                "market_data_download_allowed": False,
                "dataset_build_allowed": False,
                "backtest_allowed": False,
                "promotion_allowed": False,
                "paper_trading_allowed": False,
                "live_trading_allowed": False,
            }
        ),
        encoding="utf-8",
    )


def test_summarize_historical_payload_accepts_legacy_historical_dict() -> None:
    summary = summarize_historical_payload(
        {
            "symbol": "AAPL",
            "historical": [
                {"date": "2020-08-31", "open": 1, "high": 2, "low": 1, "close": 2, "adjClose": 2, "volume": 100},
                {"date": "2020-09-01", "open": 2, "high": 3, "low": 2, "close": 3, "adjClose": 3, "volume": 200},
            ],
        }
    )

    assert summary["row_count"] == 2
    assert summary["first_date"] == "2020-08-31"
    assert summary["last_date"] == "2020-09-01"
    assert summary["has_ohlcv"] is True
    assert summary["has_adjusted_close"] is True


def test_summarize_historical_payload_rejects_error_like_200_payload() -> None:
    summary = summarize_historical_payload([{"Error Message": "Invalid API key"}])

    assert summary["row_count"] == 1
    assert summary["first_date"] is None
    assert summary["has_ohlcv"] is False
    assert summary["has_adjusted_close"] is False


def test_summarize_delisted_payload_detects_required_symbol() -> None:
    summary = summarize_delisted_payload([{"symbol": "BBBY", "delistedDate": "2023-05-03"}], required_symbol="BBBY")

    assert summary["row_count"] == 1
    assert summary["contains_required_symbol"] is True
    assert summary["rows_with_delisting_date_fields"] == 1


def test_build_fmp_micro_probe_decision_blocks_missing_key() -> None:
    decision = build_fmp_micro_probe_decision(api_key_present=False, checks=[])

    assert decision["decision"] == "FMP_MICRO_PROBE_BLOCKED_API_KEY_MISSING"
    assert "fmp_api_key_missing" in decision["blockers"]
    assert decision["candidate_012_backtest_allowed"] is False


def test_build_fmp_micro_probe_decision_requires_delisted_and_benchmarks() -> None:
    checks = [
        {"case_id": "ACTIVE_BASELINE_AAPL", "status": "PASS"},
        {"case_id": "BENCHMARK_SPY", "status": "PASS"},
        {"case_id": "BENCHMARK_IWM", "status": "BLOCK"},
        {"case_id": "DELISTED_LIST_US_BBBY", "status": "PASS"},
        {"case_id": "DELISTED_TERMINAL_BBBY", "status": "PASS"},
    ]

    decision = build_fmp_micro_probe_decision(api_key_present=True, checks=checks)

    assert decision["decision"] == "FMP_MICRO_PROBE_COMPLETE_NOT_ADMISSIBLE"
    assert "fmp_iwm_benchmark_unverified" in decision["blockers"]


def test_run_candidate_018_blocks_without_api_key_and_writes_artifacts(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("OTHER_KEY=x\n", encoding="utf-8")
    gate = tmp_path / "gate"
    _gate(gate, env_path)

    result = run_candidate_018_fmp_micro_probe(gate_dir=gate, output_dir=tmp_path / "out")

    assert result["provider_query_performed"] is False
    assert result["decision"] == "FMP_MICRO_PROBE_BLOCKED_API_KEY_MISSING"
    assert (tmp_path / "out" / "fmp_micro_probe_result.json").exists()
    assert "OTHER_KEY" not in (tmp_path / "out" / "fmp_micro_probe_result.json").read_text(encoding="utf-8")


def test_run_candidate_018_redacts_key_and_retains_no_raw_payload(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("FMP_API_KEY=test-secret\n", encoding="utf-8")
    gate = tmp_path / "gate"
    _gate(gate, env_path)

    result = run_candidate_018_fmp_micro_probe(
        gate_dir=gate,
        output_dir=tmp_path / "out",
        client=FakeFmpClient(),
        run_id="CANDIDATE-018-FMP-MICRO-PROBE-TEST",
    )

    text = json.dumps(result)
    assert "test-secret" not in text
    assert result["provider_query_performed"] is True
    assert result["raw_payload_retained"] is False
    assert result["decision"] == "FMP_MICRO_PROBE_ADMISSIBLE_COMPONENT"
    assert not any(path.name.endswith("_raw.json") for path in (tmp_path / "out").iterdir())
