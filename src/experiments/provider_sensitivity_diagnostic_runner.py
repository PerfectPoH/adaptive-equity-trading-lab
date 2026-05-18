from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DEFAULT_PREFLIGHT_DIR = "experiments/provider_aware_research/dry_run_preflight_spec_20260518"
DEFAULT_MANUAL_INPUTS_DIR = "experiments/provider_aware_research/manual_preflight_inputs_resolution_spec_20260518"
FORBIDDEN_FLAGS = {"--all-symbols", "--sweep", "--promote", "--paper", "--live"}
REQUIRED_REAL_RUN_GATES = {
    "explicit_user_execution_approval",
    "immutable_output_directory_created",
    "trial_ledger_entry_created",
    "provider_credentials_checked_without_query",
    "final_command_review_completed",
}


def build_dry_run_plan(
    preregistration_id: str,
    trial_id: str,
    output_dir: str,
    preflight_dir: str | Path = DEFAULT_PREFLIGHT_DIR,
    manual_inputs_dir: str | Path = DEFAULT_MANUAL_INPUTS_DIR,
) -> dict[str, Any]:
    return {
        "status": "dry_run_only",
        "execution_performed": False,
        "provider_query_performed": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "preregistration_id": preregistration_id,
        "trial_id": trial_id,
        "planned_output_dir": output_dir,
        "preflight_dir": str(preflight_dir),
        "manual_inputs_dir": str(manual_inputs_dir),
        "required_next_approval": "explicit_user_execution_approval",
        "blocked_actions": sorted(FORBIDDEN_FLAGS),
    }


def build_real_run_block_report(
    preregistration_id: str,
    trial_id: str,
    output_dir: str,
    acknowledged_gates: set[str] | None = None,
) -> dict[str, Any]:
    acknowledged = acknowledged_gates or set()
    missing_gates = sorted(REQUIRED_REAL_RUN_GATES - acknowledged)
    return {
        "status": "blocked",
        "error": "real_run_gates_unresolved",
        "execution_performed": False,
        "provider_query_performed": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "preregistration_id": preregistration_id,
        "trial_id": trial_id,
        "planned_output_dir": output_dir,
        "required_gates": sorted(REQUIRED_REAL_RUN_GATES),
        "acknowledged_gates": sorted(acknowledged),
        "missing_gates": missing_gates,
    }


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args, unknown = parser.parse_known_args(argv)
    forbidden = sorted(FORBIDDEN_FLAGS.intersection(unknown))
    if forbidden:
        print(json.dumps(_error_report("forbidden_flags_present", f"forbidden={forbidden}"), indent=2, sort_keys=True))
        return 2
    if not args.dry_run and not args.real_run:
        print(json.dumps(_error_report("mode_required", "Pass --dry-run for planning or --real-run for blocked gate reporting."), indent=2, sort_keys=True))
        return 2
    if args.execute:
        print(json.dumps(_error_report("execute_forbidden", "--execute is not supported by this dry-only runner."), indent=2, sort_keys=True))
        return 2
    if args.real_run:
        report = build_real_run_block_report(
            preregistration_id=args.preregistration_id,
            trial_id=args.trial_id,
            output_dir=args.output_dir,
            acknowledged_gates=set(args.acknowledge_gate),
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    report = build_dry_run_plan(
        preregistration_id=args.preregistration_id,
        trial_id=args.trial_id,
        output_dir=args.output_dir,
        preflight_dir=args.preflight_dir,
        manual_inputs_dir=args.manual_inputs_dir,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dry-only provider sensitivity diagnostic runner.")
    parser.add_argument("--dry-run", action="store_true", help="Required. Build a non-executing diagnostic plan only.")
    parser.add_argument("--real-run", action="store_true", help="Blocked. Validate real-run gates without executing.")
    parser.add_argument("--execute", action="store_true", help="Forbidden. Present only to fail safely if attempted.")
    parser.add_argument("--acknowledge-gate", action="append", default=[], choices=sorted(REQUIRED_REAL_RUN_GATES), help="Acknowledge a required real-run gate for blocked readiness reporting.")
    parser.add_argument("--preregistration-id", required=True, help="Preregistration id to plan.")
    parser.add_argument("--trial-id", required=True, help="Trial id to plan.")
    parser.add_argument("--output-dir", required=True, help="Planned output directory. Not created by dry-run.")
    parser.add_argument("--preflight-dir", default=DEFAULT_PREFLIGHT_DIR, help="Dry-run preflight artifact directory.")
    parser.add_argument("--manual-inputs-dir", default=DEFAULT_MANUAL_INPUTS_DIR, help="Manual preflight inputs artifact directory.")
    return parser


def _error_report(error: str, detail: str) -> dict[str, Any]:
    return {
        "status": "blocked",
        "error": error,
        "detail": detail,
        "execution_performed": False,
        "provider_query_performed": False,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
    }


if __name__ == "__main__":
    raise SystemExit(main())
