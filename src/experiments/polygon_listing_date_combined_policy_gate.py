from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


RUN_ID = "POLYGON-LISTING-DATE-COMBINED-POLICY-GATE-RUN-001"
TRIAL_ID = "UNIVERSE-LISTING-DATE-COMBINED-POLICY-GATE-001"
FIRST_SAMPLE = Path("experiments/provider_aware_research/execution_outputs/POLYGON-LISTING-DATE-COVERAGE-PROBE-001/derived_listing_date_coverage_sample.csv")
CONTINUATION_SAMPLE = Path("experiments/provider_aware_research/execution_outputs/POLYGON-LISTING-DATE-COVERAGE-CONTINUATION-001/derived_listing_date_continuation_sample.csv")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/POLYGON-LISTING-DATE-COMBINED-POLICY-GATE-RUN-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Polygon-Listing-Date-Combined-Policy-Gate-2026-05-24.md")


def run_polygon_listing_date_combined_policy_gate(
    *,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    decision = assess_combined_listing_date_policy([FIRST_SAMPLE, CONTINUATION_SAMPLE], expected_min_count=10)
    rows = decision["combined_listing_date_sample"]
    _write_csv(output / "combined_listing_date_sample.csv", _fieldnames(rows), rows)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), decision)
    return decision


def assess_combined_listing_date_policy(sample_paths: list[str | Path], *, expected_min_count: int) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    blockers: list[str] = []
    missing_files = []
    for sample_path in sample_paths:
        path = Path(sample_path)
        if not path.is_file():
            missing_files.append(str(path))
            continue
        rows.extend(_read_csv(path))
    deduped = {str(row.get("ticker", "")): row for row in rows if row.get("ticker")}
    combined = [deduped[ticker] for ticker in sorted(deduped)]
    sample_count = len(combined)
    list_date_present_count = sum(1 for row in combined if str(row.get("list_date", "")).strip())
    if missing_files:
        blockers.append("missing_source_listing_date_samples")
    if sample_count < expected_min_count:
        blockers.append("combined_sample_count_below_expected_min")
    if list_date_present_count < sample_count:
        blockers.append("missing_list_dates_in_combined_sample")
    passed = not blockers
    return {
        "status": "complete",
        "decision": "POLYGON_LISTING_DATE_SAMPLE_COVERAGE_PASS_NO_PIT_UNIVERSE" if passed else "POLYGON_LISTING_DATE_SAMPLE_COVERAGE_BLOCKED",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "source_files": [str(path) for path in sample_paths],
        "missing_source_files": missing_files,
        "sample_ticker_count": sample_count,
        "expected_min_count": expected_min_count,
        "list_date_present_count": list_date_present_count,
        "list_date_coverage": round(list_date_present_count / sample_count, 6) if sample_count else 0.0,
        "blockers": blockers,
        "combined_listing_date_sample": combined,
        "provider_query_performed": False,
        "provider_call_count": 0,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
        "broad_universe_backtest_allowed": False,
        "pit_universe_construction_allowed": False,
        "next_unblocked_step": "Preregister a no-backtest PIT construction method using listing dates, delisted metadata, and as-of membership rules.",
        "quality_scope": "combined_listing_date_sample_policy_only_not_pit_universe",
    }


def validate_polygon_listing_date_combined_policy_gate_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["combined_listing_date_sample.csv", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    sample = _read_csv(path / "combined_listing_date_sample.csv")
    columns = set(sample[0].keys()) if sample else set()
    forbidden = {"api_key", "raw_payload", "raw_json"}
    _check(checks, "no_provider_query", decision.get("provider_query_performed") is False, str(decision.get("provider_query_performed")))
    _check(checks, "raw_payload_not_retained", decision.get("raw_payload_retained") is False, str(decision.get("raw_payload_retained")))
    _check(checks, "no_market_download", decision.get("market_data_downloaded") is False, str(decision.get("market_data_downloaded")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "pit_construction_blocked", decision.get("pit_universe_construction_allowed") is False, str(decision.get("pit_universe_construction_allowed")))
    _check(checks, "broad_backtest_blocked", decision.get("broad_universe_backtest_allowed") is False, str(decision.get("broad_universe_backtest_allowed")))
    _check(checks, "scope_only", decision.get("quality_scope") == "combined_listing_date_sample_policy_only_not_pit_universe", str(decision.get("quality_scope")))
    _check(checks, "forbidden_columns_absent", not (columns & forbidden), f"present={sorted(columns & forbidden)}")
    return _report(checks)


def _write_vault_report(path: Path, decision: dict[str, Any]) -> None:
    text = (
        "# Report Polygon Listing Date Combined Policy Gate - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "No-query policy gate combining previously archived derived listing-date samples. No provider query, market-data download, backtest, parameter sweep, execution, short selling, or promotion occurred.\n\n"
        "## Result\n\n"
        f"- Sample ticker count: {decision['sample_ticker_count']}\n"
        f"- List-date present count: {decision['list_date_present_count']}\n"
        f"- List-date coverage: {decision['list_date_coverage']}\n"
        f"- Blockers: {', '.join(decision.get('blockers', []))}\n\n"
        "## Interpretation\n\n"
        "The sampled Polygon details stack now supports listing dates, but this does not authorize PIT universe construction or broad-universe backtests. The next step must be a separate PIT construction method gate.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    return list(rows[0].keys()) if rows else []


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


def _report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Polygon listing-date combined policy gate.")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--vault-report", default=str(VAULT_REPORT))
    parser.add_argument("--validate-output", action="store_true")
    args = parser.parse_args(argv)
    if args.validate_output:
        report = validate_polygon_listing_date_combined_policy_gate_output(args.output_dir)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1
    decision = run_polygon_listing_date_combined_policy_gate(output_dir=args.output_dir, vault_report=args.vault_report)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
