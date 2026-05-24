from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import median
from typing import Any


RUN_ID = "ACTIVE-ONLY-MOMENTUM-SMOKE-ROBUSTNESS-RUN-001"
TRIAL_ID = "ACTIVE-ONLY-MOMENTUM-SMOKE-ROBUSTNESS-001"
TRADE_PANEL = Path("experiments/provider_aware_research/execution_outputs/ACTIVE-ONLY-MOMENTUM-SMOKE-RUN-001/trade_panel.csv")
OUTPUT_DIR = Path("experiments/provider_aware_research/execution_outputs/ACTIVE-ONLY-MOMENTUM-SMOKE-ROBUSTNESS-RUN-001")
VAULT_REPORT = Path("vault/04-Documentazione/Reports/Report-Active-Only-Momentum-Smoke-Robustness-001-2026-05-24.md")


def run_active_only_momentum_smoke_robustness_001(
    *,
    output_dir: str | Path = OUTPUT_DIR,
    vault_report: str | Path = VAULT_REPORT,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    decision = assess_active_only_momentum_smoke_robustness(TRADE_PANEL)
    _write_json(output / "final_decision.json", decision)
    _write_vault_report(Path(vault_report), decision)
    return decision


def assess_active_only_momentum_smoke_robustness(trade_panel: str | Path) -> dict[str, Any]:
    rows = _read_csv(Path(trade_panel))
    net_returns = [float(row["net_return_500bps"]) for row in rows]
    sorted_returns = sorted(net_returns, reverse=True)
    ex_top3 = sorted_returns[3:] if len(sorted_returns) > 3 else []
    net_sum = sum(net_returns)
    ex_top3_sum = sum(ex_top3)
    return {
        "status": "complete",
        "decision": "ACTIVE_ONLY_MOMENTUM_SMOKE_ROBUSTNESS_COMPLETE_NO_PROMOTION",
        "run_id": RUN_ID,
        "trial_id": TRIAL_ID,
        "source_trade_panel": str(trade_panel),
        "trade_count": len(net_returns),
        "net_return_sum_500bps": round(net_sum, 8),
        "net_return_ex_top3_500bps": round(ex_top3_sum, 8),
        "median_net_return_500bps": round(median(net_returns), 8) if net_returns else 0.0,
        "sign_flip_ex_top3": net_sum > 0 and ex_top3_sum < 0,
        "top3_dependency_flag": net_sum > 0 and ex_top3_sum < 0,
        "provider_query_performed": False,
        "provider_call_count": 0,
        "raw_payload_retained": False,
        "market_data_downloaded": False,
        "backtest_performed": False,
        "parameter_sweep_performed": False,
        "short_selling_performed": False,
        "paper_trading_performed": False,
        "live_trading_performed": False,
        "survivorship_free_claim_allowed": False,
        "active_only_survivorship_bias_declared": True,
        "strategy_promotion_performed": False,
        "promotion_allowed": False,
        "next_unblocked_step": "If top3 dependency is true, treat active-only momentum smoke as fragile exploratory evidence only.",
    }


def validate_active_only_momentum_smoke_robustness_output(output_dir: str | Path = OUTPUT_DIR) -> dict[str, Any]:
    path = Path(output_dir)
    checks: list[dict[str, str]] = []
    _check(checks, "required_file:final_decision.json", (path / "final_decision.json").is_file(), str(path / "final_decision.json"))
    if any(check["status"] == "fail" for check in checks):
        return _report(checks)
    decision = _read_json(path / "final_decision.json")
    _check(checks, "no_provider_query", decision.get("provider_query_performed") is False, str(decision.get("provider_query_performed")))
    _check(checks, "no_backtest", decision.get("backtest_performed") is False, str(decision.get("backtest_performed")))
    _check(checks, "promotion_blocked", decision.get("promotion_allowed") is False, str(decision.get("promotion_allowed")))
    _check(checks, "survivorship_claim_blocked", decision.get("survivorship_free_claim_allowed") is False, str(decision.get("survivorship_free_claim_allowed")))
    return _report(checks)


def _write_vault_report(path: Path, decision: dict[str, Any]) -> None:
    text = (
        "# Report Active-Only Momentum Smoke Robustness 001 - 2026-05-24\n\n"
        f"Decision: `{decision['decision']}`\n\n"
        "## Scope\n\n"
        "No-query robustness diagnostic on the archived active-only momentum smoke trade panel. No new backtest, provider query, execution, or promotion occurred.\n\n"
        "## Result\n\n"
        f"- Trades: {decision['trade_count']}\n"
        f"- Net return sum at 500 bps: {decision['net_return_sum_500bps']}\n"
        f"- Net return ex-top3 at 500 bps: {decision['net_return_ex_top3_500bps']}\n"
        f"- Median net return at 500 bps: {decision['median_net_return_500bps']}\n"
        f"- Sign flip ex-top3: {decision['sign_flip_ex_top3']}\n"
        f"- Promotion allowed: {decision['promotion_allowed']}\n\n"
        "## Interpretation\n\n"
        "This is only an active-only robustness diagnostic. It cannot support a survivorship-free claim or strategy promotion.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _check(checks: list[dict[str, str]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "pass" if condition else "fail", "detail": detail})


def _report(checks: list[dict[str, str]]) -> dict[str, Any]:
    failed = sum(1 for check in checks if check["status"] == "fail")
    return {
        "status": "pass" if failed == 0 else "fail",
        "checks": checks,
        "summary": {"total": len(checks), "passed": len(checks) - failed, "failed": failed},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run active-only momentum smoke robustness 001.")
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--vault-report", default=str(VAULT_REPORT))
    parser.add_argument("--validate-output", action="store_true")
    args = parser.parse_args(argv)
    if args.validate_output:
        report = validate_active_only_momentum_smoke_robustness_output(args.output_dir)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "pass" else 1
    decision = run_active_only_momentum_smoke_robustness_001(output_dir=args.output_dir, vault_report=args.vault_report)
    print(json.dumps(decision, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
