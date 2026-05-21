from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_REVIEW_DIR = "experiments/provider_aware_research/xmom_earnings_single_probe_theoretical_review_20260521"
EXPECTED_STATUS = "THEORETICAL_REVIEW_COMPLETE_NOT_APPROVED"
EXPECTED_PROVIDER = "Intrinio"
EXPECTED_SYMBOL = "CRMD"
REQUIRED_FILES = {
    "theoretical_review_manifest.json",
    "provider_candidate_review.csv",
    "timestamp_mapping_policy.csv",
    "review_sources.csv",
    "blocked_actions.csv",
    "README.md",
}
REQUIRED_BLOCKED_ACTIONS = {
    "create_live_approval_directory",
    "create_output_directory",
    "create_trial_ledger_entry",
    "execute_probe",
    "query_provider",
    "save_raw_payload",
    "implement_extractor",
    "run_oos",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
}
REQUIRED_CLASSIFICATIONS = {"BMO", "AMC", "DMT", "UNSPECIFIED"}


def validate_xmom_earnings_single_probe_theoretical_review(review_dir: str | Path = DEFAULT_REVIEW_DIR) -> dict[str, Any]:
    root = Path(review_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "review_dir_exists", root.exists() and root.is_dir(), str(root))
    if not root.exists() or not root.is_dir():
        return _report(root, checks)

    for filename in sorted(REQUIRED_FILES):
        _add_check(checks, f"required_file:{filename}", (root / filename).is_file(), str(root / filename))

    manifest = _read_json(root / "theoretical_review_manifest.json", checks)
    provider_review = _read_csv(root / "provider_candidate_review.csv", checks)
    timestamp_policy = _read_csv(root / "timestamp_mapping_policy.csv", checks)
    sources = _read_csv(root / "review_sources.csv", checks)
    blocked = _read_csv(root / "blocked_actions.csv", checks)
    readme = _read_text(root / "README.md", checks)

    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)
    if provider_review is not None:
        _validate_provider_review(provider_review, checks)
    if timestamp_policy is not None:
        _validate_timestamp_policy(timestamp_policy, checks)
    if sources is not None:
        _validate_sources(sources, checks)
    if blocked is not None:
        _validate_blocked(blocked, checks)
    if readme is not None:
        _validate_readme(readme, checks)

    return _report(root, checks)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate XMOM earnings single-probe theoretical review artifact.")
    parser.add_argument("--review-dir", default=DEFAULT_REVIEW_DIR)
    args = parser.parse_args(argv)
    report = validate_xmom_earnings_single_probe_theoretical_review(args.review_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    identity = (
        manifest.get("status") == EXPECTED_STATUS
        and manifest.get("provider_candidate") == EXPECTED_PROVIDER
        and manifest.get("symbol_candidate") == EXPECTED_SYMBOL
        and manifest.get("max_provider_calls_if_approved") == 1
    )
    not_approved = (
        manifest.get("approval_granted") is False
        and manifest.get("live_approval_directory_created") is False
        and manifest.get("output_directory_created") is False
        and manifest.get("trial_ledger_entry_created") is False
    )
    safe = (
        manifest.get("raw_payload_retention_allowed") is False
        and manifest.get("provider_query_performed") is False
        and manifest.get("network_call_performed") is False
        and manifest.get("market_data_downloaded") is False
        and manifest.get("extractor_implemented") is False
        and manifest.get("backtest_performed") is False
        and manifest.get("strategy_promotion_performed") is False
    )
    timestamp_field = bool(manifest.get("timestamp_field_candidate"))
    _add_check(checks, "manifest_review_identity", identity, f"status={manifest.get('status')}; provider={manifest.get('provider_candidate')}; symbol={manifest.get('symbol_candidate')}")
    _add_check(checks, "manifest_not_approved_or_prepared", not_approved, f"approval={manifest.get('approval_granted')}; live_dir={manifest.get('live_approval_directory_created')}")
    _add_check(checks, "manifest_no_execution_flags", safe, f"safe={safe}")
    _add_check(checks, "manifest_timestamp_field_declared", timestamp_field, f"timestamp_field={manifest.get('timestamp_field_candidate')}")


def _validate_provider_review(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"provider", "role", "fit_reason", "known_caveat", "decision"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "provider_review_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    providers = set(frame["provider"].astype(str))
    roles = set(frame["role"].astype(str))
    intrinio_row = frame[frame["provider"].astype(str).eq(EXPECTED_PROVIDER)]
    intrinio_primary = len(intrinio_row) == 1 and str(intrinio_row.iloc[0]["role"]) == "primary_candidate"
    has_alternatives = {"Databento", "Polygon"}.issubset(providers)
    _add_check(checks, "provider_review_intrinio_primary", intrinio_primary, f"roles={sorted(roles)}")
    _add_check(checks, "provider_review_alternatives_documented", has_alternatives, f"providers={sorted(providers)}")


def _validate_timestamp_policy(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"input_condition", "classification", "action", "notes"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "timestamp_policy_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    classifications = {str(value).strip() for value in frame["classification"]}
    missing_classes = sorted(REQUIRED_CLASSIFICATIONS - classifications)
    dmt_purged = _classification_action(frame, "DMT") == "purge"
    unspecified_purged = _classification_action(frame, "UNSPECIFIED") == "purge"
    timezone_required = "America/New_York" in classifications and "required" in set(frame["action"].astype(str))
    _add_check(checks, "timestamp_policy_required_classifications", not missing_classes, f"missing={missing_classes}")
    _add_check(checks, "timestamp_policy_dmt_and_unspecified_purged", dmt_purged and unspecified_purged, f"DMT={_classification_action(frame, 'DMT')}; UNSPECIFIED={_classification_action(frame, 'UNSPECIFIED')}")
    _add_check(checks, "timestamp_policy_timezone_declared", timezone_required, f"classifications={sorted(classifications)}")


def _validate_sources(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"source_name", "url", "source_type", "relevance"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "sources_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    official = frame["source_type"].astype(str).str.contains("official", case=False).all()
    urls = set(frame["url"].astype(str))
    has_intrinio = any("intrinio" in url.lower() for url in urls)
    has_databento = any("databento" in url.lower() for url in urls)
    has_polygon = any("massive.com" in url.lower() or "polygon" in url.lower() for url in urls)
    _add_check(checks, "sources_all_official_or_product_docs", bool(official), f"official={bool(official)}")
    _add_check(checks, "sources_cover_candidate_and_alternatives", has_intrinio and has_databento and has_polygon, f"urls={sorted(urls)}")


def _validate_blocked(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"action", "status", "reason"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "blocked_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    actions = set(frame["action"].astype(str))
    missing_actions = sorted(REQUIRED_BLOCKED_ACTIONS - actions)
    all_blocked = frame["status"].astype(str).str.lower().eq("blocked").all()
    _add_check(checks, "blocked_required_actions", not missing_actions, f"missing={missing_actions}")
    _add_check(checks, "blocked_all_actions_blocked", bool(all_blocked), f"all_blocked={bool(all_blocked)}")


def _validate_readme(text: str, checks: list[dict[str, str]]) -> None:
    lower = text.lower()
    _add_check(checks, "readme_status_not_approved", EXPECTED_STATUS.lower() in lower, "status marker")
    _add_check(checks, "readme_no_query_statement", "no provider query" in lower and "no network call" in lower, "no-query statement")
    _add_check(checks, "readme_mapping_purpose", "bmo/amc/dmt/unspecified" in lower, "mapping purpose")


def _classification_action(frame: pd.DataFrame, classification: str) -> str:
    rows = frame[frame["classification"].astype(str).str.strip().eq(classification)]
    if len(rows) != 1:
        return ""
    return str(rows.iloc[0]["action"]).strip()


def _read_json(path: Path, checks: list[dict[str, str]]) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, f"json_readable:{path.name}", False, f"{type(exc).__name__}: {exc}")
        return None
    _add_check(checks, f"json_readable:{path.name}", True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]]) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        _add_check(checks, f"csv_readable:{path.name}", False, f"{type(exc).__name__}: {exc}")
        return None
    _add_check(checks, f"csv_readable:{path.name}", not frame.empty, f"rows={len(frame)}")
    return frame


def _read_text(path: Path, checks: list[dict[str, str]]) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        _add_check(checks, f"text_readable:{path.name}", False, f"{type(exc).__name__}: {exc}")
        return None
    _add_check(checks, f"text_readable:{path.name}", bool(text.strip()), f"chars={len(text)}")
    return text


def _add_check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": str(detail)})


def _report(path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "review_dir": str(path),
        "status": "fail" if failed else "pass",
        "decision": "XMOM_EARNINGS_SINGLE_PROBE_THEORETICAL_REVIEW_PASS" if failed == 0 else "XMOM_EARNINGS_SINGLE_PROBE_THEORETICAL_REVIEW_FAIL",
        "approval_granted": False,
        "provider_query_performed": False,
        "network_call_performed": False,
        "extractor_implemented": False,
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
