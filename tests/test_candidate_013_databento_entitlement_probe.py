import json
from pathlib import Path

from src.experiments.candidate_013_databento_entitlement_probe import (
    build_readiness_decision,
    run_candidate_013_databento_entitlement_probe,
)


class FakeHistoricalMetadata:
    def list_datasets(self):
        return ["EQUS.MINI", "EQUS.SUMMARY"]

    def list_schemas(self, dataset):
        return ["ohlcv-1d", "trades"] if dataset == "EQUS.MINI" else ["ohlcv-1d"]

    def list_fields(self, schema, encoding):
        assert schema == "ohlcv-1d"
        assert encoding == "dbn"
        return ["open", "high", "low", "close", "volume"]

    def get_cost(self, **kwargs):
        return 0.01

    def get_record_count(self, **kwargs):
        return 1


class FakeHistoricalClient:
    def __init__(self):
        self.metadata = FakeHistoricalMetadata()


class FakeReferenceEndpoint:
    def __init__(self, error):
        self.error = error

    def get_range(self, **kwargs):
        raise self.error


class FakeReferenceClient:
    def __init__(self, error):
        self.corporate_actions = FakeReferenceEndpoint(error)
        self.security_master = FakeReferenceEndpoint(error)
        self.adjustment_factors = FakeReferenceEndpoint(error)


def _gate(root: Path) -> Path:
    gate = root / "gate"
    gate.mkdir()
    (gate / "gate_manifest.json").write_text(
        json.dumps(
            {
                "status": "APPROVED_ONE_DATABENTO_FRESH_DATA_ENTITLEMENT_PROBE_ONLY",
                "allowed_probe_count": 1,
                "api_key_source": "env-file",
                "env_file": str(root / ".env"),
                "provider_query_allowed": True,
                "market_data_download_allowed": False,
                "raw_payload_retention_allowed": False,
                "backtest_allowed": False,
                "parameter_sweep_allowed": False,
                "promotion_allowed": False,
                "paper_trading_allowed": False,
                "live_trading_allowed": False,
                "probe_contract": {
                    "historical_dataset_candidates": ["EQUS.MINI", "EQUS.SUMMARY"],
                    "tiny_cost_symbol": "AAPL",
                    "tiny_cost_start": "2026-01-02",
                    "tiny_cost_end": "2026-01-05",
                    "tiny_schema": "ohlcv-1d",
                    "retain_raw_response": False,
                },
                "fresh_data_requirements": {
                    "minimum_history_years": 5,
                    "must_include_delisted": True,
                    "must_include_listing_dates": True,
                    "must_include_delisting_dates": True,
                    "must_include_adjustment_factors": True,
                    "must_include_security_master": True,
                    "must_include_daily_adjusted_ohlcv": True,
                    "must_document_storage_licensing": True,
                },
            }
        ),
        encoding="utf-8",
    )
    (root / ".env").write_text("DATABENTO_API_KEY=test-secret\n", encoding="utf-8")
    return gate


def test_build_readiness_decision_blocks_when_reference_entitlement_missing() -> None:
    decision = build_readiness_decision(
        historical_status="PASS",
        reference_statuses={
            "corporate_actions": "BLOCKED_403",
            "security_master": "BLOCKED_403",
            "adjustment_factors": "BLOCKED_403",
        },
    )

    assert decision["decision"] == "DATABENTO_FRESH_DATA_BLOCKED_REFERENCE_ENTITLEMENT"
    assert "databento_reference_entitlement_missing" in decision["blockers"]
    assert decision["candidate_014_backtest_allowed"] is False


def test_run_probe_redacts_key_and_retains_no_raw_payload(tmp_path: Path) -> None:
    gate = _gate(tmp_path)

    result = run_candidate_013_databento_entitlement_probe(
        gate_dir=gate,
        output_dir=tmp_path / "out",
        historical_client_factory=lambda api_key: FakeHistoricalClient(),
        reference_client_factory=lambda api_key: FakeReferenceClient(RuntimeError("403 license_reference_dataset_no_subscription")),
    )

    text = json.dumps(result)
    assert "test-secret" not in text
    assert result["provider_query_performed"] is True
    assert result["market_data_download_performed"] is False
    assert result["raw_payload_retained"] is False
    assert result["historical_metadata"]["status"] == "PASS"
    assert result["reference_metadata"]["overall_status"] == "BLOCKED_REFERENCE_ENTITLEMENT"
    assert (tmp_path / "out" / "databento_entitlement_probe_result.json").exists()
    assert not any(path.name.endswith("_raw.json") for path in (tmp_path / "out").iterdir())
