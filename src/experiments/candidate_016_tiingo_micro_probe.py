from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol


RUN_ID = "CANDIDATE-016-TIINGO-MICRO-PROBE-001"
GATE_DIR = Path("experiments/provider_aware_research/candidate_016_tiingo_micro_probe_gate_20260607")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs") / RUN_ID


@dataclass(frozen=True)
class FakeTiingoResponse:
    status_code: int
    payload: Any
    error: str = ""


class TiingoClient(Protocol):
    def get_json(self, endpoint: str, params: dict[str, str]) -> FakeTiingoResponse:
        ...


class UrlLibTiingoClient:
    BASE_URL = "https://api.tiingo.com"

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def get_json(self, endpoint: str, params: dict[str, str]) -> FakeTiingoResponse:
        query = dict(params)
        query["token"] = self._api_key
        url = f"{self.BASE_URL}{endpoint}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "adaptive-equity-trading-lab/tiingo-micro-probe"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return FakeTiingoResponse(status_code=int(response.status), payload=payload)
        except urllib.error.HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode("utf-8"))
            except Exception:
                payload = {}
            return FakeTiingoResponse(status_code=int(exc.code), payload=payload, error=str(exc))
        except Exception as exc:
            return FakeTiingoResponse(status_code=0, payload={}, error=f"{type(exc).__name__}: {exc}")


def summarize_price_rows(rows: Any) -> dict[str, Any]:
    if not isinstance(rows, list):
        return {"row_count": 0, "has_adjusted_close": False, "first_date": None, "last_date": None, "non_unit_split_factor_count": 0}
    dates: list[str] = []
    has_adjusted_close = False
    non_unit_split_count = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        date = str(row.get("date", ""))[:10]
        if date:
            dates.append(date)
        has_adjusted_close = has_adjusted_close or ("adjClose" in row or "adjclose" in {str(key).lower() for key in row})
        try:
            split = float(row.get("splitFactor", row.get("splitfactor", 1.0)))
        except (TypeError, ValueError):
            split = 1.0
        if abs(split - 1.0) > 1e-12:
            non_unit_split_count += 1
    return {
        "row_count": len(rows),
        "has_adjusted_close": bool(has_adjusted_close),
        "first_date": min(dates) if dates else None,
        "last_date": max(dates) if dates else None,
        "non_unit_split_factor_count": int(non_unit_split_count),
    }


def build_tiingo_micro_probe_decision(*, api_key_present: bool, checks: list[dict[str, Any]]) -> dict[str, Any]:
    if not api_key_present:
        return {
            "decision": "TIINGO_MICRO_PROBE_BLOCKED_API_KEY_MISSING",
            "blockers": ["tiingo_api_key_missing"],
            "candidate_012_backtest_allowed": False,
            "promotion_allowed": False,
            "next_allowed_action": "add_tiingo_api_key_then_commit_rerun_gate",
        }
    passed = {str(check.get("case_id")) for check in checks if check.get("status") == "PASS"}
    blockers: list[str] = []
    if "ACTIVE_BASELINE_AAPL" not in passed:
        blockers.append("tiingo_active_ohlcv_unverified")
    if "SPLIT_AAPL_2020" not in passed:
        blockers.append("tiingo_corporate_action_split_unverified")
    if "TICKER_CHANGE_FB_META" not in passed:
        blockers.append("tiingo_identity_continuity_unverified")
    if "DELISTING_BBBY" not in passed:
        blockers.append("tiingo_delisted_coverage_unverified")
    decision = "TIINGO_MICRO_PROBE_ADMISSIBLE_COMPONENT" if not blockers else "TIINGO_MICRO_PROBE_COMPLETE_NOT_ADMISSIBLE"
    return {
        "decision": decision,
        "blockers": blockers,
        "candidate_012_backtest_allowed": False,
        "promotion_allowed": False,
        "next_allowed_action": "probe_next_provider_component" if not blockers else "resolve_tiingo_blockers_or_probe_eodhd",
    }


def run_candidate_016_tiingo_micro_probe(
    *,
    gate_dir: Path = GATE_DIR,
    output_dir: Path = OUTPUT_DIR,
    client: TiingoClient | None = None,
) -> dict[str, Any]:
    gate = _read_json(gate_dir / "gate_manifest.json")
    _validate_gate(gate)
    api_key_info = _resolve_api_key(gate)
    api_key = api_key_info["api_key"]
    if not api_key:
        decision = build_tiingo_micro_probe_decision(api_key_present=False, checks=[])
        result = _base_result(api_key_info=api_key_info, checks=[], provider_query_performed=False, decision=decision)
        _persist(output_dir, result)
        return result
    tiingo = client or UrlLibTiingoClient(api_key)
    checks = _run_checks(tiingo)
    decision = build_tiingo_micro_probe_decision(api_key_present=True, checks=checks)
    result = _base_result(api_key_info=api_key_info, checks=checks, provider_query_performed=True, decision=decision)
    _persist(output_dir, result)
    return result


def _run_checks(client: TiingoClient) -> list[dict[str, Any]]:
    checks = [
        _metadata_check(client, "ACTIVE_BASELINE_AAPL", "AAPL"),
        _price_check(client, "SPLIT_AAPL_2020", "AAPL", "2020-08-24", "2020-09-04", require_split=True),
        _search_check(client, "TICKER_CHANGE_FB_META", "META", required_ticker="META"),
        _price_check(client, "DELISTING_BBBY", "BBBY", "2023-04-01", "2023-05-10", require_rows=True),
        _price_check(client, "BENCHMARK_SPY_IWM_SPY", "SPY", "2018-01-01", "2018-01-10", require_rows=True),
        _price_check(client, "BENCHMARK_SPY_IWM_IWM", "IWM", "2018-01-01", "2018-01-10", require_rows=True),
    ]
    return checks


def _metadata_check(client: TiingoClient, case_id: str, symbol: str) -> dict[str, Any]:
    response = client.get_json(f"/tiingo/daily/{symbol}", {})
    payload = response.payload if isinstance(response.payload, dict) else {}
    status = "PASS" if response.status_code == 200 and payload.get("ticker") else "BLOCK"
    return {
        "case_id": case_id,
        "symbol": symbol,
        "endpoint": f"/tiingo/daily/{symbol}",
        "http_status": response.status_code,
        "status": status,
        "summary": {
            "ticker_present": bool(payload.get("ticker")),
            "start_date": payload.get("startDate"),
            "end_date": payload.get("endDate"),
            "field_names": sorted(str(key) for key in payload.keys())[:20],
        },
        "error": response.error,
    }


def _price_check(
    client: TiingoClient,
    case_id: str,
    symbol: str,
    start_date: str,
    end_date: str,
    *,
    require_split: bool = False,
    require_rows: bool = False,
) -> dict[str, Any]:
    response = client.get_json(
        f"/tiingo/daily/{symbol}/prices",
        {"startDate": start_date, "endDate": end_date, "format": "json"},
    )
    summary = summarize_price_rows(response.payload)
    ok = response.status_code == 200
    if require_rows:
        ok = ok and int(summary["row_count"]) > 0
    if require_split:
        ok = ok and int(summary["non_unit_split_factor_count"]) > 0 and bool(summary["has_adjusted_close"])
    return {
        "case_id": case_id,
        "symbol": symbol,
        "endpoint": f"/tiingo/daily/{symbol}/prices",
        "http_status": response.status_code,
        "status": "PASS" if ok else "BLOCK",
        "summary": summary,
        "error": response.error,
    }


def _search_check(client: TiingoClient, case_id: str, query: str, *, required_ticker: str) -> dict[str, Any]:
    response = client.get_json("/tiingo/utilities/search", {"query": query})
    payload = response.payload if isinstance(response.payload, list) else []
    tickers = [str(row.get("ticker", "")) for row in payload if isinstance(row, dict)]
    status = "PASS" if response.status_code == 200 and required_ticker in tickers else "BLOCK"
    return {
        "case_id": case_id,
        "symbol": query,
        "endpoint": "/tiingo/utilities/search",
        "http_status": response.status_code,
        "status": status,
        "summary": {"result_count": len(payload), "contains_required_ticker": required_ticker in tickers, "sample_tickers": tickers[:10]},
        "error": response.error,
    }


def _base_result(
    *,
    api_key_info: dict[str, Any],
    checks: list[dict[str, Any]],
    provider_query_performed: bool,
    decision: dict[str, Any],
) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "provider": "Tiingo",
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
    key = ""
    path = Path(env_file)
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("TIINGO_API_KEY="):
                key = line.split("=", 1)[1].strip().strip('"').strip("'")
                break
    return {"api_key": key, "source": "env-file" if key else "missing", "env_file": env_file}


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
    if gate.get("status") != "APPROVED_TIINGO_DATA_MESH_MICRO_PROBE_ONLY":
        raise RuntimeError("Candidate 016 Tiingo micro-probe gate is not approved.")
    for key, expected in required.items():
        if gate.get(key) is not expected:
            raise RuntimeError(f"Candidate 016 gate invalid: {key} must be {expected!r}.")
    if int(gate.get("max_http_requests", 0)) > 8:
        raise RuntimeError("Candidate 016 gate invalid: max_http_requests must be <= 8.")


def _persist(output_dir: Path, result: dict[str, Any]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "tiingo_micro_probe_result.json", result)
    _write_json(output_dir / "final_decision.json", result["final_decision"])
    (output_dir / "tiingo_micro_probe_report.md").write_text(_markdown_report(result), encoding="utf-8")


def _markdown_report(result: dict[str, Any]) -> str:
    lines = [
        "# Candidate 016 Tiingo Micro-Probe",
        "",
        f"Decision: `{result['decision']}`",
        "",
        "Scope: bounded Tiingo component probe only. No raw payload retention, no dataset build, no backtest, and no promotion.",
        "",
        "## Checks",
        "",
        "| Case | Symbol | Status | HTTP | Summary |",
        "|---|---|---|---|---|",
    ]
    for check in result.get("checks", []):
        summary = json.dumps(check.get("summary", {}), sort_keys=True)
        lines.append(f"| `{check.get('case_id')}` | `{check.get('symbol')}` | `{check.get('status')}` | `{check.get('http_status')}` | `{summary}` |")
    lines.extend(["", "## Blockers", ""])
    blockers = result["final_decision"].get("blockers", [])
    if blockers:
        lines.extend(f"- `{blocker}`" for blocker in blockers)
    else:
        lines.append("- None for Tiingo as component. Candidate 012 still needs a separate fresh-data build gate.")
    return "\n".join(lines) + "\n"


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12] if value else ""


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    run_candidate_016_tiingo_micro_probe()
