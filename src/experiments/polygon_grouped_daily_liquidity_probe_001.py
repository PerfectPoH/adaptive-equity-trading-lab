from __future__ import annotations

import argparse
import csv
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from src.experiments.polygon_grouped_daily_liquidity_probe_validator import validate_polygon_grouped_daily_liquidity_probe_gate


RUN_ID = "POLYGON-GROUPED-DAILY-LIQUIDITY-PROBE-001"
TRIAL_ID = "UNIVERSE-LIQUIDITY-PROBE-001"
SPEC_DIR = Path("experiments/provider_aware_research/polygon_grouped_daily_liquidity_probe_20260524")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/POLYGON-GROUPED-DAILY-LIQUIDITY-PROBE-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Polygon-Grouped-Daily-Liquidity-Probe-001-2026-05-24.md")


def run_polygon_grouped_daily_liquidity_probe_001(
    *,
    spec_dir: str | Path = SPEC_DIR,
    seed_path: str | Path | None = None,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    gate = validate_polygon_grouped_daily_liquidity_probe_gate(spec_dir)
    _write_json(output / "preflight_report.json", gate)
    if gate["status"] != "pass":
        decision = _blocked_decision("PREREGISTRATION_FAILED", provider_query=False, market_download=False)
        _write_json(output / "final_decision.json", decision)
        return decision

    manifest = json.loads((Path(spec_dir) / "probe_manifest.json").read_text(encoding="utf-8"))
    resolved_seed = Path(seed_path) if seed_path is not None else Path(manifest["seed_input"])
    seed_rows = _read_csv(resolved_seed)
    api_key = _load_polygon_api_key()
    if not api_key:
        assessment = _empty_assessment(["missing_polygon_api_key"], seed_count=len(seed_rows))
        decision = _blocked_decision("BLOCKED_POLYGON_API_KEY_MISSING", provider_query=False, market_download=False)
    else:
        try:
            payload = _fetch_polygon_grouped_daily(api_key, date=str(manifest["grouped_daily_date"]))
            assessment = assess_grouped_daily_liquidity_payload(payload, seed_rows=seed_rows, manifest=manifest)
            decision = _decision(assessment)
        except Exception as exc:  # pragma: no cover - network/entitlement path
            assessment = _empty_assessment(["provider_query_error"], seed_count=len(seed_rows))
            assessment["provider_error"] = f"{type(exc).__name__}: {exc}"
            decision = _blocked_decision("BLOCKED_PROVIDER_ENTITLEMENT_OR_PAYLOAD", provider_query=True, market_download=True)
            decision["provider_error"] = assessment["provider_error"]

    sample = list(assessment.get("liquid_candidate_sample", []))
    _write_csv(output / "liquid_candidate_sample.csv", _fieldnames(sample), sample)
    _write_json(output / "liquidity_assessment.json", assessment)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), assessment, decision)
    return decision


def assess_grouped_daily_liquidity_payload(
    payload: dict[str, Any],
    *,
    seed_rows: list[dict[str, str]],
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    spec = manifest or {
        "grouped_daily_date": "2026-05-22",
        "min_matched_seed_bar_count": 300,
        "min_liquid_candidate_count": 300,
        "min_price": 1.0,
        "min_dollar_volume": 1_000_000,
    }
    bars = payload.get("results", []) if isinstance(payload, dict) else []
    seed_by_ticker = {str(row.get("ticker", "")): row for row in seed_rows if row.get("ticker")}
    bar_by_ticker = {str(row.get("T", "")): row for row in bars if isinstance(row, dict) and row.get("T")}
    joined: list[dict[str, Any]] = []
    liquid: list[dict[str, Any]] = []
    for ticker, seed in seed_by_ticker.items():
        bar = bar_by_ticker.get(ticker)
        if not bar:
            continue
        close = _to_float(bar.get("c"))
        volume = _to_float(bar.get("v"))
        dollar_volume = close * volume
        row = {
            "ticker": ticker,
            "primary_exchange": seed.get("primary_exchange", ""),
            "type": seed.get("type", ""),
            "close": close,
            "volume": volume,
            "dollar_volume": dollar_volume,
            "passes_liquidity_filter": close >= float(spec["min_price"]) and dollar_volume >= float(spec["min_dollar_volume"]),
            "raw_payload_retained": False,
        }
        joined.append(row)
        if row["passes_liquidity_filter"]:
            liquid.append(row)
    blockers: list[str] = []
    if len(joined) < int(spec["min_matched_seed_bar_count"]):
        blockers.append("matched_seed_bar_count_below_300")
    if len(liquid) < int(spec["min_liquid_candidate_count"]):
        blockers.append("liquid_candidate_count_below_300")
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider": "Polygon/Massive",
        "grouped_daily_date": str(spec["grouped_daily_date"]),
        "seed_count": len(seed_rows),
        "provider_bar_count": len(bars),
        "matched_seed_bar_count": len(joined),
        "liquid_candidate_count": len(liquid),
        "min_price": float(spec["min_price"]),
        "min_dollar_volume": float(spec["min_dollar_volume"]),
        "passes_liquidity_probe": len(blockers) == 0,
        "blockers": blockers,
        "liquid_candidate_sample": _derived_rows(liquid[:100]),
        "provider_query_performed": True,
        "raw_payload_retained": False,
        "market_data_downloaded": True,
        "backtest_performed": False,
        "promotion_allowed": False,
        "quality_scope": "single_day_liquidity_availability_only_no_strategy_claim",
    }


def validate_polygon_grouped_daily_liquidity_probe_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    required = ["preflight_report.json", "liquid_candidate_sample.csv", "liquidity_assessment.json", "final_decision.json"]
    _check(checks, "output_dir_exists", path.exists() and path.is_dir(), str(path))
    for filename in required:
        _check(checks, f"required_file:{filename}", (path / filename).is_file(), str(path / filename))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    decision = json.loads((path / "final_decision.json").read_text(encoding="utf-8"))
    assessment = json.loads((path / "liquidity_assessment.json").read_text(encoding="utf-8"))
    sample = _read_csv(path / "liquid_candidate_sample.csv")
    columns = set(sample[0].keys()) if sample else set()
    forbidden = {"api_key", "raw_payload", "raw_json"}
    _check(checks, "raw_payload_not_retained", decision.get("raw_payload_retained") is False and assessment.get("raw_payload_retained") is False, str(decision))
    _check(checks, "market_download_snapshot_only", decision.get("market_data_downloaded") is True, str(decision.get("market_data_downloaded")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "no_promotion", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    _check(checks, "single_day_scope_only", assessment.get("quality_scope") == "single_day_liquidity_availability_only_no_strategy_claim", str(assessment.get("quality_scope")))
    _check(checks, "forbidden_columns_absent", not (columns & forbidden), f"present={sorted(columns & forbidden)}")
    return _report(checks)


def _load_polygon_api_key(env_path: str | Path = ".env") -> str:
    value = os.environ.get("POLYGON_API_KEY", "").strip()
    if value:
        return value
    path = Path(env_path)
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("POLYGON_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def _fetch_polygon_grouped_daily(api_key: str, *, date: str) -> dict[str, Any]:
    query = urllib.parse.urlencode({"adjusted": "true", "apiKey": api_key})
    request = urllib.request.Request(
        f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{date}?{query}",
        headers={"Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _decision(assessment: dict[str, Any]) -> dict[str, Any]:
    passed = bool(assessment.get("passes_liquidity_probe"))
    return {
        "status": "complete",
        "decision": "POLYGON_GROUPED_DAILY_LIQUIDITY_PASS" if passed else "POLYGON_GROUPED_DAILY_LIQUIDITY_BLOCKED",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "grouped_daily_date": assessment.get("grouped_daily_date"),
        "seed_count": assessment.get("seed_count", 0),
        "matched_seed_bar_count": assessment.get("matched_seed_bar_count", 0),
        "liquid_candidate_count": assessment.get("liquid_candidate_count", 0),
        "blockers": assessment.get("blockers", []),
        "provider_query_performed": True,
        "raw_payload_retained": False,
        "market_data_downloaded": True,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
        "next_unblocked_step": "If pass, preregister survivorship/delisted audit before any broad-universe strategy backtest.",
    }


def _blocked_decision(reason: str, *, provider_query: bool, market_download: bool) -> dict[str, Any]:
    return {
        "status": "blocked",
        "decision": reason,
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider_query_performed": provider_query,
        "raw_payload_retained": False,
        "market_data_downloaded": market_download,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
    }


def _empty_assessment(blockers: list[str], *, seed_count: int) -> dict[str, Any]:
    return {
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "provider": "Polygon/Massive",
        "grouped_daily_date": "",
        "seed_count": seed_count,
        "provider_bar_count": 0,
        "matched_seed_bar_count": 0,
        "liquid_candidate_count": 0,
        "min_price": 1.0,
        "min_dollar_volume": 1_000_000,
        "passes_liquidity_probe": False,
        "blockers": blockers,
        "liquid_candidate_sample": [],
        "provider_query_performed": False,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "promotion_allowed": False,
        "quality_scope": "single_day_liquidity_availability_only_no_strategy_claim",
    }


def _derived_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "ticker": str(row.get("ticker", "")),
            "primary_exchange": str(row.get("primary_exchange", "")),
            "type": str(row.get("type", "")),
            "close": f"{float(row.get('close', 0)):.6f}",
            "volume": f"{float(row.get('volume', 0)):.0f}",
            "dollar_volume": f"{float(row.get('dollar_volume', 0)):.2f}",
            "passes_liquidity_filter": str(bool(row.get("passes_liquidity_filter", False))),
            "raw_payload_retained": False,
        }
        for row in rows
    ]


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _write_vault_report(path: Path, assessment: dict[str, Any], decision: dict[str, Any]) -> None:
    text = (
        "# Report Polygon Grouped Daily Liquidity Probe 001 - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "Single Polygon grouped-daily market-data call for one date, joined to the active universe seed. No historical panel, strategy backtest, parameter sweep, paper/live trading, short selling, or promotion occurred.\n\n"
        "## Result\n\n"
        f"- Date: {assessment['grouped_daily_date']}\n"
        f"- Seed count: {assessment['seed_count']}\n"
        f"- Provider bar count: {assessment['provider_bar_count']}\n"
        f"- Matched seed bars: {assessment['matched_seed_bar_count']}\n"
        f"- Liquid candidates: {assessment['liquid_candidate_count']}\n"
        f"- Blockers: {', '.join(decision.get('blockers', []))}\n\n"
        "## Interpretation\n\n"
        "This probe only measures single-day daily-bar availability and coarse liquidity. It does not create alpha evidence and does not authorize any strategy backtest.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _fieldnames(rows: list[dict[str, Any]]) -> list[str]:
    return list(rows[0].keys()) if rows else []


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        if not fieldnames:
            handle.write("\n")
            return
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "gate_decision": "POLYGON_GROUPED_DAILY_LIQUIDITY_PROBE_OUTPUT_PASS" if failed == 0 else "POLYGON_GROUPED_DAILY_LIQUIDITY_PROBE_OUTPUT_FAIL",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Polygon grouped daily liquidity probe.")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args(argv)
    if not args.validate_only:
        run_polygon_grouped_daily_liquidity_probe_001()
    report = validate_polygon_grouped_daily_liquidity_probe_output()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
