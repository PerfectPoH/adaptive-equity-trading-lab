from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_FILES = [
    "README.md",
    "implementation_gate_spec.md",
    "implementation_gate_manifest.json",
    "phase_contract.csv",
    "blind_threshold_policy.csv",
    "validation_math_policy.csv",
    "blocked_actions.csv",
    "source_review.csv",
]

REQUIRED_MANIFEST_FIELDS = {
    "status",
    "gate_id",
    "trial_id",
    "preregistration_id",
    "no_provider_query",
    "no_oos_execution",
    "no_parameter_sweep",
    "no_paper_trading",
    "no_live_trading",
    "no_strategy_promotion",
    "phase_1_required",
    "phase_2_single_pass_required",
    "blind_threshold_selection_required",
    "cpcv_required",
    "purging_required",
    "embargo_required",
    "trial_accounting_required",
    "dsr_required",
    "dsr_minimum_confidence",
    "effective_trial_count_required",
}

REQUIRED_PHASES = {
    "PHASE_1_FEATURE_DISCOVERY",
    "PHASE_1_CPCV_VALIDATION",
    "PHASE_1_TRIAL_ACCOUNTING",
    "PHASE_2_FINAL_PASS",
    "PHASE_2_DSR_GATE",
}

REQUIRED_PARAMETER_FAMILIES = {
    "volume_decay_rate",
    "catalyst_lag",
    "price_digestion",
    "liquidity_participation",
}

REQUIRED_MATH_METHODS = {
    "purging",
    "embargoing",
    "CPCV",
    "trial_accounting",
    "effective_trial_count",
    "PSR",
    "DSR",
    "outlier_stress",
    "post_run_validation",
}

REQUIRED_BLOCKED_ACTIONS = {
    "execute_oos",
    "query_oos_provider_data",
    "select_thresholds_from_oos_pnl",
    "select_thresholds_from_xmom_001_pnl",
    "select_thresholds_from_crmd_aehr_winners",
    "run_parameter_sweep_after_oos",
    "manual_override_dsr_failure",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
}


def validate_xmom_catalyst_implementation_gate(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    readme = _read_text(path / "README.md", checks, "markdown_readable:README.md")
    spec = _read_text(path / "implementation_gate_spec.md", checks, "markdown_readable:implementation_gate_spec.md")
    manifest = _read_json(path / "implementation_gate_manifest.json", checks, "json_readable:implementation_gate_manifest.json")
    phases = _read_csv(path / "phase_contract.csv", checks, "csv_readable:phase_contract.csv")
    thresholds = _read_csv(path / "blind_threshold_policy.csv", checks, "csv_readable:blind_threshold_policy.csv")
    math_policy = _read_csv(path / "validation_math_policy.csv", checks, "csv_readable:validation_math_policy.csv")
    blocked = _read_csv(path / "blocked_actions.csv", checks, "csv_readable:blocked_actions.csv")
    sources = _read_csv(path / "source_review.csv", checks, "csv_readable:source_review.csv")

    if readme is not None and spec is not None:
        _validate_markdown(readme, spec, checks)
    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)
    if phases is not None:
        _validate_phase_contract(phases, checks)
    if thresholds is not None:
        _validate_threshold_policy(thresholds, checks)
    if math_policy is not None:
        _validate_math_policy(math_policy, checks)
    if blocked is not None:
        _validate_blocked_actions(blocked, checks)
    if sources is not None:
        _validate_sources(sources, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_xmom_catalyst_implementation_gate(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate XMOM catalyst implementation gate spec.")
    parser.add_argument("--spec-dir", required=True, help="Implementation gate spec directory.")
    return parser


def _validate_markdown(readme: str, spec: str, checks: list[dict[str, str]]) -> None:
    combined = f"{readme}\n{spec}"
    lower = combined.lower()
    _add_check(checks, "markdown_status_spec_only", "spec_only_not_executable" in lower, "SPEC_ONLY_NOT_EXECUTABLE present")
    _add_check(checks, "markdown_trial_identity", "trial-xmom-catalyst-001" in lower and "impl-gate-xmom-catalyst-001" in lower, "trial and gate ids present")
    _add_check(checks, "markdown_two_phase_protocol", "phase 1" in lower and "phase 2" in lower, "two phases present")
    _add_check(checks, "markdown_blind_threshold_rule", "blind to returns" in lower and "ecdf" in lower, "blind ECDF threshold rule present")
    _add_check(checks, "markdown_dsr_kill_switch", "dsr >= 0.95" in lower and "kill" in lower, "DSR kill switch present")
    authorization_absent = all(marker not in lower for marker in ["paper trading authorized", "live trading authorized", "promotion authorized", "oos authorized"])
    _add_check(checks, "markdown_no_authorization_language", authorization_absent, "no authorization language")


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    missing = sorted(REQUIRED_MANIFEST_FIELDS - set(manifest))
    _add_check(checks, "manifest_required_fields", not missing, f"missing={missing}")
    if missing:
        return
    no_execution_flags = all(
        manifest.get(flag) is True
        for flag in [
            "no_provider_query",
            "no_oos_execution",
            "no_parameter_sweep",
            "no_paper_trading",
            "no_live_trading",
            "no_strategy_promotion",
        ]
    )
    required_methods = all(
        manifest.get(flag) is True
        for flag in [
            "phase_1_required",
            "phase_2_single_pass_required",
            "blind_threshold_selection_required",
            "cpcv_required",
            "purging_required",
            "embargo_required",
            "trial_accounting_required",
            "dsr_required",
            "effective_trial_count_required",
        ]
    )
    dsr_threshold_ok = float(manifest.get("dsr_minimum_confidence", 0)) >= 0.95
    status_ok = manifest.get("status") == "SPEC_ONLY_NOT_EXECUTABLE"
    _add_check(checks, "manifest_status_spec_only", status_ok, f"status={manifest.get('status')}")
    _add_check(checks, "manifest_no_execution_flags", no_execution_flags, f"no_execution_flags={no_execution_flags}")
    _add_check(checks, "manifest_required_methods_enabled", required_methods, f"required_methods={required_methods}")
    _add_check(checks, "manifest_dsr_threshold_at_least_095", dsr_threshold_ok, f"dsr_minimum_confidence={manifest.get('dsr_minimum_confidence')}")


def _validate_phase_contract(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"phase", "status", "allowed_input", "required_output", "blocked_action"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "phase_contract_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    phases = set(frame["phase"].astype(str))
    missing_phases = sorted(REQUIRED_PHASES - phases)
    blocked_actions = set(frame["blocked_action"].astype(str))
    single_pass_blocked = "no_second_oos_pass" in blocked_actions
    _add_check(checks, "phase_contract_required_phases", not missing_phases, f"missing={missing_phases}")
    _add_check(checks, "phase_contract_blocks_second_oos_pass", single_pass_blocked, f"blocked_actions={sorted(blocked_actions)}")


def _validate_threshold_policy(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"parameter_family", "status", "selection_method", "return_visibility", "execution_policy", "notes"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "threshold_policy_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    families = set(frame["parameter_family"].astype(str))
    missing_families = sorted(REQUIRED_PARAMETER_FAMILIES - families)
    candidate_rows = frame[frame["parameter_family"].astype(str).isin(REQUIRED_PARAMETER_FAMILIES)]
    candidates_not_final = candidate_rows["status"].astype(str).str.lower().eq("not_final").all()
    candidates_blind = candidate_rows["return_visibility"].astype(str).str.lower().eq("blind_to_returns").all()
    candidates_not_executable = candidate_rows["execution_policy"].astype(str).str.lower().eq("not_executable").all()
    governance = frame[frame["parameter_family"].astype(str).eq("minimum_dsr_confidence")]
    governance_locked = len(governance) == 1 and str(governance.iloc[0]["status"]).lower() == "final" and str(governance.iloc[0]["execution_policy"]).lower() == "locked"
    _add_check(checks, "threshold_policy_required_families", not missing_families, f"missing={missing_families}")
    _add_check(checks, "threshold_policy_candidates_not_final", bool(candidates_not_final), f"not_final={bool(candidates_not_final)}")
    _add_check(checks, "threshold_policy_candidates_blind_to_returns", bool(candidates_blind), f"blind={bool(candidates_blind)}")
    _add_check(checks, "threshold_policy_candidates_not_executable", bool(candidates_not_executable), f"not_executable={bool(candidates_not_executable)}")
    _add_check(checks, "threshold_policy_dsr_governance_locked", governance_locked, f"governance_rows={len(governance)}")


def _validate_math_policy(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"method", "status", "required", "gate_role", "failure_response"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "math_policy_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    methods = set(frame["method"].astype(str))
    missing_methods = sorted(REQUIRED_MATH_METHODS - methods)
    all_required = frame["required"].astype(str).str.lower().eq("yes").all()
    dsr_row = frame[frame["method"].astype(str).eq("DSR")]
    dsr_kill_switch = len(dsr_row) == 1 and "below_0_95" in str(dsr_row.iloc[0]["failure_response"]).lower()
    _add_check(checks, "math_policy_required_methods", not missing_methods, f"missing={missing_methods}")
    _add_check(checks, "math_policy_all_required", bool(all_required), f"all_required={bool(all_required)}")
    _add_check(checks, "math_policy_dsr_kill_switch", dsr_kill_switch, f"dsr_rows={len(dsr_row)}")


def _validate_blocked_actions(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"action", "status", "reason"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "blocked_actions_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    actions = set(frame["action"].astype(str))
    missing_actions = sorted(REQUIRED_BLOCKED_ACTIONS - actions)
    all_blocked = frame["status"].astype(str).str.lower().eq("blocked").all()
    _add_check(checks, "blocked_actions_required_set", not missing_actions, f"missing={missing_actions}")
    _add_check(checks, "blocked_actions_all_blocked", bool(all_blocked), f"all_blocked={bool(all_blocked)}")


def _validate_sources(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"source_id", "source_type", "status", "use_case", "url"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "source_review_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    accepted = set(frame[frame["status"].astype(str).str.lower().eq("accepted")]["source_id"].astype(str))
    required_accepted = {"dellavigna_pollet_jf", "sadka_jfe", "bailey_ldp_dsr", "ldp_otr"}
    informal = frame[frame["source_type"].astype(str).eq("informal")]
    informal_blocked = len(informal) == 1 and str(informal.iloc[0]["status"]).lower() == "blocked_for_primary"
    _add_check(checks, "source_review_required_primary_sources", required_accepted.issubset(accepted), f"accepted={sorted(accepted)}")
    _add_check(checks, "source_review_informal_not_primary", informal_blocked, f"informal_rows={len(informal)}")


def _read_text(path: Path, checks: list[dict[str, str]], name: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {type(exc).__name__}: {exc}")
        return None
    _add_check(checks, name, bool(text.strip()), f"{path}: chars={len(text)}")
    return text


def _read_json(path: Path, checks: list[dict[str, str]], name: str) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {type(exc).__name__}: {exc}")
        return None
    _add_check(checks, name, True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]], name: str) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {type(exc).__name__}: {exc}")
        return None
    _add_check(checks, name, not frame.empty and bool(frame.columns.tolist()), f"{path}: rows={len(frame)}; columns={len(frame.columns)}")
    return frame


def _add_check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": str(detail)})


def _report(path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "spec_dir": str(path),
        "status": "fail" if failed else "pass",
        "gate_decision": "IMPLEMENTATION_GATE_SPEC_PASS" if failed == 0 else "IMPLEMENTATION_GATE_SPEC_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
