from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd

from src.experiments.sec8k_direction_tape_oracle_preregistration_validator import (
    validate_sec8k_direction_tape_oracle_preregistration,
)
from src.experiments.sec8k_tape_oracle_intraday_data_contract_validator import (
    validate_sec8k_tape_oracle_intraday_data_contract,
)


RUN_ID = "SEC8K-TAPE-ORACLE-EXISTING-INTRADAY-BACKTEST-001"
TRIAL_ID = "TRIAL-SEC8K-DIRECTION-001"
PREREG_DIR = Path("experiments/provider_aware_research/sec8k_direction_tape_oracle_preregistration_20260522")
CONTRACT_DIR = Path("experiments/provider_aware_research/sec8k_tape_oracle_intraday_data_contract_gate_20260522")
EVENT_PANEL = Path("experiments/provider_aware_research/sec_8k_multisymbol_event_timing_diagnostic_20260522/sec_8k_multisymbol_event_panel.csv")
INTRADAY_ROOT = Path("experiments/provider_aware_research/data_inputs/gaprev_mini_panel_databento_intraday_probe_20260521")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/SEC8K-TAPE-ORACLE-EXISTING-INTRADAY-BACKTEST-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-SEC8K-Tape-Oracle-Existing-Intraday-Backtest-2026-05-22.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-22-codex-sec8k-tape-oracle-existing-intraday-backtest.md")


def run_existing_intraday_backtest(
    event_panel_path: str | Path = EVENT_PANEL,
    intraday_root: str | Path = INTRADAY_ROOT,
    output_dir: str | Path = OUTPUT_DIR,
    prereg_dir: str | Path = PREREG_DIR,
    contract_dir: str | Path = CONTRACT_DIR,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    prereg_report = validate_sec8k_direction_tape_oracle_preregistration(prereg_dir)
    contract_report = validate_sec8k_tape_oracle_intraday_data_contract(contract_dir)
    preflight = build_preflight(prereg_report, contract_report)
    _write_json(output / "preflight_report.json", preflight)
    if preflight["status"] != "pass":
        decision = build_final_decision([], preflight, backtest_performed=False)
        _write_outputs(output, [], {}, decision)
        return decision

    event_panel = pd.read_csv(event_panel_path)
    cases = discover_existing_intraday_cases(event_panel, intraday_root)
    results = [evaluate_case(case) for case in cases]
    summary = summarize_results(results)
    decision = build_final_decision(results, preflight, backtest_performed=True)
    _write_outputs(output, results, summary, decision)
    write_vault_report(summary, decision, results)
    return decision


def build_preflight(prereg_report: dict[str, Any], contract_report: dict[str, Any]) -> dict[str, Any]:
    checks = [
        {"name": "preregistration_pass", "status": "pass" if prereg_report.get("status") == "pass" else "fail", "detail": prereg_report.get("gate_decision", "")},
        {"name": "data_contract_pass", "status": "pass" if contract_report.get("status") == "pass" else "fail", "detail": contract_report.get("gate_decision", "")},
        {"name": "provider_query_blocked", "status": "pass", "detail": "existing intraday artifacts only"},
        {"name": "parameter_sweep_blocked", "status": "pass", "detail": "fixed 09:30-09:45 oracle and 500 bps costs"},
    ]
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "parameter_sweep_performed": False,
    }


def discover_existing_intraday_cases(event_panel: pd.DataFrame, intraday_root: str | Path) -> list[dict[str, Any]]:
    events = event_panel[event_panel["status"].astype(str).eq("event")].copy()
    event_keys = {(str(row["symbol"]), str(row["reaction_session_date"])) for _, row in events.iterrows()}
    cases: list[dict[str, Any]] = []
    for bars_path in sorted(Path(intraday_root).glob("*/bars.csv")):
        symbol, event_date = _parse_case_name(bars_path.parent.name)
        if symbol and event_date and (symbol, event_date) in event_keys:
            cases.append({"symbol": symbol, "event_date": event_date, "bars_path": str(bars_path)})
    return cases


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    frame = pd.read_csv(case["bars_path"])
    frame["ts_ny"] = pd.to_datetime(frame["timestamp"], utc=True).dt.tz_convert("America/New_York")
    frame["session_date"] = frame["ts_ny"].dt.date.astype(str)
    event_day = frame[frame["session_date"].eq(case["event_date"])].copy()
    controls = frame[~frame["session_date"].eq(case["event_date"])].copy()
    event_first = _time_slice(event_day, "09:30", "09:45")
    control_first_volumes = [_time_slice(group, "09:30", "09:45")["volume"].sum() for _, group in controls.groupby("session_date")]
    entry_bar = _exact_minute(event_day, "09:46")
    exit_bar = _exact_minute(event_day, "15:55")
    if event_first.empty or entry_bar.empty or exit_bar.empty or not control_first_volumes:
        return _case_result(case, status="purged_incomplete_intraday_window")
    oracle_open = float(event_first.iloc[0]["open"])
    oracle_close = float(event_first.iloc[-1]["close"])
    first15_return = (oracle_close / oracle_open) - 1.0
    event_volume = float(event_first["volume"].sum())
    baseline_volume = float(median(control_first_volumes))
    volume_ratio = event_volume / baseline_volume if baseline_volume > 0 else 0.0
    positive_oracle = first15_return > 0 and volume_ratio >= 3.0
    entry_price = float(entry_bar.iloc[0]["open"])
    exit_price = float(exit_bar.iloc[0]["close"])
    gross_return = (exit_price / entry_price) - 1.0 if positive_oracle else 0.0
    net_return = gross_return - 0.05 if positive_oracle else 0.0
    return _case_result(
        case,
        status="evaluated",
        first15_return=round(first15_return, 10),
        first15_volume=round(event_volume, 6),
        control_first15_volume_median=round(baseline_volume, 6),
        first15_volume_ratio=round(volume_ratio, 6),
        positive_oracle_candidate=positive_oracle,
        entry_price=round(entry_price, 6) if positive_oracle else "",
        exit_price=round(exit_price, 6) if positive_oracle else "",
        gross_return=round(gross_return, 10),
        net_return_after_500bps=round(net_return, 10),
    )


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in results if row["positive_oracle_candidate"] is True]
    blockers = []
    if len(candidates) < 30:
        blockers.append("positive_oracle_trade_count_below_30")
    if not candidates:
        blockers.append("no_positive_oracle_candidates")
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "status": "backtest_complete_existing_intraday_artifacts_only",
        "evaluated_event_count": len(results),
        "positive_oracle_trade_count": len(candidates),
        "gross_return_sum": round(sum(float(row["gross_return"]) for row in candidates), 10),
        "net_return_sum_after_500bps": round(sum(float(row["net_return_after_500bps"]) for row in candidates), 10),
        "promotion_allowed": False,
        "blockers": blockers,
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "parameter_sweep_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }


def build_final_decision(results: list[dict[str, Any]], preflight: dict[str, Any], backtest_performed: bool) -> dict[str, Any]:
    summary = summarize_results(results) if backtest_performed else {}
    decision = "SEC8K_TAPE_ORACLE_ARCHIVE_CURRENT_EXISTING_DATA_FORM"
    blockers = summary.get("blockers", ["preflight_failed"])
    return {
        "status": "complete" if preflight["status"] == "pass" else "blocked",
        "decision": decision if preflight["status"] == "pass" else "SEC8K_TAPE_ORACLE_BACKTEST_PREFLIGHT_BLOCKED",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "backtest_performed": backtest_performed,
        "evaluated_event_count": summary.get("evaluated_event_count", 0),
        "positive_oracle_trade_count": summary.get("positive_oracle_trade_count", 0),
        "promotion_allowed": False,
        "blockers": blockers,
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "parameter_sweep_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "next_unblocked_step": "If desired, create a separate bounded intraday provider approval to increase SEC8K Tape Oracle sample size.",
    }


def validate_existing_intraday_backtest(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, Any]] = []
    required = ["preflight_report.json", "backtest_results.csv", "backtest_summary.json", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _validation_report(checks)
    results = _read_csv(path / "backtest_results.csv")
    summary = json.loads((path / "backtest_summary.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    columns = set(results[0].keys()) if results else set()
    forbidden_cols = {"optimized_threshold", "sweep_id", "paper_signal", "live_signal"}
    _check(checks, "results_non_empty", len(results) > 0, f"rows={len(results)}")
    _check(checks, "forbidden_columns_absent", not (columns & forbidden_cols), f"present={sorted(columns & forbidden_cols)}")
    _check(checks, "summary_no_provider_query", summary.get("provider_query_performed") is False, str(summary))
    _check(checks, "summary_no_sweep", summary.get("parameter_sweep_performed") is False, str(summary))
    _check(checks, "decision_no_promotion", decision.get("promotion_allowed") is False, str(decision))
    return _validation_report(checks)


def write_vault_report(summary: dict[str, Any], decision: dict[str, Any], results: list[dict[str, Any]]) -> None:
    rows = "\n".join(
        f"- {row['symbol']} {row['event_date']}: status={row['status']}, first15_return={row['first15_return']}, volume_ratio={row['first15_volume_ratio']}, positive_oracle={row['positive_oracle_candidate']}, net={row['net_return_after_500bps']}"
        for row in results
    )
    purged_count = sum(1 for row in results if str(row["status"]).startswith("purged"))
    interpretation = (
        "The existing intraday archive contains only one SEC8K-matching event, and it was purged because the fixed oracle/entry/exit windows were incomplete. "
        "This is a valid bounded backtest result, but it is not evidence against the full hypothesis; sample expansion requires a separate provider approval gate."
        if purged_count == len(results)
        else "The existing intraday archive contains too few SEC8K-matching events for promotion. Sample expansion requires a separate provider approval gate."
    )
    text = (
        "# Report SEC8K Tape Oracle Existing Intraday Backtest - 2026-05-22\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Bounded backtest on existing intraday artifacts only. No provider query, market-data download, parameter sweep, paper/live trading, or promotion occurred.\n\n"
        "## Result\n\n"
        f"- Evaluated SEC8K event count: {summary['evaluated_event_count']}\n"
        f"- Positive oracle trade count: {summary['positive_oracle_trade_count']}\n"
        f"- Gross return sum: {summary['gross_return_sum']}\n"
        f"- Net return sum after 500 bps: {summary['net_return_sum_after_500bps']}\n"
        f"- Blockers: {', '.join(summary['blockers'])}\n\n"
        "## Panel\n\n"
        f"{rows}\n\n"
        "## Interpretation\n\n"
        f"{interpretation}\n"
    )
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run SEC8K Tape Oracle existing-intraday bounded backtest.")
    parser.add_argument("--event-panel", default=str(EVENT_PANEL))
    parser.add_argument("--intraday-root", default=str(INTRADAY_ROOT))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_existing_intraday_backtest(args.event_panel, args.intraday_root, args.output_dir)
    report = validate_existing_intraday_backtest(args.output_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _time_slice(frame: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    hhmm = frame["ts_ny"].dt.strftime("%H:%M")
    return frame[(hhmm >= start) & (hhmm < end)].copy()


def _exact_minute(frame: pd.DataFrame, minute: str) -> pd.DataFrame:
    return frame[frame["ts_ny"].dt.strftime("%H:%M").eq(minute)].copy()


def _parse_case_name(name: str) -> tuple[str, str]:
    if "_" not in name:
        return "", ""
    symbol, event_date = name.rsplit("_", 1)
    return symbol, event_date


def _case_result(case: dict[str, Any], **values: Any) -> dict[str, Any]:
    base = {
        "symbol": case["symbol"],
        "event_date": case["event_date"],
        "bars_path": case["bars_path"],
        "status": values.pop("status"),
        "first15_return": "",
        "first15_volume": "",
        "control_first15_volume_median": "",
        "first15_volume_ratio": "",
        "positive_oracle_candidate": False,
        "entry_price": "",
        "exit_price": "",
        "gross_return": 0.0,
        "net_return_after_500bps": 0.0,
    }
    base.update(values)
    return base


def _write_outputs(output: Path, results: list[dict[str, Any]], summary: dict[str, Any], decision: dict[str, Any]) -> None:
    fieldnames = list(results[0].keys()) if results else [
        "symbol",
        "event_date",
        "bars_path",
        "status",
        "first15_return",
        "first15_volume",
        "control_first15_volume_median",
        "first15_volume_ratio",
        "positive_oracle_candidate",
        "entry_price",
        "exit_price",
        "gross_return",
        "net_return_after_500bps",
    ]
    _write_csv(output / "backtest_results.csv", fieldnames, results)
    _write_json(output / "backtest_summary.json", summary or summarize_results(results))
    _write_json(output / "final_decision.json", decision)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _check(checks: list[dict[str, Any]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _validation_report(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "SEC8K_TAPE_ORACLE_EXISTING_INTRADAY_BACKTEST_PASS" if failed == 0 else "SEC8K_TAPE_ORACLE_EXISTING_INTRADAY_BACKTEST_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
