from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


RUN_ID = "CANDIDATE-015-DATA-MESH-PROVIDER-SCAN-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_015_data_mesh_provider_scan_gate_20260607")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID
VAULT_NOTE = Path("vault/02-Devlog/2026-06/2026-06-07-data-mesh-provider-scan.md")

PROVIDER_REQUIREMENTS = [
    "minimum_5y_daily_ohlcv",
    "active_symbols",
    "delisted_symbols",
    "listing_dates",
    "delisting_dates",
    "delisting_terminal_return_policy",
    "adjusted_daily_ohlcv",
    "corporate_actions_documented",
    "security_master_or_stable_id",
    "point_in_time_universe",
    "spy_iwm_benchmarks",
    "storage_license_documented",
]


def build_data_mesh_provider_scan() -> dict[str, Any]:
    provider_matrix = _provider_matrix()
    micro_probe_plan = _micro_probe_plan()
    return {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "DATA_MESH_PROVIDER_SCAN_COMPLETE_NO_QUERY",
        "scope": "provider architecture scan only",
        "provider_query_performed": False,
        "market_data_download_performed": False,
        "dataset_build_performed": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "linked_blockers": {
            "candidate_013_databento": "databento_reference_entitlement_missing",
            "candidate_014_norgate_trial": "history_span_below_5_years",
        },
        "requirements": PROVIDER_REQUIREMENTS,
        "provider_matrix": provider_matrix,
        "micro_probe_plan": micro_probe_plan,
        "recommended_sequence": [
            "Prefer Norgate Full or CRSP/WRDS if accessible; they avoid building a fragile identity-reconciliation layer.",
            "If budget remains zero, run one gated micro-probe per free provider before any data mesh ingestion.",
            "Only build a hybrid mesh if at least one provider proves delisted price continuity and another proves corporate-action transparency.",
            "Do not run Candidate 012 until a separate fresh-data build gate points to an admissible dataset manifest.",
        ],
        "final_decision": {
            "decision": "DATA_MESH_PROVIDER_SCAN_COMPLETE_NO_QUERY",
            "backtest_allowed": False,
            "provider_query_allowed_now": False,
            "promotion_allowed": False,
            "next_allowed_action": "commit_one_provider_micro_probe_gate",
            "blockers": [
                "provider_claims_unverified_by_micro_probes",
                "hybrid_identity_reconciliation_not_built",
                "candidate_012_fresh_data_gate_still_required",
            ],
        },
    }


def run_candidate_015_data_mesh_provider_scan(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
    vault_note_path: Path = VAULT_NOTE,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    scan = build_data_mesh_provider_scan()
    persist_candidate_015_data_mesh_provider_scan(scan, output_dir=output_dir, vault_note_path=vault_note_path)
    return scan


def persist_candidate_015_data_mesh_provider_scan(
    scan: dict[str, Any],
    *,
    output_dir: Path = OUTPUT_DIR,
    vault_note_path: Path = VAULT_NOTE,
) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    vault_note_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "data_mesh_provider_scan.json", scan)
    _write_json(output_dir / "final_decision.json", scan["final_decision"])
    (output_dir / "data_mesh_provider_scan_report.md").write_text(_markdown_report(scan), encoding="utf-8")
    vault_note_path.write_text(_vault_note(scan), encoding="utf-8")
    return {
        "scan": output_dir / "data_mesh_provider_scan.json",
        "final_decision": output_dir / "final_decision.json",
        "report": output_dir / "data_mesh_provider_scan_report.md",
        "vault_note": vault_note_path,
    }


def _provider_matrix() -> list[dict[str, Any]]:
    return [
        {
            "provider": "Norgate Data Full US Stocks Platinum",
            "status": "ADMISSIBLE_IF_SUBSCRIBED",
            "role": "single-provider survivorship-aware daily equity source",
            "can_unlock": ["candidate_012_true_backtest", "historical_index_constituents", "delisted_coverage"],
            "requirements_claimed": [
                "minimum_5y_daily_ohlcv",
                "active_symbols",
                "delisted_symbols",
                "listing_dates",
                "delisting_dates",
                "adjusted_daily_ohlcv",
                "corporate_actions_documented",
                "point_in_time_universe",
                "spy_iwm_benchmarks",
            ],
            "blockers": ["subscription_required"],
            "candidate_012_backtest_allowed": False,
            "next_probe": "No probe needed if subscription is active; run fresh-data build gate directly.",
        },
        {
            "provider": "CRSP/WRDS",
            "status": "ADMISSIBLE_IF_ACCESS_GRANTED",
            "role": "institutional benchmark source for survivorship-free research",
            "can_unlock": ["candidate_012_true_backtest", "academic_grade_validation"],
            "requirements_claimed": PROVIDER_REQUIREMENTS[:-1],
            "blockers": ["institutional_access_required"],
            "candidate_012_backtest_allowed": False,
            "next_probe": "Verify account access and export licensing before any extraction.",
        },
        {
            "provider": "Databento Historical + Reference",
            "status": "BLOCKED_REFERENCE_ENTITLEMENT",
            "role": "high-quality price source plus paid reference layer",
            "can_unlock": ["price_history_if_reference_unblocked"],
            "requirements_claimed": ["minimum_5y_daily_ohlcv", "adjusted_daily_ohlcv"],
            "blockers": ["databento_reference_entitlement_missing"],
            "candidate_012_backtest_allowed": False,
            "next_probe": "Only retry after Reference entitlement changes.",
        },
        {
            "provider": "Norgate Trial",
            "status": "BLOCKED_HISTORY_DEPTH",
            "role": "local survivorship-aware trial source",
            "can_unlock": ["adapter_validation_only"],
            "requirements_claimed": ["active_symbols", "delisted_symbols", "adjusted_daily_ohlcv"],
            "blockers": ["history_span_below_5_years"],
            "candidate_012_backtest_allowed": False,
            "next_probe": "No further trial probe; upgrade to full history or stop.",
        },
        {
            "provider": "Tiingo",
            "status": "REQUIRES_MICRO_PROBES",
            "role": "candidate OHLCV/corporate-action/symbology component",
            "can_unlock": ["price_component_if_delisted_and_identity_pass"],
            "requirements_claimed": ["minimum_5y_daily_ohlcv", "adjusted_daily_ohlcv", "corporate_actions_documented"],
            "blockers": ["delisted_coverage_unverified", "permanent_identity_mapping_unverified", "license_cache_policy_unverified"],
            "candidate_012_backtest_allowed": False,
            "next_probe": "Bounded Tiingo active/split/ticker-change/delisted micro-probe.",
        },
        {
            "provider": "EODHD",
            "status": "REQUIRES_MICRO_PROBES",
            "role": "candidate delisted-list and terminal-price component",
            "can_unlock": ["delisted_component_if_terminal_price_passes"],
            "requirements_claimed": ["minimum_5y_daily_ohlcv", "delisted_symbols", "delisting_dates"],
            "blockers": ["terminal_return_policy_unverified", "corporate_action_policy_unverified", "license_cache_policy_unverified"],
            "candidate_012_backtest_allowed": False,
            "next_probe": "Bounded delisted endpoint plus terminal OHLCV continuity micro-probe.",
        },
        {
            "provider": "SimFin",
            "status": "REQUIRES_MICRO_PROBES",
            "role": "candidate fundamentals/PIT cross-check component",
            "can_unlock": ["corporate_action_cross_check_if_pit_passes"],
            "requirements_claimed": ["point_in_time_universe", "delisted_symbols"],
            "blockers": ["coverage_breadth_unverified", "price_history_sufficiency_unverified", "license_cache_policy_unverified"],
            "candidate_012_backtest_allowed": False,
            "next_probe": "Bounded PIT metadata and delisted availability probe.",
        },
        {
            "provider": "Financial Modeling Prep",
            "status": "REQUIRES_MICRO_PROBES",
            "role": "candidate benchmark/delisted redundancy component",
            "can_unlock": ["benchmark_or_delisted_redundancy_if_passes"],
            "requirements_claimed": ["spy_iwm_benchmarks", "delisted_symbols"],
            "blockers": ["legacy_endpoint_status_unverified", "delisted_quality_unverified", "license_cache_policy_unverified"],
            "candidate_012_backtest_allowed": False,
            "next_probe": "Bounded SPY/IWM and delisted endpoint availability probe.",
        },
        {
            "provider": "SEC EDGAR",
            "status": "REQUIRES_MICRO_PROBES",
            "role": "legal event source for Form 25 and CIK identity",
            "can_unlock": ["delisting_event_metadata_if_parser_passes"],
            "requirements_claimed": ["delisting_dates", "security_master_or_stable_id"],
            "blockers": ["form25_parser_not_validated", "terminal_price_not_provided", "rate_limit_policy_required"],
            "candidate_012_backtest_allowed": False,
            "next_probe": "One CIK/Form 25 bounded parser probe with SEC-compliant User-Agent.",
        },
        {
            "provider": "Hybrid Free Data Mesh",
            "status": "REQUIRES_MICRO_PROBES",
            "role": "assembled no-budget fallback only after component probes pass",
            "can_unlock": ["candidate_012_data_build_gate_only_if_all_identity_and_price_probes_pass"],
            "requirements_claimed": PROVIDER_REQUIREMENTS,
            "blockers": [
                "identity_reconciliation_unverified",
                "delisted_terminal_return_unverified",
                "corporate_action_policy_unverified",
                "licensing_and_cache_policy_unverified",
                "component_disagreement_resolution_unbuilt",
            ],
            "candidate_012_backtest_allowed": False,
            "next_probe": "Do not probe the mesh directly; probe each component first.",
        },
    ]


def _micro_probe_plan() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "ACTIVE_BASELINE_AAPL",
            "symbol": "AAPL",
            "purpose": "Verify active OHLCV depth, adjusted fields, split/dividend metadata, and license/cache policy.",
            "providers": ["Tiingo", "EODHD", "FMP"],
            "max_symbols": 1,
            "backtest_allowed": False,
        },
        {
            "case_id": "SPLIT_AAPL_2020",
            "symbol": "AAPL",
            "event_date": "2020-08-31",
            "purpose": "Verify split factor handling and adjusted/raw price consistency around a known split.",
            "providers": ["Tiingo", "EODHD", "FMP"],
            "max_symbols": 1,
            "backtest_allowed": False,
        },
        {
            "case_id": "TICKER_CHANGE_FB_META",
            "symbols": ["FB", "META"],
            "event_date": "2022-06-09",
            "purpose": "Verify identity continuity across a known ticker change.",
            "providers": ["Tiingo", "SEC EDGAR", "SimFin"],
            "max_symbols": 2,
            "backtest_allowed": False,
        },
        {
            "case_id": "DELISTING_BBBY",
            "symbols": ["BBBY", "BBBYQ"],
            "purpose": "Verify delisted price continuity and terminal date handling.",
            "providers": ["EODHD", "FMP", "SEC EDGAR", "Tiingo"],
            "max_symbols": 2,
            "backtest_allowed": False,
        },
        {
            "case_id": "BENCHMARK_SPY_IWM",
            "symbols": ["SPY", "IWM"],
            "purpose": "Verify benchmark adjusted OHLCV depth and dividend treatment.",
            "providers": ["Tiingo", "FMP", "EODHD"],
            "max_symbols": 2,
            "backtest_allowed": False,
        },
    ]


def _validate_gate(gate: dict[str, Any]) -> None:
    required = {
        "provider_query_allowed": False,
        "market_data_download_allowed": False,
        "raw_payload_retention_allowed": False,
        "dataset_build_allowed": False,
        "backtest_allowed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
    }
    if gate.get("status") != "APPROVED_DATA_MESH_PROVIDER_SCAN_NO_QUERY":
        raise RuntimeError("Candidate 015 data mesh provider scan gate is not approved.")
    for key, expected in required.items():
        if gate.get(key) is not expected:
            raise RuntimeError(f"Candidate 015 gate invalid: {key} must be {expected!r}.")


def _markdown_report(scan: dict[str, Any]) -> str:
    lines = [
        "# Candidate 015 Data Mesh Provider Scan",
        "",
        f"Decision: `{scan['decision']}`",
        "",
        "Scope: no-query provider architecture scan. This does not authorize provider calls, dataset builds, backtests, or promotion.",
        "",
        "## Provider Matrix",
        "",
        "| Provider | Status | Blockers | Next probe |",
        "|---|---|---|---|",
    ]
    for row in scan["provider_matrix"]:
        blockers = ", ".join(f"`{blocker}`" for blocker in row["blockers"]) or "None"
        lines.append(f"| {row['provider']} | `{row['status']}` | {blockers} | {row['next_probe']} |")
    lines.extend(
        [
            "",
            "## Micro-Probe Plan",
            "",
        ]
    )
    for case in scan["micro_probe_plan"]:
        lines.append(f"- `{case['case_id']}`: {case['purpose']} Providers: {', '.join(case['providers'])}.")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            "- Candidate 012 backtest remains blocked.",
            "- Hybrid Free Data Mesh is not trusted until component-level micro-probes pass.",
            "- Norgate Full or CRSP/WRDS remain the cleanest paths if access becomes available.",
        ]
    )
    return "\n".join(lines) + "\n"


def _vault_note(scan: dict[str, Any]) -> str:
    return (
        "# 2026-06-07 Data Mesh Provider Scan\n\n"
        f"Decision: `{scan['decision']}`\n\n"
        "The hybrid free-provider architecture is preserved as a research path, but not accepted as a backtest data source yet. "
        "Hybrid Free Data Mesh requires component-level micro-probe validation before any ingestion or Candidate 012 run.\n\n"
        "Next allowed action: commit one provider-specific micro-probe gate. No provider query, dataset build, backtest, or promotion is authorized by this scan.\n"
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    run_candidate_015_data_mesh_provider_scan()
