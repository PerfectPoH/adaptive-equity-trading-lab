from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from src.experiments.reference_data_provider_scan_validator import validate_reference_data_provider_scan_gate


RUN_ID = "REFERENCE-DATA-PROVIDER-SCAN-RUN-001"
TRIAL_ID = "REFERENCE-DATA-PROVIDER-SCAN-001"
SPEC_DIR = Path("experiments/provider_aware_research/reference_data_provider_scan_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/REFERENCE-DATA-PROVIDER-SCAN-RUN-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Reference-Data-Provider-Scan-001-2026-05-24.md")


def run_reference_data_provider_scan_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    gate = validate_reference_data_provider_scan_gate(spec_dir)
    _write_json(output / "preflight_report.json", gate)
    matrix = _read_csv(Path(spec_dir) / "provider_matrix.csv")
    scored = score_provider_candidates(matrix)
    decision = _decision(gate, scored)
    _write_csv(output / "provider_scorecard.csv", _fieldnames(scored), scored)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), decision, scored)
    return decision


def score_provider_candidates(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for row in rows:
        hard_passes = sum(1 for field in ("pit_membership", "delisted_symbols", "exchange_metadata", "security_type_metadata") if row.get(field) == "pass")
        maybe_count = sum(1 for field in ("pit_membership", "delisted_symbols", "exchange_metadata", "security_type_metadata") if row.get(field) == "maybe")
        feasible_bonus = 2 if row.get("api_probe_feasible") == "yes" else 1 if row.get("api_probe_feasible") == "maybe" else 0
        cost_bonus = {"free": 3, "paid_low": 2, "paid_medium": 1, "paid_unknown": 0}.get(row.get("pricing_status", ""), 0)
        score = hard_passes * 10 + maybe_count * 3 + feasible_bonus + cost_bonus
        if hard_passes == 4 and row.get("api_probe_feasible") == "yes":
            gate_status = "PROBE_CANDIDATE"
        elif hard_passes >= 2 and maybe_count > 0:
            gate_status = "NEEDS_ENTITLEMENT_VERIFICATION"
        else:
            gate_status = "BLOCKED_REFERENCE_METADATA_INSUFFICIENT"
        scored.append({**row, "score": score, "gate_status": gate_status})
    return sorted(scored, key=lambda item: (-int(item["score"]), str(item["provider"])))


def validate_reference_data_provider_scan_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["preflight_report.json", "provider_scorecard.csv", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    scorecard = _read_csv(path / "provider_scorecard.csv")
    columns = set(scorecard[0].keys()) if scorecard else set()
    _check(checks, "scorecard_non_empty", len(scorecard) >= 5, f"rows={len(scorecard)}")
    _check(checks, "scorecard_has_status", "gate_status" in columns and "score" in columns, str(columns))
    _check(checks, "no_provider_query", decision.get("provider_query_performed") is False, str(decision.get("provider_query_performed")))
    _check(checks, "no_market_download", decision.get("market_data_downloaded") is False, str(decision.get("market_data_downloaded")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "no_promotion", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    return _report(checks)


def _decision(gate: dict[str, Any], scored: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = [row for row in scored if row["gate_status"] == "PROBE_CANDIDATE"]
    selected = candidates[0] if candidates else (scored[0] if scored else {})
    return {
        "status": "complete" if gate.get("status") == "pass" else "blocked",
        "decision": "REFERENCE_DATA_PROVIDER_SCAN_COMPLETE_PROBE_CANDIDATE_SELECTED" if candidates else "REFERENCE_DATA_PROVIDER_SCAN_COMPLETE_NO_CLEAN_PROVIDER",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider_count": len(scored),
        "probe_candidate_count": len(candidates),
        "recommended_next_probe_provider": selected.get("provider", ""),
        "recommended_next_probe_url": selected.get("official_source_url", ""),
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
        "next_unblocked_step": "Preregister a single provider-specific source probe for the selected provider; do not download market data or run a strategy.",
    }


def _write_vault_report(path: Path, decision: dict[str, Any], scored: list[dict[str, Any]]) -> None:
    lines = [
        "# Report Reference Data Provider Scan 001 - 2026-05-24",
        "",
        f"Decision: `{decision['decision']}`",
        "",
        "## Scope",
        "",
        "Documentation scan only. No provider API query, market-data download, strategy backtest, parameter sweep, short selling, paper/live trading, or promotion occurred.",
        "",
        "## Result",
        "",
        f"- Providers scanned: {decision['provider_count']}",
        f"- Probe candidates: {decision['probe_candidate_count']}",
        f"- Recommended next probe: {decision['recommended_next_probe_provider']}",
        "",
        "## Scorecard",
        "",
    ]
    for row in scored:
        lines.append(
            f"- {row['provider']}: status={row['gate_status']} score={row['score']} pit={row['pit_membership']} delisted={row['delisted_symbols']} exchange={row['exchange_metadata']} type={row['security_type_metadata']} source={row['official_source_url']}"
        )
    lines.extend(["", "## Next Step", "", decision["next_unblocked_step"]])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    return list(rows[0].keys()) if rows else []


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
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
        "gate_decision": "REFERENCE_DATA_PROVIDER_SCAN_OUTPUT_PASS" if failed == 0 else "REFERENCE_DATA_PROVIDER_SCAN_OUTPUT_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run reference-data provider scan 001.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_reference_data_provider_scan_001()
    report = validate_reference_data_provider_scan_output()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
