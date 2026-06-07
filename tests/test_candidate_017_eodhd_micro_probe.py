from __future__ import annotations

import json
from pathlib import Path

from src.experiments.candidate_017_eodhd_micro_probe import (
    EodhdResponse,
    build_eodhd_micro_probe_decision,
    run_candidate_017_eodhd_micro_probe,
    summarize_delisted_symbols,
    summarize_eod_rows,
)


class FakeEodhdClient:
    def get_json(self, endpoint: str, params: dict[str, str]) -> EodhdResponse:
        if endpoint == "/api/exchange-symbol-list/US" and params.get("delisted") == "1":
            return EodhdResponse(
                status_code=200,
                payload=[
                    {"Code": "BBBY", "Name": "Bed Bath & Beyond Inc", "Exchange": "US", "Type": "Common Stock", "IsDelisted": True},
                    {"Code": "ABC", "Name": "Old ABC Corp", "Exchange": "US", "Type": "Common Stock", "IsDelisted": True},
                ],
            )
        if endpoint == "/api/eod/BBBY.US":
            return EodhdResponse(
                status_code=200,
                payload=[
                    {"date": "2023-04-03", "open": 0.42, "high": 0.45, "low": 0.39, "close": 0.41, "adjusted_close": 0.41, "volume": 1000},
                    {"date": "2023-05-03", "open": 0.08, "high": 0.09, "low": 0.07, "close": 0.08, "adjusted_close": 0.08, "volume": 3000},
                ],
            )
        if endpoint == "/api/eod/AAPL.US":
            return EodhdResponse(status_code=200, payload=[{"date": "2020-08-31", "close": 129.04, "adjusted_close": 129.04, "volume": 1}])
        return EodhdResponse(status_code=404, payload={"error": "not found"})


def _gate(gate_dir: Path, env_path: Path) -> None:
    gate_dir.mkdir()
    (gate_dir / "gate_manifest.json").write_text(
        json.dumps(
            {
                "status": "APPROVED_EODHD_DATA_MESH_MICRO_PROBE_ONLY",
                "api_key_source": "env-file",
                "env_file": str(env_path),
                "provider_query_allowed": True,
                "max_http_requests": 6,
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


def test_summarize_delisted_symbols_detects_known_delisted() -> None:
    summary = summarize_delisted_symbols(
        [
            {"Code": "BBBY", "Name": "Bed Bath & Beyond Inc", "IsDelisted": True},
            {"Code": "ABC", "Name": "Old ABC Corp", "IsDelisted": True},
        ],
        required_symbol="BBBY",
    )

    assert summary["row_count"] == 2
    assert summary["contains_required_symbol"] is True
    assert summary["sample_symbols"] == ["BBBY", "ABC"]


def test_summarize_eod_rows_detects_terminal_ohlcv_continuity() -> None:
    summary = summarize_eod_rows(
        [
            {"date": "2023-04-03", "close": 0.41, "adjusted_close": 0.41, "volume": 1000},
            {"date": "2023-05-03", "close": 0.08, "adjusted_close": 0.08, "volume": 3000},
        ]
    )

    assert summary["row_count"] == 2
    assert summary["first_date"] == "2023-04-03"
    assert summary["last_date"] == "2023-05-03"
    assert summary["has_adjusted_close"] is True


def test_build_eodhd_micro_probe_decision_blocks_missing_key() -> None:
    decision = build_eodhd_micro_probe_decision(api_key_present=False, checks=[])

    assert decision["decision"] == "EODHD_MICRO_PROBE_BLOCKED_API_KEY_MISSING"
    assert "eodhd_api_key_missing" in decision["blockers"]
    assert decision["candidate_012_backtest_allowed"] is False


def test_build_eodhd_micro_probe_decision_requires_delisted_list_and_terminal_prices() -> None:
    checks = [
        {"case_id": "DELISTED_LIST_US_BBBY", "status": "PASS"},
        {"case_id": "DELISTED_TERMINAL_BBBY", "status": "BLOCK"},
        {"case_id": "ACTIVE_BASELINE_AAPL", "status": "PASS"},
    ]

    decision = build_eodhd_micro_probe_decision(api_key_present=True, checks=checks)

    assert decision["decision"] == "EODHD_MICRO_PROBE_COMPLETE_NOT_ADMISSIBLE"
    assert "eodhd_terminal_ohlcv_unverified" in decision["blockers"]


def test_run_candidate_017_blocks_http_200_payload_without_ohlcv_dates(tmp_path: Path) -> None:
    class HtmlLikeSuccessClient:
        def get_json(self, endpoint: str, params: dict[str, str]) -> EodhdResponse:
            if endpoint == "/api/exchange-symbol-list/US":
                return EodhdResponse(status_code=200, payload=[{"Code": "BBBY"}])
            return EodhdResponse(status_code=200, payload=[{"message": "not an OHLCV row"}])

    env_path = tmp_path / ".env"
    env_path.write_text("EODHD_API_KEY=test-secret\n", encoding="utf-8")
    gate = tmp_path / "gate"
    _gate(gate, env_path)

    result = run_candidate_017_eodhd_micro_probe(
        gate_dir=gate,
        output_dir=tmp_path / "out",
        client=HtmlLikeSuccessClient(),
        run_id="CANDIDATE-017-EODHD-MICRO-PROBE-INVALID-OHLCV",
    )

    assert result["decision"] == "EODHD_MICRO_PROBE_COMPLETE_NOT_ADMISSIBLE"
    assert "eodhd_terminal_ohlcv_unverified" in result["final_decision"]["blockers"]
    assert "eodhd_active_ohlcv_unverified" in result["final_decision"]["blockers"]


def test_run_candidate_017_blocks_without_api_key_and_writes_artifacts(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("OTHER_KEY=x\n", encoding="utf-8")
    gate = tmp_path / "gate"
    _gate(gate, env_path)

    result = run_candidate_017_eodhd_micro_probe(gate_dir=gate, output_dir=tmp_path / "out")

    assert result["provider_query_performed"] is False
    assert result["decision"] == "EODHD_MICRO_PROBE_BLOCKED_API_KEY_MISSING"
    assert (tmp_path / "out" / "eodhd_micro_probe_result.json").exists()
    assert "OTHER_KEY" not in (tmp_path / "out" / "eodhd_micro_probe_result.json").read_text(encoding="utf-8")


def test_run_candidate_017_redacts_key_and_retains_no_raw_payload(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("EODHD_API_KEY=test-secret\n", encoding="utf-8")
    gate = tmp_path / "gate"
    _gate(gate, env_path)

    result = run_candidate_017_eodhd_micro_probe(
        gate_dir=gate,
        output_dir=tmp_path / "out",
        client=FakeEodhdClient(),
        run_id="CANDIDATE-017-EODHD-MICRO-PROBE-TEST",
    )

    text = json.dumps(result)
    assert "test-secret" not in text
    assert result["run_id"] == "CANDIDATE-017-EODHD-MICRO-PROBE-TEST"
    assert result["provider_query_performed"] is True
    assert result["raw_payload_retained"] is False
    assert result["decision"] == "EODHD_MICRO_PROBE_ADMISSIBLE_COMPONENT"
    assert not any(path.name.endswith("_raw.json") for path in (tmp_path / "out").iterdir())
