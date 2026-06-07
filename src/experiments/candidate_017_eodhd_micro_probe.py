from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


RUN_ID = "CANDIDATE-017-EODHD-MICRO-PROBE-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_017_eodhd_micro_probe_gate_20260607")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID


@dataclass(frozen=True)
class EodhdResponse:
    status_code: int
    payload: Any
    error: str = ""


class EodhdClient(Protocol):
    def get_json(self, endpoint: str, params: dict[str, str]) -> EodhdResponse:
        ...


class UrlLibEodhdClient:
    BASE_URL = "https://eodhd.com"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def get_json(self, endpoint: str, params: dict[str, str]) -> EodhdResponse:
        query = dict(params)
        query["api_token"] = self._api_key
        query["fmt"] = "json"
        url = f"{self.BASE_URL}{endpoint}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "adaptive-equity-trading-lab/eodhd-micro-probe"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return EodhdResponse(status_code=int(response.status), payload=payload)
        except urllib.error.HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode("utf-8"))
            except Exception:
                payload = {}
            return EodhdResponse(status_code=int(exc.code), payload=payload, error=str(exc))
        except Exception as exc:
            return EodhdResponse(status_code=0, payload={}, error=f"{type(exc).__name__}: {exc}")


def summarize_delisted_symbols(rows: Any, *, required_symbol: str) -> dict[str, Any]:
    if not isinstance(rows, list):
        return {"row_count": 0, "contains_required_symbol": False, "sample_symbols": []}
    symbols = []
    for row in rows:
        if isinstance(row, dict):
            symbol = str(row.get("Code", row.get("code", row.get("symbol", "")))).upper()
            if symbol:
                symbols.append(symbol)
    return {
        "row_count": len(rows),
        "contains_required_symbol": required_symbol.upper() in symbols,
        "sample_symbols": symbols[:20],
    }


def summarize_eod_rows(rows: Any) -> dict[str, Any]:
    if not isinstance(rows, list):
        return {"row_count": 0, "first_date": None, "last_date": None, "has_adjusted_close": False}
    dates = []
    has_adjusted = False
    for row in rows:
        if not isinstance(row, dict):
            continue
        date = str(row.get("date", ""))[:10]
        if date:
            dates.append(date)
        keys = {str(key).lower() for key in row}
        has_adjusted = has_adjusted or "adjusted_close" in keys or "adjustedclose" in keys
    return {
        "row_count": len(rows),
        "first_date": min(dates) if dates else None,
        "last_date": max(dates) if dates else None,
        "has_adjusted_close": bool(has_adjusted),
    }


def build_eodhd_micro_probe_decision(*, api_key_present: bool, checks: list[dict[str, Any]]) -> dict[str, Any]:
    if not api_key_present:
        return {
            "decision": "EODHD_MICRO_PROBE_BLOCKED_API_KEY_MISSING",
            "blockers": ["eodhd_api_key_missing"],
            "candidate_012_backtest_allowed": False,
            "promotion_allowed": False,
            "next_allowed_action": "add_eodhd_api_key_then_commit_rerun_gate",
        }
    passed = {str(check.get("case_id")) for check in checks if check.get("status") == "PASS"}
    blockers: list[str] = []
    if "DELISTED_LIST_US_BBBY" not in passed:
        blockers.append("eodhd_delisted_list_unverified")
    if "DELISTED_TERMINAL_BBBY" not in passed:
        blockers.append("eodhd_terminal_ohlcv_unverified")
    if "ACTIVE_BASELINE_AAPL" not in passed:
        blockers.append("eodhd_active_ohlcv_unverified")
    decision = "EODHD_MICRO_PROBE_ADMISSIBLE_COMPONENT" if not blockers else "EODHD_MICRO_PROBE_COMPLETE_NOT_ADMISSIBLE"
    return {
        "decision": decision,
        "blockers": blockers,
        "candidate_012_backtest_allowed": False,
        "promotion_allowed": False,
        "next_allowed_action": "probe_sec_edgar_form25_or_fmp_crosscheck" if not blockers else "resolve_eodhd_blockers_or_probe_fmp",
    }


def run_candidate_017_eodhd_micro_probe(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
    client: EodhdClient | None = None,
    run_id: str = RUN_ID,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    api_key_info = _resolve_api_key(gate)
    api_key = api_key_info["api_key"]
    if not api_key:
        decision = build_eodhd_micro_probe_decision(api_key_present=False, checks=[])
        result = _base_result(api_key_info=api_key_info, checks=[], provider_query_performed=False, decision=decision, run_id=run_id)
        _persist(output_dir, result)
        return result
    eodhd = client or UrlLibEodhdClient(api_key)
    checks = _run_checks(eodhd)
    decision = build_eodhd_micro_probe_decision(api_key_present=True, checks=checks)
    result = _base_result(api_key_info=api_key_info, checks=checks, provider_query_performed=True, decision=decision, run_id=run_id)
    _persist(output_dir, result)
    return result


def _run_checks(client: EodhdClient) -> list[dict[str, Any]]:
    return [
        _delisted_list_check(client),
        _eod_check(client, "DELISTED_TERMINAL_BBBY", "BBBY.US", "2023-04-01", "2023-05-10", require_rows=True),
        _eod_check(client, "ACTIVE_BASELINE_AAPL", "AAPL.US", "2020-08-24", "2020-09-04", require_rows=True),
    ]


def _delisted_list_check(client: EodhdClient) -> dict[str, Any]:
    response = client.get_json("/api/exchange-symbol-list/US", {"delisted": "1"})
    summary = summarize_delisted_symbols(response.payload, required_symbol="BBBY")
    ok = response.status_code == 200 and int(summary["row_count"]) > 0 and bool(summary["contains_required_symbol"])
    return {
        "case_id": "DELISTED_LIST_US_BBBY",
        "symbol": "BBBY",
        "endpoint": "/api/exchange-symbol-list/US",
        "http_status": response.status_code,
        "status": "PASS" if ok else "BLOCK",
        "summary": summary,
        "error": response.error,
    }


def _eod_check(client: EodhdClient, case_id: str, symbol: str, start_date: str, end_date: str, *, require_rows: bool) -> dict[str, Any]:
    response = client.get_json(f"/api/eod/{symbol}", {"from": start_date, "to": end_date})
    summary = summarize_eod_rows(response.payload)
    ok = response.status_code == 200
    if require_rows:
        ok = (
            ok
            and int(summary["row_count"]) > 0
            and summary["first_date"] is not None
            and summary["last_date"] is not None
            and bool(summary["has_adjusted_close"])
        )
    return {
        "case_id": case_id,
        "symbol": symbol,
        "endpoint": f"/api/eod/{symbol}",
        "http_status": response.status_code,
        "status": "PASS" if ok else "BLOCK",
        "summary": summary,
        "error": response.error,
    }


def _base_result(
    *,
    api_key_info: dict[str, Any],
    checks: list[dict[str, Any]],
    provider_query_performed: bool,
    decision: dict[str, Any],
    run_id: str,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "provider": "EODHD",
        "decision": decision["decision"],
        "api_key_diagnostics": {
            "api_key": "REDACTED" if api_key_info["api_key"] else "",
            "api_key_present": bool(api_key_info["api_key"]),
            "api_key_fingerprint": _fingerprint(api_key_info["api_key"]),
            "api_key_source_resolved": api_key_info["source"],
            "env_file": api_key_info["env_file"],
        },
        "provider_query_performed": provider_query_performed,
        "market_data_download_performed": False,
        "dataset_build_performed": False,
        "backtest_performed": False,
        "raw_payload_retained": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
        "checks": checks,
        "final_decision": decision,
    }


def _resolve_api_key(gate: dict[str, Any]) -> dict[str, str]:
    env_file = str(gate.get("env_file", ".env"))
    path = Path(env_file)
    for key_name in ("EODHD_API_KEY", "EOD_HISTORICAL_DATA_API_KEY", "EOD_API_KEY"):
        key = _read_env_key(path, key_name)
        if key:
            return {"api_key": key, "source": f"env-file:{key_name}", "env_file": env_file}
    return {"api_key": "", "source": "missing", "env_file": env_file}


def _read_env_key(path: Path, key_name: str) -> str:
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith(f"{key_name}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _validate_gate(gate: dict[str, Any]) -> None:
    required = {
        "provider_query_allowed": True,
        "raw_payload_retention_allowed": False,
        "market_data_download_allowed": False,
        "dataset_build_allowed": False,
        "backtest_allowed": False,
        "promotion_allowed": False,
        "paper_trading_allowed": False,
        "live_trading_allowed": False,
    }
    if gate.get("status") != "APPROVED_EODHD_DATA_MESH_MICRO_PROBE_ONLY":
        raise RuntimeError("Candidate 017 EODHD micro-probe gate is not approved.")
    for key, expected in required.items():
        if gate.get(key) is not expected:
            raise RuntimeError(f"Candidate 017 gate invalid: {key} must be {expected!r}.")
    if int(gate.get("max_http_requests", 0)) > 6:
        raise RuntimeError("Candidate 017 gate invalid: max_http_requests must be <= 6.")


def _persist(output_dir: Path, result: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "eodhd_micro_probe_result.json", result)
    _write_json(output_dir / "final_decision.json", result["final_decision"])
    (output_dir / "eodhd_micro_probe_report.md").write_text(_markdown_report(result), encoding="utf-8")


def _markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# Candidate 017 EODHD Micro-Probe",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: bounded EODHD component probe only. No raw payload retention, no dataset build, no backtest, and no promotion.",
        "",
        "## Checks",
        "",
        "| Case | Symbol | Status | HTTP | Summary |",
        "|---|---|---|---|---|",
    ]
    for check in result.get("checks", []):
        lines.append(
            f"| `{check.get('case_id')}` | `{check.get('symbol')}` | `{check.get('status')}` | "
            f"`{check.get('http_status')}` | `{json.dumps(check.get('summary', {}), sort_keys=True)}` |"
        )
    lines.extend(["", "## Blockers", ""])
    blockers = result["final_decision"].get("blockers", [])
    if blockers:
        lines.extend(f"- `{blocker}`" for blocker in blockers)
    else:
        lines.append("- None for EODHD as component. Candidate 012 still needs a separate fresh-data build gate.")
    return "\n".join(lines) + "\n"


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12] if value else ""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the bounded Candidate 017 EODHD micro-probe.")
    parser.add_argument("--run-id", default=RUN_ID)
    parser.add_argument("--gate-dir", type=Path, default=GATE_DIR)
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    output_dir = args.output_dir or Path("experiments/provider_aware_research/execution_outputs") / args.run_id
    run_candidate_017_eodhd_micro_probe(gate_dir=args.gate_dir, output_dir=output_dir, run_id=args.run_id)
