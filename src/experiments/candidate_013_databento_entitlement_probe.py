from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from dotenv import dotenv_values


RUN_ID = "CANDIDATE-013-DATABENTO-ENTITLEMENT-PROBE-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_013_databento_fresh_data_entitlement_gate_20260606")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID
API_KEY_NAME = "DATABENTO_API_KEY"


def run_candidate_013_databento_entitlement_probe(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
    run_id: str = RUN_ID,
    historical_client_factory: Callable[[str], Any] | None = None,
    reference_client_factory: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    api_key, key_diagnostics = _resolve_api_key(gate["api_key_source"], Path(gate["env_file"]))
    if not api_key:
        historical = {"status": "BLOCKED_API_KEY_MISSING", "checks": []}
        reference = {"overall_status": "BLOCKED_API_KEY_MISSING", "checks": []}
        final_decision = build_readiness_decision("BLOCKED_API_KEY_MISSING", {})
    else:
        historical = _run_historical_metadata_probe(api_key, gate["probe_contract"], historical_client_factory)
        reference = _run_reference_metadata_probe(api_key, gate["probe_contract"], reference_client_factory)
        final_decision = build_readiness_decision(
            str(historical["status"]),
            {str(check["endpoint"]): str(check["status"]) for check in reference["checks"]},
        )

    result = {
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "decision": final_decision["decision"],
        "linked_gate": str(gate_dir / "gate_manifest.json"),
        "linked_candidate_012_spec": gate.get("linked_candidate_012_spec"),
        "provider": "Databento",
        "provider_query_performed": bool(api_key),
        "market_data_download_performed": False,
        "raw_payload_retained": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "api_key_diagnostics": key_diagnostics,
        "probe_contract": gate["probe_contract"],
        "fresh_data_requirements": gate["fresh_data_requirements"],
        "historical_metadata": historical,
        "reference_metadata": reference,
        "final_decision": final_decision,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "databento_entitlement_probe_result.json", result)
    _write_json(output_dir / "final_decision.json", final_decision)
    (output_dir / "databento_entitlement_probe_report.md").write_text(_markdown_report(result), encoding="utf-8")
    return result


def build_readiness_decision(historical_status: str, reference_statuses: dict[str, str]) -> dict[str, Any]:
    blockers: list[str] = []
    if historical_status != "PASS":
        blockers.append("databento_historical_metadata_not_ready")
    required_reference = {"corporate_actions", "security_master", "adjustment_factors"}
    missing_reference = [
        endpoint
        for endpoint in sorted(required_reference)
        if reference_statuses.get(endpoint) not in {"PASS", "EMPTY_PASS"}
    ]
    if missing_reference:
        blockers.append("databento_reference_entitlement_missing")
    if blockers:
        decision = (
            "DATABENTO_FRESH_DATA_BLOCKED_REFERENCE_ENTITLEMENT"
            if "databento_reference_entitlement_missing" in blockers
            else "DATABENTO_FRESH_DATA_BLOCKED_HISTORICAL_METADATA"
        )
    else:
        decision = "DATABENTO_FRESH_DATA_ENTITLEMENT_READY_FOR_DATA_GATE"
    return {
        "decision": decision,
        "blockers": blockers,
        "candidate_014_backtest_allowed": False,
        "promotion_allowed": False,
        "next_allowed_action": "create_candidate_014_fresh_data_gate" if not blockers else "resolve_provider_entitlement_or_choose_provider",
    }


def _run_historical_metadata_probe(
    api_key: str,
    contract: dict[str, Any],
    historical_client_factory: Callable[[str], Any] | None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    try:
        client = historical_client_factory(api_key) if historical_client_factory else _default_historical_client(api_key)
        datasets = list(client.metadata.list_datasets())
        checks.append({"name": "list_datasets", "status": "PASS", "dataset_count": len(datasets)})
        for dataset in contract["historical_dataset_candidates"]:
            dataset_check: dict[str, Any] = {"dataset": dataset, "available": dataset in datasets}
            if dataset not in datasets:
                dataset_check["status"] = "BLOCKED_DATASET_UNAVAILABLE"
                checks.append({"name": "dataset_candidate", **dataset_check})
                continue
            schemas = list(client.metadata.list_schemas(dataset))
            dataset_check["schemas"] = schemas
            dataset_check["schema_available"] = contract["tiny_schema"] in schemas
            if contract["tiny_schema"] in schemas:
                fields = list(client.metadata.list_fields(contract["tiny_schema"], "dbn"))
                tiny_kwargs = {
                    "dataset": dataset,
                    "schema": contract["tiny_schema"],
                    "symbols": contract["tiny_cost_symbol"],
                    "start": contract["tiny_cost_start"],
                    "end": contract["tiny_cost_end"],
                }
                dataset_check["fields"] = fields
                dataset_check["tiny_cost"] = _safe_float(client.metadata.get_cost(**tiny_kwargs))
                dataset_check["tiny_record_count"] = int(client.metadata.get_record_count(**tiny_kwargs))
            dataset_check["status"] = "PASS" if dataset_check.get("schema_available") else "BLOCKED_SCHEMA_UNAVAILABLE"
            checks.append({"name": "dataset_candidate", **dataset_check})
    except Exception as exc:
        return {"status": _classify_exception(exc), "checks": checks, "error_type": type(exc).__name__, "error_message": _redact(str(exc))}
    status = "PASS" if any(check.get("name") == "dataset_candidate" and check.get("status") == "PASS" for check in checks) else "BLOCKED_NO_DATASET_PASS"
    return {"status": status, "checks": checks}


def _run_reference_metadata_probe(
    api_key: str,
    contract: dict[str, Any],
    reference_client_factory: Callable[[str], Any] | None,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    try:
        client = reference_client_factory(api_key) if reference_client_factory else _default_reference_client(api_key)
    except Exception as exc:
        return {
            "overall_status": _classify_exception(exc),
            "checks": [{"endpoint": "reference_client_constructible", "status": _classify_exception(exc), "error_type": type(exc).__name__, "error_message": _redact(str(exc))}],
        }
    for endpoint in ("corporate_actions", "security_master", "adjustment_factors"):
        checks.append(_probe_reference_endpoint(client, endpoint, contract))
    overall = "PASS" if all(check["status"] in {"PASS", "EMPTY_PASS"} for check in checks) else "BLOCKED_REFERENCE_ENTITLEMENT"
    return {"overall_status": overall, "checks": checks}


def _probe_reference_endpoint(client: Any, endpoint: str, contract: dict[str, Any]) -> dict[str, Any]:
    accessor = getattr(client, endpoint)
    try:
        response = accessor.get_range(
            symbols=contract["tiny_cost_symbol"],
            start=contract["tiny_cost_start"],
            end=contract["tiny_cost_end"],
            **({"pit": True} if endpoint == "corporate_actions" else {}),
        )
        count = _response_count(response)
        return {"endpoint": endpoint, "status": "PASS" if count > 0 else "EMPTY_PASS", "record_count": count}
    except Exception as exc:
        return {
            "endpoint": endpoint,
            "status": _classify_exception(exc),
            "error_type": type(exc).__name__,
            "error_message": _redact(str(exc)),
        }


def _validate_gate(gate: dict[str, Any]) -> None:
    approved_statuses = {
        "APPROVED_ONE_DATABENTO_FRESH_DATA_ENTITLEMENT_PROBE_ONLY",
        "APPROVED_ONE_DATABENTO_FRESH_DATA_ENTITLEMENT_PROBE_RERUN_ONLY",
    }
    if gate.get("status") not in approved_statuses:
        raise RuntimeError("Candidate 013 gate is not approved.")
    if gate.get("allowed_probe_count") != 1:
        raise RuntimeError("Candidate 013 gate must authorize exactly one probe.")
    for key in ("market_data_download_allowed", "raw_payload_retention_allowed", "backtest_allowed", "parameter_sweep_allowed", "promotion_allowed", "paper_trading_allowed", "live_trading_allowed"):
        if gate.get(key):
            raise RuntimeError(f"Gate unexpectedly allows {key}.")
    if not gate.get("provider_query_allowed"):
        raise RuntimeError("Candidate 013 requires provider_query_allowed=true for the entitlement probe.")


def _resolve_api_key(api_key_source: str, env_file: Path) -> tuple[str, dict[str, Any]]:
    env_key = os.environ.get(API_KEY_NAME, "")
    file_key = ""
    if env_file.exists():
        file_key = str(dotenv_values(env_file).get(API_KEY_NAME) or "")
    selected = ""
    source = "missing"
    if api_key_source == "environment":
        selected, source = env_key, "environment"
    elif api_key_source == "env-file":
        selected, source = file_key, "env-file"
    elif env_key:
        selected, source = env_key, "environment"
    elif file_key:
        selected, source = file_key, "env-file"
    else:
        source = "missing"
    diagnostics = {
        "api_key": "REDACTED",
        "api_key_source_requested": api_key_source,
        "api_key_source_resolved": source,
        "api_key_fingerprint": _fingerprint(selected),
        "environment_key_present": bool(env_key),
        "environment_key_fingerprint": _fingerprint(env_key),
        "env_file": str(env_file),
        "env_file_exists": env_file.exists(),
        "env_file_key_present": bool(file_key),
        "env_file_key_fingerprint": _fingerprint(file_key),
    }
    return selected, diagnostics


def _default_historical_client(api_key: str) -> Any:
    import databento as db

    return db.Historical(api_key)


def _default_reference_client(api_key: str) -> Any:
    import databento as db

    return db.Reference(api_key)


def _response_count(response: Any) -> int:
    if response is None:
        return 0
    if hasattr(response, "to_df"):
        return int(len(response.to_df()))
    if hasattr(response, "__len__"):
        return int(len(response))
    return 1


def _classify_exception(exc: Exception) -> str:
    text = str(exc).lower()
    if "403" in text or "license" in text or "subscription" in text or "entitlement" in text:
        return "BLOCKED_403"
    if "401" in text or "api key" in text or "auth" in text:
        return "BLOCKED_AUTH"
    return f"ERROR_{type(exc).__name__}"


def _safe_float(value: Any) -> float | str:
    try:
        return float(value)
    except Exception:
        return str(value)


def _fingerprint(secret: str) -> str:
    if not secret:
        return ""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()[:12]


def _redact(text: str) -> str:
    return text.replace(os.environ.get(API_KEY_NAME, ""), "REDACTED") if os.environ.get(API_KEY_NAME) else text


def _markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# Candidate 013 Databento Fresh Data Entitlement Probe",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: bounded metadata/reference entitlement probe only. No market-data download, no dataset build, no backtest.",
        "",
        "## Historical Metadata",
        "",
        f"- Status: `{result['historical_metadata']['status']}`",
    ]
    for check in result["historical_metadata"].get("checks", []):
        if check.get("name") == "dataset_candidate":
            lines.append(
                f"- `{check.get('dataset')}`: status `{check.get('status')}`, schema_available `{check.get('schema_available')}`, "
                f"tiny_cost `{check.get('tiny_cost')}`, tiny_record_count `{check.get('tiny_record_count')}`"
            )
    lines.extend(["", "## Reference Metadata", "", f"- Overall: `{result['reference_metadata']['overall_status']}`"])
    for check in result["reference_metadata"].get("checks", []):
        lines.append(f"- `{check.get('endpoint')}`: `{check.get('status')}`")
    lines.extend(["", "## Blockers", ""])
    for blocker in result["final_decision"]["blockers"]:
        lines.append(f"- `{blocker}`")
    return "\n".join(lines) + "\n"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    run_candidate_013_databento_entitlement_probe()
