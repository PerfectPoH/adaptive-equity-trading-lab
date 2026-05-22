from __future__ import annotations

import argparse
import csv
import json
import urllib.request
from datetime import date, timedelta
from pathlib import Path
from statistics import median
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from src.validation.earnings_timestamp_classifier import classify_earnings_timestamp


RUN_ID = "SEC-8K-MULTISYMBOL-TIMING-DIAGNOSTIC-001"
TRIAL_ID = "TRIAL-SEC-8K-MULTISYMBOL-TIMING-DIAGNOSTIC-001"
ROOT = Path("experiments/provider_aware_research")
PRICE_FILE = ROOT / "data_inputs" / "databento_xmom_20260520" / "prices.csv"
ARTIFACT_DIR = ROOT / "sec_8k_multisymbol_event_timing_diagnostic_20260522"
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-SEC-8K-Multisymbol-Event-Timing-Diagnostic-2026-05-22.md")
VAULT_DEVLOG = Path("vault/02-Devlog/2026-05/2026-05-22-codex-sec-8k-multisymbol-event-timing-diagnostic.md")
SEC_UA = "adaptive-equity-trading-lab research-contact@example.com"
NY = ZoneInfo("America/New_York")
DEFAULT_EXCLUDED_SYMBOLS = {"IWM"}


def run_sec_8k_multisymbol_event_timing_diagnostic(
    price_file: str | Path = PRICE_FILE,
    symbols: list[str] | None = None,
    lookback_days: int = 20,
    min_event_count: int = 30,
) -> dict[str, Any]:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    prices = pd.read_csv(price_file)
    selected_symbols = symbols or infer_equity_symbols(prices)
    events = fetch_sec_8k_item_202_events(selected_symbols)
    _write_csv(ARTIFACT_DIR / "sec_8k_multisymbol_event_panel.csv", _event_fieldnames(), events)
    timing_panel = build_multisymbol_timing_panel(events, prices, lookback_days=lookback_days)
    _write_csv(ARTIFACT_DIR / "sec_8k_multisymbol_timing_panel.csv", list(timing_panel[0].keys()) if timing_panel else [], timing_panel)
    _write_csv(ARTIFACT_DIR / "blocked_actions.csv", ["action", "status", "reason"], build_blocked_actions())
    summary = summarize_multisymbol_timing_panel(
        timing_panel,
        symbols=selected_symbols,
        event_count_fetched=len(events),
        lookback_days=lookback_days,
        min_event_count=min_event_count,
    )
    _write_json(ARTIFACT_DIR / "diagnostic_summary.json", summary)
    decision = write_final_decision(summary)
    write_vault_report(summary, decision, events)
    return decision


def infer_equity_symbols(prices: pd.DataFrame) -> list[str]:
    symbols = sorted(str(value) for value in prices["symbol"].dropna().unique())
    return [symbol for symbol in symbols if symbol not in DEFAULT_EXCLUDED_SYMBOLS]


def fetch_sec_8k_item_202_events(symbols: list[str]) -> list[dict[str, Any]]:
    ticker_payload = _fetch_json("https://www.sec.gov/files/company_tickers.json")
    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        match = _find_ticker(ticker_payload, symbol)
        if match is None:
            rows.append(_event_error(symbol, "symbol_not_found_in_sec_company_tickers"))
            continue
        cik = f"{int(match['cik_str']):010d}"
        try:
            submissions = _fetch_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
        except Exception as exc:  # pragma: no cover - network/provider dependent
            rows.append(_event_error(symbol, f"sec_submissions_error:{type(exc).__name__}"))
            continue
        for record in _extract_recent_earnings_8k_records(submissions):
            classified = classify_earnings_timestamp(str(record.get("acceptanceDateTime", "")))
            if classified.classification not in {"BMO", "AMC"}:
                continue
            acceptance_utc = pd.Timestamp(record["acceptanceDateTime"], tz="UTC")
            rows.append(
                {
                    "status": "event",
                    "symbol": symbol,
                    "cik": cik,
                    "accessionNumber": record["accessionNumber"],
                    "filingDate": record["filingDate"],
                    "acceptanceDateTime": record["acceptanceDateTime"],
                    "classification": classified.classification,
                    "reaction_session_date": _reaction_session_date(acceptance_utc, classified.classification).isoformat(),
                    "items": record["items"],
                    "event_source": "SEC_EDGAR_8K_ITEM_2_02",
                    "raw_payload_retained": False,
                }
            )
    return rows


def build_multisymbol_timing_panel(events: list[dict[str, Any]], prices: pd.DataFrame, lookback_days: int) -> list[dict[str, Any]]:
    event_dates_by_symbol: dict[str, set[str]] = {}
    for row in events:
        if row.get("status") != "event":
            continue
        event_dates_by_symbol.setdefault(str(row["symbol"]), set()).add(str(row["reaction_session_date"]))
    rows: list[dict[str, Any]] = []
    for symbol in sorted(event_dates_by_symbol):
        symbol_prices = prices[prices["symbol"].astype(str).eq(symbol)].copy()
        if symbol_prices.empty:
            continue
        symbol_prices["date"] = pd.to_datetime(symbol_prices["date"])
        symbol_prices = symbol_prices.sort_values("date").reset_index(drop=True)
        for index, price_row in symbol_prices.iterrows():
            if index < lookback_days:
                continue
            previous_close = float(symbol_prices.iloc[index - 1]["close"])
            close = float(price_row["close"])
            if previous_close <= 0:
                continue
            lookback = symbol_prices.iloc[index - lookback_days : index]
            volumes = [float(value) for value in lookback["volume"].tolist() if float(value) > 0]
            if not volumes:
                continue
            current_date = price_row["date"].date().isoformat()
            median_volume = median(volumes)
            rows.append(
                {
                    "symbol": symbol,
                    "date": current_date,
                    "is_sec_8k_event_day": current_date in event_dates_by_symbol[symbol],
                    "return_abs": round(abs(close / previous_close - 1.0), 10),
                    "signed_return": round(close / previous_close - 1.0, 10),
                    "volume": int(float(price_row["volume"])),
                    "volume_ratio_vs_20d_median": round(float(price_row["volume"]) / median_volume if median_volume > 0 else 0.0, 8),
                    "lookback_days": lookback_days,
                    "source": "sec_edgar_submissions_and_existing_databento_prices",
                }
            )
    return rows


def summarize_multisymbol_timing_panel(
    rows: list[dict[str, Any]],
    *,
    symbols: list[str],
    event_count_fetched: int,
    lookback_days: int,
    min_event_count: int,
) -> dict[str, Any]:
    events = [row for row in rows if row["is_sec_8k_event_day"] is True]
    controls = [row for row in rows if row["is_sec_8k_event_day"] is False]
    event_abs = _median_value(events, "return_abs")
    control_abs = _median_value(controls, "return_abs")
    event_volume = _median_value(events, "volume_ratio_vs_20d_median")
    control_volume = _median_value(controls, "volume_ratio_vs_20d_median")
    abs_lift = event_abs - control_abs
    volume_lift = event_volume - control_volume
    blockers: list[str] = []
    if len(events) < min_event_count:
        blockers.append(f"event_count_below_{min_event_count}")
    if event_abs <= control_abs:
        blockers.append("event_abs_return_not_above_control")
    if event_volume <= control_volume:
        blockers.append("event_volume_ratio_not_above_control")
    decision = "SEC_8K_MULTISYMBOL_TIMING_CANDIDATE_ONLY" if not blockers else "SEC_8K_MULTISYMBOL_TIMING_ARCHIVE_CURRENT_FORM"
    return {
        "status": "diagnostic_complete_sec_queries_bounded",
        "decision": decision,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "symbols": symbols,
        "lookback_days": lookback_days,
        "min_event_count": min_event_count,
        "event_count_fetched": event_count_fetched,
        "event_day_count": len(events),
        "control_day_count": len(controls),
        "event_median_abs_return": round(event_abs, 10),
        "control_median_abs_return": round(control_abs, 10),
        "abs_return_lift": round(abs_lift, 10),
        "event_median_volume_ratio": round(event_volume, 8),
        "control_median_volume_ratio": round(control_volume, 8),
        "volume_ratio_lift": round(volume_lift, 8),
        "candidate_timing_signal_allowed": not blockers,
        "promotion_allowed": False,
        "blockers": blockers or ["candidate_requires_separate_preregistration_and_direction_source"],
        "provider_query_performed": True,
        "provider": "SEC EDGAR submissions API",
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }


def write_final_decision(summary: dict[str, Any]) -> dict[str, Any]:
    decision = {
        "status": "complete",
        "decision": summary["decision"],
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "symbols": summary["symbols"],
        "event_day_count": summary["event_day_count"],
        "control_day_count": summary["control_day_count"],
        "candidate_timing_signal_allowed": summary["candidate_timing_signal_allowed"],
        "promotion_allowed": False,
        "blockers": summary["blockers"],
        "provider_query_performed": True,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "next_unblocked_step": "If candidate_timing_signal_allowed is true, preregister a separate event-window regime study; still no trade direction without ex-ante surprise or catalyst classification.",
    }
    _write_json(ARTIFACT_DIR / "final_decision.json", decision)
    return decision


def validate_sec_8k_multisymbol_event_timing_diagnostic(diag_dir: str | Path = ARTIFACT_DIR) -> dict[str, Any]:
    path = Path(diag_dir)
    checks: list[dict[str, Any]] = []
    required = [
        "sec_8k_multisymbol_event_panel.csv",
        "sec_8k_multisymbol_timing_panel.csv",
        "blocked_actions.csv",
        "diagnostic_summary.json",
        "final_decision.json",
    ]
    _check(checks, "diagnostic_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    events = _read_csv(path / "sec_8k_multisymbol_event_panel.csv")
    panel = _read_csv(path / "sec_8k_multisymbol_timing_panel.csv")
    blocked = _read_csv(path / "blocked_actions.csv")
    summary = json.loads((path / "diagnostic_summary.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    panel_columns = set(panel[0].keys()) if panel else set()
    forbidden_columns = {"pnl", "sharpe", "dsr", "strategy_return", "optimized_threshold"}
    _check(checks, "event_panel_has_events", any(row.get("status") == "event" for row in events), f"rows={len(events)}")
    _check(checks, "timing_panel_non_empty", len(panel) > 0, f"rows={len(panel)}")
    _check(checks, "forbidden_columns_absent", not (panel_columns & forbidden_columns), f"present={sorted(panel_columns & forbidden_columns)}")
    _check(checks, "has_event_and_control_days", _has_both_classes(panel), "event/control")
    _check(checks, "blocked_actions_all_blocked", all(row["status"] == "blocked" for row in blocked), "blocked")
    _check(checks, "summary_sec_query_bounded", summary.get("provider_query_performed") is True and summary.get("raw_payload_retained") is False, str(summary))
    _check(checks, "summary_no_backtest", summary.get("backtest_performed") is False and summary.get("market_data_downloaded") is False, str(summary))
    _check(checks, "decision_no_promotion", decision.get("promotion_allowed") is False, str(decision))
    return _report(checks)


def write_vault_report(summary: dict[str, Any], decision: dict[str, Any], events: list[dict[str, Any]]) -> None:
    by_symbol: dict[str, int] = {}
    for row in events:
        if row.get("status") == "event":
            by_symbol[str(row["symbol"])] = by_symbol.get(str(row["symbol"]), 0) + 1
    symbol_rows = "\n".join(f"- {symbol}: {count}" for symbol, count in sorted(by_symbol.items()))
    text = (
        "# Report SEC 8-K Multisymbol Event Timing Diagnostic - 2026-05-22\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Bounded multi-symbol SEC EDGAR Item 2.02 timing diagnostic on symbols already present in the XMOM Databento price panel. "
        "SEC submissions were queried for event timestamps; no raw SEC payload was retained. Existing Databento prices were reused. "
        "No market-data download, strategy backtest, parameter sweep, paper/live trading or promotion was performed.\n\n"
        "## Result\n\n"
        f"- Symbols: {', '.join(summary['symbols'])}\n"
        f"- Event days covered by prices: {summary['event_day_count']}\n"
        f"- Control days: {summary['control_day_count']}\n"
        f"- Event median absolute return: {summary['event_median_abs_return']}\n"
        f"- Control median absolute return: {summary['control_median_abs_return']}\n"
        f"- Absolute-return lift: {summary['abs_return_lift']}\n"
        f"- Event median volume ratio: {summary['event_median_volume_ratio']}\n"
        f"- Control median volume ratio: {summary['control_median_volume_ratio']}\n"
        f"- Volume-ratio lift: {summary['volume_ratio_lift']}\n"
        f"- Blockers: {', '.join(summary['blockers'])}\n\n"
        "## Events By Symbol\n\n"
        f"{symbol_rows}\n\n"
        "## Interpretation\n\n"
        "This diagnostic tests whether SEC 8-K Item 2.02 acceptance timing marks high-volatility/high-volume regimes across multiple issuers. "
        "It does not infer earnings surprise or tradable direction from future returns.\n"
    )
    VAULT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    VAULT_DEVLOG.parent.mkdir(parents=True, exist_ok=True)
    VAULT_REPORT.write_text(text, encoding="utf-8")
    VAULT_DEVLOG.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run multi-symbol SEC 8-K event timing diagnostic.")
    parser.add_argument("--price-file", default=str(PRICE_FILE))
    parser.add_argument("--symbols", default="")
    parser.add_argument("--lookback-days", type=int, default=20)
    parser.add_argument("--min-event-count", type=int, default=30)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    symbols = [value.strip().upper() for value in args.symbols.split(",") if value.strip()] or None
    if not args.validate_only:
        run_sec_8k_multisymbol_event_timing_diagnostic(args.price_file, symbols, args.lookback_days, args.min_event_count)
    report = validate_sec_8k_multisymbol_event_timing_diagnostic()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def build_blocked_actions() -> list[list[Any]]:
    return [
        ["retain_raw_sec_payload", "blocked", "Only derived event rows are retained."],
        ["infer_direction_from_returns", "blocked", "Would create look-ahead leakage."],
        ["run_strategy_backtest", "blocked", "Timing regime diagnostic only."],
        ["parameter_sweep", "blocked", "No optimized event-window thresholds."],
        ["paper_trading", "blocked", "No strategy has been promoted."],
        ["live_trading", "blocked", "No strategy has been promoted."],
    ]


def _reaction_session_date(acceptance_utc: pd.Timestamp, classification: str) -> date:
    local = acceptance_utc.tz_convert(NY)
    if classification == "AMC":
        return _next_weekday(local.date())
    return local.date()


def _next_weekday(day: date) -> date:
    candidate = day + timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def _fetch_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": SEC_UA, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _find_ticker(payload: dict[str, Any], symbol: str) -> dict[str, Any] | None:
    upper = symbol.upper()
    for value in payload.values():
        if str(value.get("ticker", "")).upper() == upper:
            return value
    return None


def _extract_recent_earnings_8k_records(submissions: dict[str, Any]) -> list[dict[str, Any]]:
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    rows = []
    for idx, form in enumerate(forms):
        items = _get_recent_value(recent, "items", idx)
        if form != "8-K" or "2.02" not in str(items):
            continue
        rows.append(
            {
                "accessionNumber": _get_recent_value(recent, "accessionNumber", idx),
                "filingDate": _get_recent_value(recent, "filingDate", idx),
                "acceptanceDateTime": _get_recent_value(recent, "acceptanceDateTime", idx),
                "items": items,
            }
        )
    return rows


def _get_recent_value(recent: dict[str, list[Any]], key: str, idx: int) -> Any:
    values = recent.get(key, [])
    if idx >= len(values):
        return ""
    return values[idx]


def _event_error(symbol: str, reason: str) -> dict[str, Any]:
    return {
        "status": "error",
        "symbol": symbol,
        "cik": "",
        "accessionNumber": "",
        "filingDate": "",
        "acceptanceDateTime": "",
        "classification": "",
        "reaction_session_date": "",
        "items": "",
        "event_source": "SEC_EDGAR_8K_ITEM_2_02",
        "raw_payload_retained": False,
        "error": reason,
    }


def _event_fieldnames() -> list[str]:
    return [
        "status",
        "symbol",
        "cik",
        "accessionNumber",
        "filingDate",
        "acceptanceDateTime",
        "classification",
        "reaction_session_date",
        "items",
        "event_source",
        "raw_payload_retained",
        "error",
    ]


def _median_value(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    return median(float(row[key]) for row in rows)


def _has_both_classes(rows: list[dict[str, str]]) -> bool:
    values = {str(row["is_sec_8k_event_day"]).lower() for row in rows}
    return "true" in values and "false" in values


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]] | list[list[Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        if rows and isinstance(rows[0], dict):
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)  # type: ignore[arg-type]
        else:
            writer = csv.writer(handle)
            writer.writerow(fieldnames)
            writer.writerows(rows)  # type: ignore[arg-type]


def _check(checks: list[dict[str, Any]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, Any]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "SEC_8K_MULTISYMBOL_TIMING_DIAGNOSTIC_PASS" if failed == 0 else "SEC_8K_MULTISYMBOL_TIMING_DIAGNOSTIC_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
