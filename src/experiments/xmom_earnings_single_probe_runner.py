from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.experiments.xmom_earnings_single_probe_approval_validator import (
    validate_xmom_earnings_single_probe_approval,
)


DEFAULT_APPROVAL_DIR = "experiments/provider_aware_research/xmom_earnings_single_probe_approval_20260521"
EXPECTED_GATE_ID = "EARNINGS-SINGLE-PROBE-XMOM-CATALYST-001"
EXPECTED_TRIAL_ID = "TRIAL-XMOM-CATALYST-001"
REQUIRED_REAL_RUN_GATES = {
    "explicit_single_probe_approval_granted",
    "provider_selected",
    "symbol_selected",
    "endpoint_selected",
    "immutable_output_directory_created",
    "trial_ledger_entry_created",
    "raw_payload_retention_blocked",
}
FORBIDDEN_FLAGS = {
    "--all-symbols",
    "--multi-provider",
    "--download-market-data",
    "--save-raw-payload",
    "--implement-extractor",
    "--run-oos",
    "--paper",
    "--live",
    "--promote",
}


def build_dry_run_plan(
    *,
    approval_dir: str | Path = DEFAULT_APPROVAL_DIR,
    provider: str = "unselected",
    symbol: str = "unselected",
    endpoint: str = "earnings_calendar_or_equivalent",
    output_dir: str = "not_created",
) -> dict[str, Any]:
    approval_report = validate_xmom_earnings_single_probe_approval(approval_dir)
    return {
        "status": "dry_run_only",
        "gate_id": EXPECTED_GATE_ID,
        "trial_id": EXPECTED_TRIAL_ID,
        "approval_dir": str(approval_dir),
        "approval_gate_status": approval_report["status"],
        "approval_gate_decision": approval_report["gate_decision"],
        "provider": provider,
        "symbol": symbol,
        "endpoint": endpoint,
        "planned_output_dir": output_dir,
        "execution_performed": False,
        "provider_query_performed": False,
        "network_call_performed": False,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "extractor_implemented": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "required_next_approval": "explicit_single_probe_approval_granted",
        "blocked_actions": sorted(FORBIDDEN_FLAGS),
    }


def build_real_run_block_report(
    *,
    approval_dir: str | Path = DEFAULT_APPROVAL_DIR,
    provider: str = "unselected",
    symbol: str = "unselected",
    endpoint: str = "earnings_calendar_or_equivalent",
    output_dir: str = "not_created",
    acknowledged_gates: set[str] | None = None,
) -> dict[str, Any]:
    approval_report = validate_xmom_earnings_single_probe_approval(approval_dir)
    manifest = _read_manifest(Path(approval_dir))
    acknowledged = acknowledged_gates or set()
    missing = set(REQUIRED_REAL_RUN_GATES - acknowledged)
    if manifest.get("approval_status") != "granted":
        missing.add("explicit_single_probe_approval_granted")
    if provider in {"", "unselected"}:
        missing.add("provider_selected")
    if symbol in {"", "unselected"}:
        missing.add("symbol_selected")
    if endpoint in {"", "unselected"}:
        missing.add("endpoint_selected")
    if output_dir in {"", "not_created"}:
        missing.add("immutable_output_directory_created")
    if manifest.get("raw_payload_retention_allowed") is not False:
        missing.add("raw_payload_retention_blocked")

    return {
        "status": "blocked",
        "error": "single_probe_real_run_gates_unresolved",
        "gate_id": EXPECTED_GATE_ID,
        "trial_id": EXPECTED_TRIAL_ID,
        "approval_dir": str(approval_dir),
        "approval_gate_status": approval_report["status"],
        "approval_gate_decision": approval_report["gate_decision"],
        "approval_status": manifest.get("approval_status", "missing"),
        "provider": provider,
        "symbol": symbol,
        "endpoint": endpoint,
        "planned_output_dir": output_dir,
        "required_gates": sorted(REQUIRED_REAL_RUN_GATES),
        "acknowledged_gates": sorted(acknowledged),
        "missing_gates": sorted(missing),
        "execution_performed": False,
        "provider_query_performed": False,
        "network_call_performed": False,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "extractor_implemented": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args, unknown = parser.parse_known_args(argv)
    forbidden = sorted(FORBIDDEN_FLAGS.intersection(unknown))
    if forbidden:
        print(json.dumps(_blocked("forbidden_flags_present", f"forbidden={forbidden}"), indent=2, sort_keys=True))
        return 2
    if args.execute:
        print(json.dumps(_blocked("execute_forbidden", "--execute is not supported by this gated runner."), indent=2, sort_keys=True))
        return 2
    if not args.dry_run and not args.real_run:
        print(json.dumps(_blocked("mode_required", "Pass --dry-run or --real-run."), indent=2, sort_keys=True))
        return 2
    if args.dry_run and args.real_run:
        print(json.dumps(_blocked("conflicting_modes", "Choose only one mode."), indent=2, sort_keys=True))
        return 2
    if args.real_run:
        report = build_real_run_block_report(
            approval_dir=args.approval_dir,
            provider=args.provider,
            symbol=args.symbol,
            endpoint=args.endpoint,
            output_dir=args.output_dir,
            acknowledged_gates=set(args.acknowledge_gate),
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    report = build_dry_run_plan(
        approval_dir=args.approval_dir,
        provider=args.provider,
        symbol=args.symbol,
        endpoint=args.endpoint,
        output_dir=args.output_dir,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Gated dry-run runner for XMOM earnings single metadata probe.")
    parser.add_argument("--dry-run", action="store_true", help="Build a non-executing plan.")
    parser.add_argument("--real-run", action="store_true", help="Return a blocked real-run gate report.")
    parser.add_argument("--execute", action="store_true", help="Forbidden. Present only to fail safely if attempted.")
    parser.add_argument("--approval-dir", default=DEFAULT_APPROVAL_DIR)
    parser.add_argument("--provider", default="unselected")
    parser.add_argument("--symbol", default="unselected")
    parser.add_argument("--endpoint", default="earnings_calendar_or_equivalent")
    parser.add_argument("--output-dir", default="not_created")
    parser.add_argument("--acknowledge-gate", action="append", default=[], choices=sorted(REQUIRED_REAL_RUN_GATES))
    return parser


def _read_manifest(approval_dir: Path) -> dict[str, Any]:
    path = approval_dir / "single_probe_approval_manifest.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _blocked(error: str, detail: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "error": error,
        "detail": detail,
        "execution_performed": False,
        "provider_query_performed": False,
        "network_call_performed": False,
        "market_data_downloaded": False,
        "raw_payload_retained": False,
        "extractor_implemented": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
