from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import src.experiments.sec8k_tape_oracle_clean_run_002 as clean


def test_clean_run_blocks_without_databento_key(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(clean, "_resolve_databento_key", lambda: "")

    decision = clean.run_sec8k_tape_oracle_clean_run_002(
        spec_dir=clean.CLEAN_RUN_GATE_DIR,
        data_dir=tmp_path / "data",
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
    )

    assert decision["status"] == "blocked"
    assert decision["decision"] == "SEC8K_TAPE_ORACLE_CLEAN_RUN_002_BLOCKED"
    assert decision["provider_query_performed"] is False
    assert decision["market_data_downloaded"] is False


def test_clean_run_uses_preexisting_gate_and_writes_002_manifests(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(clean, "_resolve_databento_key", lambda: "test-key")
    monkeypatch.setattr(clean, "fetch_case_bars", _fake_fetch_case_bars)

    event_panel = tmp_path / "events.csv"
    prices = tmp_path / "prices.csv"
    pd.DataFrame([{"symbol": "AEHR", "reaction_session_date": "2026-01-09", "status": "event"}]).to_csv(event_panel, index=False)
    pd.DataFrame(
        [{"symbol": "AEHR", "date": date} for date in ["2026-01-02", "2026-01-05", "2026-01-06", "2026-01-07", "2026-01-08", "2026-01-09"]]
    ).to_csv(prices, index=False)

    decision = clean.run_sec8k_tape_oracle_clean_run_002(
        spec_dir=clean.CLEAN_RUN_GATE_DIR,
        event_panel_path=event_panel,
        price_file=prices,
        data_dir=tmp_path / "data",
        output_dir=tmp_path / "out",
        vault_report=tmp_path / "report.md",
        max_events_override=1,
    )

    dataset_manifest = json.loads((tmp_path / "data" / "dataset_manifest.json").read_text(encoding="utf-8"))
    final_decision = json.loads((tmp_path / "out" / "clean_run_final_decision.json").read_text(encoding="utf-8"))

    assert decision["run_id"] == "SEC8K-TAPE-ORACLE-CLEAN-RUN-002"
    assert dataset_manifest["run_id"] == "SEC8K-TAPE-ORACLE-CLEAN-RUN-002"
    assert dataset_manifest["query_count"] == 1
    assert final_decision["promotion_allowed"] is False
    assert final_decision["invalidated_run_usage"] == "blocked_audit_trail_only"


def _fake_fetch_case_bars(case: dict, api_key: str, data_root: Path) -> dict:
    case_dir = data_root / f"{case['symbol']}_{case['event_date']}"
    case_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(_bars(case["symbol"], case["event_date"])).to_csv(case_dir / "bars.csv", index=False)
    return {
        "symbol": case["symbol"],
        "event_date": case["event_date"],
        "control_dates": case["control_dates"],
        "dataset": case["dataset"],
        "schema": case["schema"],
        "start": case["start"],
        "end": case["end"],
        "status": "pass",
        "rows": 8,
        "detail": "fake_bars_written",
        "derived_bars_sha256": "fake",
        "raw_payload_retained": False,
        "bars_path": str(case_dir / "bars.csv"),
    }


def _bars(symbol: str, event_date: str) -> list[dict[str, object]]:
    rows = []
    for date, volume_scale in [("2026-01-08", 1), (event_date, 10)]:
        for hour, minute, price in [(9, 30, 10.0), (9, 44, 10.5), (9, 46, 10.5), (15, 55, 11.0)]:
            timestamp = pd.Timestamp(f"{date} {hour:02d}:{minute:02d}", tz="America/New_York").tz_convert("UTC").isoformat().replace("+00:00", "Z")
            rows.append({"symbol": symbol, "timestamp": timestamp, "open": price, "high": price, "low": price, "close": price, "volume": 100 * volume_scale})
    return rows
