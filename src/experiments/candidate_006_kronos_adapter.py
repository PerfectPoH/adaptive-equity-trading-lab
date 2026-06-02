from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


RUN_ID = "CANDIDATE-006-KRONOS-COMPATIBILITY-AUDIT-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_006_kronos_compatibility_gate_20260602")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID
KRONOS_REPO = "https://github.com/shiyu-coder/Kronos"
REQUIRED_KRONOS_COLUMNS = ["open", "high", "low", "close"]
OPTIONAL_KRONOS_COLUMNS = ["volume", "amount"]
FEATURE_CONTRACT = [
    "kronos_forecast_return_mean",
    "kronos_forecast_return_median",
    "kronos_forecast_return_std",
    "kronos_probability_up",
    "kronos_forecast_drawdown_proxy",
    "kronos_sample_path_agreement",
]


def normalize_ohlcv_for_kronos(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert local OHLCV frames into Kronos' lower-case K-line schema."""
    if frame.empty:
        return pd.DataFrame(columns=[*REQUIRED_KRONOS_COLUMNS, *OPTIONAL_KRONOS_COLUMNS])
    data = frame.copy().sort_index()
    renamed = {
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
        "Turnover": "amount",
    }
    data = data.rename(columns={column: renamed[column] for column in renamed if column in data.columns})
    missing = [column for column in REQUIRED_KRONOS_COLUMNS if column not in data.columns]
    if missing:
        raise ValueError(f"Missing Kronos OHLC columns: {missing}")
    if "volume" not in data.columns:
        data["volume"] = 0.0
    if "amount" not in data.columns:
        data["amount"] = pd.to_numeric(data["close"], errors="coerce") * pd.to_numeric(data["volume"], errors="coerce")
    out = data[[*REQUIRED_KRONOS_COLUMNS, *OPTIONAL_KRONOS_COLUMNS]].copy()
    out.index = pd.to_datetime(out.index).tz_localize(None)
    return out.apply(pd.to_numeric, errors="coerce")


def build_kronos_feature_contract() -> dict[str, Any]:
    return {
        "contract_id": "CANDIDATE-006-KRONOS-FEATURE-CONTRACT-001",
        "role": "feature_generator_only",
        "required_input_columns": REQUIRED_KRONOS_COLUMNS,
        "optional_input_columns": OPTIONAL_KRONOS_COLUMNS,
        "allowed_features": FEATURE_CONTRACT,
        "forbidden_uses": [
            "direct live trading signal",
            "model confidence calibrated on test PnL",
            "future realized return used as an input feature",
            "fine-tuning on active-only survivorship-biased data",
            "promotion without separate Kronos overlay backtest gate",
        ],
        "candidate_006_use": "Overlay Candidate 005 recovery breadth ranking only after a separate smoke/inference gate.",
    }


def run_candidate_006_kronos_compatibility_audit(
    *,
    output_dir: Path = OUTPUT_DIR,
    gate_dir: Path = GATE_DIR,
    sample_frame: pd.DataFrame | None = None,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    repo_check = _git_ls_remote_check(KRONOS_REPO) if gate.get("repo_metadata_query_allowed") else {"status": "not_allowed"}
    dependencies = _dependency_presence(["torch", "transformers", "huggingface_hub", "pandas", "numpy"])
    schema_check = _schema_check(sample_frame if sample_frame is not None else _default_sample_frame())
    feature_contract = build_kronos_feature_contract()
    blockers = []
    if repo_check.get("status") != "reachable":
        blockers.append("kronos_repo_metadata_unreachable")
    if not dependencies["torch"]["available"]:
        blockers.append("torch_missing_for_future_inference")
    if not dependencies["transformers"]["available"]:
        blockers.append("transformers_missing_for_future_model_loading")
    if not schema_check["normalization_passed"]:
        blockers.append("norgate_to_kronos_schema_mapping_failed")

    result = {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": "CANDIDATE_006_KRONOS_COMPATIBILITY_AUDIT_COMPLETE_NO_MODEL_DOWNLOAD",
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "external_query_performed": True,
        "external_query_scope": "git ls-remote metadata only",
        "git_clone_performed": False,
        "model_download_performed": False,
        "dependency_install_performed": False,
        "inference_performed": False,
        "fine_tuning_performed": False,
        "portfolio_backtest_performed": False,
        "parameter_sweep_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "financial_performance_claimed": False,
        "repo_check": repo_check,
        "dependency_presence": dependencies,
        "schema_check": schema_check,
        "feature_contract": feature_contract,
        "blockers": blockers,
        "next_allowed_action": "create_candidate_006_kronos_inference_smoke_gate_if_dependencies_available",
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "kronos_compatibility_audit_result.json", result)
    _write_json(output_dir / "feature_contract.json", feature_contract)
    _write_json(output_dir / "final_decision.json", _final_decision(result))
    (output_dir / "kronos_compatibility_audit_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def _validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("status") != "APPROVED_COMPATIBILITY_AUDIT_ONLY_NO_MODEL_DOWNLOAD":
        raise RuntimeError("Candidate 006 Kronos compatibility gate is not approved.")
    forbidden = [
        "model_download_allowed",
        "inference_allowed",
        "fine_tuning_allowed",
        "portfolio_backtest_allowed",
        "parameter_sweep_allowed",
        "promotion_allowed",
    ]
    for key in forbidden:
        if gate.get(key):
            raise RuntimeError(f"Gate unexpectedly allows {key}.")


def _git_ls_remote_check(repo: str) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["git", "ls-remote", "--heads", repo],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    heads = [line for line in proc.stdout.splitlines() if line.strip()]
    return {
        "status": "reachable" if proc.returncode == 0 and heads else "unreachable",
        "returncode": proc.returncode,
        "head_count": len(heads),
        "stderr": proc.stderr.strip()[:500],
    }


def _dependency_presence(names: list[str]) -> dict[str, dict[str, Any]]:
    rows = {}
    for name in names:
        spec = importlib.util.find_spec(name)
        rows[name] = {"available": spec is not None, "origin": getattr(spec, "origin", None) if spec else None}
    rows["python"] = {"available": True, "version": sys.version.split()[0]}
    return rows


def _schema_check(frame: pd.DataFrame) -> dict[str, Any]:
    try:
        normalized = normalize_ohlcv_for_kronos(frame)
    except Exception as exc:
        return {"normalization_passed": False, "error": str(exc)}
    return {
        "normalization_passed": True,
        "rows": int(len(normalized)),
        "columns": list(normalized.columns),
        "required_columns_present": all(column in normalized.columns for column in REQUIRED_KRONOS_COLUMNS),
        "optional_columns_present": all(column in normalized.columns for column in OPTIONAL_KRONOS_COLUMNS),
    }


def _default_sample_frame() -> pd.DataFrame:
    index = pd.bdate_range("2026-01-01", periods=5)
    return pd.DataFrame(
        {
            "Open": [10, 10.1, 10.2, 10.3, 10.4],
            "High": [10.2, 10.3, 10.4, 10.5, 10.6],
            "Low": [9.9, 10.0, 10.1, 10.2, 10.3],
            "Close": [10.1, 10.2, 10.3, 10.4, 10.5],
            "Volume": [1000, 1100, 1200, 1300, 1400],
            "Turnover": [10100, 11220, 12360, 13520, 14700],
        },
        index=index,
    )


def _final_decision(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": result["decision"],
        "external_query_performed": result["external_query_performed"],
        "git_clone_performed": False,
        "model_download_performed": False,
        "inference_performed": False,
        "portfolio_backtest_performed": False,
        "promotion_allowed": False,
        "blockers": result["blockers"],
        "next_allowed_action": result["next_allowed_action"],
    }


def _markdown_report(result: dict[str, Any]) -> str:
    deps = result["dependency_presence"]
    lines = [
        "# Candidate 006 Kronos Compatibility Audit 001",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: compatibility audit only. No clone, model download, inference, fine-tuning, backtest, or promotion.",
        "",
        "## Repo Check",
        "",
        f"- Kronos repo metadata status: `{result['repo_check']['status']}`.",
        f"- Head count observed: `{result['repo_check'].get('head_count')}`.",
        "",
        "## Local Dependencies",
        "",
    ]
    for name in ["python", "torch", "transformers", "huggingface_hub", "pandas", "numpy"]:
        rows = deps.get(name, {})
        lines.append(f"- {name}: available=`{rows.get('available')}` version/origin=`{rows.get('version') or rows.get('origin')}`")
    lines.extend(
        [
            "",
            "## Schema",
            "",
            f"- Norgate-to-Kronos normalization passed: `{result['schema_check']['normalization_passed']}`.",
            f"- Columns: `{result['schema_check'].get('columns')}`.",
            "",
            "## Blockers",
            "",
        ]
    )
    if result["blockers"]:
        for blocker in result["blockers"]:
            lines.append(f"- `{blocker}`")
    else:
        lines.append("- None for compatibility. A separate smoke gate is still required before any inference.")
    lines.extend(["", "## Next Allowed Action", "", f"`{result['next_allowed_action']}`", ""])
    return "\n".join(lines)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    run_candidate_006_kronos_compatibility_audit()
