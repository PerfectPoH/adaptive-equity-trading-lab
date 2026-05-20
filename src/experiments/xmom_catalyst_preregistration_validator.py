from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_FILES = [
    "README.md",
    "hypothesis.md",
    "catalyst_taxonomy.csv",
    "allowed_features.csv",
    "parameter_freeze.csv",
    "decision_rule.csv",
    "blocked_actions.csv",
    "source_hierarchy.csv",
    "feature_threshold_rationale.md",
    "threshold_candidate_policy.csv",
]

REQUIRED_ALLOWED_FEATURES = {
    "catalyst_known_before_entry",
    "catalyst_lag_trading_days",
    "volume_persistence_ratio_3d",
    "volume_decay_ratio",
    "price_digestion_hold_ratio",
    "post_catalyst_max_retrace_pct",
    "gap_hold_flag",
}

REQUIRED_BLOCKED_ACTIONS = {
    "execute_backtest",
    "run_parameter_sweep",
    "markov_hmm_patch",
    "paper_trading",
    "live_trading",
    "strategy_promotion",
    "use_future_news",
    "select_thresholds_from_xmom_001_pnl",
    "merge_fda_with_commercial_rollout",
}

REQUIRED_CATALYST_TYPES = {
    "earnings_results",
    "guidance_preliminary_results",
    "commercial_rollout",
    "contract_order",
    "m_and_a",
    "offering_dilution",
    "regulatory_fda",
    "no_obvious_catalyst",
}

REQUIRED_THRESHOLD_CANDIDATES = {
    "candidate_lag_min_trading_days",
    "candidate_lag_max_trading_days",
    "volume_persistence_threshold_3d",
    "volume_persistence_threshold_5d",
    "volume_decay_threshold",
    "price_digestion_hold_threshold",
    "post_catalyst_retrace_limit",
    "gap_hold_required",
}

REQUIRED_LOCKED_GOVERNANCE_THRESHOLDS = {
    "minimum_accepted_trades_for_promotion": "30",
    "top3_contribution_promotion_cap": "100%",
}


def validate_xmom_catalyst_preregistration(spec_dir: str | Path) -> dict[str, Any]:
    path = Path(spec_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "spec_dir_exists", path.exists() and path.is_dir(), str(path))
    if not path.exists() or not path.is_dir():
        return _report(path, checks)

    for filename in REQUIRED_FILES:
        file_path = path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    readme = _read_text(path / "README.md", checks, "markdown_readable:README.md")
    hypothesis = _read_text(path / "hypothesis.md", checks, "markdown_readable:hypothesis.md")
    taxonomy = _read_csv(path / "catalyst_taxonomy.csv", checks, "csv_readable:catalyst_taxonomy.csv")
    features = _read_csv(path / "allowed_features.csv", checks, "csv_readable:allowed_features.csv")
    parameters = _read_csv(path / "parameter_freeze.csv", checks, "csv_readable:parameter_freeze.csv")
    decision = _read_csv(path / "decision_rule.csv", checks, "csv_readable:decision_rule.csv")
    blocked = _read_csv(path / "blocked_actions.csv", checks, "csv_readable:blocked_actions.csv")
    sources = _read_csv(path / "source_hierarchy.csv", checks, "csv_readable:source_hierarchy.csv")
    rationale = _read_text(path / "feature_threshold_rationale.md", checks, "markdown_readable:feature_threshold_rationale.md")
    threshold_policy = _read_csv(path / "threshold_candidate_policy.csv", checks, "csv_readable:threshold_candidate_policy.csv")

    if readme is not None and hypothesis is not None:
        _validate_markdown_status(readme, hypothesis, checks)
    if taxonomy is not None:
        _validate_taxonomy(taxonomy, checks)
    if features is not None:
        _validate_features(features, checks)
    if parameters is not None:
        _validate_parameters(parameters, checks)
    if decision is not None:
        _validate_decision(decision, checks)
    if blocked is not None:
        _validate_blocked_actions(blocked, checks)
    if sources is not None:
        _validate_sources(sources, checks)
    if rationale is not None:
        _validate_feature_threshold_rationale(rationale, checks)
    if threshold_policy is not None:
        _validate_threshold_candidate_policy(threshold_policy, checks)

    return _report(path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_xmom_catalyst_preregistration(args.spec_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate XMOM catalyst preregistration spec-only artifacts.")
    parser.add_argument("--spec-dir", required=True, help="XMOM catalyst preregistration spec directory.")
    return parser


def _validate_markdown_status(readme: str, hypothesis: str, checks: list[dict[str, str]]) -> None:
    combined = f"{readme}\n{hypothesis}"
    _add_check(checks, "status_spec_only_not_executed", "SPEC_ONLY_NOT_EXECUTED" in combined, "SPEC_ONLY_NOT_EXECUTED present")
    _add_check(checks, "trial_id_present", "TRIAL-XMOM-CATALYST-001" in combined, "trial id present")
    _add_check(checks, "preregistration_id_present", "PREREG-XMOM-CATALYST-001" in combined, "preregistration id present")
    forbidden_markers_absent = all(marker not in combined.lower() for marker in ["paper trading authorized", "live trading authorized", "promotion authorized"])
    _add_check(checks, "markdown_no_authorization_language", forbidden_markers_absent, "no authorization language")


def _validate_taxonomy(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"catalyst_type", "status", "description", "initial_handling"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "taxonomy_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    catalyst_types = set(frame["catalyst_type"].astype(str))
    missing_types = sorted(REQUIRED_CATALYST_TYPES - catalyst_types)
    all_frozen = frame["status"].astype(str).str.lower().eq("frozen").all()
    regulatory_separate = "regulatory_fda" in catalyst_types and "commercial_rollout" in catalyst_types
    _add_check(checks, "taxonomy_required_types", not missing_types, f"missing={missing_types}")
    _add_check(checks, "taxonomy_status_frozen", bool(all_frozen), f"all_frozen={bool(all_frozen)}")
    _add_check(checks, "taxonomy_regulatory_separate_from_commercial", regulatory_separate, f"regulatory_separate={regulatory_separate}")


def _validate_features(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"feature_name", "status", "definition", "lookahead_policy", "notes"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "features_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    feature_names = set(frame["feature_name"].astype(str))
    missing_features = sorted(REQUIRED_ALLOWED_FEATURES - feature_names)
    lookahead_ok = frame["lookahead_policy"].astype(str).str.contains("pre_entry", case=False).all()
    no_tbd_required = frame[frame["status"].astype(str).str.lower().isin({"final", "carryover"})]["definition"].astype(str).str.lower().isin({"", "tbd"}).sum() == 0
    _add_check(checks, "features_required_ex_ante_set", not missing_features, f"missing={missing_features}")
    _add_check(checks, "features_strict_pre_entry", bool(lookahead_ok), f"lookahead_ok={bool(lookahead_ok)}")
    _add_check(checks, "features_final_definitions_not_tbd", bool(no_tbd_required), f"no_tbd_required={bool(no_tbd_required)}")


def _validate_parameters(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"parameter_name", "status", "value", "change_after_execution_policy", "notes"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "parameters_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    params = {str(row["parameter_name"]): str(row["value"]) for _, row in frame.iterrows()}
    changes_blocked = frame["change_after_execution_policy"].astype(str).str.lower().isin({"new_preregistration_required", "no_reset_allowed"}).all()
    status_ok = params.get("trial_status") == "SPEC_ONLY_NOT_EXECUTED"
    no_xmom_thresholds = "TBD_IN_FUTURE_SPEC" in params.get("volume_persistence_threshold", "") and "TBD_IN_FUTURE_SPEC" in params.get("price_digestion_threshold", "")
    _add_check(checks, "parameters_changes_blocked", bool(changes_blocked), f"changes_blocked={bool(changes_blocked)}")
    _add_check(checks, "parameters_trial_status_spec_only", status_ok, f"trial_status={params.get('trial_status')}")
    _add_check(checks, "parameters_thresholds_not_selected_from_xmom_001", no_xmom_thresholds, "thresholds deferred")


def _validate_decision(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"decision_item", "status", "rule"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "decision_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    rows = {str(row["decision_item"]): str(row["status"]).lower() for _, row in frame.iterrows()}
    required_items = {"execution_precondition", "data_precondition", "primary_metric", "robustness_gate", "sample_size_gate", "catalyst_gate", "promotion_rule", "stop_rule"}
    missing_items = sorted(required_items - set(rows))
    promotion_blocked = rows.get("promotion_rule") == "blocked"
    sample_gate_present = rows.get("sample_size_gate") == "required"
    robustness_gate_present = rows.get("robustness_gate") == "required"
    _add_check(checks, "decision_required_items", not missing_items, f"missing={missing_items}")
    _add_check(checks, "decision_promotion_blocked", promotion_blocked, f"promotion_status={rows.get('promotion_rule')}")
    _add_check(checks, "decision_sample_size_gate_required", sample_gate_present, f"sample_size_gate={rows.get('sample_size_gate')}")
    _add_check(checks, "decision_robustness_gate_required", robustness_gate_present, f"robustness_gate={rows.get('robustness_gate')}")


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
    required = {"source_rank", "source_type", "status", "use_case", "notes"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "source_required_columns", not missing, f"missing={missing}")
    if missing:
        return
    sources = set(frame["source_type"].astype(str))
    preferred = {"issuer_press_release", "sec_edgar_filing"}
    forum_rows = frame[frame["source_type"].astype(str).eq("forum_social_media")]
    forum_blocked = len(forum_rows) == 1 and str(forum_rows.iloc[0]["status"]).lower() == "blocked_for_primary"
    _add_check(checks, "source_preferred_primary_sources", preferred.issubset(sources), f"sources={sorted(sources)}")
    _add_check(checks, "source_forums_not_primary", forum_blocked, f"forum_rows={len(forum_rows)}")


def _validate_feature_threshold_rationale(text: str, checks: list[dict[str, str]]) -> None:
    lower = text.lower()
    _add_check(
        checks,
        "rationale_theory_review_only_not_executable",
        "theory_review_only_not_executable" in lower,
        "rationale status present",
    )
    _add_check(
        checks,
        "rationale_does_not_authorize_execution",
        "does not make `trial-xmom-catalyst-001` executable" in lower or "does not make trial-xmom-catalyst-001 executable" in lower,
        "execution remains blocked",
    )
    forbidden_selection_blocked = all(
        phrase in lower
        for phrase in [
            "select thresholds from crmd/aehr winners",
            "select thresholds from trial-xmom-001 pnl",
            "select thresholds by maximizing the old run result",
        ]
    )
    _add_check(
        checks,
        "rationale_blocks_old_run_threshold_selection",
        forbidden_selection_blocked,
        "old-run threshold selection is explicitly blocked",
    )


def _validate_threshold_candidate_policy(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required = {"candidate_parameter", "status", "proposed_value", "source_basis", "execution_policy", "notes"}
    missing = sorted(required - set(frame.columns))
    _add_check(checks, "threshold_policy_required_columns", not missing, f"missing={missing}")
    if missing:
        return

    params = set(frame["candidate_parameter"].astype(str))
    missing_candidates = sorted(REQUIRED_THRESHOLD_CANDIDATES - params)
    _add_check(checks, "threshold_policy_required_candidates", not missing_candidates, f"missing={missing_candidates}")

    candidate_rows = frame[frame["candidate_parameter"].astype(str).isin(REQUIRED_THRESHOLD_CANDIDATES)]
    candidates_not_final = candidate_rows["status"].astype(str).str.lower().eq("not_final").all()
    candidates_tbd = candidate_rows["proposed_value"].astype(str).str.upper().eq("TBD").all()
    candidates_not_executable = candidate_rows["execution_policy"].astype(str).str.lower().eq("not_executable").all()
    candidate_basis_ok = candidate_rows["source_basis"].astype(str).str.lower().eq("literature_logic_review_only").all()
    _add_check(checks, "threshold_policy_candidates_not_final", bool(candidates_not_final), f"not_final={bool(candidates_not_final)}")
    _add_check(checks, "threshold_policy_candidates_tbd", bool(candidates_tbd), f"tbd={bool(candidates_tbd)}")
    _add_check(checks, "threshold_policy_candidates_not_executable", bool(candidates_not_executable), f"not_executable={bool(candidates_not_executable)}")
    _add_check(checks, "threshold_policy_candidates_literature_only", bool(candidate_basis_ok), f"literature_only={bool(candidate_basis_ok)}")

    rows = {str(row["candidate_parameter"]): row for _, row in frame.iterrows()}
    locked_ok = True
    for parameter, expected_value in REQUIRED_LOCKED_GOVERNANCE_THRESHOLDS.items():
        row = rows.get(parameter)
        if row is None:
            locked_ok = False
            continue
        locked_ok = locked_ok and str(row["status"]).lower() == "final"
        locked_ok = locked_ok and str(row["proposed_value"]) == expected_value
        locked_ok = locked_ok and str(row["execution_policy"]).lower() == "locked"
    _add_check(checks, "threshold_policy_governance_thresholds_locked", bool(locked_ok), f"locked_ok={bool(locked_ok)}")


def _read_csv(path: Path, checks: list[dict[str, str]], name: str) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {type(exc).__name__}: {exc}")
        return None
    _add_check(checks, name, True, f"{path}: rows={len(frame)}; columns={len(frame.columns)}")
    return frame


def _read_text(path: Path, checks: list[dict[str, str]], name: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {type(exc).__name__}: {exc}")
        return None
    _add_check(checks, name, bool(text.strip()), f"{path}: chars={len(text)}")
    return text


def _add_check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "spec_dir": str(path),
        "status": "fail" if failed else "pass",
        "gate_decision": "SPEC_VALIDATION_PASS" if failed == 0 else "SPEC_VALIDATION_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


if __name__ == "__main__":
    raise SystemExit(main())
