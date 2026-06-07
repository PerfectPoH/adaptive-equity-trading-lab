from __future__ import annotations

import json
from pathlib import Path

from src.experiments.candidate_016_tiingo_micro_probe import (
    FakeTiingoResponse,
    build_tiingo_micro_probe_decision,
    run_candidate_016_tiingo_micro_probe,
    summarize_price_rows,
)


class FakeTiingoClient:
    def get_json(self, endpoint: str, params: dict[str, str]) -> FakeTiingoResponse:
        if endpoint == "/tiingo/daily/AAPL/prices":
            return FakeTiingoResponse(
                status_code=200,
                payload=[
                    {"date": "2020-08-28T00:00:00.000Z", "open": 499.0, "high": 505.0, "low": 498.0, "close": 499.23, "adjClose": 124.8075, "volume": 100, "divCash": 0.0, "splitFactor": 1.0},
                    {"date": "2020-08-31T00:00:00.000Z", "open": 127.0, "high": 131.0, "low": 126.0, "close": 129.04, "adjClose": 129.04, "volume": 400, "divCash": 0.0, "splitFactor": 4.0},
                ],
            )
        if endpoint == "/tiingo/daily/AAPL":
            return FakeTiingoResponse(status_code=200, payload={"ticker": "AAPL", "startDate": "1980-12-12", "endDate": "2026-06-05"})
        if endpoint == "/tiingo/daily/BBBY/prices":
            return FakeTiingoResponse(status_code=404, payload={"detail": "Not found"})
        if endpoint == "/tiingo/utilities/search":
            return FakeTiingoResponse(status_code=200, payload=[{"ticker": "META", "name": "Meta Platforms Inc"}])
        return FakeTiingoResponse(status_code=200, payload=[])


def _gate(gate_dir: Path, env_path: Path) -> None:
    gate_dir.mkdir()
    (gate_dir / "gate_manifest.json").write_text(
        json.dumps(
            {
                "status": "APPROVED_TIINGO_DATA_MESH_MICRO_PROBE_ONLY",
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


def test_summarize_price_rows_detects_adjusted_fields_and_split_event() -> None:
    summary = summarize_price_rows(
        [
            {"date": "2020-08-28T00:00:00.000Z", "open": 499.0, "close": 499.23, "adjClose": 124.8075, "splitFactor": 1.0},
            {"date": "2020-08-31T00:00:00.000Z", "open": 127.0, "close": 129.04, "adjClose": 129.04, "splitFactor": 4.0},
        ]
    )

    assert summary["row_count"] == 2
    assert summary["has_adjusted_close"] is True
    assert summary["non_unit_split_factor_count"] == 1
    assert summary["first_date"] == "2020-08-28"
    assert summary["last_date"] == "2020-08-31"


def test_build_tiingo_micro_probe_decision_blocks_missing_key() -> None:
    decision = build_tiingo_micro_probe_decision(api_key_present=False, checks=[])

    assert decision["decision"] == "TIINGO_MICRO_PROBE_BLOCKED_API_KEY_MISSING"
    assert "tiingo_api_key_missing" in decision["blockers"]
    assert decision["candidate_012_backtest_allowed"] is False


def test_build_tiingo_micro_probe_decision_requires_delisted_and_identity_evidence() -> None:
    checks = [
        {"case_id": "ACTIVE_BASELINE_AAPL", "status": "PASS"},
        {"case_id": "SPLIT_AAPL_2020", "status": "PASS"},
        {"case_id": "TICKER_CHANGE_FB_META", "status": "PASS"},
        {"case_id": "DELISTING_BBBY", "status": "BLOCK"},
    ]

    decision = build_tiingo_micro_probe_decision(api_key_present=True, checks=checks)

    assert decision["decision"] == "TIINGO_MICRO_PROBE_COMPLETE_NOT_ADMISSIBLE"
    assert "tiingo_delisted_coverage_unverified" in decision["blockers"]
    assert decision["candidate_012_backtest_allowed"] is False


def test_run_candidate_016_blocks_without_api_key_and_writes_artifacts(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("OTHER_KEY=x\n", encoding="utf-8")
    gate = tmp_path / "gate"
    _gate(gate, env_path)

    result = run_candidate_016_tiingo_micro_probe(gate_dir=gate, output_dir=tmp_path / "out")

    assert result["provider_query_performed"] is False
    assert result["decision"] == "TIINGO_MICRO_PROBE_BLOCKED_API_KEY_MISSING"
    assert (tmp_path / "out" / "tiingo_micro_probe_result.json").exists()
    assert "OTHER_KEY" not in (tmp_path / "out" / "tiingo_micro_probe_result.json").read_text(encoding="utf-8")


def test_run_candidate_016_redacts_key_and_retains_no_raw_payload(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("TIINGO_API_KEY=test-secret\n", encoding="utf-8")
    gate = tmp_path / "gate"
    _gate(gate, env_path)

    result = run_candidate_016_tiingo_micro_probe(
        gate_dir=gate,
        output_dir=tmp_path / "out",
        client=FakeTiingoClient(),
    )

    text = json.dumps(result)
    assert "test-secret" not in text
    assert result["provider_query_performed"] is True
    assert result["raw_payload_retained"] is False
    assert result["checks"][0]["status"] == "PASS"
    assert result["checks"][1]["summary"]["non_unit_split_factor_count"] == 1
    assert not any(path.name.endswith("_raw.json") for path in (tmp_path / "out").iterdir())
