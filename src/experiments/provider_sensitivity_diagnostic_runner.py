from __future__ import annotations

import argparse
import csv
import json
import subprocess
from datetime import UTC, datetime
from importlib import import_module
from pathlib import Path
from typing import Any

from dotenv import dotenv_values

DEFAULT_PREFLIGHT_DIR = "experiments/provider_aware_research/dry_run_preflight_spec_20260518"
DEFAULT_MANUAL_INPUTS_DIR = "experiments/provider_aware_research/manual_preflight_inputs_resolution_spec_20260518"
DEFAULT_SPEC_DIR = "experiments/provider_sensitivity/provider_sensitivity_test_spec_20260518"
DEFAULT_CANDIDATES_FILE = "overlap_selection_candidates.csv"
DEFAULT_ENV_FILE = ".env"
DEFAULT_RUN_ID = "RUN-PREREG-PA-SMALLCAP-001-001"
DEFAULT_LEDGER_PATH = "experiments/provider_aware_research/trial_ledger/provider_sensitivity_trial_ledger.csv"
DEFAULT_MINI_PANEL_ID = "MINIPANEL-PREREG-PA-SMALLCAP-001-001"
DEFAULT_MINI_PANEL_GATE_DIR = "experiments/provider_aware_research/mini_panel_approval_gate_20260518"
DEFAULT_MINI_PANEL_APPROVAL_DIR = "experiments/provider_aware_research/mini_panel_explicit_approval_20260518"
DEFAULT_MINI_PANEL_LEDGER_PATH = "experiments/provider_aware_research/trial_ledger/mini_panel_trial_ledger.csv"
EXPECTED_PREREGISTRATION_ID = "PREREG-PA-SMALLCAP-001"
EXPECTED_TRIAL_ID = "TRIAL-001"
EXPECTED_MINI_PANEL_TRIAL_ID = "MINIPANEL-TRIAL-001"
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


def run_approved_mini_panel_diagnostic(
    preregistration_id: str,
    trial_id: str,
    output_dir: str | Path,
    *,
    gate_dir: str | Path = DEFAULT_MINI_PANEL_GATE_DIR,
    approval_dir: str | Path = DEFAULT_MINI_PANEL_APPROVAL_DIR,
    env_file: str | Path = DEFAULT_ENV_FILE,
    ledger_path: str | Path = DEFAULT_MINI_PANEL_LEDGER_PATH,
    skip_polygon: bool = False,
    candidate_checker: Any | None = None,
) -> dict[str, Any]:
    if preregistration_id != EXPECTED_PREREGISTRATION_ID or trial_id != EXPECTED_MINI_PANEL_TRIAL_ID:
        return _error_report("unexpected_mini_panel_identity", f"preregistration_id={preregistration_id}; trial_id={trial_id}")
    output_path = Path(output_dir)
    if output_path.name != DEFAULT_MINI_PANEL_ID or not output_path.exists() or not output_path.is_dir():
        return _error_report("approved_mini_panel_output_dir_missing", str(output_path))
    if (output_path / "mini_panel_execution_manifest.json").exists():
        return _error_report("mini_panel_already_executed", str(output_path / "mini_panel_execution_manifest.json"))
    candidates = _read_candidates(Path(gate_dir) / "mini_panel_candidates.csv")
    approval = _read_json(Path(approval_dir) / "mini_panel_explicit_approval_manifest.json")
    approval_error = _validate_mini_panel_approval(approval, candidates, output_path)
    if approval_error:
        return approval_error
    proposed_candidates = [candidate for candidate in candidates if candidate.get("candidate_role") == "proposed_new_query"]
    databento_key = _resolve_key("DATABENTO_API_KEY", Path(env_file))
    polygon_key = _resolve_key("POLYGON_API_KEY", Path(env_file))
    if not databento_key:
        return _error_report("databento_key_missing", "DATABENTO_API_KEY missing from approved credential source.")
    if not polygon_key and not skip_polygon:
        return _error_report("polygon_key_missing", "POLYGON_API_KEY missing from approved credential source.")
    checker = candidate_checker or _default_candidate_checker
    started_at = datetime.now(UTC).isoformat()
    results = [checker(candidate, databento_key, polygon_key, skip_polygon=skip_polygon) for candidate in proposed_candidates]
    completed_at = datetime.now(UTC).isoformat()
    git_sha = _git_sha()
    _write_result_rows(output_path / "provider_sensitivity_mini_panel_results.csv", results)
    execution_manifest = {
        "panel_id": DEFAULT_MINI_PANEL_ID,
        "preregistration_id": preregistration_id,
        "batch_trial_id": trial_id,
        "git_sha": git_sha,
        "execution_started_at_utc": started_at,
        "execution_completed_at_utc": completed_at,
        "execution_status": "completed",
        "provider_query_performed": True,
        "backtest_performed": False,
        "raw_payload_retained": False,
        "strategy_promotion": False,
        "candidate_count": len(candidates),
        "new_provider_query_count": len(results),
        "candidate_symbols": [str(result.get("symbol", "")) for result in results],
    }
    (output_path / "mini_panel_execution_manifest.json").write_text(json.dumps(execution_manifest, indent=2, sort_keys=True), encoding="utf-8")
    (output_path / "mini_panel_diagnostic_summary.json").write_text(json.dumps({"status": "completed", "results": results}, indent=2, sort_keys=True), encoding="utf-8")
    (output_path / "mini_panel_interpretation_report.md").write_text(_mini_panel_interpretation_report(results), encoding="utf-8")
    _append_mini_panel_execution_ledger(Path(ledger_path), preregistration_id, output_path, git_sha, proposed_candidates, results)
    return {
        "status": "completed",
        "execution_performed": True,
        "provider_query_performed": True,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "raw_payload_retained": False,
        "preregistration_id": preregistration_id,
        "trial_id": trial_id,
        "output_dir": str(output_path),
        "candidate_count": len(candidates),
        "new_provider_query_count": len(results),
        "results": results,
    }

def run_approved_single_diagnostic(
    preregistration_id: str,
    trial_id: str,
    output_dir: str | Path,
    *,
    spec_dir: str | Path = DEFAULT_SPEC_DIR,
    candidates_file: str = DEFAULT_CANDIDATES_FILE,
    env_file: str | Path = DEFAULT_ENV_FILE,
    ledger_path: str | Path = DEFAULT_LEDGER_PATH,
    skip_polygon: bool = False,
    candidate_checker: Any | None = None,
) -> dict[str, Any]:
    if preregistration_id != EXPECTED_PREREGISTRATION_ID or trial_id != EXPECTED_TRIAL_ID:
        return _error_report("unexpected_run_identity", f"preregistration_id={preregistration_id}; trial_id={trial_id}")
    output_path = Path(output_dir)
    if output_path.name != DEFAULT_RUN_ID or not output_path.exists() or not output_path.is_dir():
        return _error_report("approved_output_dir_missing", str(output_path))
    candidates = _read_candidates(Path(spec_dir) / candidates_file)
    if not candidates:
        return _error_report("no_candidates", str(Path(spec_dir) / candidates_file))
    databento_key = _resolve_key("DATABENTO_API_KEY", Path(env_file))
    polygon_key = _resolve_key("POLYGON_API_KEY", Path(env_file))
    if not databento_key:
        return _error_report("databento_key_missing", "DATABENTO_API_KEY missing from approved credential source.")
    if not polygon_key and not skip_polygon:
        return _error_report("polygon_key_missing", "POLYGON_API_KEY missing from approved credential source.")
    checker = candidate_checker or _default_candidate_checker
    started_at = datetime.now(UTC).isoformat()
    result = checker(candidates[0], databento_key, polygon_key, skip_polygon=skip_polygon)
    completed_at = datetime.now(UTC).isoformat()
    git_sha = _git_sha()
    _write_single_result(output_path / "provider_sensitivity_single_result.csv", result)
    execution_manifest = {
        "run_id": DEFAULT_RUN_ID,
        "preregistration_id": preregistration_id,
        "trial_id": trial_id,
        "git_sha": git_sha,
        "execution_started_at_utc": started_at,
        "execution_completed_at_utc": completed_at,
        "execution_status": "completed",
        "provider_query_performed": True,
        "backtest_performed": False,
        "raw_payload_retained": False,
        "strategy_promotion": False,
        "candidate_count": 1,
        "candidate_symbol": result.get("symbol", ""),
    }
    (output_path / "execution_manifest.json").write_text(json.dumps(execution_manifest, indent=2, sort_keys=True), encoding="utf-8")
    (output_path / "diagnostic_summary.json").write_text(json.dumps({"status": "completed", "result": result}, indent=2, sort_keys=True), encoding="utf-8")
    (output_path / "interpretation_report.md").write_text(_interpretation_report(result), encoding="utf-8")
    _append_execution_ledger(Path(ledger_path), preregistration_id, trial_id, output_path, git_sha)
    return {
        "status": "completed",
        "execution_performed": True,
        "provider_query_performed": True,
        "backtest_performed": False,
        "strategy_promotion_performed": False,
        "raw_payload_retained": False,
        "preregistration_id": preregistration_id,
        "trial_id": trial_id,
        "output_dir": str(output_path),
        "candidate_count": 1,
        "result": result,
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
    if args.approved_single_run and args.approved_mini_panel_run:
        print(json.dumps(_error_report("conflicting_approved_modes", "Choose only one approved execution mode."), indent=2, sort_keys=True))
        return 2
    if args.real_run and args.approved_single_run:
        report = run_approved_single_diagnostic(
            preregistration_id=args.preregistration_id,
            trial_id=args.trial_id,
            output_dir=args.output_dir,
            spec_dir=args.spec_dir,
            candidates_file=args.candidates_file,
            env_file=args.env_file,
            ledger_path=args.ledger_path,
            skip_polygon=args.skip_polygon,
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "completed" else 2
    if args.real_run and args.approved_mini_panel_run:
        report = run_approved_mini_panel_diagnostic(
            preregistration_id=args.preregistration_id,
            trial_id=args.trial_id,
            output_dir=args.output_dir,
            gate_dir=args.mini_panel_gate_dir,
            approval_dir=args.approval_dir,
            env_file=args.env_file,
            ledger_path=args.mini_panel_ledger_path,
            skip_polygon=args.skip_polygon,
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "completed" else 2
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
    parser.add_argument("--approved-single-run", action="store_true", help="Execute the approved single diagnostic run only.")
    parser.add_argument("--approved-mini-panel-run", action="store_true", help="Execute the approved bounded mini-panel diagnostic only.")
    parser.add_argument("--execute", action="store_true", help="Forbidden. Present only to fail safely if attempted.")
    parser.add_argument("--acknowledge-gate", action="append", default=[], choices=sorted(REQUIRED_REAL_RUN_GATES), help="Acknowledge a required real-run gate for blocked readiness reporting.")
    parser.add_argument("--preregistration-id", required=True, help="Preregistration id to plan.")
    parser.add_argument("--trial-id", required=True, help="Trial id to plan.")
    parser.add_argument("--output-dir", required=True, help="Planned output directory. Not created by dry-run.")
    parser.add_argument("--preflight-dir", default=DEFAULT_PREFLIGHT_DIR, help="Dry-run preflight artifact directory.")
    parser.add_argument("--manual-inputs-dir", default=DEFAULT_MANUAL_INPUTS_DIR, help="Manual preflight inputs artifact directory.")
    parser.add_argument("--spec-dir", default=DEFAULT_SPEC_DIR, help="Provider sensitivity spec directory containing candidates.")
    parser.add_argument("--candidates-file", default=DEFAULT_CANDIDATES_FILE, help="Candidate CSV file inside spec dir.")
    parser.add_argument("--env-file", default=DEFAULT_ENV_FILE, help="Approved env file for provider keys.")
    parser.add_argument("--ledger-path", default=DEFAULT_LEDGER_PATH, help="Trial ledger path to append execution result.")
    parser.add_argument("--mini-panel-gate-dir", default=DEFAULT_MINI_PANEL_GATE_DIR, help="Approved mini-panel gate artifact directory.")
    parser.add_argument("--approval-dir", default=DEFAULT_MINI_PANEL_APPROVAL_DIR, help="Explicit mini-panel approval artifact directory.")
    parser.add_argument("--mini-panel-ledger-path", default=DEFAULT_MINI_PANEL_LEDGER_PATH, help="Mini-panel trial ledger path to append execution result.")
    parser.add_argument("--skip-polygon", action="store_true", help="Skip Polygon reference query.")
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


def _read_candidates(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _resolve_key(name: str, env_file: Path) -> str:
    if not env_file.exists():
        return ""
    return str(dotenv_values(env_file).get(name) or "")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _validate_mini_panel_approval(approval: dict[str, Any], candidates: list[dict[str, str]], output_path: Path) -> dict[str, Any] | None:
    if approval.get("status") != "APPROVAL_GRANTED_FOR_MINI_PANEL_PREPARATION":
        return _error_report("mini_panel_approval_not_granted", f"status={approval.get('status')}")
    if approval.get("panel_id") != DEFAULT_MINI_PANEL_ID or approval.get("preregistration_id") != EXPECTED_PREREGISTRATION_ID:
        return _error_report("mini_panel_approval_identity_mismatch", f"panel_id={approval.get('panel_id')}; preregistration_id={approval.get('preregistration_id')}")
    if approval.get("provider_query_performed") is not False or approval.get("backtest_performed") is not False or approval.get("strategy_promotion_performed") is not False:
        return _error_report("mini_panel_approval_already_consumed_or_unsafe", "approval manifest must be pre-execution only.")
    if approval.get("raw_payload_retention_allowed") is not False:
        return _error_report("mini_panel_raw_retention_not_blocked", "raw payload retention must remain disabled.")
    if approval.get("output_directory_created") is not True or approval.get("trial_ledger_entries_created") is not True:
        return _error_report("mini_panel_pre_execution_artifacts_missing", "output directory and ledger entries must be prepared before execution.")
    max_new = int(approval.get("max_new_provider_queries", 0))
    max_total = int(approval.get("max_total_panel_candidates", 0))
    proposed = [candidate for candidate in candidates if candidate.get("candidate_role") == "proposed_new_query"]
    anchors = [candidate for candidate in candidates if candidate.get("candidate_role") == "executed_anchor"]
    if output_path.name != approval.get("panel_id"):
        return _error_report("mini_panel_output_identity_mismatch", f"output_dir={output_path}")
    if not 3 <= len(candidates) <= 5 or len(candidates) > max_total:
        return _error_report("mini_panel_candidate_count_out_of_bounds", f"candidate_count={len(candidates)}; max_total={max_total}")
    if len(anchors) != 1:
        return _error_report("mini_panel_anchor_count_invalid", f"anchor_count={len(anchors)}")
    if not proposed or len(proposed) > max_new:
        return _error_report("mini_panel_new_query_count_out_of_bounds", f"new_query_count={len(proposed)}; max_new={max_new}")
    if any(candidate.get("execution_status") != "not_executed" for candidate in proposed):
        return _error_report("mini_panel_candidate_already_executed", "all proposed candidates must be not_executed before mini-panel run.")
    if any(candidate.get("provider_query_allowed_without_new_approval") != "no" for candidate in candidates):
        return _error_report("mini_panel_candidate_approval_flag_invalid", "all candidates must require approval before provider query.")
    return None


def _default_candidate_checker(candidate: dict[str, str], databento_key: str, polygon_key: str, *, skip_polygon: bool) -> dict[str, object]:
    module = import_module("experiments.provider_sensitivity_micro_check")
    return module._check_candidate(candidate, databento_key, polygon_key, skip_polygon=skip_polygon)


def _write_single_result(path: Path, result: dict[str, object]) -> None:
    _write_result_rows(path, [result])


def _write_result_rows(path: Path, results: list[dict[str, object]]) -> None:
    fields: list[str] = []
    for result in results:
        for key in result:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(results)


def _append_execution_ledger(path: Path, preregistration_id: str, trial_id: str, output_dir: Path, git_sha: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if write_header:
            writer.writerow(["trial_id", "preregistration_id", "stage", "executed_at", "code_commit", "artifact_dir", "trial_number", "within_budget", "result_status", "decision", "notes"])
        writer.writerow([trial_id, preregistration_id, "new_signal_research", datetime.now(UTC).isoformat(), git_sha, str(output_dir), "1", "yes", "completed", "pending_interpretation", "approved_single_provider_sensitivity_diagnostic_executed"])


def _append_mini_panel_execution_ledger(path: Path, preregistration_id: str, output_dir: Path, git_sha: str, candidates: list[dict[str, str]], results: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if write_header:
            writer.writerow(["panel_id", "trial_id", "candidate_symbol", "candidate_role", "stage", "executed_at", "code_commit", "artifact_dir", "trial_number", "within_budget", "result_status", "decision", "notes"])
        for offset, candidate in enumerate(candidates, start=2):
            result = results[offset - 2]
            writer.writerow([DEFAULT_MINI_PANEL_ID, f"MINIPANEL-TRIAL-{offset:03d}", result.get("symbol", candidate.get("symbol", "")), candidate.get("candidate_role", ""), "new_signal_research", datetime.now(UTC).isoformat(), git_sha, str(output_dir), str(offset), "yes", "completed", "pending_interpretation", f"approved_mini_panel_provider_sensitivity_diagnostic_executed; preregistration_id={preregistration_id}"])


def _interpretation_report(result: dict[str, object]) -> str:
    return "\n".join([
        "# Provider sensitivity single diagnostic result",
        "",
        "```text",
        "APPROVED_SINGLE_DIAGNOSTIC_COMPLETED",
        "NO_RAW_PAYLOAD_RETENTION",
        "NO_BACKTEST",
        "NO_STRATEGY_PROMOTION",
        "```",
        "",
        f"symbol: {result.get('symbol', '')}",
        f"sensitivity_class: {result.get('sensitivity_class', '')}",
        f"databento_status: {result.get('databento_status', '')}",
        f"polygon_status: {result.get('polygon_status', '')}",
        "",
    ])


def _mini_panel_interpretation_report(results: list[dict[str, object]]) -> str:
    lines = [
        "# Provider sensitivity mini-panel diagnostic result",
        "",
        "```text",
        "APPROVED_MINI_PANEL_DIAGNOSTIC_COMPLETED",
        "NO_RAW_PAYLOAD_RETENTION",
        "NO_BACKTEST",
        "NO_STRATEGY_PROMOTION",
        "```",
        "",
        f"new_provider_query_count: {len(results)}",
        "",
    ]
    for result in results:
        lines.extend([
            f"symbol: {result.get('symbol', '')}",
            f"sensitivity_class: {result.get('sensitivity_class', '')}",
            f"databento_status: {result.get('databento_status', '')}",
            f"polygon_status: {result.get('polygon_status', '')}",
            "",
        ])
    return "\n".join(lines)



def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
