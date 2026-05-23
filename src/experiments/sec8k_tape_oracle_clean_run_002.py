from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.experiments.sec8k_tape_oracle_clean_run_gate_validator import (
    validate_sec8k_tape_oracle_clean_run_gate,
)
from src.experiments.sec8k_tape_oracle_databento_mini_panel import (
    PRICE_FILE,
    _resolve_databento_key,
    fetch_case_bars,
    select_event_cases,
)
from src.experiments.sec8k_tape_oracle_existing_intraday_backtest import (
    CONTRACT_DIR,
    EVENT_PANEL,
    PREREG_DIR,
    run_existing_intraday_backtest,
    validate_existing_intraday_backtest,
)


RUN_ID = "SEC8K-TAPE-ORACLE-CLEAN-RUN-002"
TRIAL_ID = "TRIAL-SEC8K-DIRECTION-001"
CLEAN_RUN_GATE_DIR = Path("experiments/provider_aware_research/sec8k_tape_oracle_clean_run_gate_20260523")
DATA_DIR = Path("experiments/provider_aware_research/data_inputs/sec8k_tape_oracle_clean_run_002_20260523")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/SEC8K-TAPE-ORACLE-CLEAN-RUN-002")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-SEC8K-Tape-Oracle-Clean-Run-002-2026-05-23.md")


def run_sec8k_tape_oracle_clean_run_002(
    *,
    spec_dir: str | Path = CLEAN_RUN_GATE_DIR,
    event_panel_path: str | Path = EVENT_PANEL,
    price_file: str | Path = PRICE_FILE,
    data_dir: str | Path = DATA_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
    max_events_override: int | None = None,
) -> dict[str, Any]:
    spec_path = Path(spec_dir)
    data_root = Path(data_dir)
    output = Path(output_dir)
    data_root.mkdir(parents=True, exist_ok=True)
    output.mkdir(parents=True, exist_ok=True)

    gate_report = validate_sec8k_tape_oracle_clean_run_gate(spec_path)
    _write_json(output / "pre_run_gate_validation_report.json", gate_report)
    if gate_report["status"] != "pass":
        return _blocked_decision(output, data_root, "PRE_RUN_GATE_FAILED")

    manifest = _read_json(spec_path / "run_authorization_manifest.json")
    key = _resolve_databento_key()
    if not key:
        return _blocked_decision(output, data_root, "DATABENTO_API_KEY_MISSING")

    max_events = min(int(manifest["max_events"]), int(manifest["max_provider_calls"]))
    if max_events_override is not None:
        max_events = min(max_events, int(max_events_override))

    cases = select_event_cases(
        event_panel_path,
        price_file,
        max_events=max_events,
        control_sessions=int(manifest["control_sessions_per_event"]),
    )
    approved_symbols = set(manifest["approved_symbols"])
    cases = [case for case in cases if str(case["symbol"]) in approved_symbols]
    _write_csv(data_root / "selected_cases.csv", list(cases[0].keys()) if cases else [], cases)

    query_results = [fetch_case_bars(case, key, data_root) for case in cases]
    _write_csv(data_root / "query_results.csv", list(query_results[0].keys()) if query_results else [], query_results)

    dataset_manifest = _dataset_manifest(query_results, manifest)
    _write_json(data_root / "dataset_manifest.json", dataset_manifest)

    backtest_decision = run_existing_intraday_backtest(
        event_panel_path=event_panel_path,
        intraday_root=data_root,
        output_dir=output,
        prereg_dir=PREREG_DIR,
        contract_dir=CONTRACT_DIR,
        run_id=RUN_ID,
        trial_id=TRIAL_ID,
        write_report=False,
    )
    validation = validate_existing_intraday_backtest(output)
    _write_json(output / "clean_run_backtest_validation_report.json", validation)

    summary = _read_json(output / "backtest_summary.json")
    final_decision = _final_decision(dataset_manifest, summary, backtest_decision)
    _write_json(output / "clean_run_final_decision.json", final_decision)
    _write_vault_report(Path(vault_report), dataset_manifest, summary, final_decision)
    return final_decision


def _dataset_manifest(query_results: list[dict[str, Any]], manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "approval_id": manifest["approval_id"],
        "status": "complete",
        "query_count": len(query_results),
        "pass_count": sum(1 for row in query_results if row["status"] == "pass"),
        "empty_count": sum(1 for row in query_results if row["status"] == "empty"),
        "error_count": sum(1 for row in query_results if row["status"] == "error"),
        "max_provider_calls": manifest["max_provider_calls"],
        "raw_payload_retained": False,
        "invalidated_run_usage": manifest["invalidated_run_usage"],
        "provider_query_performed": bool(query_results),
        "market_data_downloaded": bool(query_results),
        "parameter_sweep_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }


def _final_decision(dataset_manifest: dict[str, Any], summary: dict[str, Any], backtest_decision: dict[str, Any]) -> dict[str, Any]:
    positive_trades = int(summary.get("positive_oracle_trade_count", 0))
    net_return = float(summary.get("net_return_sum_after_500bps", 0.0))
    blockers = list(summary.get("blockers", []))
    if net_return <= 0:
        blockers.append("net_return_after_500bps_not_positive")

    decision = "SEC8K_TAPE_ORACLE_CLEAN_RUN_002_ARCHIVE_COST_OR_SAMPLE_FAILED"
    dsr_cpcv_escalation = False
    if positive_trades >= 30 and net_return > 0:
        decision = "SEC8K_TAPE_ORACLE_CLEAN_RUN_002_CANDIDATE_REQUIRES_DSR_CPCV_POST_RUN_GATE"
        dsr_cpcv_escalation = True

    return {
        "status": "complete",
        "decision": decision,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider_query_performed": dataset_manifest["provider_query_performed"],
        "market_data_downloaded": dataset_manifest["market_data_downloaded"],
        "query_count": dataset_manifest["query_count"],
        "evaluated_event_count": summary.get("evaluated_event_count", 0),
        "positive_oracle_trade_count": positive_trades,
        "gross_return_sum": summary.get("gross_return_sum", 0.0),
        "net_return_sum_after_500bps": net_return,
        "invalidated_run_usage": dataset_manifest["invalidated_run_usage"],
        "parameter_sweep_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "promotion_allowed": False,
        "dsr_cpcv_escalation_allowed": dsr_cpcv_escalation,
        "blockers": sorted(set(blockers)),
        "source_backtest_decision": backtest_decision.get("decision"),
    }


def _blocked_decision(output: Path, data_root: Path, reason: str) -> dict[str, Any]:
    decision = {
        "status": "blocked",
        "decision": "SEC8K_TAPE_ORACLE_CLEAN_RUN_002_BLOCKED",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "reason": reason,
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "promotion_allowed": False,
    }
    _write_json(output / "clean_run_final_decision.json", decision)
    _write_json(data_root / "dataset_manifest.json", {"run_id": RUN_ID, "status": "blocked", "reason": reason, "provider_query_performed": False})
    return decision


def _write_vault_report(path: Path, dataset_manifest: dict[str, Any], summary: dict[str, Any], decision: dict[str, Any]) -> None:
    text = (
        "# Report SEC8K Tape Oracle Clean Run 002 - 2026-05-23\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Bounded Databento clean run authorized by a pre-existing gate. Raw payloads were not retained. "
        "The protocol-violated mini-panel 001 remains audit-trail only and was not used for thresholds, calibration, evidence, or promotion.\n\n"
        "## Data\n\n"
        f"- Query count: {dataset_manifest['query_count']}\n"
        f"- Pass count: {dataset_manifest['pass_count']}\n"
        f"- Empty count: {dataset_manifest['empty_count']}\n"
        f"- Error count: {dataset_manifest['error_count']}\n\n"
        "## Backtest\n\n"
        f"- Evaluated event count: {summary.get('evaluated_event_count', 0)}\n"
        f"- Positive oracle trade count: {summary.get('positive_oracle_trade_count', 0)}\n"
        f"- Gross return sum: {summary.get('gross_return_sum', 0.0)}\n"
        f"- Net return sum after 500 bps: {summary.get('net_return_sum_after_500bps', 0.0)}\n"
        f"- Blockers: {', '.join(decision['blockers']) if decision.get('blockers') else reason_text(decision)}\n\n"
        "## Decision Rule\n\n"
        "If cost or sample-size gates fail, archive without DSR/CPCV escalation. DSR/CPCV is reserved for candidates that first survive cost realism and minimum trade count.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def reason_text(decision: dict[str, Any]) -> str:
    return str(decision.get("reason", "none"))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run SEC8K Tape Oracle clean run 002.")
    parser.add_argument("--max-events", type=int, default=None)
    args = parser.parse_args(argv)
    decision = run_sec8k_tape_oracle_clean_run_002(max_events_override=args.max_events)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0 if decision["status"] in {"complete", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
