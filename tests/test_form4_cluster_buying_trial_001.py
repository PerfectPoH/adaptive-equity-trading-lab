from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd

import src.experiments.form4_cluster_buying_trial_001 as trial
from src.experiments.form4_cluster_buying_preregistration_validator import validate_form4_cluster_buying_preregistration


SPEC_DIR = Path("experiments/provider_aware_research/form4_cluster_buying_preregistration_20260523")


def test_form4_cluster_buying_preregistration_passes_real_spec() -> None:
    report = validate_form4_cluster_buying_preregistration(SPEC_DIR)

    assert report["status"] == "pass"
    assert report["gate_decision"] == "FORM4_CLUSTER_BUYING_PREREGISTRATION_PASS"


def test_form4_cluster_buying_preregistration_fails_if_short_selling_allowed(tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(SPEC_DIR, spec)
    manifest_path = spec / "preregistration_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["short_selling_allowed"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    report = validate_form4_cluster_buying_preregistration(spec)

    assert report["status"] == "fail"
    assert any(check["name"] == "short_selling_blocked" and check["status"] == "fail" for check in report["checks"])


def test_parse_form4_xml_extracts_only_open_market_acquisitions() -> None:
    rows = trial.parse_form4_xml(
        _form4_xml(transactions=[("P", "A", "2025-01-02", 10_000, 6.0), ("S", "D", "2025-01-03", 9_000, 7.0)]),
        symbol="CRMD",
        cik="1410098",
        accession_number="0001410098-25-000001",
        filing_date="2025-01-06",
        acceptance_datetime="2025-01-06T21:30:00",
    )

    assert len(rows) == 1
    assert rows[0]["transactionCode"] == "P"
    assert rows[0]["acquiredDisposedCode"] == "A"
    assert rows[0]["value_usd"] == 60_000.0
    assert rows[0]["raw_payload_retained"] is False


def test_parse_form4_xml_recovers_ownership_document_embedded_in_text() -> None:
    wrapped = f"<SEC-DOCUMENT>\n<HTML><body>bad wrapper</body></HTML>\n{_form4_xml(transactions=[('P', 'A', '2025-01-02', 10_000, 6.0)])}\n</SEC-DOCUMENT>"

    rows = trial.parse_form4_xml(
        wrapped,
        symbol="CRMD",
        cik="1410098",
        accession_number="0001410098-25-000001",
        filing_date="2025-01-06",
        acceptance_datetime="2025-01-06T21:30:00",
    )

    assert len(rows) == 1
    assert rows[0]["ownerName"] == "Jane Director"


def test_fetch_sec_panel_skips_one_malformed_document_without_losing_later_rows(monkeypatch) -> None:
    def fake_tickers(symbols: list[str]) -> dict[str, str]:
        return {"AEHR": "0001040470"}

    def fake_json(url: str) -> dict:
        return {
            "filings": {
                "recent": {
                    "form": ["4", "4"],
                    "accessionNumber": ["0001040470-25-000001", "0001040470-25-000002"],
                    "filingDate": ["2025-01-05", "2025-01-06"],
                    "acceptanceDateTime": ["2025-01-05T20:00:00", "2025-01-06T20:00:00"],
                    "primaryDocument": ["bad.xml", "good.xml"],
                }
            }
        }

    def fake_text(url: str) -> str:
        if url.endswith("bad.xml"):
            return "<not><valid>"
        return _form4_xml(transactions=[("P", "A", "2025-01-06", 10_000, 10.0)])

    monkeypatch.setattr(trial, "_load_sec_company_tickers", fake_tickers)
    monkeypatch.setattr(trial, "_sec_json", fake_json)
    monkeypatch.setattr(trial, "_sec_text", fake_text)
    monkeypatch.setattr(trial.time, "sleep", lambda seconds: None)

    rows = trial.fetch_sec_form4_transaction_panel(
        allowed_symbols=["AEHR"],
        start_date="2025-01-01",
        end_date="2025-12-31",
        max_document_requests=2,
    )

    assert len(rows) == 1
    assert rows[0]["symbol"] == "AEHR"


def test_build_form4_clusters_requires_two_owners_and_minimum_value() -> None:
    transactions = [
        _tx("AEHR", "Owner A", "2025-02-03", 60_000),
        _tx("AEHR", "Owner B", "2025-02-07", 55_000),
        _tx("AEHR", "Owner C", "2025-04-01", 90_000),
        _tx("ARRY", "Solo Owner", "2025-02-04", 200_000),
    ]

    clusters = trial.build_form4_clusters(
        transactions,
        cluster_window_days=10,
        min_distinct_owners=2,
        min_cluster_value_usd=100_000,
    )

    assert len(clusters) == 1
    assert clusters[0]["symbol"] == "AEHR"
    assert clusters[0]["signal_date"] == "2025-02-07"
    assert clusters[0]["distinct_owner_count"] == 2
    assert clusters[0]["cluster_value_usd"] == 115_000.0


def test_build_form4_backtest_uses_first_open_after_filing_signal() -> None:
    prices = _synthetic_prices(days=140, start="2025-02-03")
    clusters = [
        {
            "symbol": "AEHR",
            "signal_date": "2025-02-07",
            "cluster_start_date": "2025-02-03",
            "cluster_end_date": "2025-02-07",
            "distinct_owner_count": 2,
            "cluster_value_usd": 120_000.0,
            "owner_names": "Owner A|Owner B",
        }
    ]

    trades = trial.build_form4_cluster_backtest_trades(
        clusters,
        prices,
        holding_days=90,
        round_trip_cost_bps=500,
    )

    assert len(trades) == 1
    assert trades[0]["signal_date"] == "2025-02-07"
    assert trades[0]["entry_date"] == "2025-02-10"
    assert trades[0]["exit_date"] > trades[0]["entry_date"]
    assert trades[0]["net_return"] == round(trades[0]["gross_return"] - 0.05, 10)
    assert trades[0]["short_selling_performed"] is False


def test_trial_run_writes_clean_artifacts_with_monkeypatched_sec_panel(tmp_path: Path, monkeypatch) -> None:
    prices = tmp_path / "prices.csv"
    _synthetic_prices(days=150, start="2025-01-02").to_csv(prices, index=False)

    def fake_panel(*, allowed_symbols: list[str], start_date: str, end_date: str, max_document_requests: int) -> list[dict]:
        return [
            _tx("AEHR", "Owner A", "2025-02-03", 70_000),
            _tx("AEHR", "Owner B", "2025-02-07", 80_000),
            _tx("CRMD", "Owner C", "2025-03-03", 75_000),
            _tx("CRMD", "Owner D", "2025-03-10", 75_000),
        ]

    monkeypatch.setattr(trial, "fetch_sec_form4_transaction_panel", fake_panel)
    decision = trial.run_form4_cluster_buying_trial_001(
        spec_dir=SPEC_DIR,
        price_file=prices,
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
        minimum_trade_count=2,
    )
    report = trial.validate_form4_cluster_buying_trial_output(tmp_path / "out")

    assert report["status"] == "pass"
    assert decision["backtest_performed"] is True
    assert decision["provider_query_performed"] is True
    assert decision["raw_payload_retained"] is False
    assert decision["short_selling_performed"] is False
    assert (tmp_path / "out" / "event_clusters.csv").is_file()
    assert (tmp_path / "out" / "trade_log.csv").is_file()


def _tx(symbol: str, owner: str, filing_date: str, value: float) -> dict:
    return {
        "symbol": symbol,
        "cik": "0000000000",
        "accessionNumber": f"{symbol}-{owner}-{filing_date}",
        "filingDate": filing_date,
        "acceptanceDateTime": f"{filing_date}T20:00:00",
        "transactionDate": filing_date,
        "ownerName": owner,
        "isDirector": True,
        "isOfficer": False,
        "isTenPercentOwner": False,
        "transactionCode": "P",
        "acquiredDisposedCode": "A",
        "shares": value / 10.0,
        "price": 10.0,
        "value_usd": value,
        "raw_payload_retained": False,
    }


def _form4_xml(transactions: list[tuple[str, str, str, float, float]]) -> str:
    tx_xml = "\n".join(
        f"""
        <nonDerivativeTransaction>
          <transactionDate><value>{date}</value></transactionDate>
          <transactionCoding><transactionCode>{code}</transactionCode></transactionCoding>
          <transactionAmounts>
            <transactionShares><value>{shares}</value></transactionShares>
            <transactionPricePerShare><value>{price}</value></transactionPricePerShare>
            <transactionAcquiredDisposedCode><value>{ad}</value></transactionAcquiredDisposedCode>
          </transactionAmounts>
        </nonDerivativeTransaction>
        """
        for code, ad, date, shares, price in transactions
    )
    return f"""<?xml version="1.0"?>
    <ownershipDocument>
      <issuer>
        <issuerCik>1410098</issuerCik>
        <issuerTradingSymbol>CRMD</issuerTradingSymbol>
      </issuer>
      <reportingOwner>
        <reportingOwnerId><rptOwnerName>Jane Director</rptOwnerName></reportingOwnerId>
        <reportingOwnerRelationship>
          <isDirector>1</isDirector>
          <isOfficer>0</isOfficer>
          <isTenPercentOwner>0</isTenPercentOwner>
        </reportingOwnerRelationship>
      </reportingOwner>
      <nonDerivativeTable>{tx_xml}</nonDerivativeTable>
    </ownershipDocument>
    """


def _synthetic_prices(days: int, start: str) -> pd.DataFrame:
    rows = []
    for index in range(days):
        date = (pd.Timestamp(start) + pd.offsets.BDay(index)).date().isoformat()
        for symbol, drift in (("AEHR", 0.001), ("CRMD", 0.002)):
            close = 10.0 * (1.0 + drift * index)
            rows.append(
                {
                    "symbol": symbol,
                    "date": date,
                    "open": close * 0.999,
                    "high": close * 1.01,
                    "low": close * 0.99,
                    "close": close,
                    "volume": 500_000,
                    "provider_dataset": "UNIT.TEST",
                }
            )
    return pd.DataFrame(rows)
