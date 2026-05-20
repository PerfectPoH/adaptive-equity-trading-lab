from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

REQUIRED_FILES = [
    "pre_run_gate_manifest.json",
    "pre_run_gate_checklist.csv",
    "pre_run_gate_summary.md",
]

REQUIRED_CHECKS = {
    "databento_data_exists",
    "config_hash_match",
    "ledger_status_is_prepared",
}


def validate_xmom_pre_run_gate(gate_dir: str | Path) -> dict[str, Any]:
    gate_path = Path(gate_dir)
    checks: list[dict[str, str]] = []
    _add_check(checks, "gate_dir_exists", gate_path.exists() and gate_path.is_dir(), str(gate_path))
    if not gate_path.exists() or not gate_path.is_dir():
        return _report(gate_path, checks)

    for filename in REQUIRED_FILES:
        file_path = gate_path / filename
        _add_check(checks, f"required_file:{filename}", file_path.exists() and file_path.is_file(), str(file_path))

    manifest = _read_json(gate_path / "pre_run_gate_manifest.json", checks, "manifest_json")
    checklist = _read_csv(gate_path / "pre_run_gate_checklist.csv", checks, "csv_readable:pre_run_gate_checklist.csv")
    _read_text(gate_path / "pre_run_gate_summary.md", checks, "markdown_readable:pre_run_gate_summary.md")

    if isinstance(manifest, dict):
        _validate_manifest(manifest, checks)
    if checklist is not None:
        _validate_checklist_structure(checklist, checks)
        _evaluate_runtime_checks(manifest if isinstance(manifest, dict) else {}, checklist, checks)

    return _report(gate_path, checks)


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_xmom_pre_run_gate(args.gate_dir)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate XMOM pre-run gate and compute executable decision.")
    parser.add_argument("--gate-dir", required=True, help="Path to the XMOM pre-run gate artifact directory.")
    return parser


def _validate_manifest(manifest: dict[str, Any], checks: list[dict[str, str]]) -> None:
    required_fields = {
        "status",
        "decision",
        "trial_id",
        "preregistration_id",
        "required_checks",
        "fail_closed_policy",
        "on_failure_action",
        "execution_status",
    }
    missing = sorted(required_fields - set(manifest.keys()))
    required_checks = manifest.get("required_checks")
    checks_set_ok = isinstance(required_checks, list) and REQUIRED_CHECKS.issubset(set(required_checks))
    fail_closed_ok = manifest.get("fail_closed_policy") is True and manifest.get("on_failure_action") == "EXIT_1_BLOCK_EXECUTION"
    execution_blocked_ok = manifest.get("execution_status") == "not_executed"
    _add_check(checks, "manifest_required_fields", not missing and checks_set_ok, f"missing={missing}; checks_set_ok={checks_set_ok}")
    _add_check(checks, "manifest_fail_closed_policy", fail_closed_ok, f"on_failure_action={manifest.get('on_failure_action')}")
    _add_check(checks, "manifest_execution_status_not_executed", execution_blocked_ok, f"execution_status={manifest.get('execution_status')}")


def _validate_checklist_structure(frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    required_columns = {"check", "required", "current_status", "pass_condition", "failure_action", "evidence_source"}
    missing_columns = sorted(required_columns - set(frame.columns))
    _add_check(checks, "checklist_required_columns", not missing_columns, f"missing={missing_columns}")
    if missing_columns:
        return
    present = set(frame["check"].astype(str))
    missing_checks = sorted(REQUIRED_CHECKS - present)
    all_required_yes = frame["required"].astype(str).str.lower().eq("yes").all()
    all_exit_1 = frame["failure_action"].astype(str).str.contains("EXIT_1_BLOCK_EXECUTION", case=False, regex=False).all()
    _add_check(checks, "checklist_required_checks_present", not missing_checks, f"missing={missing_checks}")
    _add_check(checks, "checklist_all_required_yes", bool(all_required_yes), f"all_required_yes={bool(all_required_yes)}")
    _add_check(checks, "checklist_failure_action_exit_1", bool(all_exit_1), f"all_exit_1={bool(all_exit_1)}")


def _evaluate_runtime_checks(manifest: dict[str, Any], frame: pd.DataFrame, checks: list[dict[str, str]]) -> None:
    rows = {str(row["check"]): row for _, row in frame.iterrows()}
    databento_ok = _databento_data_exists(str(rows.get("databento_data_exists", {}).get("evidence_source", "")))
    hash_ok, hash_detail = _config_hash_match(manifest, str(rows.get("config_hash_match", {}).get("evidence_source", "")))
    ledger_ok = _ledger_status_is_prepared(
        trial_id=str(manifest.get("trial_id", "")),
        evidence_source=str(rows.get("ledger_status_is_prepared", {}).get("evidence_source", "")),
    )
    _add_check(checks, "runtime_databento_data_exists", databento_ok, str(rows.get("databento_data_exists", {}).get("evidence_source", "")))
    _add_check(checks, "runtime_config_hash_match", hash_ok, hash_detail)
    _add_check(checks, "runtime_ledger_status_is_prepared", ledger_ok, str(rows.get("ledger_status_is_prepared", {}).get("evidence_source", "")))


def _databento_data_exists(evidence_source: str) -> bool:
    if not evidence_source:
        return False
    path = Path(evidence_source.replace("*", "")).parent if "*" in evidence_source else Path(evidence_source)
    if not path.exists():
        return False
    return any(child.is_file() for child in path.rglob("*"))


def _config_hash_match(manifest: dict[str, Any], _evidence_source: str) -> tuple[bool, str]:
    prereg_dir_raw = manifest.get("linked_preregistration_dir")
    expected_hash = str(manifest.get("expected_trial_config_hash", "")).strip()
    if not prereg_dir_raw or not expected_hash:
        return False, "missing linked_preregistration_dir or expected_trial_config_hash in manifest"
    prereg_dir = Path(str(prereg_dir_raw))
    parameter_file = prereg_dir / "parameter_freeze.csv"
    feature_file = prereg_dir / "feature_freeze.csv"
    if not parameter_file.exists() or not feature_file.exists():
        return False, f"missing prereg files: {parameter_file} / {feature_file}"
    payload = parameter_file.read_text(encoding="utf-8") + "\n" + feature_file.read_text(encoding="utf-8")
    computed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return computed == expected_hash, f"computed={computed}; expected={expected_hash}"


def _ledger_status_is_prepared(trial_id: str, evidence_source: str) -> bool:
    if not trial_id or not evidence_source:
        return False
    ledger_path = Path(evidence_source)
    if not ledger_path.exists():
        return False
    frame = pd.read_csv(ledger_path)
    if "trial_id" not in frame.columns or "result_status" not in frame.columns:
        return False
    trial_rows = frame[frame["trial_id"].astype(str).eq(trial_id)]
    if trial_rows.empty:
        return False
    return trial_rows["result_status"].astype(str).str.lower().eq("prepared_not_executed").any()


def _read_json(path: Path, checks: list[dict[str, str]], name: str) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, True, str(path))
    return payload


def _read_csv(path: Path, checks: list[dict[str, str]], name: str) -> pd.DataFrame | None:
    try:
        frame = pd.read_csv(path)
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, not frame.empty, f"{path}: rows={len(frame)}; columns={len(frame.columns)}")
    return frame


def _read_text(path: Path, checks: list[dict[str, str]], name: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        _add_check(checks, name, False, f"{path}: {exc}")
        return None
    _add_check(checks, name, bool(text.strip()), f"{path}: chars={len(text)}")
    return text


def _add_check(checks: list[dict[str, str]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if passed else "fail", "detail": str(detail)})


def _report(gate_path: Path, checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = [check for check in checks if check["status"] == "fail"]
    return {
        "gate_dir": str(gate_path),
        "status": "pass" if not failed else "fail",
        "gate_decision": "PASS_READY_TO_EXECUTE" if not failed else "BLOCKED_EXIT_1",
        "summary": {"total": len(checks), "failed": len(failed), "passed": len(checks) - len(failed)},
        "checks": checks,
    }


if __name__ == "__main__":
    raise SystemExit(main())
