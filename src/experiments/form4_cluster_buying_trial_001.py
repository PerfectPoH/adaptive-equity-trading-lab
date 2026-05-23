from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from statistics import median
from typing import Any

import pandas as pd

from src.experiments.form4_cluster_buying_preregistration_validator import validate_form4_cluster_buying_preregistration


RUN_ID = "FORM4-CLUSTER-BUYING-BACKTEST-001"
TRIAL_ID = "TRIAL-FORM4-CLUSTER-BUYING-001"
SPEC_DIR = Path("experiments/provider_aware_research/form4_cluster_buying_preregistration_20260523")
PRICE_FILE = Path("experiments/provider_aware_research/data_inputs/databento_xmom_20260520/prices.csv")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/FORM4-CLUSTER-BUYING-BACKTEST-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Form4-Cluster-Buying-Trial-001-2026-05-23.md")
SEC_USER_AGENT = "adaptive-equity-trading-lab research-contact@example.com"


def run_form4_cluster_buying_trial_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    price_file: str | Path = PRICE_FILE,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
    minimum_trade_count: int | None = None,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    prereg = validate_form4_cluster_buying_preregistration(spec_dir)
    _write_json(output / "preflight_report.json", prereg)
    if prereg["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED")
        _write_json(output / "final_decision.json", decision)
        return decision

    manifest = json.loads((Path(spec_dir) / "preregistration_manifest.json").read_text(encoding="utf-8"))
    try:
        transactions = fetch_sec_form4_transaction_panel(
            allowed_symbols=list(manifest["allowed_symbols"]),
            start_date=str(manifest["start_date"]),
            end_date=str(manifest["end_date"]),
            max_document_requests=int(manifest["max_document_requests"]),
        )
        provider_error = None
    except Exception as exc:  # pragma: no cover - network failure path
        transactions = []
        provider_error = f"{type(exc).__name__}: {exc}"

    clusters = build_form4_clusters(
        transactions,
        cluster_window_days=int(manifest["cluster_window_days"]),
        min_distinct_owners=int(manifest["min_distinct_owners"]),
        min_cluster_value_usd=float(manifest["min_cluster_value_usd"]),
    )
    prices = pd.read_csv(price_file)
    trades = build_form4_cluster_backtest_trades(
        clusters,
        prices,
        holding_days=int(manifest["holding_days"]),
        round_trip_cost_bps=int(manifest["round_trip_cost_bps"]),
    )
    summary = summarize_form4_cluster_backtest(
        transactions,
        clusters,
        trades,
        minimum_trade_count=minimum_trade_count or int(manifest["minimum_trade_count"]),
        provider_error=provider_error,
    )
    decision = _final_decision(summary)
    _write_csv(output / "derived_form4_transactions.csv", _fieldnames(transactions), transactions)
    _write_csv(output / "event_clusters.csv", _fieldnames(clusters), clusters)
    _write_csv(output / "trade_log.csv", _fieldnames(trades), trades)
    _write_json(output / "backtest_summary.json", summary)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), summary, decision)
    return decision


def fetch_sec_form4_transaction_panel(
    *,
    allowed_symbols: list[str],
    start_date: str,
    end_date: str,
    max_document_requests: int,
) -> list[dict[str, Any]]:
    start = pd.Timestamp(start_date)
    end = pd.Timestamp(end_date)
    cik_by_symbol = _load_sec_company_tickers(allowed_symbols)
    rows: list[dict[str, Any]] = []
    requests_made = 0
    for symbol in allowed_symbols:
        cik = cik_by_symbol.get(symbol.upper())
        if not cik:
            continue
        submissions = _sec_json(f"https://data.sec.gov/submissions/CIK{cik}.json")
        recent = submissions.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accession_numbers = recent.get("accessionNumber", [])
        filing_dates = recent.get("filingDate", [])
        acceptance_datetimes = recent.get("acceptanceDateTime", [])
        primary_documents = recent.get("primaryDocument", [])
        for form, accession, filing_date, accepted, document in zip(forms, accession_numbers, filing_dates, acceptance_datetimes, primary_documents):
            filing_ts = pd.Timestamp(filing_date)
            if form not in {"4", "4/A"} or filing_ts < start or filing_ts > end:
                continue
            if requests_made >= max_document_requests:
                return rows
            accession_no_dashes = str(accession).replace("-", "")
            url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession_no_dashes}/{document}"
            xml_text = _sec_text(url)
            requests_made += 1
            rows.extend(
                parse_form4_xml(
                    xml_text,
                    symbol=symbol,
                    cik=cik,
                    accession_number=str(accession),
                    filing_date=str(filing_date),
                    acceptance_datetime=str(accepted),
                )
            )
            time.sleep(0.11)
    return rows


def parse_form4_xml(
    xml_text: str,
    *,
    symbol: str,
    cik: str,
    accession_number: str,
    filing_date: str,
    acceptance_datetime: str,
) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    owner = _text(root, ".//reportingOwner/reportingOwnerId/rptOwnerName") or "UNKNOWN"
    relationship = root.find(".//reportingOwner/reportingOwnerRelationship")
    is_director = _flag(relationship, "isDirector")
    is_officer = _flag(relationship, "isOfficer")
    is_ten_percent = _flag(relationship, "isTenPercentOwner")
    rows: list[dict[str, Any]] = []
    for tx in root.findall(".//nonDerivativeTransaction"):
        code = _text(tx, ".//transactionCoding/transactionCode")
        acquired = _text(tx, ".//transactionAmounts/transactionAcquiredDisposedCode/value")
        if code != "P" or acquired != "A":
            continue
        shares = _to_float(_text(tx, ".//transactionAmounts/transactionShares/value"))
        price = _to_float(_text(tx, ".//transactionAmounts/transactionPricePerShare/value"))
        tx_date = _text(tx, ".//transactionDate/value")
        if shares is None or price is None or shares <= 0 or price <= 0 or not tx_date:
            continue
        rows.append(
            {
                "symbol": symbol.upper(),
                "cik": str(cik).zfill(10),
                "accessionNumber": accession_number,
                "filingDate": filing_date,
                "acceptanceDateTime": acceptance_datetime,
                "transactionDate": tx_date,
                "ownerName": owner,
                "isDirector": is_director,
                "isOfficer": is_officer,
                "isTenPercentOwner": is_ten_percent,
                "transactionCode": code,
                "acquiredDisposedCode": acquired,
                "shares": round(shares, 6),
                "price": round(price, 6),
                "value_usd": round(shares * price, 2),
                "raw_payload_retained": False,
            }
        )
    return rows


def build_form4_clusters(
    transactions: list[dict[str, Any]],
    *,
    cluster_window_days: int,
    min_distinct_owners: int,
    min_cluster_value_usd: float,
) -> list[dict[str, Any]]:
    if not transactions:
        return []
    frame = pd.DataFrame(transactions).copy()
    frame["filingDate"] = pd.to_datetime(frame["filingDate"])
    clusters: list[dict[str, Any]] = []
    for symbol, group in frame.sort_values(["symbol", "filingDate", "ownerName"]).groupby("symbol"):
        used_until = pd.Timestamp.min
        rows = group.to_dict("records")
        for index, row in enumerate(rows):
            signal_date = pd.Timestamp(row["filingDate"])
            if signal_date <= used_until:
                continue
            start_date = signal_date - pd.Timedelta(days=cluster_window_days - 1)
            window = [candidate for candidate in rows[: index + 1] if start_date <= pd.Timestamp(candidate["filingDate"]) <= signal_date]
            owners = sorted({str(candidate["ownerName"]) for candidate in window})
            value = float(sum(float(candidate["value_usd"]) for candidate in window))
            if len(owners) < min_distinct_owners or value < min_cluster_value_usd:
                continue
            clusters.append(
                {
                    "run_id": RUN_ID,
                    "trial_id": TRIAL_ID,
                    "symbol": str(symbol),
                    "signal_date": signal_date.date().isoformat(),
                    "cluster_start_date": min(pd.Timestamp(candidate["filingDate"]) for candidate in window).date().isoformat(),
                    "cluster_end_date": signal_date.date().isoformat(),
                    "distinct_owner_count": len(owners),
                    "cluster_value_usd": round(value, 2),
                    "transaction_count": len(window),
                    "owner_names": "|".join(owners),
                    "raw_payload_retained": False,
                    "short_selling_allowed": False,
                }
            )
            used_until = signal_date + pd.Timedelta(days=cluster_window_days - 1)
    return clusters


def build_form4_cluster_backtest_trades(
    clusters: list[dict[str, Any]],
    prices: pd.DataFrame,
    *,
    holding_days: int,
    round_trip_cost_bps: int,
) -> list[dict[str, Any]]:
    frame = prices.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values(["symbol", "date"]).reset_index(drop=True)
    trading_dates = sorted(frame["date"].drop_duplicates().tolist())
    cost = round_trip_cost_bps / 10_000.0
    trades: list[dict[str, Any]] = []
    for cluster in clusters:
        symbol = str(cluster["symbol"])
        signal_date = pd.Timestamp(cluster["signal_date"])
        entry_date = _next_trading_date(trading_dates, signal_date)
        if entry_date is None:
            continue
        exit_date = _offset_trading_date(trading_dates, entry_date, holding_days)
        if exit_date is None:
            continue
        entry = _row(frame, symbol, entry_date)
        exit_ = _row(frame, symbol, exit_date)
        if entry is None or exit_ is None:
            continue
        entry_open = float(entry["open"])
        exit_close = float(exit_["close"])
        if entry_open <= 0:
            continue
        gross = exit_close / entry_open - 1.0
        trades.append(
            {
                "run_id": RUN_ID,
                "trial_id": TRIAL_ID,
                "symbol": symbol,
                "signal_date": signal_date.date().isoformat(),
                "entry_date": entry_date.date().isoformat(),
                "exit_date": exit_date.date().isoformat(),
                "distinct_owner_count": int(cluster["distinct_owner_count"]),
                "cluster_value_usd": float(cluster["cluster_value_usd"]),
                "entry_open": round(entry_open, 6),
                "exit_close": round(exit_close, 6),
                "gross_return": round(gross, 10),
                "round_trip_cost_bps": round_trip_cost_bps,
                "net_return": round(gross - cost, 10),
                "provider_query_performed": True,
                "market_data_downloaded": False,
                "raw_payload_retained": False,
                "parameter_sweep_performed": False,
                "short_selling_performed": False,
                "paper_trading_performed": False,
                "live_trading_performed": False,
                "promotion_allowed": False,
            }
        )
    return trades


def summarize_form4_cluster_backtest(
    transactions: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    trades: list[dict[str, Any]],
    *,
    minimum_trade_count: int,
    provider_error: str | None,
) -> dict[str, Any]:
    net = [float(row["net_return"]) for row in trades]
    gross = [float(row["gross_return"]) for row in trades]
    total_net = sum(net)
    total_gross = sum(gross)
    median_net = median(net) if net else 0.0
    ex_top3 = _sum_excluding_top(net, 3)
    blockers: list[str] = []
    if provider_error:
        blockers.append("sec_provider_query_error")
    if len(clusters) < minimum_trade_count:
        blockers.append(f"event_count_below_{minimum_trade_count}")
    if len(trades) < minimum_trade_count:
        blockers.append(f"trade_count_below_{minimum_trade_count}")
    if total_net <= 0:
        blockers.append("net_return_not_positive_after_500bps")
    if median_net <= 0:
        blockers.append("median_net_return_not_positive")
    if total_net > 0 and ex_top3 <= 0:
        blockers.append("sign_flip_ex_top3")
    decision = "FORM4_CLUSTER_BUYING_CANDIDATE_ONLY_REQUIRES_SEPARATE_VALIDATION" if not blockers else "FORM4_CLUSTER_BUYING_ARCHIVE_CURRENT_FORM"
    return {
        "status": "backtest_complete_sec_form4_bounded_query",
        "decision": decision,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "derived_transaction_count": len(transactions),
        "event_cluster_count": len(clusters),
        "trade_count": len(trades),
        "minimum_trade_count": minimum_trade_count,
        "gross_return_sum": round(total_gross, 10),
        "net_return_sum_after_500bps": round(total_net, 10),
        "median_net_return": round(median_net, 10),
        "net_win_rate": round(sum(1 for value in net if value > 0) / len(net), 6) if net else 0.0,
        "net_return_sum_ex_top3": round(ex_top3, 10),
        "symbols_traded": sorted({str(row["symbol"]) for row in trades}),
        "provider_query_performed": True,
        "provider_error": provider_error,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "backtest_performed": True,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
        "candidate_allowed": not blockers,
        "blockers": blockers or ["candidate_requires_separate_validation_gate"],
    }


def validate_form4_cluster_buying_trial_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["preflight_report.json", "derived_form4_transactions.csv", "event_clusters.csv", "trade_log.csv", "backtest_summary.json", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _validation_report(checks)
    summary = json.loads((path / "backtest_summary.json").read_text(encoding="utf-8"))
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    trades = _read_csv(path / "trade_log.csv")
    columns = set(trades[0].keys()) if trades else set()
    forbidden_cols = {"raw_xml", "raw_json", "optimized_threshold", "short_return"}
    _check(checks, "provider_query_recorded", summary.get("provider_query_performed") is True, str(summary.get("provider_query_performed")))
    _check(checks, "raw_payload_not_retained", summary.get("raw_payload_retained") is False and decision.get("raw_payload_retained") is False, str(summary))
    _check(checks, "market_download_blocked", summary.get("market_data_downloaded") is False, str(summary.get("market_data_downloaded")))
    _check(checks, "no_short_selling", summary.get("short_selling_performed") is False and decision.get("short_selling_performed") is False, str(decision))
    _check(checks, "decision_no_promotion", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    _check(checks, "forbidden_columns_absent", not (columns & forbidden_cols), f"present={sorted(columns & forbidden_cols)}")
    return _validation_report(checks)


def _load_sec_company_tickers(allowed_symbols: list[str]) -> dict[str, str]:
    payload = _sec_json("https://www.sec.gov/files/company_tickers.json")
    wanted = {symbol.upper() for symbol in allowed_symbols}
    result: dict[str, str] = {}
    for row in payload.values():
        symbol = str(row.get("ticker", "")).upper()
        if symbol in wanted:
            result[symbol] = str(row["cik_str"]).zfill(10)
    return result


def _sec_json(url: str) -> dict[str, Any]:
    return json.loads(_sec_text(url))


def _sec_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": SEC_USER_AGENT, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def _text(node: ET.Element, path: str) -> str | None:
    found = node.find(path)
    return found.text.strip() if found is not None and found.text else None


def _flag(node: ET.Element | None, tag: str) -> bool:
    if node is None:
        return False
    found = node.find(tag)
    return bool(found is not None and found.text and found.text.strip() in {"1", "true", "True", "Y"})


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def _row(frame: pd.DataFrame, symbol: str, date: pd.Timestamp) -> pd.Series | None:
    rows = frame[frame["symbol"].astype(str).eq(symbol) & frame["date"].eq(date)]
    if rows.empty:
        return None
    return rows.iloc[0]


def _next_trading_date(trading_dates: list[pd.Timestamp], signal_date: pd.Timestamp) -> pd.Timestamp | None:
    for date in trading_dates:
        if date > signal_date:
            return date
    return None


def _offset_trading_date(trading_dates: list[pd.Timestamp], entry_date: pd.Timestamp, offset: int) -> pd.Timestamp | None:
    try:
        index = trading_dates.index(entry_date)
    except ValueError:
        return None
    target = index + offset
    return trading_dates[target] if target < len(trading_dates) else None


def _sum_excluding_top(values: list[float], count: int) -> float:
    if not values:
        return 0.0
    ordered = sorted(values, reverse=True)
    return sum(ordered[count:]) if len(ordered) > count else 0.0


def _final_decision(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "complete",
        "decision": summary["decision"],
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "event_cluster_count": summary["event_cluster_count"],
        "trade_count": summary["trade_count"],
        "gross_return_sum": summary["gross_return_sum"],
        "net_return_sum_after_500bps": summary["net_return_sum_after_500bps"],
        "candidate_allowed": summary["candidate_allowed"],
        "promotion_allowed": False,
        "blockers": summary["blockers"],
        "provider_query_performed": True,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "backtest_performed": True,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
    }


def _blocked_decision(reason: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": "FORM4_CLUSTER_BUYING_BACKTEST_BLOCKED",
        "reason": reason,
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "short_selling_performed": False,
    }


def _write_vault_report(path: Path, summary: dict[str, Any], decision: dict[str, Any]) -> None:
    text = (
        "# Report Form 4 Cluster Buying Trial 001 - 2026-05-23\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Official SEC EDGAR Form 4 query bounded to AEHR, ARRY, CABA, CRMD and IOVA. Only derived transaction rows were retained. No raw SEC payload, market-data download, parameter sweep, short selling, paper/live trading, or promotion occurred.\n\n"
        "## Result\n\n"
        f"- Derived transaction count: {summary['derived_transaction_count']}\n"
        f"- Event cluster count: {summary['event_cluster_count']}\n"
        f"- Completed trade count: {summary['trade_count']}\n"
        f"- Gross return sum: {summary['gross_return_sum']}\n"
        f"- Net return sum after 500 bps: {summary['net_return_sum_after_500bps']}\n"
        f"- Median net return: {summary['median_net_return']}\n"
        f"- Net win rate: {summary['net_win_rate']}\n"
        f"- Net return sum ex-top3: {summary['net_return_sum_ex_top3']}\n"
        f"- Symbols traded: {', '.join(summary['symbols_traded'])}\n"
        f"- Blockers: {', '.join(summary['blockers'])}\n\n"
        "## Interpretation\n\n"
        "This is a long-only Form 4 cluster buying diagnostic. A positive result may only become a candidate for separate validation; it cannot promote a strategy in this run.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    return list(rows[0].keys()) if rows else []


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fieldnames:
            handle.write("\n")
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _validation_report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "FORM4_CLUSTER_BUYING_BACKTEST_OUTPUT_PASS" if failed == 0 else "FORM4_CLUSTER_BUYING_BACKTEST_OUTPUT_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Form 4 cluster buying trial 001.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_form4_cluster_buying_trial_001()
    report = validate_form4_cluster_buying_trial_output()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
