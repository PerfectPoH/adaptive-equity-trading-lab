from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

from src.experiments.polygon_pit_construction_method_gate_validator import (
    validate_polygon_pit_construction_method_gate,
)


RUN_ID = "POLYGON-PIT-CONSTRUCTION-METHOD-GATE-RUN-001"
TRIAL_ID = "UNIVERSE-PIT-CONSTRUCTION-METHOD-GATE-001"
SPEC_DIR = Path("experiments/provider_aware_research/polygon_pit_construction_method_gate_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/POLYGON-PIT-CONSTRUCTION-METHOD-GATE-RUN-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Polygon-PIT-Construction-Method-Gate-2026-05-24.md")


def run_polygon_pit_construction_method_gate_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    gate = validate_polygon_pit_construction_method_gate(spec_dir)
    _write_json(output / "preflight_report.json", gate)
    if gate["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED")
        _write_json(output / "final_decision.json", decision)
        return decision
    manifest = json.loads((Path(spec_dir) / "method_manifest.json").read_text(encoding="utf-8"))
    listing_rows = _read_csv(Path(manifest["listing_date_sample"]))
    delisted_rows = _normalize_delisted_rows(_read_csv(Path(manifest["delisted_reference_sample"])))
    membership_rows = build_pit_membership_sample(
        listing_rows,
        delisted_rows,
        as_of_dates=[str(value) for value in manifest["as_of_dates"]],
    )
    decision = _decision(manifest, listing_rows, delisted_rows, membership_rows)
    _write_csv(output / "pit_membership_method_sample.csv", _fieldnames(membership_rows), membership_rows)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), decision)
    return decision


def is_member_asof(row: dict[str, Any], as_of_date: str) -> bool:
    listed = _parse_date(str(row.get("list_date", "") or ""))
    asof = _parse_date(as_of_date)
    if listed is None or asof is None or listed > asof:
        return False
    delisted = _parse_date(str(row.get("delisted_date", "") or ""))
    return delisted is None or asof < delisted


def build_pit_membership_sample(
    listing_rows: list[dict[str, Any]],
    delisted_rows: list[dict[str, Any]],
    *,
    as_of_dates: list[str],
) -> list[dict[str, str]]:
    universe = [row for row in _merge_security_rows(listing_rows, delisted_rows) if str(row.get("list_date", "") or "").strip()]
    output = []
    for as_of_date in as_of_dates:
        for row in sorted(universe, key=lambda item: str(item.get("ticker", ""))):
            output.append(
                {
                    "as_of_date": as_of_date,
                    "ticker": str(row.get("ticker", "")),
                    "primary_exchange": str(row.get("primary_exchange", "")),
                    "type": str(row.get("type", "")),
                    "active": str(row.get("active", "")),
                    "list_date": str(row.get("list_date", "")),
                    "delisted_date": str(row.get("delisted_date", "")),
                    "is_member": str(is_member_asof(row, as_of_date)),
                    "raw_payload_retained": "False",
                }
            )
    return output


def validate_polygon_pit_construction_method_gate_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["preflight_report.json", "pit_membership_method_sample.csv", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    decision = _read_json(path / "final_decision.json")
    sample = _read_csv(path / "pit_membership_method_sample.csv")
    columns = set(sample[0].keys()) if sample else set()
    forbidden = {"api_key", "raw_payload", "raw_json"}
    _check(checks, "no_provider_query", decision.get("provider_query_performed") is False, str(decision.get("provider_query_performed")))
    _check(checks, "no_market_download", decision.get("market_data_downloaded") is False, str(decision.get("market_data_downloaded")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "sample_method_approved", decision.get("pit_sample_construction_allowed") is True, str(decision.get("pit_sample_construction_allowed")))
    _check(checks, "broad_backtest_blocked", decision.get("broad_universe_backtest_allowed") is False, str(decision.get("broad_universe_backtest_allowed")))
    _check(checks, "promotion_blocked", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    _check(checks, "forbidden_columns_absent", not (columns & forbidden), f"present={sorted(columns & forbidden)}")
    return _report(checks)


def _decision(
    manifest: dict[str, Any],
    listing_rows: list[dict[str, Any]],
    delisted_rows: list[dict[str, Any]],
    membership_rows: list[dict[str, str]],
) -> dict[str, Any]:
    member_counts = {
        as_of_date: sum(1 for row in membership_rows if row["as_of_date"] == as_of_date and row["is_member"] == "True")
        for as_of_date in manifest["as_of_dates"]
    }
    return {
        "status": "complete",
        "decision": "POLYGON_PIT_CONSTRUCTION_METHOD_APPROVED_PARTIAL_SAMPLE_ONLY",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "membership_rule": manifest["membership_rule"],
        "as_of_dates": manifest["as_of_dates"],
        "listing_date_sample_count": len(listing_rows),
        "delisted_reference_sample_count": len(delisted_rows),
        "delisted_rows_with_listing_date_count": sum(1 for row in delisted_rows if str(row.get("list_date", "") or "").strip()),
        "membership_row_count": len(membership_rows),
        "member_counts_by_as_of_date": member_counts,
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
        "pit_sample_construction_allowed": True,
        "pit_universe_construction_allowed": False,
        "broad_universe_backtest_allowed": False,
        "broad_backtest_blockers": [
            "sample_only_method_gate",
            "delisted_listing_dates_unavailable_for_full_pit",
            "full_historical_membership_artifact_unbuilt",
            "strategy_trial_not_preregistered",
        ],
        "next_unblocked_step": "Preregister a bounded full-universe PIT artifact build before any broad-universe strategy backtest.",
    }


def _blocked_decision(reason: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": reason,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider_query_performed": False,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "pit_sample_construction_allowed": False,
        "pit_universe_construction_allowed": False,
        "broad_universe_backtest_allowed": False,
    }


def _merge_security_rows(listing_rows: list[dict[str, Any]], delisted_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for row in listing_rows + delisted_rows:
        ticker = str(row.get("ticker", "") or "")
        if ticker:
            merged[ticker] = row
    return list(merged.values())


def _normalize_delisted_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    normalized = []
    for row in rows[:10]:
        item = dict(row)
        item["delisted_date"] = _date_part(item.get("delisted_date") or item.get("delisted_utc") or "")
        item.setdefault("list_date", "")
        normalized.append(item)
    return normalized


def _date_part(value: str) -> str:
    return value[:10] if value else ""


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _write_vault_report(path: Path, decision: dict[str, Any]) -> None:
    text = (
        "# Report Polygon PIT Construction Method Gate - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "No-query method gate using archived derived metadata only. It builds a sample PIT membership table to validate the as-of rule, but it does not build a full PIT universe and does not authorize any strategy backtest.\n\n"
        "## Method\n\n"
        f"`{decision['membership_rule']}`\n\n"
        "## Result\n\n"
        f"- Listing-date sample count: {decision['listing_date_sample_count']}\n"
        f"- Delisted reference sample count: {decision['delisted_reference_sample_count']}\n"
        f"- Membership row count: {decision['membership_row_count']}\n"
        f"- Member counts by as-of date: {decision['member_counts_by_as_of_date']}\n"
        f"- Broad backtest allowed: {decision['broad_universe_backtest_allowed']}\n"
        f"- Broad backtest blockers: {', '.join(decision['broad_backtest_blockers'])}\n\n"
        "## Interpretation\n\n"
        "The PIT construction method is approved only at sample level. The next step must be a separately preregistered full-universe PIT artifact build; no broad strategy backtest is authorized by this gate.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    parser = argparse.ArgumentParser(description="Run Polygon PIT construction method gate 001.")
    parser.add_argument("--spec-dir", default=str(SPEC_DIR))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--vault-report", default=str(VAULT_REPORT))
    parser.add_argument("--validate-output", action="store_true")
    args = parser.parse_args(argv)
    if args.validate_output:
        report = validate_polygon_pit_construction_method_gate_output(args.output_dir)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1
    decision = run_polygon_pit_construction_method_gate_001(
        spec_dir=args.spec_dir,
        output_dir=args.output_dir,
        vault_report=args.vault_report,
    )
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
