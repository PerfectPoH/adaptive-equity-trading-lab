from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_FILES = [
    "README.md",
    "source_scan_manifest.json",
    "candidate_sources.csv",
    "decision_rule.csv",
    "blocked_actions.csv",
    "source_scan_summary.md",
]

REQUIRED_BLOCKED_ACTIONS = {
    "provider_query",
    "web_scraping",
    "market_data_download",
    "extractor_implementation",
    "backtest",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
}

REQUIRED_SOURCES = {
    "Alpha Vantage Earnings",
    "SEC EDGAR Companyfacts",
    "Yahoo Finance unofficial",
    "Nasdaq Data Link Zacks",
    "Polygon Earnings",
}


def validate_pead_free_source_scan(scan_dir: str | Path) -> dict[str, Any]:
    path = Path(scan_dir)
    checks: list[dict[str, str]] = []
    _check(checks, "scan_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists():
        return _report(checks)

    for filename in REQUIRED_FILES:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)

    manifest = json.loads((path / "source_scan_manifest.json").read_text(encoding="utf-8"))
    candidates = _read_csv(path / "candidate_sources.csv")
    blocked = _read_csv(path / "blocked_actions.csv")
    summary = (path / "source_scan_summary.md").read_text(encoding="utf-8").lower()

    _check(checks, "scan_id", manifest.get("scan_id") == "PROBE-PEAD-FREE-SOURCE-SCAN-001", str(manifest.get("scan_id")))
    _check(checks, "status_spec_only", manifest.get("status") == "SPEC_ONLY_NOT_QUERIED", str(manifest.get("status")))
    _check(checks, "provider_query_blocked", manifest.get("provider_query_allowed") is False, str(manifest.get("provider_query_allowed")))
    _check(checks, "web_scraping_blocked", manifest.get("web_scraping_allowed") is False, str(manifest.get("web_scraping_allowed")))
    _check(checks, "extractor_blocked", manifest.get("extractor_implementation_allowed") is False, str(manifest.get("extractor_implementation_allowed")))
    _check(checks, "backtest_blocked", manifest.get("backtest_allowed") is False, str(manifest.get("backtest_allowed")))
    _check(checks, "promotion_blocked", manifest.get("promotion_allowed") is False, str(manifest.get("promotion_allowed")))

    actions = {row["action"] for row in blocked}
    all_blocked = all(row.get("status") == "blocked" for row in blocked)
    _check(checks, "blocked_actions_present", REQUIRED_BLOCKED_ACTIONS.issubset(actions), f"missing={sorted(REQUIRED_BLOCKED_ACTIONS - actions)}")
    _check(checks, "blocked_actions_all_blocked", all_blocked, f"all_blocked={all_blocked}")

    sources = {row["source"] for row in candidates}
    selected = [row for row in candidates if row.get("status") == "selected"]
    _check(checks, "candidate_sources_present", REQUIRED_SOURCES.issubset(sources), f"missing={sorted(REQUIRED_SOURCES - sources)}")
    _check(checks, "exactly_one_next_probe_selected", len(selected) == 1, f"selected={len(selected)}")
    if selected:
        selected_capabilities = []
        for row in selected:
            has_actual = row.get("actual_eps") in {"expected_available", "available"}
            has_consensus = row.get("consensus_eps") in {"expected_available", "available"}
            next_probe = row.get("next_action", "").startswith("PROBE-PEAD-")
            selected_capabilities.append(has_actual and has_consensus and next_probe)
        row = selected[0]
        _check(checks, "selected_candidate_has_required_capabilities", all(selected_capabilities), str(selected))
        _check(checks, "manifest_matches_selected_source", len(selected) == 1 and manifest.get("selected_source") == row.get("source"), str(manifest.get("selected_source")))
        _check(checks, "manifest_matches_selected_probe", len(selected) == 1 and manifest.get("selected_next_probe") == row.get("next_action"), str(manifest.get("selected_next_probe")))
    else:
        _check(checks, "selected_candidate_has_required_capabilities", False, "no selected row")
        _check(checks, "manifest_matches_selected_source", False, "no selected row")
        _check(checks, "manifest_matches_selected_probe", False, "no selected row")

    _check(checks, "summary_no_query_statement", "no provider query" in summary and "no provider query, scraping" in summary, "summary blocks queries")
    _check(checks, "summary_sec_edgar_consensus_blocker", "consensus eps" in summary and "cannot unlock sue alone" in summary, "SEC EDGAR blocker documented")

    return _report(checks)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "PEAD_FREE_SOURCE_SCAN_PASS" if failed == 0 else "PEAD_FREE_SOURCE_SCAN_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
        "provider_query_performed": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan-dir", required=True)
    args = parser.parse_args(argv)
    report = validate_pead_free_source_scan(args.scan_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
